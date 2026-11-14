"""Private discovery actions for offline fixtures or the opt-in synthetic pilot."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import date
from secrets import token_urlsafe
from threading import Lock
from time import time
from typing import Iterator, Literal

from fastapi import APIRouter, Request, Response
from httpx2 import Client
from pydantic import BaseModel, ConfigDict, Field

from private_client_graph.application.discovery import DiscoverySession, WorkspaceScope
from private_client_graph.application.discovery.collection import Candidate, CollectionReview, ReviewPreview
from private_client_graph.application.discovery.session import DiscoveryView
from private_client_graph.application.matter_proposals import analyse_finalized_sources
from private_client_graph.application.proposal_contracts import MatterIntakeMetadata, MatterProposalDetail
from private_client_graph.application.proposal_errors import ProposalFailure
from private_client_graph.application.proposal_sources import MAX_PROPOSAL_SOURCES
from .auth import allowed_subjects, available_auth_config
from .workspace_pilot import Pilot, reconnect


class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terms: str = Field(max_length=160)
    folder: str
    label: str
    first_day: date | None = None
    last_day: date | None = None


class SessionAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session: str


class FollowUp(SessionAction):
    revision: int
    query: str


class EmailRead(SessionAction):
    message_id: str


class Selection(SessionAction):
    candidates: list[Candidate] = Field(min_length=1, max_length=MAX_PROPOSAL_SOURCES)


class Import(SessionAction):
    preview: str
    metadata: MatterIntakeMetadata
    publish_synthetic: Literal[True]


@dataclass
class _Flow:
    handle: str
    review: CollectionReview


class _Sessions:
    """One active private journey per signed login. Replacement retires its previous handle."""
    def __init__(self) -> None:
        self._entries: dict[tuple[str, float], _Flow] = {}
        self._lock = Lock()

    def start(self, request: Request, review: CollectionReview) -> str:
        with self._lock:
            now = time()
            self._entries = {k: v for k, v in self._entries.items() if k[1] > now}
            flow = _Flow(token_urlsafe(), review)
            self._entries[(request.session["sub"], request.session["expires"])] = flow
            return flow.handle

    def get(self, request: Request, action: SessionAction) -> CollectionReview:
        with self._lock:
            flow = self._entries.get((request.session["sub"], request.session["expires"]))
            if flow is None or flow.handle != action.session:
                raise ProposalFailure("unknown_discovery", "Start private discovery again.", status_code=404)
            return flow.review


def discovery_router(http: Client | None = None, *, pilot: Pilot | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/matter-proposals/discovery", include_in_schema=False)
    sessions = _Sessions()
    base_scope = pilot.config.scope if pilot else WorkspaceScope("synthetic@example.test", "alder-label", "folder-1")

    def review(request: Request, body: SessionAction) -> CollectionReview:
        if pilot:
            # Disconnect, expiry and journey replacement use the same lock.
            with pilot.lock:
                journey = pilot.connected(request).journey
                if not journey or journey[0] != body.session:
                    raise ProposalFailure("unknown_discovery", "Start private discovery again.", status_code=409)
                return journey[1]
        return sessions.get(request, body)

    @contextmanager
    def active_review(request: Request, body: SessionAction) -> Iterator[CollectionReview]:
        collection = review(request, body)
        try:
            yield collection
        finally:
            # A concurrent disconnect or replacement invalidates in-flight results too.
            if pilot:
                review(request, body)

    @router.post("/start")
    def start(request: Request, body: Start) -> dict:
        connection = pilot.connected(request) if pilot else None
        client = connection.http if connection else http
        if client is None:
            raise reconnect()
        try:
            if (body.label, body.folder) != (base_scope.label, base_scope.folder):
                raise ValueError("Invalid scope")
            scope = replace(base_scope, first_day=body.first_day, last_day=body.last_day)
            discovery = DiscoverySession(
                client, scope,
                message_ids=pilot.config.message_ids if pilot else None,
                file_ids=pilot.config.file_ids if pilot else None,
            )
            view = discovery.start(body.terms)
        except ValueError:
            raise ProposalFailure("invalid_discovery", "Check your discovery inputs.") from None
        except RuntimeError:
            # A client closed by a simultaneous disconnect cannot issue another read.
            if pilot and pilot.connected(request) is not connection:
                raise reconnect() from None
            raise
        collection = CollectionReview(discovery)
        if connection and pilot:
            with pilot.lock:
                if pilot.connected(request) is not connection:
                    raise reconnect()
                handle = token_urlsafe()
                connection.journey = handle, collection
        else:
            handle = sessions.start(request, collection)
        return {"session": handle, "view": view}

    @router.post("/inspect")
    def inspect(request: Request, body: SessionAction) -> DiscoveryView:
        with active_review(request, body) as collection:
            return collection.discovery.inspect_more()

    @router.post("/follow-up")
    def follow_up(request: Request, body: FollowUp) -> dict:
        try:
            with active_review(request, body) as collection:
                approval = collection.discovery.approve(body.revision, body.query)
        except ValueError:
            raise ProposalFailure("invalid_followup", "Choose an available suggested search.") from None
        return {"messages": approval.messages, "files": approval.files, "stop_reason": approval.stop_reason,
                "more_pages": approval.more_pages}

    @router.post("/email")
    def read_email(request: Request, body: EmailRead) -> dict[str, str]:
        with active_review(request, body) as collection:
            source = collection.read_email(body.message_id)
            return {"title": source.title, "text": source.text}

    @router.post("/preview")
    def preview(request: Request, body: Selection) -> ReviewPreview:
        with active_review(request, body) as collection:
            return collection.preview(body.candidates)

    @router.post("/import", status_code=201)
    def publish(request: Request, body: Import, response: Response) -> MatterProposalDetail:
        with active_review(request, body) as collection:
            sources = collection.approve(body.preview)
            if pilot:
                if available_auth_config(request) is None:
                    raise ProposalFailure("authentication_unavailable", "Authentication is unavailable.", status_code=503)
                if request.session["sub"] not in allowed_subjects():
                    raise ProposalFailure("access_denied", "Access is not allowed.", status_code=403)
        # The final active_review check authorizes handoff. Subsequent disconnects
        # cannot revoke the finalized Sources or undo a provider reservation.
        proposal = analyse_finalized_sources(body.metadata, sources, request.app.state.proposal_analysis)
        response.headers["Location"] = f"/api/matter-proposals/{proposal.id}"
        return proposal

    return router
