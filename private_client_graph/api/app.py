"""Thin HTTP boundary for the fixed synthetic professional-review workspace."""

from pathlib import Path

from fastapi import FastAPI, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.application.matters import MatterSummary, list_matters
from private_client_graph.persistence.database import database_engine
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from private_client_graph.application.case_analysis import analyse_case, get_case
from private_client_graph.application.contracts import (
    AnalysisError,
    AnalysisRequest,
    CaseAnalysis,
    CaseDetail,
)
from private_client_graph.application.errors import AnalysisFailure

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"


def health() -> JSONResponse:
    try:
        with database_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, ValueError):
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(content={"status": "ok"})


def matter_collection() -> list[MatterSummary] | JSONResponse:
    try:
        return list_matters()
    except (SQLAlchemyError, ValueError):
        return JSONResponse(status_code=503, content={"error": {
            "message": "Matters could not be loaded.",
        }})


def case_detail() -> CaseDetail:
    return get_case()


def case_analysis(request: AnalysisRequest) -> CaseAnalysis:
    return analyse_case(request.mode)


async def analysis_failure(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AnalysisFailure)
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.error.model_dump()}
    )


async def invalid_request(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    error = AnalysisError(
        stage="request", message="Choose live or sample analysis only."
    )
    return JSONResponse(status_code=422, content={"error": error.model_dump()})


def create_app(web_dist: Path = WEB_DIST) -> FastAPI:
    application = FastAPI(title="Private Client Graph")
    application.add_api_route("/health", health, methods=["GET"])
    application.add_api_route(
        "/api/matters", matter_collection, methods=["GET"], response_model=list[MatterSummary]
    )
    application.add_api_route(
        "/api/showcase/case-01", case_detail, methods=["GET"], response_model=CaseDetail
    )
    application.add_api_route(
        "/api/showcase/case-01/analysis",
        case_analysis,
        methods=["POST"],
        response_model=CaseAnalysis,
    )
    application.add_exception_handler(AnalysisFailure, analysis_failure)
    application.add_exception_handler(RequestValidationError, invalid_request)
    if web_dist.is_dir():
        def practitioner_shell() -> FileResponse:
            return FileResponse(web_dist / "index.html")

        application.add_api_route("/app", practitioner_shell, include_in_schema=False)
        application.add_api_route("/app/", practitioner_shell, include_in_schema=False)
        application.mount(
            "/", StaticFiles(directory=web_dist, html=True), name="frontend"
        )
    return application


app = create_app()
