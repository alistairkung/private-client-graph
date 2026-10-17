"""Authenticated HTTP boundary for proposal intake and review."""

from uuid import UUID

from fastapi import APIRouter, Request, Response
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import FormData, UploadFile
from starlette.responses import JSONResponse

from private_client_graph.application.matter_proposals import analyse_proposal, analyse_proposal_sources
from private_client_graph.application.pdf_acquisition import MAX_PDF_BYTES
from private_client_graph.application.proposal_contracts import (
    MatterProposalDetail,
    MatterProposalSummary,
    MatterIntakeMetadata,
    ProposalSourceMetadata,
    ProposalMetadata,
)
from private_client_graph.application.proposal_errors import ProposalFailure
from private_client_graph.persistence.matter_proposals import (
    discard_proposal,
    get_proposal,
    list_proposals,
)
from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure

from private_client_graph.application.proposal_sources import MAX_PROPOSAL_SOURCES, PdfSourceInput

from .proposal_upload import proposal_form

router = APIRouter(prefix="/api/matter-proposals")


@router.post("", status_code=201, response_model=MatterProposalDetail)
async def create_proposal(request: Request, response: Response) -> MatterProposalDetail:
    async with proposal_form(request) as form:
        config = request.app.state.proposal_analysis
        if "sources" in form:
            metadata, source_metadata = _bundle_metadata(form)
            uploads = form.getlist("pdfs")
            if len(source_metadata) != len(uploads):
                raise ProposalFailure("invalid_sources", "Supply one PDF for every listed Source, in the same order.")
            inputs = []
            for source, upload in zip(source_metadata, uploads, strict=True):
                assert isinstance(upload, UploadFile)
                inputs.append(PdfSourceInput(source, await upload.read(MAX_PDF_BYTES + 1)))
            proposal = await run_in_threadpool(analyse_proposal_sources, metadata, inputs, config)
        else:
            legacy_metadata = _legacy_metadata(form)
            upload = form["pdf"]
            assert isinstance(upload, UploadFile)
            pdf = await upload.read(MAX_PDF_BYTES + 1)
            proposal = await run_in_threadpool(analyse_proposal, legacy_metadata, pdf, config)
    response.headers["Location"] = f"/api/matter-proposals/{proposal.id}"
    return proposal


def _bundle_metadata(form: FormData) -> tuple[MatterIntakeMetadata, list[ProposalSourceMetadata]]:
    try:
        metadata = MatterIntakeMetadata.model_validate({name: form[name] for name in ("external_reference", "matter_title")})
        source_json = form["sources"]
        assert isinstance(source_json, str)  # Validated by proposal_form.
        sources = TypeAdapter(list[ProposalSourceMetadata]).validate_json(source_json)
    except (ValidationError, ValueError) as exc:
        raise ProposalFailure("invalid_metadata", "Enter a valid Matter reference and a distinct identifier and title for each Source.") from exc
    if not 1 <= len(sources) <= MAX_PROPOSAL_SOURCES or len({source.id for source in sources}) != len(sources):
        raise ProposalFailure("invalid_sources", "Supply between one and five Sources with distinct identifiers.")
    return metadata, sources


def _legacy_metadata(form: FormData) -> ProposalMetadata:
    try:
        return ProposalMetadata.model_validate({name: form[name] for name in ("external_reference", "matter_title", "source_title")})
    except ValidationError as exc:
        raise ProposalFailure("invalid_metadata", "Enter a reference of 1–100 characters and titles of 1–200 characters, without controls or line breaks.") from exc


@router.get("", response_model=list[MatterProposalSummary])
def proposal_collection() -> list[MatterProposalSummary]:
    try:
        return list_proposals()
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure(
            "proposals_unavailable",
            "Matter Proposals could not be loaded.",
            status_code=503,
        ) from exc


@router.get("/{proposal_id}", response_model=MatterProposalDetail)
def proposal_detail(proposal_id: UUID) -> MatterProposalDetail:
    try:
        proposal = get_proposal(proposal_id)
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure(
            "proposal_unavailable",
            "Matter Proposal could not be loaded.",
            status_code=503,
        ) from exc
    if proposal is None:
        raise ProposalFailure(
            "proposal_not_found", "Matter Proposal not found.", status_code=404
        )
    return proposal


@router.delete("/{proposal_id}", status_code=204)
def proposal_discard(proposal_id: UUID) -> Response:
    try:
        discarded = discard_proposal(proposal_id)
    except ProposalPersistenceFailure as exc:
        message = (
            "The discard outcome is unknown. Reload to check whether the intake remains."
            if exc.ambiguous else
            "The intake could not be discarded. It remains available. You may retry discard."
        )
        raise ProposalFailure(
            "discard_failed",
            message,
            status_code=503,
            retryable=True,
            outcome_unknown=exc.ambiguous,
        ) from exc
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure(
            "discard_unavailable",
            "The intake could not be discarded. Reload to try again.",
            status_code=503,
        ) from exc
    if not discarded:
        raise ProposalFailure(
            "proposal_not_found", "Matter Proposal not found.", status_code=404
        )
    return Response(status_code=204)


async def proposal_failure(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProposalFailure)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error.model_dump(mode="json")},
    )
