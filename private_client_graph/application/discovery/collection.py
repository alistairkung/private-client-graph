"""Re-read an explicitly ordered collection before releasing finalized Sources for analysis."""
from dataclasses import dataclass
from hashlib import sha256
from secrets import token_urlsafe
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict

from private_client_graph.models.source import Source

from ..pdf_acquisition import MAX_SOURCE_CHARACTERS, PdfAcquisitionError
from ..proposal_contracts import ProposalSourceMetadata
from ..proposal_errors import ProposalFailure
from ..proposal_sources import MAX_PROPOSAL_SOURCES, MAX_TOTAL_PDF_BYTES
from .limits import Action, LimitReached
from .session import DiscoverySession


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal["email", "pdf"]
    id: str


@dataclass(frozen=True)
class ReviewPreview:
    token: str
    sources: list[Source]


@dataclass(frozen=True)
class _Snapshot:
    candidate: Candidate
    source: Source
    digest: str
    version: str | None
    pdf_bytes: int


class CollectionReview:
    def __init__(self, discovery: DiscoverySession):
        self.discovery = discovery
        self._review: tuple[str, list[_Snapshot]] | None = None
        self._lock = Lock()

    def read_email(self, message_id: str) -> Source:
        """Read one candidate without replacing the practitioner's publication preview."""
        return self._acquire([Candidate(kind="email", id=message_id)])[0].source

    def preview(self, candidates: list[Candidate]) -> ReviewPreview:
        with self._lock:
            self._review = None
            if not 1 <= len(candidates) <= MAX_PROPOSAL_SOURCES or len(set(candidates)) != len(candidates):
                raise ProposalFailure("invalid_sources", "Select one to five distinct Sources.")
            snapshots = self._acquire(candidates)
            token = token_urlsafe()
            self._review = token, snapshots
            return ReviewPreview(token, [item.source for item in snapshots])

    def approve(self, token: str) -> list[Source]:
        with self._lock:
            if self._review is None or self._review[0] != token:
                raise ProposalFailure("preview_required", "Preview the selected Sources again.", status_code=409)
            _, reviewed = self._review
            self._review = None
            current = self._acquire([item.candidate for item in reviewed])
            if current != reviewed:
                raise ProposalFailure("preview_required", "Preview the selected Sources again.", status_code=409)
            return [item.source for item in current]

    def _acquire(self, candidates: list[Candidate]) -> list[_Snapshot]:
        action = self.discovery.new_action()
        snapshots = []
        pdf_bytes = characters = 0
        for index, candidate in enumerate(candidates, 1):
            try:
                snapshot = self._read(candidate, index, action)
            except (KeyError, TypeError, ValueError):
                raise ProposalFailure(
                    "source_unavailable", "Check the selection and preview again.", status_code=409,
                ) from None
            except LimitReached:
                raise ProposalFailure("discovery_limit", "Discovery budget exhausted.") from None
            except PdfAcquisitionError as exc:
                raise ProposalFailure(exc.code, exc.message) from None
            characters += len(snapshot.source.text)
            pdf_bytes += snapshot.pdf_bytes
            if characters > MAX_SOURCE_CHARACTERS or pdf_bytes > MAX_TOTAL_PDF_BYTES:
                raise ProposalFailure("collection_too_large", "Select fewer or shorter Sources.")
            snapshots.append(snapshot)
        return snapshots

    def _read(self, candidate: Candidate, index: int, action: Action) -> _Snapshot:
        if candidate.kind == "pdf":
            pdf = self.discovery.read_pdf(candidate.id, action, refresh=True)
            title, text = pdf.file.title, pdf.text
            digest, version, size = pdf.sha256, pdf.file.version, pdf.size
        else:
            email = self.discovery.read_message(candidate.id, action)
            title, text = email.title, email.text
            digest, version, size = sha256(text.encode()).hexdigest(), None, 0
        metadata = ProposalSourceMetadata(id=f"source_{index:03}", title=title)
        if not text.strip():
            raise ValueError("Empty Source")
        source = Source(id=metadata.id, title=metadata.title, text=text)
        return _Snapshot(candidate, source, digest, version, size)
