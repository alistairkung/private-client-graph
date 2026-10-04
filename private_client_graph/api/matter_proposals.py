"""Authenticated HTTP boundary for proposal intake and review."""

from uuid import UUID

from fastapi import APIRouter, Request, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.responses import JSONResponse

from private_client_graph.application.matter_proposals import analyse_proposal
from private_client_graph.application.proposal_contracts import (
    MatterProposalDetail, MatterProposalSummary, ProposalMetadata, ProposalPersistenceFailure,
)
from private_client_graph.application.proposal_errors import ProposalFailure
from private_client_graph.persistence.matter_proposals import list_proposals, get_proposal, discard_proposal
from private_client_graph.application.pdf_acquisition import MAX_PDF_BYTES
from .proposal_upload import proposal_form

router = APIRouter(prefix='/api/matter-proposals')


@router.post('', status_code=201, response_model=MatterProposalDetail)
async def create_proposal(request: Request, response: Response) -> MatterProposalDetail:
    async with proposal_form(request) as form:
        try:
            metadata = ProposalMetadata.model_validate({
                name: form[name] for name in ('external_reference', 'matter_title', 'source_title')
            })
        except ValidationError as exc:
            raise ProposalFailure('invalid_metadata',
                'Enter a reference of 1–100 characters and titles of 1–200 characters, without controls or line breaks.') from exc
        upload = form['pdf']
        assert isinstance(upload, UploadFile)
        pdf = await upload.read(MAX_PDF_BYTES + 1)
        proposal = await run_in_threadpool(analyse_proposal, metadata, pdf, request.app.state.proposal_analysis)
    response.headers['Location'] = f'/api/matter-proposals/{proposal.id}'
    return proposal


@router.get('', response_model=list[MatterProposalSummary])
def proposal_collection() -> list[MatterProposalSummary]:
    try:
        return list_proposals()
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure('proposals_unavailable', 'Matter Proposals could not be loaded.', status_code=503) from exc


@router.get('/{proposal_id}', response_model=MatterProposalDetail)
def proposal_detail(proposal_id: UUID) -> MatterProposalDetail:
    try:
        proposal = get_proposal(proposal_id)
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure('proposal_unavailable', 'Matter Proposal could not be loaded.', status_code=503) from exc
    if proposal is None:
        raise ProposalFailure('proposal_not_found', 'Matter Proposal not found.', status_code=404)
    return proposal


@router.delete('/{proposal_id}', status_code=204)
def proposal_discard(proposal_id: UUID) -> Response:
    try:
        discarded = discard_proposal(proposal_id)
    except ProposalPersistenceFailure as exc:
        message = ('The discard outcome is unknown. Reload to check whether the intake remains.' if exc.ambiguous else
                   'The intake could not be discarded. It remains available. You may retry discard.')
        raise ProposalFailure('discard_failed', message, status_code=503,
                              retryable=True, outcome_unknown=exc.ambiguous) from exc
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure('discard_unavailable', 'The intake could not be discarded. Reload to try again.', status_code=503) from exc
    if not discarded:
        raise ProposalFailure('proposal_not_found', 'Matter Proposal not found.', status_code=404)
    return Response(status_code=204)


async def proposal_failure(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProposalFailure)
    return JSONResponse(status_code=exc.status_code,
                        content={'error': exc.error.model_dump(mode='json')})
