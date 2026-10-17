"""Retained provider outputs enter saved Run planning without fixture substitution."""
import json

import pytest

from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.provider import ModelResponse
from private_client_graph.research.runner import execute
from private_client_graph.workbench.case_catalog import repository_inputs
from private_client_graph.workbench.run_planning import freeze_run, preview_run
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate, FreezeRun, RunConfiguration
from private_client_graph.workbench.workspaces import create_experiment, update_draft


def baseline(root):
    workspace = create_experiment(root, CreateExperiment(request_id='create', name='Replay control'))
    config = RunConfiguration(input_ids=['case_01_fixture'], input_mode='fresh',
        execution_mode='recorded', invocation_cap=1)
    update_draft(root, workspace.id, DraftUpdate(request_id='draft', expected_revision=0, configuration=config))
    frozen = freeze_run(root, workspace.id, FreezeRun(request_id='baseline', expected_revision=1))
    sample = next(item for item in repository_inputs() if item.sample_id == 'case_01_fixture')
    # Deliberately differ from the ideal fixture: retain a real observed omission.
    payload = sample.sourced_extraction.model_dump()
    payload['relationships'] = payload['relationships'][:1]
    bundle = Bundle.open(root / frozen.id)
    execute(bundle, provider=lambda request: ModelResponse(payload=payload))
    write_json_once(bundle.path / 'lifecycle' / 'complete.json', {'at': '2026-10-17T00:00:00+00:00', 'state': 'complete'})
    return workspace, frozen, payload


def replay_configuration(workspace, frozen):
    return RunConfiguration(input_ids=['case_01_fixture_fresh_01'], input_mode='saved',
        retained_experiment_id=workspace.id, retained_run_id=frozen.id)


def test_saved_plan_uses_actual_output_and_freezes_lineage(tmp_path):
    workspace, original, payload = baseline(tmp_path)
    config = replay_configuration(workspace, original)
    preview = preview_run(config, tmp_path)
    assert preview.extraction_call_maximum == preview.matrix_call_maximum == 0
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='replay', expected_revision=1, configuration=config))
    frozen = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='control', expected_revision=2))
    plan = Bundle.open(tmp_path / frozen.id).plan
    assert plan.inputs[0].sourced_extraction.model_dump() == payload
    assert plan.inputs[0].cohort == 'historical'
    assert plan.retained_input_lineage.run_id == original.id
    assert plan.retained_input_lineage.samples['case_01_fixture_fresh_01'].original_cohort == 'fresh'
    assert plan.case_metadata['case_01_fixture_fresh_01'].id == 'case_01_fixture_fresh_01'


def test_retained_snapshot_must_match_actual_provider_output(tmp_path):
    workspace, original, _ = baseline(tmp_path)
    path = tmp_path / original.id / 'fresh_inputs' / 'case_01_fixture_fresh_01.json'
    altered = json.loads(path.read_text())
    altered['sourced_extraction']['relationships'] = []
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='provider output'):
        preview_run(replay_configuration(workspace, original), tmp_path)


def test_retained_inputs_cannot_move_to_another_experiment(tmp_path):
    workspace, original, _ = baseline(tmp_path)
    other = create_experiment(tmp_path, CreateExperiment(request_id='other', name='Other'))
    update_draft(tmp_path, other.id, DraftUpdate(request_id='copy', expected_revision=0,
        configuration=replay_configuration(workspace, original)))
    with pytest.raises(ValueError, match='original Experiment'):
        freeze_run(tmp_path, other.id, FreezeRun(request_id='wrong', expected_revision=1))


def test_retained_lineage_rejects_frozen_extraction_changes(tmp_path):
    from private_client_graph.research.run_plan import RunPlan

    workspace, original, _ = baseline(tmp_path)
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='copy', expected_revision=1,
        configuration=replay_configuration(workspace, original)))
    frozen = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='saved', expected_revision=2))
    payload = Bundle.open(tmp_path / frozen.id).plan.model_dump(mode='json')
    payload['inputs'][0]['sourced_extraction']['relationships'] = []
    with pytest.raises(ValueError, match='digest mismatch'):
        RunPlan.model_validate(payload)


def test_source_aware_saved_inputs_allow_one_resolver_observation(tmp_path):
    from private_client_graph.research.run_plan import RunPlan

    samples = [sample for sample in repository_inputs() if sample.sample_id == 'case_04_fixture']
    plan = RunPlan(inputs=samples, resolver='generative', execution_mode='recorded',
        max_calls=1, invocation_cap=1)
    assert len(plan.planned_slots) == 1
    assert plan.planned_slots[0].extraction_attempt_id is None


def test_missing_retained_attempt_and_incomplete_run_fail_closed(tmp_path):
    workspace, original, _ = baseline(tmp_path)
    attempt = tmp_path / original.id / 'attempts' / 'case_01_fixture_fresh_01-extraction.finished.json'
    attempt.unlink()
    with pytest.raises((OSError, ValueError)):
        preview_run(replay_configuration(workspace, original), tmp_path)


def test_retained_replay_is_zero_call_and_preserves_original_artifact_digest(tmp_path):
    from private_client_graph.workbench.artifacts import artifact_digest

    workspace, original, _ = baseline(tmp_path)
    digest = artifact_digest(tmp_path / original.id)
    config = replay_configuration(workspace, original)
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='replay', expected_revision=1, configuration=config))
    first = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='control', expected_revision=2))
    second = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='second', expected_revision=2))
    for frozen in (first, second):
        bundle = Bundle.open(tmp_path / frozen.id)
        def forbidden(request):
            raise AssertionError('Saved no-resolution replay must not invoke any provider')
        execute(bundle, provider=forbidden)
        assert bundle.attempt_count == 0
        assert bundle.results()[0]['evaluation']['fn'] > 0
    assert artifact_digest(tmp_path / original.id) == digest
