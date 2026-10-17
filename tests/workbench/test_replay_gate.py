"""Authorization requires an exact zero-call control before retained resolver treatment."""
import json

import pytest

from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.research.provider import ModelResponse
from private_client_graph.research.runner import execute
from private_client_graph.workbench.approval import authorize
from private_client_graph.workbench.case_catalog import repository_inputs
from private_client_graph.workbench.execution_contracts import LiveApproval
from private_client_graph.workbench.planning import live_budget, open_executable
from private_client_graph.workbench.run_planning import freeze_run
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate, FreezeRun, RunConfiguration
from private_client_graph.workbench.workspaces import create_experiment, update_draft


def approve(root, frozen, request_id='approve'):
    budget = live_budget(root)
    request = LiveApproval(request_id=request_id, plan_digest=frozen.digest,
        task_id=frozen.task_id, expected_task_usage=budget.used, expected_task_cap=budget.cap,
        task_cap=frozen.preview.proposal.task_call_cap, approved=True)
    bundle, _ = open_executable(root, frozen.id)
    authorize(bundle, frozen, request, 'http://localhost')
    bundle.authorization_id = request_id
    return bundle


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    initialize_task(tmp_path, 'Substituted retained comparison')
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='create', name='Paired replay'))
    config = RunConfiguration(input_ids=['case_01_fixture'], input_mode='fresh',
        execution_mode='live', invocation_cap=1, task_call_cap=30)
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='draft', expected_revision=0, configuration=config))
    original = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='original', expected_revision=1))
    sample = next(item for item in repository_inputs() if item.sample_id == 'case_01_fixture')
    payload = sample.sourced_extraction.model_dump()
    payload['relationships'] = payload['relationships'][:1]
    bundle = approve(tmp_path, original)
    execute(bundle, live=True, provider=lambda request: ModelResponse(payload=payload))
    complete(bundle)
    return tmp_path, workspace, original


def complete(bundle):
    write_json_once(bundle.path / 'lifecycle' / 'complete.json',
        {'at': '2026-10-17T00:00:00+00:00', 'state': 'complete'})


def retained_run(experiment, *, resolver='none', request_id='control', **changes):
    root, workspace, original = experiment
    from private_client_graph.workbench.workspaces import read_experiment
    revision = read_experiment(root, workspace.id).draft.revision
    values = dict(input_ids=['case_01_fixture_fresh_01'], input_mode='saved',
        retained_experiment_id=workspace.id, retained_run_id=original.id)
    if resolver == 'generative':
        values.update(execution_mode='live', resolver='generative', invocation_cap=1, task_call_cap=30)
    config = RunConfiguration(**(values | changes))
    update_draft(root, workspace.id, DraftUpdate(request_id=f'draft-{request_id}',
        expected_revision=revision, configuration=config))
    return freeze_run(root, workspace.id, FreezeRun(request_id=request_id, expected_revision=revision + 1))


def test_retained_resolver_requires_completed_control_before_authorization(experiment):
    root, _, _ = experiment
    treatment = retained_run(experiment, resolver='generative', request_id='treatment')
    before = live_budget(root).used
    with pytest.raises(ValueError, match='control'):
        approve(root, treatment)
    assert live_budget(root).used == before == 1
    assert not list((root / treatment.id / 'authorizations').glob('*.json'))


def completed_control(experiment):
    root, _, _ = experiment
    frozen = retained_run(experiment)
    bundle = Bundle.open(root / frozen.id)
    execute(bundle, provider=lambda request: pytest.fail('Replay invoked provider'))
    complete(bundle)
    return frozen


def test_exact_control_authorizes_and_binds_immutable_evidence(experiment, monkeypatch):
    from private_client_graph.workbench.artifacts import artifact_digest

    root, _, original = experiment
    original_digest = artifact_digest(root / original.id)
    control = completed_control(experiment)
    treatment = retained_run(experiment, resolver='generative', request_id='treatment')
    bundle = approve(root, treatment)
    gate = json.loads((bundle.path / 'replay-gates' / 'approve.json').read_text())
    assert gate['control_run_id'] == control.id
    assert gate['original_artifact_digest'] == original_digest
    assert gate['matched_samples'] == 1
    assert live_budget(root).used == 1
    authority = json.loads((bundle.path / 'authorizations' / 'approve.json').read_text())
    assert authority['replay_gate_digest']
    # Starting rechecks retained files, not just a previous authorization.
    write_json_once(root / control.id / 'unexpected.json', {'altered': True})
    from private_client_graph.workbench.execution_contracts import Command
    from private_client_graph.workbench.workspace_execution import start_run
    from private_client_graph.workbench import supervisor
    monkeypatch.setattr(supervisor, '_launch_worker', lambda *args: pytest.fail('Changed control launched worker'))
    with pytest.raises(ValueError, match='changed after authorization'):
        start_run(root, treatment.id, Command(request_id='approve', plan_digest=treatment.digest),
            origin='http://localhost')
    assert artifact_digest(root / original.id) == original_digest


def test_changed_control_graph_cannot_authorize(experiment):
    root, _, _ = experiment
    control = completed_control(experiment)
    result_path = next((root / control.id / 'results').glob('*.json'))
    row = json.loads(result_path.read_text())
    row['graph']['relationships'] = []
    result_path.write_text(json.dumps(row))
    treatment = retained_run(experiment, resolver='generative', request_id='treatment')
    with pytest.raises(ValueError, match='control'):
        approve(root, treatment)
    assert live_budget(root).used == 1


@pytest.mark.parametrize('changes', [{'temperature': 0.2}, {'resolver_repetitions': 2, 'invocation_cap': 2}])
def test_treatment_settings_and_repetition_are_fixed(experiment, changes):
    root, _, _ = experiment
    completed_control(experiment)
    treatment = retained_run(experiment, resolver='generative', request_id='treatment', **changes)
    with pytest.raises(ValueError, match='settings or task'):
        approve(root, treatment)
    assert live_budget(root).used == 1


def test_original_mutation_after_freeze_blocks_authorization(experiment):
    root, _, original = experiment
    completed_control(experiment)
    treatment = retained_run(experiment, resolver='generative', request_id='treatment')
    write_json_once(root / original.id / 'unexpected.json', {'altered': True})
    with pytest.raises(ValueError, match='frozen original'):
        approve(root, treatment)
    assert live_budget(root).used == 1


def test_ten_snapshot_controls_pair_and_treatment_never_reextracts(tmp_path, monkeypatch):
    from private_client_graph.workbench.run_evaluation import compare_runs, evaluate_run
    from private_client_graph.workbench.workspaces import read_experiment

    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    initialize_task(tmp_path, 'Ten substituted observations, no paid provider')
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='create', name='Ten paired observations'))
    templates = [sample for sample in repository_inputs()
        if sample.sample_id in {f'case_{index:02d}_fixture' for index in range(1, 6)}]
    config = RunConfiguration(input_ids=[sample.sample_id for sample in templates], input_mode='fresh',
        extraction_samples=2, execution_mode='live', invocation_cap=10, task_call_cap=30)
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='original-draft', expected_revision=0, configuration=config))
    original = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='original', expected_revision=1))
    bundle = approve(tmp_path, original)
    templates_by_source = {sample.source: sample for sample in templates}
    seen = {}
    def extraction(request):
        assert request.stage == 'extraction'
        seen[request.source] = seen.get(request.source, 0) + 1
        payload = templates_by_source[request.source].sourced_extraction.model_dump()
        # Distinct retained outputs per Case make all ten exact inputs uniquely pairable.
        payload['relationships'] = payload['relationships'][:seen[request.source] - 1]
        return ModelResponse(payload=payload)
    execute(bundle, live=True, provider=extraction)
    complete(bundle)
    input_ids = [slot.sample_id for slot in bundle.plan.planned_slots]
    def freeze_saved(name, **changes):
        revision = read_experiment(tmp_path, workspace.id).draft.revision
        values = dict(input_ids=input_ids, input_mode='saved', retained_experiment_id=workspace.id,
            retained_run_id=original.id)
        update_draft(tmp_path, workspace.id, DraftUpdate(request_id=f'draft-{name}', expected_revision=revision,
            configuration=RunConfiguration(**(values | changes))))
        return freeze_run(tmp_path, workspace.id, FreezeRun(request_id=name, expected_revision=revision + 1))
    control = freeze_saved('control')
    control_bundle = Bundle.open(tmp_path / control.id)
    execute(control_bundle, provider=lambda request: pytest.fail('Control called provider'))
    complete(control_bundle)
    treatment = freeze_saved('treatment', execution_mode='live', resolver='generative',
        invocation_cap=10, task_call_cap=30)
    treatment_bundle = approve(tmp_path, treatment)
    requests = []
    def resolver(request):
        requests.append(request)
        assert request.stage == 'resolution'
        if len(requests) == 1:
            raise RuntimeError('Substituted provider failure')
        return ModelResponse(payload={'edits': []})
    execute(treatment_bundle, live=True, provider=resolver)
    complete(treatment_bundle)
    comparison = compare_runs(control_bundle, treatment_bundle)
    assert comparison.matched_inputs == len(comparison.pairs) == 10
    assert comparison.comparable_scope and not comparison.exclusions
    assert len(requests) == 10
    assert all(attempt['request']['stage'] == 'resolution' for attempt in treatment_bundle.attempts())
    assert treatment_bundle.attempt_count == 10 and control_bundle.attempt_count == 0
    coverage = evaluate_run(treatment_bundle).aggregate.coverage
    assert coverage.planned == 10 and coverage.scored == 9 and coverage.failed == 1
    assert live_budget(tmp_path).used == 20


def test_unrelated_corrupt_run_does_not_hide_a_valid_control(experiment):
    root, _, _ = experiment
    unrelated = retained_run(experiment, request_id='unrelated')
    (root / unrelated.id / 'manifest-checksum.json').write_text('"corrupt"')
    control = completed_control(experiment)
    treatment = retained_run(experiment, resolver='generative', request_id='treatment')
    bundle = approve(root, treatment)
    gate = json.loads((bundle.path / 'replay-gates' / 'approve.json').read_text())
    assert gate['control_run_id'] == control.id
    assert live_budget(root).used == 1
