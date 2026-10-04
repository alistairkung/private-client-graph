"""Thin HTTP boundary for the fixed synthetic professional-review workspace."""

from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.application.matters import MatterDetail, MatterSummary, get_matter, list_matters
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
from private_client_graph.application.showcase_live import LiveConfig, live_availability

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


def matter_detail(internal_id: UUID) -> MatterDetail | JSONResponse:
    try:
        matter = get_matter(internal_id)
    except (SQLAlchemyError, ValueError):
        return JSONResponse(status_code=503, content={"error": {
            "message": "Matter could not be loaded.",
        }})
    if matter is None:
        return JSONResponse(status_code=404, content={"error": {"message": "Matter not found"}})
    return matter


def case_detail(request: Request, response: Response) -> CaseDetail:
    response.headers["Cache-Control"] = "no-store"
    detail = get_case()
    detail.live_analysis = live_availability(request.app.state.showcase_live)
    return detail


def case_analysis(body: AnalysisRequest, request: Request) -> CaseAnalysis:
    return analyse_case(body.mode, request.app.state.showcase_live)


async def analysis_failure(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AnalysisFailure)
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.error.model_dump(mode="json")}
    )


async def invalid_request(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    if request.url.path.startswith("/api/matters/"):
        return JSONResponse(status_code=422, content={"error": {"message": "Invalid Matter UUID."}})
    error = AnalysisError(
        stage="request", message="Choose live or sample analysis only."
    )
    return JSONResponse(status_code=422, content={"error": error.model_dump()})


def create_app(web_dist: Path = WEB_DIST) -> FastAPI:
    load_dotenv(ROOT / ".env")
    application = FastAPI(title="Private Client Graph")
    application.state.showcase_live = LiveConfig.from_environment()
    application.add_api_route("/health", health, methods=["GET"])
    application.add_api_route(
        "/api/matters", matter_collection, methods=["GET"], response_model=list[MatterSummary]
    )
    application.add_api_route(
        "/api/matters/{internal_id}", matter_detail, methods=["GET"], response_model=MatterDetail
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
        application.add_api_route(
            "/app/matters/{internal_id}", practitioner_shell, include_in_schema=False
        )
        application.mount(
            "/", StaticFiles(directory=web_dist, html=True), name="frontend"
        )
    return application


app = create_app()
