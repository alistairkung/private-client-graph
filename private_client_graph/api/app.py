"""Thin HTTP boundary for the fixed synthetic professional-review workspace."""

from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.api.public_research import router as public_research_router
from private_client_graph.api.auth import configure_auth
from private_client_graph.api.matter_proposals import router as proposal_router, proposal_failure
from private_client_graph.application.matter_confirmation import confirm_matter
from private_client_graph.application.proposal_errors import ProposalFailure
from private_client_graph.application.matters import MatterDetail, MatterSummary, get_matter, list_matters
from private_client_graph.persistence.database import database_engine
from private_client_graph.pipeline import PipelineExecutionError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from private_client_graph.application.showcase_cases import ShowcaseCase, ShowcaseCaseSummary, get_showcase_case, list_showcase_cases
from private_client_graph.application.proposal_config import ProposalAnalysisConfig

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"


def health(request: Request) -> JSONResponse:
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


class MatterConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matter_proposal_id: UUID


def create_matter(body: MatterConfirmation, response: Response) -> MatterDetail:
    matter = confirm_matter(body.matter_proposal_id)
    response.headers["Location"] = f"/api/matters/{matter.id}"
    return matter


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


def showcase_case(case_id: str) -> ShowcaseCase | JSONResponse:
    try:
        case = get_showcase_case(case_id)
    except (OSError, UnicodeError, ValueError, PipelineExecutionError):
        return JSONResponse(status_code=503, content={"error": {"message": "Synthetic case could not be loaded."}})
    if case is None:
        return JSONResponse(status_code=404, content={"error": {"message": "Synthetic case not found."}})
    return case


async def invalid_request(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    if request.url.path.startswith("/api/matter-proposals/"):
        return JSONResponse(
            status_code=422,
            content={"error": {
                "code": "invalid_proposal_id",
                "message": "Invalid Matter Proposal UUID.",
            }},
        )
    if request.url.path == "/api/matters" and request.method == "POST":
        return JSONResponse(status_code=422, content={"error": {
            "code": "invalid_confirmation",
            "message": "Supply exactly one valid Matter Proposal identifier.",
        }})
    if request.url.path.startswith("/api/matters/"):
        return JSONResponse(status_code=422, content={"error": {"message": "Invalid Matter UUID."}})
    return JSONResponse(status_code=422, content={"error": {"message": "Invalid request."}})


def create_app(web_dist: Path = WEB_DIST) -> FastAPI:
    load_dotenv(ROOT / ".env")
    application = FastAPI(title="Private Client Graph")
    configure_auth(application)
    try:
        proposal_config = ProposalAnalysisConfig.from_environment()
        database_engine()  # Validate deployment storage independently of proposal settings.
        application.state.proposal_analysis = proposal_config
    except ValueError:
        application.state.proposal_analysis = None
    application.include_router(proposal_router)
    application.include_router(public_research_router)
    application.add_exception_handler(ProposalFailure, proposal_failure)
    application.add_api_route("/health", health, methods=["GET"])
    application.add_api_route(
        "/api/matters", matter_collection, methods=["GET"], response_model=list[MatterSummary]
    )
    application.add_api_route(
        "/api/matters",
        create_matter,
        methods=["POST"],
        status_code=201,
        response_model=MatterDetail,
    )
    application.add_api_route(
        "/api/matters/{internal_id}", matter_detail, methods=["GET"], response_model=MatterDetail
    )
    application.add_api_route("/api/showcase/cases", list_showcase_cases, methods=["GET"], response_model=list[ShowcaseCaseSummary])
    application.add_api_route("/api/showcase/cases/{case_id}", showcase_case, methods=["GET"], response_model=ShowcaseCase)
    application.add_exception_handler(RequestValidationError, invalid_request)
    if web_dist.is_dir():
        def practitioner_shell() -> FileResponse:
            return FileResponse(web_dist / "index.html")

        application.add_api_route("/app", practitioner_shell, include_in_schema=False)
        application.add_api_route("/app/", practitioner_shell, include_in_schema=False)
        application.add_api_route(
            "/app/matters/{internal_id}", practitioner_shell, include_in_schema=False
        )
        application.add_api_route("/app/matter-proposals/new", practitioner_shell, include_in_schema=False)
        application.add_api_route(
            "/app/matter-proposals/{proposal_id}", practitioner_shell, include_in_schema=False
        )
        # Public presentation-only routes never enter the practitioner namespace.
        application.add_api_route("/research-results", practitioner_shell, include_in_schema=False)
        application.add_api_route("/research-results/", practitioner_shell, include_in_schema=False)
        def legacy_demo(demo_path: str = "") -> RedirectResponse:
            return RedirectResponse("/app", status_code=308)

        application.add_api_route("/demo", legacy_demo, include_in_schema=False)
        application.add_api_route("/demo/{demo_path:path}", legacy_demo, include_in_schema=False)
        application.mount(
            "/", StaticFiles(directory=web_dist, html=True), name="frontend"
        )
    return application


app = create_app()
