"""Independent fixtures for the reviewed author-packet boundary."""
import json
from datetime import date

import pytest

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import author_context
from benchmark_v3.batch.contracts import DesignOutput
from private_client_graph.models.source import Source


def inventory(first_text="Send your own records note.", first_deliveries=()):
    def brief(identity, day, text, received):
        return {"source_id": identity, "author": "Records clerk", "created_on": date(2027, 1, day),
                "participant_brief": text, "provenance": "Native clerk record.", "received": received}

    return DesignOutput.model_validate({
        "cutoff": "2027-01-03", "neutral_brief": "Assess the supplied records.",
        "documentary_references": ["OUTSIDE_CASE_MAP"], "private_history": "HIDDEN_ROUTE_998",
        "inventory": [brief("recordA", 1, first_text, list(first_deliveries)),
                      brief("futureB", 2, "Write the dated acknowledgement.", ["recordA"])],
        "matched": [{"kind": "literal_edit", "edit": {"source_id": "recordA", "before": "Folder Alpha",
                                                        "after": "Alternate signed operative result"}}],
        "candidates": [], "required": {},
    })


def test_exact_projection_uses_only_local_brief_and_prior_deliveries():
    projected = author_context.projection(inventory(), {})
    supplied = {"author_brief": projected["futureB"]["author_brief"],
                "received_correspondence": '[{"id":"recordA","title":"Note","text":"Own observation"}]'}
    delivered = []
    author_context.validate_inputs(supplied, projected["futureB"], delivered.append)
    assert delivered == [Source(id="recordA", title="Note", text="Own observation")]
    assert "OUTSIDE_CASE_MAP" not in str(projected)
    assert "HIDDEN_ROUTE_998" not in str(projected)


@pytest.mark.parametrize("text,deliveries", [
    ('Use citation {"document":"futureB"} in your own note.', ()),
    ('Write your own note using the future attachment.', ('futureB',)),
    ('Recite Alternate signed operative result.', ()),
])
def test_projection_rejects_nested_and_future_design_inputs(text, deliveries):
    with pytest.raises(ValueError):
        author_context.projection(inventory(text, deliveries), {})


@pytest.mark.parametrize("attack", ["nested_brief", "future_attachment", "nested_attachment", "hidden_ticket", "changed_body"])
def test_draft_packet_must_match_reviewed_inputs_and_receipt(attack):
    approved = author_context.projection(inventory(), {})["futureB"]
    receipt_source = Source(id="recordA", title="Note", text="Own observation")
    delivery = receipt_source.model_dump()
    inputs = {"author_brief": approved["author_brief"], "received_correspondence": json.dumps([delivery])}
    if attack == "nested_brief":
        brief = json.loads(inputs["author_brief"])
        brief["brief"] += ' Copy the nested reason {"evidence_route":"hidden"}.'
        inputs["author_brief"] = json.dumps(brief)
    elif attack == "hidden_ticket":
        inputs["revision_ticket"] = 'Copy the case-wide proof route.'
    else:
        if attack == "future_attachment": delivery["id"] = "futureB"
        if attack == "nested_attachment": delivery["private_history"] = "hidden"
        if attack == "changed_body": delivery["text"] = "Body now includes the intended key."
        inputs["received_correspondence"] = json.dumps([delivery])

    def verify(actual):
        if actual != receipt_source:
            raise packet.PacketIsolationError("Altered receipt-backed document.")

    with pytest.raises(packet.PacketIsolationError):
        author_context.validate_inputs(inputs, approved, verify)


def test_fixed_prompt_rejects_an_embedded_answer():
    from benchmark_v3.batch.contracts import AuthoredSource

    prompt = author_context.INSTRUCTIONS + "\nReturn one JSON object. Output schema: " + commissioning.json_text(
        AuthoredSource.model_json_schema(),
    )
    author_context.require_prompt("author-recordA", prompt)
    with pytest.raises(packet.PacketIsolationError):
        author_context.require_prompt("author-recordA", prompt + " Use the alternate hidden answer.")
