"""Re-read an explicitly ordered collection before releasing finalized Sources for analysis."""
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from secrets import token_urlsafe
from threading import Lock
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict

from private_client_graph.models.source import Source

from ..pdf_acquisition import MAX_SOURCE_CHARACTERS, PdfAcquisitionError
from ..proposal_contracts import ProposalSourceMetadata
from ..proposal_errors import ProposalFailure
from ..proposal_sources import MAX_TOTAL_PDF_BYTES
from .google import MailPreview
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


@dataclass(frozen=True)
class PreviewProgress:
    continuation: str
    completed: int
    total: int


@dataclass
class _Draft:
    candidates: tuple[Candidate, ...]
    snapshots: list[_Snapshot] = field(default_factory=list)
    pdf_bytes: int = 0
    characters: int = 0


REVIEW_BATCH_SIZE = 5


class CollectionReview:
    def __init__(self, discovery: DiscoverySession):
        self.discovery = discovery
        self._review: tuple[str, list[_Snapshot]] | None = None
        self._pending: tuple[str, _Draft] | None = None
        self._lock = Lock()

    def read_email(self, message_id: str) -> MailPreview:
        """Address headers belong to the private reader, outside the publication snapshot."""
        with _acquisition_errors():
            email = self.discovery.read_message(message_id, self.discovery.new_action())
            source = _source(1, email.title, email.text)
            _check_size(len(source.text), 0)
            return replace(email, title=source.title)

    def preview(self, candidates: list[Candidate]) -> ReviewPreview | PreviewProgress:
        with self._lock:
            self._pending = self._review = None
            if not candidates or len(set(candidates)) != len(candidates):
                raise ProposalFailure("invalid_selection", "Select distinct Workspace results.")
            available = self.discovery.collection_candidates()
            for index, candidate in enumerate(candidates, 1):
                if (candidate.kind, candidate.id) not in available:
                    raise ProposalFailure("source_unavailable", "Check the selection and preview again.",
                                          status_code=409, source_number=index)
            return self._advance(_Draft(tuple(candidates)))

    def continue_preview(self, continuation: str) -> ReviewPreview | PreviewProgress:
        with self._lock:
            if not self._pending or self._pending[0] != continuation:
                raise _preview_required()
            _, draft = self._pending
            self._pending = None
            return self._advance(draft)

    def _advance(self, draft: _Draft) -> ReviewPreview | PreviewProgress:
        action = self.discovery.review_action()
        start = len(draft.snapshots)
        batch = draft.candidates[start:start + REVIEW_BATCH_SIZE]
        for index, candidate in enumerate(batch, start + 1):
            with _acquisition_errors(index):
                snapshot = self._read(candidate, index, action)
            draft.characters += len(snapshot.source.text)
            draft.pdf_bytes += snapshot.pdf_bytes
            _check_size(draft.characters, draft.pdf_bytes)
            draft.snapshots.append(snapshot)
        token = token_urlsafe()
        completed = len(draft.snapshots)
        if completed < len(draft.candidates):
            self._pending = token, draft
            return PreviewProgress(token, completed, len(draft.candidates))
        self._review = token, draft.snapshots
        return ReviewPreview(token, [item.source.model_copy() for item in draft.snapshots])

    def approve(self, token: str) -> list[Source]:
        with self._lock:
            if self._review is None or self._review[0] != token:
                raise _preview_required()
            _, reviewed = self._review
            self._review = None
            for start in range(0, len(reviewed), REVIEW_BATCH_SIZE):
                action = self.discovery.review_action()
                for index, item in enumerate(reviewed[start:start + REVIEW_BATCH_SIZE], start + 1):
                    with _acquisition_errors(index):
                        current = self._read(item.candidate, index, action)
                    if current != item:
                        raise ProposalFailure("source_changed", "A Source changed after preview.",
                                              status_code=409, source_number=index)
            return [item.source for item in reviewed]

    def _read(self, candidate: Candidate, index: int, action: Action) -> _Snapshot:
        if candidate.kind == "pdf":
            pdf = self.discovery.read_pdf(candidate.id, action, refresh=True)
            title, text = pdf.file.title, pdf.text
            digest, version, size = pdf.sha256, pdf.file.version, pdf.size
        else:
            email = self.discovery.read_message(candidate.id, action)
            title, text = email.title, email.text
            digest, version, size = sha256(text.encode()).hexdigest(), None, 0
        return _Snapshot(candidate, _source(index, title, text), digest, version, size)


def _preview_required() -> ProposalFailure:
    return ProposalFailure("preview_required", "Preview the selected Sources again.", status_code=409)


def _source(index: int, title: str, text: str) -> Source:
    metadata = ProposalSourceMetadata(id=f"source_{index:03}", title=title)
    if not text.strip():
        raise ValueError("Empty Source")
    return Source(id=metadata.id, title=metadata.title, text=text)


def _check_size(characters: int, pdf_bytes: int) -> None:
    if pdf_bytes > MAX_TOTAL_PDF_BYTES:
        raise ProposalFailure("pdf_too_large", "Select PDFs totalling no more than 10 MiB.")
    if characters > MAX_SOURCE_CHARACTERS:
        raise ProposalFailure("collection_text_limit", "Select Sources with at most 100,000 characters combined.")


@contextmanager
def _acquisition_errors(source_number: int | None = None) -> Iterator[None]:
    try:
        yield
    except (KeyError, TypeError, ValueError):
        raise ProposalFailure(
            "source_unavailable", "Check the selection and preview again.", status_code=409, source_number=source_number,
        ) from None
    except LimitReached:
        if source_number is not None:
            raise ProposalFailure("review_limit", "The private review reached its reading budget.") from None
        raise ProposalFailure("discovery_limit", "Discovery budget exhausted.") from None
    except PdfAcquisitionError as exc:
        raise ProposalFailure(exc.code, exc.message, source_number=source_number) from None
