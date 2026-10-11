"""Version 2 read-only Research Workbench routes; no execution authority."""
from pathlib import Path

from fastapi import FastAPI, HTTPException

from private_client_graph.persistence.database import database_engine
from private_client_graph.research.artifacts import Bundle
from .case_catalog import CaseMetadata, load_case_catalog
from .run_evaluation import compare_runs
from .run_evaluation_contracts import RunComparison
from .run_inspection import RunDetail, RunObservation, read_run
from .workspace_contracts import WorkspaceDetail, WorkspaceHistory
from .workspace_index import workspace_history
from .workspaces import read_experiment

PREFIX = '/api/research/v2'


def mount_workspace_reads(app: FastAPI, root: Path, refresh=None) -> None:
    @app.get(f'{PREFIX}/cases', response_model=list[CaseMetadata])
    def cases():
        return load_case_catalog()

    @app.get(f'{PREFIX}/experiments', response_model=WorkspaceHistory)
    def history():
        if refresh:
            refresh()
        return workspace_history(database_engine(), root)

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}', response_model=WorkspaceDetail)
    def experiment(experiment_id: str):
        return read_experiment(root, experiment_id)

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}/runs', response_model=list[RunDetail])
    def runs(experiment_id: str):
        workspace = read_experiment(root, experiment_id)
        return [read_run(root, experiment_id, identity) for identity in workspace.run_ids]

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}', response_model=RunDetail)
    def detail(experiment_id: str, run_id: str):
        return read_run(root, experiment_id, run_id)

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/observations/{{observation_id}}', response_model=RunObservation)
    def observation(experiment_id: str, run_id: str, observation_id: str):
        detail = read_run(root, experiment_id, run_id)
        for item in detail.observations:
            if item.id == observation_id:
                return item
        raise HTTPException(404, 'Observation not in the frozen Run matrix')

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}/comparison', response_model=RunComparison)
    def comparison(experiment_id: str, left: str, right: str):
        if left == right:
            raise HTTPException(422, 'Select two distinct Runs')
        read_run(root, experiment_id, left)
        read_run(root, experiment_id, right)
        return compare_runs(Bundle.open(root / left), Bundle.open(root / right))
