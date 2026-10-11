"""Single-configuration runs freeze every intended observation before dispatch."""
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.run_plan import RunPlan


def test_saved_run_freezes_only_selected_configuration_slots():
    plan = RunPlan(inputs=load_inputs()[:3], resolver='generative',
        execution_mode='recorded', repetitions=2, max_calls=6, invocation_cap=6)
    assert plan.maximum_attempts == 6
    assert [slot.observation_id for slot in plan.planned_slots] == [
        'case_01_fixture-resolve-1', 'case_01_fixture-resolve-2',
        'case_02_fixture-resolve-1', 'case_02_fixture-resolve-2',
        'case_03_fixture-resolve-1', 'case_03_fixture-resolve-2']
    assert {slot.configuration for slot in plan.planned_slots} == {'generative_full_source'}


def test_execute_selected_resolver_preserves_single_configuration(tmp_path):
    import json
    from private_client_graph.research.artifacts import Bundle
    from private_client_graph.research.provider import ModelResponse
    from private_client_graph.research.runner import execute

    plan = RunPlan(inputs=load_inputs()[:1], resolver='generative',
        execution_mode='recorded', repetitions=1, max_calls=1, invocation_cap=1)
    bundle = Bundle.create(tmp_path / 'run', plan, task_ledger=tmp_path / 'ledger')
    execute(bundle, provider=lambda request: ModelResponse(payload={'edits': []}))
    results = [json.loads(path.read_text()) for path in (bundle.path / 'results').glob('*.json')]
    assert len(results) == 1
    assert results[0]['configuration'] == 'generative_full_source'
    assert results[0]['evaluation']['f1'] == 1.0
    assert isinstance(Bundle.open(bundle.path).plan, RunPlan)


def test_fresh_runs_plan_all_cases_and_retain_failed_membership(tmp_path):
    import json
    from private_client_graph.research.artifacts import Bundle
    from private_client_graph.research.provider import ModelResponse
    from private_client_graph.research.runner import execute

    samples = load_inputs()[:2]
    plan = RunPlan(inputs=samples, input_mode='fresh', fresh_extractions=2,
        execution_mode='recorded', resolver='generative', repetitions=1,
        max_calls=8, invocation_cap=8)
    assert len(plan.planned_slots) == 4
    bundle = Bundle.create(tmp_path / 'run', plan, task_ledger=tmp_path / 'ledger')
    def provider(request):
        if request.stage == 'resolution':
            return ModelResponse(payload={'edits': []})
        if request.source == samples[1].source:
            raise RuntimeError('Substituted provider failure')
        return ModelResponse(payload=samples[0].extraction.model_dump())
    execute(bundle, provider=provider)
    results = [json.loads(path.read_text()) for path in (bundle.path / 'results').glob('*.json')]
    assert len(results) == 4
    assert {result['configuration'] for result in results} == {'generative_full_source'}
    assert sum(result['evaluation'] is not None for result in results) == 2
    assert len(Bundle.open(bundle.path).plan.planned_slots) == 4
    assert bundle.attempt_count == 6
    execute(bundle, provider=provider)
    assert bundle.attempt_count == 6


def test_catalog_keeps_case_names_distinct_from_diagnostic_fixture_names():
    from private_client_graph.workbench.case_catalog import default_input_ids, load_case_catalog, frozen_case_metadata

    catalog = {entry.id: entry for entry in load_case_catalog()}
    assert default_input_ids() == ['case_01_fixture', 'case_02_fixture', 'case_03_fixture']
    assert catalog['case_03_fixture'].name == 'Riverside Family Trust — varied references'
    assert catalog['alias_merge'].fixture_name == 'Nickname refers to the same person'
    assert catalog['alias_distinct'].fixture_name == 'Similar names refer to distinct people'
    assert catalog['alias_merge'].kind == 'diagnostic'
    frozen = frozen_case_metadata(load_inputs()[:1])
    assert frozen['case_01_fixture'].name == 'Evergreen Family Trust — explicit names'


def test_frozen_slot_changes_are_rejected_on_reload():
    import pytest
    from pydantic import ValidationError

    plan = RunPlan(inputs=load_inputs()[:1], max_calls=0, invocation_cap=0)
    payload = plan.model_dump(mode='json')
    payload['planned_slots'] = []
    with pytest.raises(ValidationError, match='Frozen observation slots'):
        RunPlan.model_validate(payload)


def test_discovered_case_defaults_and_frozen_labels_do_not_follow_repository_edits(tmp_path):
    import json
    import shutil
    from private_client_graph.research.fixtures import ROOT
    from private_client_graph.workbench.case_catalog import default_input_ids, frozen_case_metadata, repository_inputs

    shutil.copytree(ROOT / 'cases', tmp_path / 'cases')
    shutil.copytree(ROOT / 'research/fixtures', tmp_path / 'research/fixtures')
    shutil.copytree(tmp_path / 'cases/case_01', tmp_path / 'cases/case_04')
    metadata_path = tmp_path / 'cases/case_04/metadata.json'
    metadata_path.write_text(json.dumps({'id': 'case_04', 'name': 'New benchmark', 'description': 'Additional authored case.'}))
    assert default_input_ids(tmp_path)[-1] == 'case_04_fixture'
    inputs = [sample for sample in repository_inputs(tmp_path) if sample.case_id == 'case_04']
    labels = frozen_case_metadata(inputs, tmp_path)
    plan = RunPlan(inputs=inputs, max_calls=0, invocation_cap=0, case_metadata=labels)
    metadata_path.write_text(json.dumps({'id': 'case_04', 'name': 'Renamed benchmark', 'description': 'Changed description.'}))
    assert RunPlan.model_validate_json(plan.model_dump_json()).case_metadata['case_04_fixture'].name == 'New benchmark'
    assert frozen_case_metadata(inputs, tmp_path)['case_04_fixture'].name == 'Renamed benchmark'


def test_catalog_rejects_blank_authored_names(tmp_path):
    import json
    import shutil
    import pytest
    from private_client_graph.research.fixtures import ROOT
    from private_client_graph.workbench.case_catalog import load_case_catalog

    shutil.copytree(ROOT / 'cases', tmp_path / 'cases')
    shutil.copytree(ROOT / 'research/fixtures', tmp_path / 'research/fixtures')
    path = tmp_path / 'cases/case_01/metadata.json'
    metadata = json.loads(path.read_text())
    metadata['name'] = '   '
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='must not be blank'):
        load_case_catalog(tmp_path)


def test_uniform_fresh_matrix_may_exceed_one_invocation():
    plan = RunPlan(inputs=load_inputs()[:3], input_mode='fresh', fresh_extractions=5,
        execution_mode='recorded', resolver='generative', repetitions=3,
        max_calls=60, invocation_cap=38)
    assert plan.maximum_attempts == 60
    assert len(plan.planned_slots) == 45


def test_experiment_run_requires_frozen_metadata():
    import pytest
    with pytest.raises(ValueError, match='metadata for every input'):
        RunPlan(inputs=load_inputs()[:1], experiment_id='experiment', max_calls=0)


def test_catalog_reports_explicit_missing_metadata_without_borrowing_labels(tmp_path):
    import shutil
    from private_client_graph.research.fixtures import ROOT
    from private_client_graph.workbench.case_catalog import frozen_case_metadata

    shutil.copytree(ROOT / 'cases', tmp_path / 'cases')
    (tmp_path / 'cases/case_01/metadata.json').unlink()
    labels = frozen_case_metadata(load_inputs()[:1], tmp_path)['case_01_fixture']
    assert labels.metadata_available is False
    assert labels.description is None
    assert labels.name == 'Benchmark case case_01 (name unavailable)'


def test_real_fresh_failures_and_uncertainty_keep_authoritative_coverage(tmp_path):
    from private_client_graph.research.artifacts import Bundle
    from private_client_graph.research.provider import ModelRequest
    from private_client_graph.research.runner import execute
    from private_client_graph.workbench.run_evaluation import evaluate_run

    for state in ('failed', 'uncertain'):
        plan = RunPlan(inputs=load_inputs()[:1], input_mode='fresh', fresh_extractions=1,
            execution_mode='recorded', resolver='generative', repetitions=2,
            max_calls=3, invocation_cap=3)
        bundle = Bundle.create(tmp_path / state, plan, task_ledger=tmp_path / 'ledger')
        calls = []
        def failure(request):
            calls.append(request)
            raise RuntimeError('Substituted extraction failure')
        if state == 'uncertain':
            bundle.reserve(plan.planned_slots[0].extraction_attempt_id,
                ModelRequest(stage='extraction', source=plan.inputs[0].source,
                             settings=plan.settings).model_dump(mode='json'))
        execute(bundle, provider=failure)
        evaluation = evaluate_run(bundle)
        assert evaluation.aggregate.coverage.planned == 2
        assert getattr(evaluation.aggregate.coverage, state) == 2
        assert evaluation.aggregate.coverage.unavailable == 0
        assert evaluation.aggregate.f1 is None
        execute(bundle, provider=failure)
        assert bundle.attempt_count == 1
        assert len(calls) == (1 if state == 'failed' else 0)
