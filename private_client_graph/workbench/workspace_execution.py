"""Persistent-workspace commands using the existing local execution safeguards."""
import json
from pathlib import Path

from fastapi import FastAPI, Request

from private_client_graph.persistence.database import database_engine
from .approval import authorize
from .execution_contracts import Command, FrozenPlan, LiveApproval, Preview, RunStatus
from .planning import open_executable, require_live
from .run_planning import copy_run_draft, freeze_run, preview_run
from .supervisor import command_lock, start, stop
from .workspace_api import PREFIX
from .workspace_contracts import (CopyRunDraft, CreateExperiment, DraftUpdate, FreezeRun,
                                 RunConfiguration, RunDraft, WorkspaceDetail)
from .workspace_index import rebuild_workspaces
from .workspaces import create_experiment, read_experiment, update_draft


def prepare_authorization(root: Path, identity: str, approval: LiveApproval, origin: str) -> None:
    with command_lock(root):
        bundle, frozen = open_executable(root, identity)
        require_live(root)
        if bundle.plan.kind != 'live_experiment':
            raise ValueError('Only live Runs require provider authorization')
        authorize(bundle, frozen, approval, origin)


def start_run(root: Path, identity: str, command: Command, *, continuation: bool = False,
              origin: str) -> RunStatus:
    bundle, _ = open_executable(root, identity)
    approval = None
    if bundle.plan.kind == 'live_experiment':
        record = json.loads((bundle.path / 'authorizations' / f'{command.request_id}.json').read_text())
        approval = LiveApproval.model_validate(record['request'])
        if approval.continuation != continuation or record['origin'] != origin:
            raise ValueError('Start does not match the authorized invocation')
    return start(root, identity, command, continuation=continuation, approval=approval,
                 origin=origin, preauthorized=approval is not None)


def mount_workspace_commands(app: FastAPI, root: Path) -> None:
    def refresh():
        rebuild_workspaces(database_engine(), root)

    def member(experiment_id: str, identity: str):
        if identity not in read_experiment(root, experiment_id).run_ids:
            raise ValueError('Run does not belong to this Experiment')

    @app.post(f'{PREFIX}/experiments', response_model=WorkspaceDetail)
    def create(command: CreateExperiment):
        result = create_experiment(root, command)
        refresh()
        return result

    @app.put(f'{PREFIX}/experiments/{{experiment_id}}/draft', response_model=RunDraft)
    def draft(experiment_id: str, command: DraftUpdate):
        preview_run(command.configuration, root)
        result = update_draft(root, experiment_id, command)
        refresh()
        return result

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/draft/copy', response_model=RunDraft)
    def copy(experiment_id: str, command: CopyRunDraft):
        result = copy_run_draft(root, experiment_id, command)
        refresh()
        return result

    @app.post(f'{PREFIX}/preview', response_model=Preview)
    def preview(configuration: RunConfiguration):
        return preview_run(configuration, root)

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/runs', response_model=FrozenPlan)
    def freeze(experiment_id: str, command: FreezeRun):
        result = freeze_run(root, experiment_id, command)
        refresh()
        return result

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/authorize')
    def approval(experiment_id: str, run_id: str, command: LiveApproval, request: Request):
        member(experiment_id, run_id)
        prepare_authorization(root, run_id, command, request.headers['origin'])
        return {'authorized': True, 'invocation_id': command.request_id, 'started': False}

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/start', response_model=RunStatus)
    def begin(experiment_id: str, run_id: str, command: Command, request: Request):
        member(experiment_id, run_id)
        return start_run(root, run_id, command, origin=request.headers['origin'])

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/continue', response_model=RunStatus)
    def resume(experiment_id: str, run_id: str, command: Command, request: Request):
        member(experiment_id, run_id)
        return start_run(root, run_id, command, continuation=True, origin=request.headers['origin'])

    @app.post(f'{PREFIX}/experiments/{{experiment_id}}/runs/{{run_id}}/stop', response_model=RunStatus)
    def halt(experiment_id: str, run_id: str, command: Command):
        member(experiment_id, run_id)
        return stop(root, run_id, command)
