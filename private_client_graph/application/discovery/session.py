"""Private in-process discovery session. A trusted caller supplies its authorized scope and HTTP client."""
from dataclasses import dataclass, field
from hashlib import sha256
from threading import RLock

from httpx2 import Client

from .google import DriveFile, OutsideScope, PdfPreview, ReadFailure, WorkspaceReader, WorkspaceScope, _key, literal
from .leads import Suggestion, ranked_suggestions
from .limits import Action, LimitReached, Limits, Usage


@dataclass
class _Search:
    query: str
    message_ids: set[str] = field(default_factory=set)
    files: dict[str, DriveFile] = field(default_factory=dict)
    mail_page: str | None = ""
    drive_page: str | None = ""

    @property
    def more_pages(self) -> bool:
        return self.mail_page is not None or self.drive_page is not None

    def enumerate(self, reader: WorkspaceReader, action: Action) -> None:
        while self.mail_page is not None:
            page = reader.mail_page(self.query, self.mail_page, action)
            self.message_ids.update(_key(row["id"]) for row in page.get("messages", []))
            self.mail_page = _next_page(page)
        while self.drive_page is not None:
            page = reader.drive_page(self.query, self.drive_page, action)
            for row in page.get("files", []):
                try:
                    item = reader.admitted_file(row)
                except OutsideScope:
                    continue
                self.files[item.id] = item
            self.drive_page = _next_page(page)


def _next_page(page: dict) -> str | None:
    token = page.get("nextPageToken")
    if token is not None and not isinstance(token, str):
        raise ReadFailure("Invalid page token")
    return token or None


@dataclass(frozen=True)
class DiscoveryView:
    revision: int
    returned_messages: tuple[str, ...]
    pending: tuple[str, ...]
    inspected: tuple[str, ...]
    skipped: tuple[str, ...]
    failed: tuple[str, ...]
    files: tuple[DriveFile, ...]
    suggestions: tuple[Suggestion, ...]
    more_pages: bool
    stop_reason: str | None
    requests: int
    bytes: int


@dataclass(frozen=True)
class Approval:
    display: DiscoveryView
    query: str
    inspected: tuple[tuple[str, str], ...]
    requests_before: int
    bytes_before: int
    messages: tuple[str, ...]
    files: tuple[DriveFile, ...]
    more_pages: bool
    stop_reason: str | None

    @property
    def shortlist(self) -> tuple[Suggestion, ...]:
        return self.display.suggestions


class DiscoverySession:
    def __init__(self, http: Client, scope: WorkspaceScope, limits: Limits = Limits()):
        self._reader = WorkspaceReader(http, scope)
        self._limits = limits
        self._usage = Usage()
        self._original: _Search | None = None
        self._texts: dict[str, str] = {}
        self._digests: dict[str, str] = {}
        self._skipped: set[str] = set()
        self._failed: set[str] = set()
        self._views: list[DiscoveryView] = []
        self._approvals: dict[tuple[int, str], Approval] = {}
        self._lock = RLock()

    @property
    def approvals(self) -> tuple[Approval, ...]:
        with self._lock:
            return tuple(self._approvals.values())

    @property
    def suggestions(self) -> tuple[Suggestion, ...]:
        with self._lock:
            return self._views[-1].suggestions if self._views else ()

    def start(self, terms: str) -> DiscoveryView:
        with self._lock:
            if self._original is not None:
                raise ValueError("Discovery already started")
            self._original = _Search(literal(terms))
            return self.inspect_more()

    def inspect_more(self) -> DiscoveryView:
        """Enumerate original matches, then inspect up to five outstanding Gmail IDs in lexical order."""
        with self._lock:
            original = self._original
            if original is None:
                raise ValueError("Start discovery first")
            action = Action(self._limits, self._usage)
            reason = None
            try:
                original.enumerate(self._reader, action)
                for key in self._pending(original)[:5]:
                    self._inspect_message(key, action)
            except LimitReached as exc:
                reason = str(exc)
            except (ReadFailure, KeyError, TypeError, ValueError):
                reason = "Original search incomplete"
            pending = self._pending(original)
            view = DiscoveryView(len(self._views), tuple(sorted(original.message_ids)), pending,
                                 tuple(self._texts), tuple(sorted(self._skipped)), tuple(sorted(self._failed)),
                                 tuple(original.files.values()), ranked_suggestions(self._texts),
                                 original.more_pages, reason or ("Batch complete" if pending else None),
                                 self._usage.requests, self._usage.bytes)
            self._views.append(view)
            return view

    def _pending(self, original: _Search) -> tuple[str, ...]:
        return tuple(sorted(original.message_ids - self._texts.keys() - self._skipped - self._failed))

    def _inspect_message(self, key: str, action: Action) -> None:
        try:
            text = self._reader.message_text(key, action)
        except OutsideScope:
            self._skipped.add(key)
        except (ReadFailure, KeyError, TypeError, ValueError):
            self._failed.add(key)
        else:
            self._texts[key] = text
            self._digests[key] = sha256(text.encode()).hexdigest()

    def preview_pdf(self, file_id: str) -> PdfPreview:
        """Only an admitted candidate can enter the existing PDF acquisition boundary."""
        with self._lock:
            candidates = dict(self._original.files) if self._original else {}
            for approval in self._approvals.values():
                candidates.update((item.id, item) for item in approval.files)
            if file_id not in candidates:
                raise ValueError("Unknown PDF candidate")
            return self._reader.preview_pdf(candidates[file_id], Action(self._limits, self._usage))

    def approve(self, revision: int, query: str) -> Approval:
        """Execute exactly the displayed lead; retain a partial/failed search as a charged approval."""
        with self._lock:
            key = revision, query
            if key in self._approvals:
                return self._approvals[key]
            if not 0 <= revision < len(self._views):
                raise ValueError("Unknown discovery revision")
            display = self._views[revision]
            if query not in {s.query for s in display.suggestions}:
                raise ValueError("Query was not suggested in this revision")
            if len(self._approvals) >= 3:
                raise ValueError("Follow-up limit reached")
            before = self._usage.requests, self._usage.bytes
            search = _Search(query)
            reason = None
            try:
                search.enumerate(self._reader, Action(self._limits, self._usage))
            except LimitReached as exc:
                reason = str(exc)
            except (ReadFailure, KeyError, TypeError, ValueError):
                reason = "Follow-up search incomplete"
            approved = Approval(display, query, tuple((i, self._digests[i]) for i in display.inspected),
                                *before, tuple(sorted(search.message_ids)), tuple(search.files.values()),
                                search.more_pages, reason)
            self._approvals[key] = approved
            return approved
