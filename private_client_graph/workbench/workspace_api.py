"""Version 2 read-only Research Workbench routes; no execution authority."""
from pathlib import Path

from fastapi import FastAPI, HTTPException

from private_client_graph.persistence.database import database_engine
from private_client_graph.research.artifacts import Bundle
from .case_catalog import CaseMetadata, load_case_catalog
from .execution_state import ExecutionAvailability, execution_availability
from .run_evaluation import compare_runs
from .run_evaluation_contracts import RunComparison, RunEvaluation
from .run_inspection import RunDetail, RunObservation, read_run
from .workspace_contracts import (WorkspaceDetail, WorkspaceHistory, LegacyHistoryRecord,
                                  LegacyCaseLabel, LegacyStudyDetail)
from .index import history_page, experiment_detail
from .workspace_index import workspace_history
from .workspaces import read_experiment

PREFIX = '/api/research/v2'


def mount_workspace_reads(app: FastAPI, root: Path, refresh=None) -> None:
    @app.get(f'{PREFIX}/legacy/experiments', response_model=list[LegacyHistoryRecord])
    def legacy_history():
        if refresh:
            refresh()
        page = history_page(database_engine(), root, limit=100)
        return [legacy_metadata(item) for item in page.items]

    @app.get(f'{PREFIX}/legacy/experiments/{{identity}}', response_model=LegacyStudyDetail)
    def legacy_detail(identity: str):
        detail = experiment_detail(database_engine(), root, identity)
        if detail is None:
            raise HTTPException(404, 'Legacy study not found')
        return LegacyStudyDetail(metadata=legacy_metadata(detail.history), detail=detail,
            cases=[LegacyCaseLabel(case_id=sample.case_id, input_id=sample.id,
                name=f'Benchmark case {sample.case_id} (name unavailable)',
                fixture_name=f'Input {sample.id} (name unavailable)') for sample in detail.samples])

    @app.get(f'{PREFIX}/status', response_model=ExecutionAvailability)
    def status():
        return execution_availability(root)

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

    @app.get(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/aggregate', response_model=RunEvaluation)
    def aggregate(experiment_id: str, run_id: str):
        return read_run(root, experiment_id, run_id).evaluation

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


def legacy_metadata(history):
    return LegacyHistoryRecord(id=history.id,
        name=f'Legacy study {history.artifact_path} (name unavailable)', history=history)
