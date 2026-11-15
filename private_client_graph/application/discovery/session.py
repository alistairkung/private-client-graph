"""Private in-process discovery session. A trusted caller supplies its authorized scope and HTTP client."""
from dataclasses import dataclass, field, replace
from hashlib import sha256
from threading import RLock

from httpx2 import Client

from .google import DriveFile, MailPreview, OutsideScope, PdfPreview, ReadFailure, WorkspaceReader, WorkspaceScope, item_id, literal
from .leads import Suggestion, ranked_suggestions
from .limits import Action, LimitReached, Limits, SessionLimitReached, Usage


ORIGINAL_BATCH_SIZE = 5


@dataclass
class _Search:
    query: str
    message_ids: dict[str, None] = field(default_factory=dict)
    files: dict[str, DriveFile] = field(default_factory=dict)
    mail_page: str | None = ""
    drive_page: str | None = ""

    @property
    def more_pages(self) -> bool:
        return self.mail_page is not None or self.drive_page is not None

    @property
    def item_count(self) -> int:
        return len(self.message_ids) + len(self.files)

    def enumerate(self, reader: WorkspaceReader, action: Action) -> None:
        while self.mail_page is not None:
            self.read_mail_page(reader, action)
        while self.drive_page is not None:
            self.read_drive_page(reader, action)

    def read_mail_page(self, reader: WorkspaceReader, action: Action, size: int = 100) -> None:
        if self.mail_page is None:
            return
        page = reader.mail_page(self.query, self.mail_page, action, size)
        cursor = _next_page(page, self.mail_page)
        rows = page.get("messages", [])
        if len(rows) > size:
            raise ReadFailure("Unexpected Gmail page size")
        self.message_ids.update(dict.fromkeys(sorted(item_id(row["id"]) for row in rows)))
        self.mail_page = cursor

    def read_drive_page(self, reader: WorkspaceReader, action: Action, size: int = 100) -> None:
        if self.drive_page is None:
            return
        page = reader.drive_page(self.query, self.drive_page, action, size)
        cursor = _next_page(page, self.drive_page)
        rows = page.get("files", [])
        if len(rows) > size:
            raise ReadFailure("Unexpected Drive page size")
        for row in rows:
            try:
                item = reader.admitted_file(row)
            except OutsideScope:
                continue
            self.files[item.id] = item
        self.drive_page = cursor


def _next_page(page: dict, previous: str) -> str | None:
    token = page.get("nextPageToken")
    if token is not None and (not isinstance(token, str) or token == previous):
        raise ReadFailure("Invalid page token")
    return token or None


@dataclass(frozen=True)
class DiscoveryView:
    scope: WorkspaceScope
    original_query: str
    original_item_limit: int
    revision: int
    can_inspect_more: bool
    returned_messages: tuple[str, ...]
    pending: tuple[str, ...]
    inspected: tuple[str, ...]
    inspected_titles: dict[str, str]
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
    def __init__(self, http: Client, scope: WorkspaceScope, limits: Limits = Limits(), *,
                 message_ids: frozenset[str] | None = None, file_ids: frozenset[str] | None = None):
        self._reader = WorkspaceReader(http, scope, message_ids=message_ids, file_ids=file_ids)
        self._limits = limits
        self._usage = Usage()
        self._review_usage = Usage()
        self._original: _Search | None = None
        self._drive_first = False
        self._texts: dict[str, str] = {}
        self._titles: dict[str, str] = {}
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

    def inspect_more(self, revision: int | None = None) -> DiscoveryView:
        """Advance the displayed original search by one batch. Replays return the latest view."""
        with self._lock:
            original = self._original
            if original is None:
                raise ValueError("Start discovery first")
            if self._views:
                latest = self._views[-1]
                if not latest.can_inspect_more or (revision is not None and revision != latest.revision):
                    return latest
            action = Action(self._limits, self._usage)
            reason = None
            session_blocked = False
            try:
                self._original_batch(original, action)
            except LimitReached as exc:
                reason = str(exc)
                session_blocked = isinstance(exc, SessionLimitReached)
            except (KeyError, TypeError, ValueError):
                reason = "Original search incomplete"
            pending = self._pending(original)
            at_cap = original.item_count >= self._limits.original_items
            if at_cap and original.more_pages and not pending and not reason:
                reason = "Original item limit"
            view = DiscoveryView(
                scope=self._reader.scope,
                original_query=original.query,
                original_item_limit=self._limits.original_items,
                revision=len(self._views),
                can_inspect_more=(bool(pending or (original.more_pages and not at_cap)) and not session_blocked
                                  and self._usage.requests < self._limits.session_requests
                                  and self._usage.bytes < self._limits.session_bytes),
                returned_messages=tuple(original.message_ids),
                pending=pending,
                inspected=tuple(self._texts),
                inspected_titles=dict(self._titles),
                skipped=tuple(sorted(self._skipped)),
                failed=tuple(sorted(self._failed)),
                files=tuple(original.files.values()),
                suggestions=ranked_suggestions(self._texts),
                more_pages=original.more_pages,
                stop_reason=reason or ("Batch complete" if pending else None),
                requests=self._usage.requests,
                bytes=self._usage.bytes,
            )
            self._views.append(view)
            return view

    def _original_batch(self, original: _Search, action: Action) -> None:
        pending = self._pending(original)[:ORIGINAL_BATCH_SIZE]
        for key in pending:
            self._inspect_message(key, action)
        room = min(ORIGINAL_BATCH_SIZE - len(pending), self._limits.original_items - original.item_count)

        # A full Gmail page must not consume every batch before Drive gets a turn.
        providers = ("drive", "mail") if self._drive_first else ("mail", "drive")
        for provider in providers:
            if not room:
                break
            before = original.item_count
            if provider == "mail" and not pending and original.mail_page is not None:
                original.read_mail_page(self._reader, action, room)
                self._drive_first = True
                for key in self._pending(original):
                    self._inspect_message(key, action)
            elif provider == "drive" and original.drive_page is not None:
                original.read_drive_page(self._reader, action, room)
                self._drive_first = False
            room -= original.item_count - before

    def _pending(self, original: _Search) -> tuple[str, ...]:
        return tuple(sorted(original.message_ids.keys() - self._texts.keys() - self._skipped - self._failed))

    def _inspect_message(self, key: str, action: Action) -> None:
        try:
            email = self._reader.message(key, action)
        except OutsideScope:
            self._skipped.add(key)
        except (KeyError, TypeError, ValueError):
            self._failed.add(key)
        else:
            self._texts[key] = email.text
            self._titles[key] = email.title
            self._digests[key] = sha256(email.text.encode()).hexdigest()

    def preview_message(self, message_id: str) -> str:
        """An explicit preview never contributes text to automatic query expansion."""
        with self._lock:
            return self.read_message(message_id, self.new_action()).text

    def new_action(self) -> Action:
        return Action(self._limits, self._usage)

    def collection_candidates(self) -> set[tuple[str, str]]:
        with self._lock:
            original = self._original
            if original is None:
                return set()
            mail = set(original.message_ids)
            files = set(original.files)
            for approval in self._approvals.values():
                mail.update(approval.messages)
                files.update(item.id for item in approval.files)
            return ({("email", key) for key in mail - self._skipped - self._failed}
                    | {("pdf", key) for key in files})

    def review_action(self) -> Action:
        # Budget one preview and revalidation, plus a second pair for a revised
        # selection. Retries share the same ledger. Search has its own limits.
        candidates = self.collection_candidates()
        requests_per_pass = sum(2 if kind == "email" else 3 for kind, _ in candidates)
        limits = replace(self._limits, session_requests=self._limits.action_requests + 4 * requests_per_pass)
        return Action(limits, self._review_usage)

    def read_message(self, message_id: str, action: Action) -> MailPreview:
        with self._lock:
            original_hit = self._original and message_id in self._original.message_ids
            followup_hit = any(message_id in approval.messages for approval in self._approvals.values())
            if not original_hit and not followup_hit:
                raise ValueError("Unknown message candidate")
            return self._reader.message(message_id, action)

    def preview_pdf(self, file_id: str) -> PdfPreview:
        """Only an admitted candidate can enter the existing PDF acquisition boundary."""
        return self.read_pdf(file_id, self.new_action())

    def read_pdf(self, file_id: str, action: Action, *, refresh: bool = False) -> PdfPreview:
        with self._lock:
            candidates = dict(self._original.files) if self._original else {}
            for approval in self._approvals.values():
                candidates.update((item.id, item) for item in approval.files)
            if file_id not in candidates:
                raise ValueError("Unknown PDF candidate")
            return self._reader.preview_pdf(candidates[file_id], action, refresh=refresh)

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
            requests_before = self._usage.requests
            bytes_before = self._usage.bytes
            search = _Search(query)
            reason = None
            try:
                search.enumerate(self._reader, Action(self._limits, self._usage))
            except LimitReached as exc:
                reason = str(exc)
            except (KeyError, TypeError, ValueError):
                reason = "Follow-up search incomplete"
            approved = Approval(
                display=display,
                query=query,
                inspected=tuple((i, self._digests[i]) for i in display.inspected),
                requests_before=requests_before,
                bytes_before=bytes_before,
                messages=tuple(sorted(search.message_ids)),
                files=tuple(search.files.values()),
                more_pages=search.more_pages,
                stop_reason=reason,
            )
            self._approvals[key] = approved
            return approved
