"""Hide unused or failed Runs while retaining their artifacts and accounting."""
from pathlib import Path

from private_client_graph.research.artifacts import Bundle, utc_now
from private_client_graph.research.run_plan import RunPlan
from .execution_state import active_run_id
from .run_lifecycle import can_archive, latest_event
from .supervisor import command_lock
from .workspaces import experiment_path, read_experiment, run_is_archived, workspace_lock, write_record


def archive_run(root: Path, experiment_id: str, run_id: str) -> None:
    with command_lock(root), workspace_lock(root):
        if len(run_id) != 32 or any(character not in '0123456789abcdef' for character in run_id):
            raise ValueError('Invalid Run identity')
        workspace = read_experiment(root, experiment_id)
        if workspace.read_only_import:
            raise ValueError('Imported Runs are read-only')
        if run_is_archived(root, experiment_id, run_id):
            return
        if run_id not in workspace.run_ids:
            raise ValueError('Run does not belong to this Experiment')
        bundle = Bundle.open(root / run_id)
        if not isinstance(bundle.plan, RunPlan) or bundle.plan.experiment_id != experiment_id:
            raise ValueError('Run membership does not match its frozen plan')
        if active_run_id(root) in (run_id, 'unknown') or not can_archive(bundle, latest_event(bundle)['state']):
            raise ValueError('Only unused or failed Runs can be removed from history')
        marker = experiment_path(root, experiment_id) / 'archived-runs' / f'{run_id}.json'
        write_record(marker, {'experiment_id': experiment_id, 'run_id': run_id, 'archived_at': utc_now()})
