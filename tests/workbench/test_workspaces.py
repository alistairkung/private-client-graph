"""Persistent workspace public application contract, independent of execution."""
import pytest
from private_client_graph.workbench.workspaces import create_experiment, read_experiment, update_draft
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate


def test_named_experiments_recover_draft_and_idempotent_identity(tmp_path):
    command = CreateExperiment(request_id='create', name='Alias consistency', hypothesis='Resolution helps')
    first = create_experiment(tmp_path, command)
    assert create_experiment(tmp_path, command).id == first.id
    duplicate_name = create_experiment(tmp_path, command.model_copy(update={'request_id': 'other'}))
    assert duplicate_name.id != first.id
    recovered = read_experiment(tmp_path, first.id)
    assert recovered.name == 'Alias consistency'
    assert recovered.hypothesis == 'Resolution helps'
    assert recovered.draft.configuration.input_ids == ['case_01_fixture', 'case_02_fixture', 'case_03_fixture']
    update = DraftUpdate(request_id='draft', expected_revision=0, configuration=recovered.draft.configuration)
    saved = update_draft(tmp_path, first.id, update)
    assert saved.revision == 1
    assert update_draft(tmp_path, first.id, update) == saved
    assert read_experiment(tmp_path, first.id).draft == saved
    with pytest.raises(ValueError, match='revision'):
        update_draft(tmp_path, first.id, update.model_copy(update={'request_id': 'stale'}))
    with pytest.raises(ValueError):
        CreateExperiment(request_id='blank', name='  ')


def test_repeated_configuration_freezes_new_runs_without_mutating_draft(tmp_path):
    from private_client_graph.workbench.run_planning import freeze_run, copy_run_draft
    from private_client_graph.workbench.workspace_contracts import FreezeRun, CopyRunDraft
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='e', name='Repeated run'))
    command = FreezeRun(request_id='first', expected_revision=0)
    first = freeze_run(tmp_path, workspace.id, command)
    assert freeze_run(tmp_path, workspace.id, command) == first
    second = freeze_run(tmp_path, workspace.id, command.model_copy(update={'request_id': 'second'}))
    assert second.id != first.id
    assert read_experiment(tmp_path, workspace.id).run_ids == [first.id, second.id]
    before = (tmp_path / first.id / 'manifest.json').read_bytes()
    copied = copy_run_draft(tmp_path, workspace.id, CopyRunDraft(request_id='copy', expected_revision=0, run_id=first.id))
    assert copied.revision == 1 and copied.copied_from_run == first.id
    assert (tmp_path / first.id / 'manifest.json').read_bytes() == before
    assert not list((tmp_path / first.id / 'authorizations').glob('*'))


def test_draft_and_membership_corruption_fail_without_repair(tmp_path):
    import json
    from private_client_graph.workbench.workspaces import experiment_path
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='e', name='Integrity'))
    record = experiment_path(tmp_path, workspace.id) / 'workspace.json'
    original = json.loads(record.read_text())
    original['record']['command']['name'] = 'Corrupted'
    record.write_text(json.dumps(original))
    before = record.read_bytes()
    with pytest.raises(ValueError, match='checksum'):
        read_experiment(tmp_path, workspace.id)
    assert record.read_bytes() == before


def test_freeze_recovers_published_plan_before_membership_without_duplicate(tmp_path):
    from private_client_graph.workbench.run_planning import freeze_run
    from private_client_graph.workbench.workspace_contracts import FreezeRun
    from private_client_graph.workbench.workspaces import experiment_path
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='e', name='Recovery'))
    command = FreezeRun(request_id='one', expected_revision=0)
    frozen = freeze_run(tmp_path, workspace.id, command)
    membership = experiment_path(tmp_path, workspace.id) / 'runs' / f'{frozen.id}.json'
    membership.unlink()  # Crash boundary: plan durable, membership not yet published.
    recovered = freeze_run(tmp_path, workspace.id, command)
    assert recovered == frozen
    assert read_experiment(tmp_path, workspace.id).run_ids == [frozen.id]


def test_copy_rejects_corrupt_frozen_preview_without_changing_draft(tmp_path):
    import json
    from private_client_graph.workbench.run_planning import freeze_run, copy_run_draft
    from private_client_graph.workbench.workspace_contracts import FreezeRun, CopyRunDraft
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='e', name='Integrity'))
    frozen = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='run', expected_revision=0))
    artifact = tmp_path / frozen.id / 'execution.json'
    changed = json.loads(artifact.read_text())
    changed['preview']['proposal']['temperature'] = 0.7
    artifact.write_text(json.dumps(changed))
    before = read_experiment(tmp_path, workspace.id).draft
    with pytest.raises(ValueError, match='preview mismatch'):
        copy_run_draft(tmp_path, workspace.id, CopyRunDraft(request_id='copy', expected_revision=0, run_id=frozen.id))
    assert read_experiment(tmp_path, workspace.id).draft == before
