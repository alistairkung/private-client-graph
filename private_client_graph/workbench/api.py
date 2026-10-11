"""Local read-only ASGI entry point. No runner, provider, or credential setup."""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from private_client_graph.persistence.database import database_engine
from .comparison import compare_experiments
from .contracts import Comparison, ExperimentDetail, HistoryPage
from .index import experiment_detail, history_page

PREFIX = '/api/research/v1'


def create_app() -> FastAPI:
    app = FastAPI(title='PCG Research read-only API', version='1')
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', '[::1]', 'testserver'])
    root = Path(os.getenv('PCG_RESEARCH_ARTIFACTS', 'runs/research'))

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(request, error):
        return JSONResponse(status_code=503, content={'detail': 'Research index unavailable. Check PostgreSQL and migrations.'})

    @app.get('/health')
    def health():
        with database_engine().connect() as connection:
            connection.execute(text('SELECT 1 FROM research_experiments LIMIT 1'))
        return {'status': 'ok', 'read_only': True}

    @app.get(f'{PREFIX}/experiments', response_model=HistoryPage)
    def history(q: str = Query('', max_length=300), lifecycle: str | None = None,
                kind: str | None = None, integrity: str | None = None,
                offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)):
        return history_page(database_engine(), root, query=q, lifecycle=lifecycle,
                            kind=kind, integrity=integrity, offset=offset, limit=limit)

    def load(identity: str) -> ExperimentDetail:
        detail = experiment_detail(database_engine(), root, identity)
        if detail is None:
            raise HTTPException(404, 'Experiment not found in the research index.')
        return detail

    @app.get(f'{PREFIX}/experiments/{{identity}}', response_model=ExperimentDetail)
    def detail(identity: str):
        return load(identity)

    @app.get(f'{PREFIX}/comparison', response_model=Comparison)
    def comparison(left: str, right: str):
        if left == right:
            raise HTTPException(422, 'Choose two different experiments.')
        first, second = load(left), load(right)
        if any(item.history.integrity != 'verified' or item.history.freshness != 'current'
               for item in (first, second)):
            raise HTTPException(409, 'Comparison requires current, verified artifacts.')
        return compare_experiments(first, second)

    static = Path(os.getenv('PCG_RESEARCH_WEB', 'web/research-dist'))
    if static.is_dir():
        app.mount('/assets', StaticFiles(directory=static / 'assets'), name='research-assets')

        @app.get('/', include_in_schema=False)
        def frontend():
            return FileResponse(static / 'index.html')

    return app


app = create_app()
