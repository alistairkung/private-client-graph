"""Bounded acquisition of explicitly identified PDF Sources before analysis."""
from dataclasses import dataclass

from private_client_graph.models.source import Source

from .pdf_acquisition import MAX_PDF_BYTES, MAX_SOURCE_CHARACTERS, PdfAcquisitionError, extract_pdf_source
from .proposal_contracts import ProposalSourceMetadata
from .proposal_errors import ProposalFailure

MAX_PROPOSAL_SOURCES = 5
MAX_TOTAL_PDF_BYTES = MAX_PDF_BYTES


@dataclass(frozen=True)
class PdfSourceInput:
    metadata: ProposalSourceMetadata
    pdf: bytes


def acquire_proposal_sources(inputs: list[PdfSourceInput]) -> list[Source]:
    if not 1 <= len(inputs) <= MAX_PROPOSAL_SOURCES:
        raise ProposalFailure("invalid_sources", "Select between one and five PDF documents.")
    if len({item.metadata.id for item in inputs}) != len(inputs):
        raise ProposalFailure("invalid_sources", "Every document must have a distinct Source identifier.")
    if sum(len(item.pdf) for item in inputs) > MAX_TOTAL_PDF_BYTES:
        raise ProposalFailure("pdf_too_large", "The combined PDF upload limit is 10 MiB.")
    sources = []
    characters = 0
    for item in inputs:
        try:
            text = extract_pdf_source(item.pdf)
        except PdfAcquisitionError as exc:
            raise ProposalFailure(exc.code, exc.message, retryable=exc.retryable) from exc
        characters += len(text)
        if characters > MAX_SOURCE_CHARACTERS:
            raise ProposalFailure("source_too_long", "Select PDFs with at most 100,000 extracted characters combined.")
        sources.append(Source(id=item.metadata.id, title=item.metadata.title, text=text))
    return sources
