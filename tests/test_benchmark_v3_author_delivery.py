from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import author_context, author_delivery
from benchmark_v3.batch.contracts import DesignOutput
from private_client_graph.models.source import Source

DAY = date(2027, 6, 24)
STATEMENT = Source(id="upstream", title="Holdings", text="Portfolio value £82,600")


def _design(provenance, *, day="2027-06-30"):
    return DesignOutput.model_validate({
        "neutral_brief": "Review the supplied file.",
        "cutoff": day, "documentary_references": [], "private_history": "Private history.",
        "inventory": [
            {"source_id": STATEMENT.id, "author": "Kian Venn", "created_on": DAY,
             "participant_brief": "Issue the holdings statement.", "provenance": provenance, "received": []},
            {"source_id": "downstream", "author": "Devin Stoll, accountant", "created_on": day,
             "participant_brief": "Record your own cost allocation.", "provenance": "Internal record.",
             "received": [STATEMENT.id]},
        ],
        "matched": [], "candidates": [], "required": {},
    })


@pytest.mark.parametrize("provenance", [
    "The trustees put the statement in the firm's trust file.",
    "Devin Stoll countersigns the statement. A signed copy is kept by both practices.",
    "A copy is available in the trust workstream.\nDelivered 2027-06-24 to Another Person",
    "Sent to the named firm.\nDelivered 2027-06-25 to Devin Stoll",
    "Sent to the named firm.\nDelivered 2027-06-24 to Devin Stoll Ltd",
])
def test_received_declaration_cannot_create_a_sender_grant(provenance):
    design = _design(provenance)
    assert author_context.projection(design, {})["downstream"]["received_ids"] == [STATEMENT.id]
    with pytest.raises(ValueError, match="sender grant"):
        author_delivery.projection(design, {})


@pytest.mark.parametrize("corruption", [
    None, "missing_grant", "wrong_recipient", "wrong_date", "modified_attachment", "legacy_approval",
])
def test_dispatch_binds_the_independently_reviewed_delivery_to_the_actual_sender_receipt(corruption):
    design = _design("The account service officer sends his statement.\nDelivered 2027-06-24 to Devin Stoll")
    projected = author_delivery.projection(design, {})
    request = {"author_brief": projected["downstream"]["author_brief"],
               "received_correspondence": commissioning.json_text([STATEMENT.model_dump()])}
    if corruption == "modified_attachment":
        request["received_correspondence"] = request["received_correspondence"].replace("82,600", "92,600")

    originating_brief = projected[STATEMENT.id]["author_brief"]
    grants = commissioning._read_json(originating_brief)["outgoing_deliveries"]
    if corruption == "missing_grant":
        grants = []
    if corruption == "wrong_recipient":
        grants[0]["recipient"] = "The trustees"
    if corruption == "wrong_date":
        grants[0]["sent_on"] = "2027-06-30"

    def committed(stage, job, role, result):
        assert stage == "author"
        if role == "audit":
            assert job == author_context.JOB
            approved = {"participant_packets": projected}
            if corruption != "legacy_approval":
                approved["delivery_attestation"] = 1
            return (result(verdict="accept", findings={key: "Reviewed." for key in projected}, objections=[]),
                    {}, {"inputs": {"audit_rules": commissioning.json_text(approved)}})
        assert role == "author" and job == "author-upstream"
        return (result(title=STATEMENT.title, text=STATEMENT.text, deliveries=grants), {},
                {"inputs": {"author_brief": originating_brief}})

    from benchmark_v3.batch.sessions import SessionRunner

    ledger = SimpleNamespace(attempts=lambda _: [{"job": "author-upstream", "revision": 1}])
    runner = SessionRunner(ledger, None, "T", 2, Path("/custody/T/2"), "fixture")
    from unittest.mock import patch
    with patch.object(SessionRunner, "committed_result", side_effect=committed):
        if corruption is None:
            author_delivery.require_projection(runner, "author-downstream", request)
        else:
            with pytest.raises((ValueError, packet.PacketIsolationError)):
                author_delivery.require_projection(runner, "author-downstream", request)


def test_future_attachment_cannot_be_authorised_by_a_valid_sender_grant():
    design = _design("A personally transmitted copy.\nDelivered 2027-06-24 to Devin Stoll", day="2027-06-23")
    with pytest.raises(ValueError, match="future correspondence"):
        author_delivery.projection(design, {})


def test_a_large_whole_file_confirmation_cannot_satisfy_targeted_mask_coverage():
    from benchmark_v3.batch import audit_boundary, science

    sources = [Source(id=f"record-{i}", title="Record", text=f"Text {i}.") for i in range(21)]
    edge = ("Edda Kaul", "trustee_of", "Barker Trust")
    whole = audit_boundary.MaskAssignment(
        condition="T000", risk="large_or_complex", reason="Independent full-file view.",
        question="What relationships does the record establish?", included=[source.id for source in sources],
        present=[edge], absent=[],
    )
    targeted = whole.model_copy(update={"included": whole.included[:-1]})
    audit = audit_boundary.MilestoneAudit(
        verdict="accept", summary="Independent controls.", completeness={}, sufficiency={}, negative_controls={},
        shortcuts={}, matched_controls={}, risks=["large_or_complex"], masks=[whole, targeted],
        objections=[], limitations=[],
    )
    assert audit_boundary.targeted_audit(audit, {"T000": sources}).masks == [targeted]
    assert audit_boundary.large_confirmation(whole, sources)
    with pytest.raises(ValueError, match="must remove evidence"):
        science.mask_sources(whole, sources)
    assert not audit_boundary.large_confirmation(whole.model_copy(update={"risk": "shortcut"}), sources)
