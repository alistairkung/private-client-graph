"""Independent scoring and replay contracts for the synthetic discovery study."""
from dataclasses import replace
from hashlib import sha256

import pytest

from local_development.workspace import fixture_client
from private_client_graph.application.discovery import DiscoverySession
from research.discovery.evaluate import evaluate, fraction
from research.discovery.replay import LIMITS, QUERY, SCOPE, checkpoint


@pytest.mark.parametrize(("variant", "actor", "denominator"), [
    ("primary", "Mara Voss", 10), ("paired", "Ben Wong", 11),
])
def test_gain_is_from_approved_query_at_matched_original_coverage(variant, actor, denominator):
    arms = evaluate()["arms"][variant]
    baseline = arms["original"]["checkpoints"]
    expanded = arms["expanded"]["checkpoints"]
    assert [p["original_inspected"] for p in baseline] == [
        p["original_inspected"] for p in expanded if p["stage"] in {"first_batch", "original_batch"}
    ]
    before, after = expanded[-2:]
    assert baseline[-1]["recall"] == before["recall"] == fraction(2, 3)
    assert baseline[-1]["precision"] == fraction(2, 8)
    assert after["precision"] == fraction(3, denominator)
    assert after["recall"] == fraction(3, 3)
    assert after["original_skipped"] == ["07"]
    assert after["usage"]["requests"] - before["usage"]["requests"] == 2
    first, last = arms["expanded"]["approvals"]
    assert first["false_lead"] and not last["false_lead"]
    assert "06" not in first["inspected_body_sha256"]
    assert last["shortlist"][0]["query"] == last["query"] == actor
    assert last["shortlist"][0]["passage"] == f"{actor} will circulate the executed appointment separately."
    assert last["shortlist"][0]["origin"] == "06"
    assert last["inspected_body_sha256"]["06"] == sha256((
        "Please accept my resignation as trustee of Alder Trust. Alice Reed, Ben Wong, Cora Patel, "
        f"Leo Dunn and Mara Voss attended. {actor} will circulate the executed appointment separately."
    ).encode()).hexdigest()


def test_read_and_repeat_click_cannot_turn_followup_into_a_new_discovery_round():
    with fixture_client() as http:
        session = DiscoverySession(http, SCOPE, LIMITS)
        first = session.start(QUERY)
        approved = session.approve(first.revision, "Alice Reed")
        assert "Cora Patel will circulate" in session.preview_message(approved.messages[0])
        usage = checkpoint("read", session, first, approved.messages)["usage"]
        assert session.approve(first.revision, "Alice Reed") == approved
        with pytest.raises(ValueError, match="not suggested"):
            session.approve(first.revision, "Cora Patel")
        assert session.approvals == (approved,)
        assert checkpoint("repeat", session, first, approved.messages)["usage"] == usage


def test_exhaustion_keeps_unread_returned_items_and_missing_pages_visible():
    with fixture_client() as http:
        session = DiscoverySession(http, SCOPE, replace(LIMITS, session_requests=1))
        point = checkpoint("limited", session, session.start(QUERY), ())
    assert point["original_pending"] == ["01", "02", "03", "04", "05"]
    assert not point["original_inspected"] and point["original_more_pages"]
    assert point["original_stop"] == "Session request limit"
    assert point["usage"]["requests"] == 1
    assert fraction(0, 0) == {"numerator": 0, "denominator": 0, "value": None}
