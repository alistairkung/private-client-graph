"""Thin HTTP boundary for the fixed synthetic professional-review workspace."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


def health() -> dict[str, str]:
    return {"status": "ok"}


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
        "/api/case-01", case_detail, methods=["GET"], response_model=CaseDetail
    )
    application.add_api_route(
        "/api/case-01/analysis",
        case_analysis,
        methods=["POST"],
        response_model=CaseAnalysis,
    )
    application.add_exception_handler(AnalysisFailure, analysis_failure)
    application.add_exception_handler(RequestValidationError, invalid_request)
    if web_dist.is_dir():
        application.mount(
            "/", StaticFiles(directory=web_dist, html=True), name="frontend"
        )
    return application


app = create_app()
