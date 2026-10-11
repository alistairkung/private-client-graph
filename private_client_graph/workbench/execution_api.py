"""Opt-in local commands; credentials are read only inside the approved worker."""
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from private_client_graph.persistence.database import database_engine
from .api import PREFIX, create_app
from .execution_contracts import Capabilities, Command, FrozenPlan, Preview, Proposal, RunStatus, LiveApproval
from .index import rebuild_index
from .planning import capabilities, freeze, preview
from .supervisor import reconcile, start, status, stop


def mount_execution(app: FastAPI, root: Path) -> None:
    app.state.execution_enabled = True
    previous_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with previous_lifespan(application):
            reconcile(root)
            yield

    app.router.lifespan_context = lifespan
    @app.middleware('http')
    async def local_commands(request: Request, call_next):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            host = request.headers.get('host', '')
            if (origin != f'http://{host}'
                    or request.headers.get('content-type', '').split(';')[0] != 'application/json'):
                return JSONResponse(status_code=403, content={'detail': 'Commands require a same-origin local JSON request.'})
        return await call_next(request)

    @app.exception_handler(ValueError)
    async def rejected(request, error):
        return JSONResponse(status_code=409, content={'detail': str(error)})

    @app.exception_handler(OSError)
    async def missing(request, error):
        return JSONResponse(status_code=409, content={'detail': 'Required executable artifact or accounting is unavailable.'})

    @app.get(f'{PREFIX}/capabilities', response_model=Capabilities)
    def available():
        return capabilities(root)

    @app.post(f'{PREFIX}/preview', response_model=Preview)
    def review(proposal: Proposal):
        return preview(proposal, root)

    @app.post(f'{PREFIX}/plans', response_model=FrozenPlan)
    def create_plan(proposal: Proposal):
        result = freeze(root, proposal)
        rebuild_index(database_engine(), root)
        return result

    @app.get(f'{PREFIX}/plans/{{identity}}', response_model=RunStatus)
    def progress(identity: str):
        result = status(root, identity)
        if result.state not in ('running', 'stopping'):
            rebuild_index(database_engine(), root)
        return result

    @app.post(f'{PREFIX}/plans/{{identity}}/start', response_model=RunStatus)
    def begin(identity: str, command: Command):
        return start(root, identity, command)

    @app.post(f'{PREFIX}/plans/{{identity}}/authorize', response_model=RunStatus)
    def approve(identity: str, approval: LiveApproval, request: Request):
        command = Command(request_id=approval.request_id, plan_digest=approval.plan_digest)
        return start(root, identity, command, continuation=approval.continuation,
                     approval=approval, origin=request.headers['origin'])

    @app.post(f'{PREFIX}/plans/{{identity}}/stop', response_model=RunStatus)
    def halt(identity: str, command: Command):
        return stop(root, identity, command)

    @app.post(f'{PREFIX}/plans/{{identity}}/continue', response_model=RunStatus)
    def resume(identity: str, command: Command):
        return start(root, identity, command, continuation=True)


def create_execution_app() -> FastAPI:
    import os
    root = Path(os.getenv('PCG_RESEARCH_ARTIFACTS', 'runs/research'))
    root.mkdir(parents=True, exist_ok=True)
    def refresh_index() -> None:
        rebuild_index(database_engine(), root)

    app = create_app(refresh=refresh_index)
    mount_execution(app, root)
    return app


app = create_execution_app()
