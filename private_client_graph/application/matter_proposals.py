"""Synchronous synthetic intake: finalized Source, proposed graph, durable review."""

from langchain_core.exceptions import OutputParserException
from langchain_deepseek import ChatDeepSeek
from openai import APIConnectionError, APIStatusError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.extract import extract_relationships_from_text
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult
from private_client_graph.persistence.matter_proposals import find_reference, save_proposal
from private_client_graph.persistence.proposal_allowance import claim_slot

from .pdf_acquisition import PdfAcquisitionError, extract_pdf_source
from .proposal_config import ProposalAnalysisConfig
from .proposal_contracts import (
    DuplicateReference, MatterProposalDetail, ProposalMetadata, ProposalPersistenceFailure, ReferenceOwner,
)
from .proposal_errors import ProposalFailure


def analyse_proposal(metadata: ProposalMetadata, pdf: bytes,
                     config: ProposalAnalysisConfig | None) -> MatterProposalDetail:
    try:
        source = extract_pdf_source(pdf)
    except PdfAcquisitionError as exc:
        raise ProposalFailure(exc.code, exc.message, retryable=exc.retryable) from exc
    _require_unclaimed_reference(metadata.external_reference)
    extraction = _extract_proposal(source, config)
    try:
        graph = build_graph(extraction.relationships, document=metadata.source_title, source_text=source)
    except ValueError as exc:
        raise ProposalFailure('invalid_graph',
            'No valid proposal was produced. The proposed relationships or Evidence failed validation. You may try a fresh analysis.',
            retryable=True) from exc
    try:
        return save_proposal(metadata, source, graph)
    except DuplicateReference as exc:
        raise duplicate_failure(exc.owner) from exc
    except ProposalPersistenceFailure as exc:
        raise persistence_failure(exc) from exc


def duplicate_failure(owner: ReferenceOwner) -> ProposalFailure:
    return ProposalFailure('duplicate_reference', 'This external Matter reference already exists.',
        status_code=409, existing_resource=owner.model_dump(mode='json'))


def persistence_failure(exc: ProposalPersistenceFailure) -> ProposalFailure:
    if exc.ambiguous:
        return ProposalFailure('outcome_unknown',
            'The outcome is unknown. Retry to check the external reference before any new analysis.',
            status_code=503, retryable=True, outcome_unknown=True)
    return ProposalFailure('persistence_failed', 'No Matter Proposal was saved. You may retry the full analysis.',
                           status_code=503, retryable=True)


def _require_unclaimed_reference(reference: str) -> None:
    try:
        owner = find_reference(reference)
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure('reference_unavailable',
            'The external reference could not be checked. No analysis was started. Retry when available.',
            status_code=503, retryable=True) from exc
    if owner is not None:
        raise duplicate_failure(owner)


def _extract_proposal(source: str, config: ProposalAnalysisConfig | None) -> ExtractionResult:
    if config is None:
        raise ProposalFailure('analysis_unavailable', 'Proposal analysis is unavailable. Contact the deployment operator.',
                              status_code=503)
    try:
        llm = ChatDeepSeek(model=config.model, api_key=config.api_key, max_retries=0,
                          timeout=90, extra_body={'thinking': {'type': 'disabled'}})
    except Exception as exc:
        raise ProposalFailure('analysis_unavailable', 'Proposal analysis is unavailable. Contact the deployment operator.',
                              status_code=503) from exc
    _consume_attempt(config)
    try:
        result = extract_relationships_from_text(source, llm=llm)
        return ExtractionResult.model_validate(result)
    except (ValidationError, OutputParserException, RuntimeError) as exc:
        raise ProposalFailure('invalid_extraction', 'No valid proposal was produced. You may try a fresh analysis.',
                              status_code=422, retryable=True) from exc
    except Exception as exc:
        retryable = isinstance(exc, APIConnectionError) or (
            isinstance(exc, APIStatusError) and (exc.status_code in (408, 429) or exc.status_code >= 500)
        )
        message = ('Analysis could not be completed. You may retry the full analysis.' if retryable else
                   'Proposal analysis is unavailable. Contact the deployment operator.')
        raise ProposalFailure('provider_failed', message, status_code=502, retryable=retryable) from exc


def _consume_attempt(config: ProposalAnalysisConfig) -> None:
    try:
        reset = claim_slot(limit=config.limit, window_seconds=config.window_seconds)
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure('allowance_unavailable', 'The analysis allowance could not be checked. No analysis was started.',
                              status_code=503, retryable=True) from exc
    if reset is not None:
        raise ProposalFailure('allowance_exhausted', 'The proposal analysis allowance is exhausted until the next window.',
                              status_code=429, resets_at=reset)
