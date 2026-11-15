"""Run the frozen discovery protocol using only the local HTTP fixture."""
from dataclasses import asdict
from hashlib import sha256
from time import perf_counter

from local_development.workspace import ROOT, fixture_client
from private_client_graph.application.discovery import DiscoverySession, Limits, WorkspaceScope
from private_client_graph.application.discovery.session import Approval, DiscoveryView

CORPUS_SHA256 = "cb4c8dddc43f3cfe80324c1b0ec67fccb7eb4951c21eda9591c152c8c45c064d"
SCOPE = WorkspaceScope("synthetic@example.test", "alder-label", "folder-1")
QUERY = "Alder Trust"
LIMITS = Limits(action_requests=40, session_requests=160, action_bytes=12 << 20,
               session_bytes=32 << 20, original_items=50)


def checkpoint(stage: str, session: DiscoverySession, view: DiscoveryView, opened: tuple[str, ...]) -> dict:
    return {
        "stage": stage,
        "revision": view.revision,
        "surfaced": sorted(f"{kind}:{key}" for kind, key in session.collection_candidates()),
        "original_returned_emails": list(view.returned_messages),
        "original_listed_pdfs": [file.id for file in view.files],
        "original_inspected": list(view.inspected),
        "original_pending": list(view.pending),
        "original_skipped": list(view.skipped),
        "original_failed": list(view.failed),
        "original_more_pages": view.more_pages,
        "original_stop": view.stop_reason,
        "usage": asdict(session.new_action().session),
        "opened_emails": list(opened),
        "opens": len(opened),
        "executed_approvals": len(session.approvals),
        "selections": 0,
    }


def approval_record(approval: Approval) -> dict:
    return {
        "revision": approval.display.revision,
        "query": approval.query,
        "shortlist": [asdict(s) for s in approval.shortlist],
        "inspected_body_sha256": dict(approval.inspected),
        "requests_before": approval.requests_before,
        "bytes_before": approval.bytes_before,
        "hits": sorted([f"email:{key}" for key in approval.messages]
                       + [f"pdf:{file.id}" for file in approval.files]),
        "more_pages": approval.more_pages,
        "stop_reason": approval.stop_reason,
    }


def replay(*, expand: bool, alternate: bool, timing: bool = False) -> dict:
    if sha256((ROOT / "corpus.json").read_bytes()).hexdigest() != CORPUS_SHA256:
        raise ValueError("The Alder Trust corpus differs from the frozen evaluation input")
    start = perf_counter()
    with fixture_client(alternate_appointment=alternate) as http:
        session = DiscoverySession(http, SCOPE, LIMITS)
        view = session.start(QUERY)
        opened: tuple[str, ...] = ()
        stages = [checkpoint("first_batch", session, view, opened)]
        if expand:
            query = view.suggestions[0].query
            approval = session.approve(view.revision, query)
            # Open the follow-up-only dispatch that contains another actionable promise.
            session.preview_message(approval.messages[0])
            opened = (approval.messages[0],)
            stages.append(checkpoint("first_followup", session, view, opened))
        while view.can_inspect_more:
            view = session.inspect_more(view.revision)
            stages.append(checkpoint("original_batch", session, view, opened))
        if expand:
            session.approve(view.revision, view.suggestions[0].query)
            stages.append(checkpoint("final_followup", session, view, opened))
        result: dict = {"checkpoints": stages, "approvals": [approval_record(a) for a in session.approvals]}
    if timing:
        result["offline_replay_ms"] = round(1000 * (perf_counter() - start), 3)
    return result
