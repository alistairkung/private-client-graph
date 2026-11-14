"""Private, same-session actions mounted only by the offline practitioner app."""
from dataclasses import dataclass
from datetime import date
from secrets import token_urlsafe
from threading import Lock
from time import time
from typing import Literal

from fastapi import APIRouter, Request, Response
from httpx2 import Client
from pydantic import BaseModel, ConfigDict, Field

from private_client_graph.application.discovery import DiscoverySession, WorkspaceScope
from private_client_graph.application.discovery.collection import Candidate, CollectionReview
from private_client_graph.application.discovery.session import DiscoveryView
from private_client_graph.application.matter_proposals import analyse_finalized_sources
from private_client_graph.application.proposal_contracts import MatterIntakeMetadata, MatterProposalDetail
from private_client_graph.application.proposal_errors import ProposalFailure


class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terms: str = Field(max_length=160)
    folder: Literal["folder-1"]
    label: Literal["alder-label"]
    first_day: date | None = None
    last_day: date | None = None


class SessionAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session: str


class FollowUp(SessionAction):
    revision: int
    query: str


class Selection(SessionAction):
    candidates: list[Candidate] = Field(min_length=1, max_length=5)


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


def discovery_router(http: Client) -> APIRouter:
    router = APIRouter(prefix="/api/matter-proposals/discovery", include_in_schema=False)
    sessions = _Sessions()

    @router.post("/start")
    def start(request: Request, body: Start) -> dict:
        try:
            scope = WorkspaceScope("synthetic@example.test", body.label, body.folder, body.first_day, body.last_day)
            discovery = DiscoverySession(http, scope)
            view = discovery.start(body.terms)
        except ValueError:
            raise ProposalFailure("invalid_discovery", "Check your discovery inputs.") from None
        return {"session": sessions.start(request, CollectionReview(discovery)), "view": view}

    @router.post("/inspect")
    def inspect(request: Request, body: SessionAction) -> DiscoveryView:
        return sessions.get(request, body).discovery.inspect_more()

    @router.post("/follow-up")
    def follow_up(request: Request, body: FollowUp) -> dict:
        discovery = sessions.get(request, body).discovery
        try:
            approval = discovery.approve(body.revision, body.query)
        except ValueError:
            raise ProposalFailure("invalid_followup", "Choose an available suggested search.") from None
        return {"messages": approval.messages, "files": approval.files, "stop_reason": approval.stop_reason,
                "more_pages": approval.more_pages}

    @router.post("/preview")
    def preview(request: Request, body: Selection):
        return sessions.get(request, body).preview(body.candidates)

    @router.post("/import", status_code=201)
    def publish(request: Request, body: Import, response: Response) -> MatterProposalDetail:
        sources = sessions.get(request, body).approve(body.preview)
        proposal = analyse_finalized_sources(body.metadata, sources, request.app.state.proposal_analysis)
        response.headers["Location"] = f"/api/matter-proposals/{proposal.id}"
        return proposal

    return router
