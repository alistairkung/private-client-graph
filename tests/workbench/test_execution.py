"""Version compatibility and real deterministic runner/pipeline/evaluator acceptance."""
import json
import shutil

import pytest

from private_client_graph.research.demo import recorded_response
from private_client_graph.research.runner import execute
from private_client_graph.workbench.artifacts import read_artifact
from private_client_graph.workbench.execution_contracts import Command, Proposal
from private_client_graph.workbench.planning import freeze, open_executable, preview
from private_client_graph.workbench.supervisor import event, start, status


def proposal(**values):
    return Proposal.model_validate({'input_ids': ['case_03_fixture'], **values})


def test_replay_real_pipeline_and_evidence(tmp_path):
    plan = freeze(tmp_path, proposal())
    bundle, _ = open_executable(tmp_path, plan.id)
    def forbidden(request):
        pytest.fail('Replay dispatched a provider')
    execute(bundle, provider=forbidden)
    detail = read_artifact(bundle.path, plan.id)
    assert bundle.manifest['schema_version'] == 2
    assert detail.history.integrity == 'verified'
    assert detail.history.scored == detail.history.planned
    assert detail.history.planned == 1
    assert bundle.attempt_count == 0
    assert detail.samples[0].observations[0].evaluation is not None
    assert any(r.expected for r in detail.samples[0].observations[0].relationships)


@pytest.mark.parametrize('changes', [
    {'input_ids': ['../../source']}, {'input_ids': ['case_03_fixture'] * 2},
    {'execution_mode': 'live'}, {'resolver': 'generative'},
    {'extraction_samples': 2}, {'resolver_repetitions': 2},
    {'input_mode': 'fresh'}, {'invocation_cap': 1},
    {'input_mode': 'fresh', 'execution_mode': 'recorded', 'input_ids': ['case_01_fixture'], 'invocation_cap': 1},
])
def test_invalid_finite_matrix(changes):
    with pytest.raises(ValueError):
        preview(proposal(**changes))


def test_fresh_samples_separate_from_resolver_repetitions(tmp_path):
    request = proposal(input_mode='fresh', execution_mode='recorded', resolver='generative',
                       extraction_samples=2, resolver_repetitions=3, invocation_cap=8)
    reviewed = preview(request)
    assert (reviewed.extraction_call_maximum, reviewed.resolution_call_maximum, reviewed.matrix_call_maximum) == (2, 6, 8)
    assert reviewed.planned_observations == 8
    assert reviewed.task_paid_remaining == 0
    frozen = freeze(tmp_path, request)
    bundle, _ = open_executable(tmp_path, frozen.id)
    execute(bundle, provider=recorded_response)
    assert bundle.attempt_count == 8
    assert len(bundle.results()) == 8
    assert len(list((bundle.path / 'fresh_inputs').glob('*.json'))) == 2
    requests = bundle.attempts()
    assert all('truth' not in attempt['request'] for attempt in requests)
    for sample in ('fresh_01', 'fresh_02'):
        resolutions = [a['request']['extraction'] for a in requests if a['attempt_id'].startswith(sample + '-resolve')]
        assert resolutions[0] == resolutions[1] == resolutions[2]
    assert read_artifact(bundle.path, frozen.id).history.scored == 8


def test_stop_and_uncertain_attempt_never_reissued(tmp_path):
    plan = freeze(tmp_path, proposal(execution_mode='recorded', resolver='generative', resolver_repetitions=3, invocation_cap=3))
    bundle, _ = open_executable(tmp_path, plan.id)
    requests = []
    def provider(request):
        requests.append(request)
        return recorded_response(request)
    execute(bundle, provider=provider, should_stop=lambda: len(requests) == 1)
    assert bundle.attempt_count == 1
    assert len(bundle.results()) == 2
    # A crash leaves an uncertain durable reservation. Continuation must not call it again.
    bundle.reserve('case_03_fixture-resolve-2', requests[0].model_dump(mode='json'))
    execute(bundle, provider=provider)
    assert len(requests) == 2
    assert bundle.attempt_count == 3
    assert next(r for r in bundle.results() if r['repetition'] == 2)['status'] == 'uncertain'


def test_accounting_relocation_and_recording_mismatches(tmp_path):
    plan = freeze(tmp_path, proposal())
    bundle, _ = open_executable(tmp_path, plan.id)
    other = tmp_path / 'other'
    shutil.copytree(bundle.path, other / plan.id)
    with pytest.raises(ValueError, match='relocation'):
        open_executable(other, plan.id)
    ledger = bundle.task_ledger / 'offline.json'
    contents = ledger.read_text()
    ledger.unlink()
    with pytest.raises(FileNotFoundError):
        open_executable(tmp_path, plan.id)
    ledger.write_text(contents)
    (bundle.path / 'recorded-responses.json').write_text('{}')
    with pytest.raises(ValueError, match='responses changed'):
        open_executable(tmp_path, plan.id)


def test_restart_reconciles_without_resuming(tmp_path, monkeypatch):
    plan = freeze(tmp_path, proposal())
    bundle, _ = open_executable(tmp_path, plan.id)
    event(bundle, 'running', 'started', 'old')
    monkeypatch.setattr('subprocess.Popen', lambda *a, **kw: pytest.fail('Automatic resume'))
    state = status(tmp_path, plan.id)
    assert state.state == 'interrupted'
    assert state.completed_observations == 0
    with pytest.raises(ValueError, match='continuation'):
        start(tmp_path, plan.id, Command(request_id='start', plan_digest=plan.digest))


@pytest.mark.parametrize('key', ['code', 'dependencies'])
def test_resume_rejects_changed_provenance(tmp_path, monkeypatch, key):
    plan = freeze(tmp_path, proposal())
    symbol = 'code_snapshot' if key == 'code' else 'dependency_versions'
    monkeypatch.setattr(f'private_client_graph.research.runner.{symbol}', lambda: {})
    with pytest.raises(ValueError, match='changed since'):
        start(tmp_path, plan.id, Command(request_id='first', plan_digest=plan.digest))


def test_execution_code_mismatch(tmp_path, monkeypatch):
    plan = freeze(tmp_path, proposal())
    monkeypatch.setattr('private_client_graph.workbench.planning.execution_code_digest', lambda: 'changed')
    with pytest.raises(ValueError, match='Execution code changed'):
        open_executable(tmp_path, plan.id)


def test_command_publication_crash_needs_continuation(tmp_path):
    from private_client_graph.research.artifacts import write_json_once
    from private_client_graph.workbench.supervisor import reconcile
    frozen = freeze(tmp_path, proposal())
    command = Command(request_id='published', plan_digest=frozen.digest)
    write_json_once(tmp_path / frozen.id / 'commands/published.json',
                    {**command.model_dump(), 'continuation': False})
    reconcile(tmp_path)
    assert status(tmp_path, frozen.id).state == 'interrupted'
    with pytest.raises(ValueError, match='continuation'):
        start(tmp_path, frozen.id, Command(request_id='new', plan_digest=frozen.digest))


def test_frozen_input_and_model_settings_survive_repository_changes(tmp_path, monkeypatch):
    frozen = freeze(tmp_path, proposal(temperature=.4, timeout_seconds=30))
    before, _ = open_executable(tmp_path, frozen.id)
    monkeypatch.setattr('private_client_graph.workbench.planning.load_inputs', lambda: [])
    after, _ = open_executable(tmp_path, frozen.id)
    assert before.plan.inputs == after.plan.inputs
    assert after.plan.settings.temperature == .4
    assert after.plan.settings.timeout_seconds == 30


def test_plan_digest_binds_preview_and_recorded_execution_provenance(tmp_path):
    frozen = freeze(tmp_path, proposal())
    binding = tmp_path / frozen.id / 'execution-binding.json'
    changed = json.loads(binding.read_text())
    changed['execution_code_digest'] = 'changed'
    binding.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='digest mismatch'):
        open_executable(tmp_path, frozen.id)


def test_execution_dependency_mismatch(tmp_path, monkeypatch):
    frozen = freeze(tmp_path, proposal())
    monkeypatch.setattr('private_client_graph.workbench.planning.execution_dependencies', lambda: {})
    with pytest.raises(ValueError, match='Execution dependencies changed'):
        open_executable(tmp_path, frozen.id)


def test_read_index_rejects_corrupt_execution_binding(tmp_path):
    frozen = freeze(tmp_path, proposal())
    binding = tmp_path / frozen.id / 'execution-binding.json'
    binding.write_text('{}')
    detail = read_artifact(binding.parent, frozen.id)
    assert detail.history.integrity == 'corrupt'
    assert not detail.samples
