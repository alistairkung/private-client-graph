import json
from pathlib import Path

import pytest

from benchmark_v3 import commissioning, design_candidate, packet
from benchmark_v3.portfolio import Portfolio


@pytest.fixture
def candidate_slot():
    portfolio = Portfolio.model_validate_json(commissioning.trusted_bytes(
        "planning/development-20/portfolio.json",
    ))
    return next(slot for slot in portfolio.slots if slot.family_id == "M")


def test_candidate_stages_only_exact_unapproved_proposal(candidate_slot):
    request = {
        "inputs": {
            "hypothesis_revision": "former-name-explicit-link@1",
            "portfolio_slot": candidate_slot.model_dump_json(),
        },
    }
    design_candidate.prepare(request)
    brief = json.loads(request["inputs"]["capability_brief"])
    assert brief["proposal"] == candidate_slot.hypothesis.model_dump()
    assert "commission" not in brief
    assert request["candidate_design"] is True
    with pytest.raises(ValueError, match="human-approved"):
        commissioning.approved_hypothesis("former-name-explicit-link@1")


def test_candidate_cannot_change_the_proposed_scenario(candidate_slot):
    changed = candidate_slot.model_copy(update={"natural_condition": "Different scenario"})
    with pytest.raises(ValueError, match="differs from the registered proposal"):
        design_candidate.prepare({"inputs": {
            "hypothesis_revision": "former-name-explicit-link@1",
            "portfolio_slot": changed.model_dump_json(),
        }})


def test_command_line_candidate_requires_reservation(tmp_path: Path, candidate_slot):
    (tmp_path / "request.json").write_text(json.dumps({
        "role": "designer", "model": "fixture", "effort": "high",
        "rationale": "Check offline gate", "parent": None, "prompt": "candidate-designer-v1",
        "inputs": {"hypothesis_revision": "former-name-explicit-link@1",
                   "portfolio_slot": candidate_slot.model_dump_json()},
    }))
    with pytest.raises(packet.PacketError, match="require a design-only reservation"):
        packet.run_packet(tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {"request.json"}


def test_validation_checks_literal_in_its_chronological_source(candidate_slot):
    slot = candidate_slot.model_copy(update={"expected_sources": 2})
    ordinary = ("Alix Emery", "parent_of", "Nell Emery")
    critical = ("Sam Niles", "parent_of", "Jo Niles")
    design = design_candidate.CandidateDesign.model_validate({
        "neutral_brief": "Check estate papers before a meeting.",
        "cutoff": "2026-04-14",
        "documentary_references": ["Civil registration"],
        "private_history": "Fixture history.",
        "inventory": [
            {"source_id": "s1", "author": "First person", "created_on": "2026-04-13",
             "provenance": "Original message", "participant_brief": "Report the account.",
             "received": []},
            {"source_id": "s2", "author": "Second person", "created_on": "2026-04-14",
             "provenance": "Received verified papers", "participant_brief": "Record entry: verified",
             "received": ["s1"]},
        ],
        "matched": [{"kind": "literal_edit", "edit": {"source_id": "s2", "before": "verified",
                                                      "after": "open"}}],
        "candidates": [critical], "required": {"M000": [critical], "M001": []},
        "expected_graphs": {"M000": [ordinary, critical], "M001": [ordinary]},
        "evidence_routes": {"M000": ["Joint s1 and s2"], "M001": ["Ordinary s1"]},
        "knowledge_boundaries": ["Only the second author has both items."],
        "documentary_assumptions": ["Both records reach the adviser."],
        "shortcut_predictions": ["A fixed-name guess fails."],
        "independent_review_plan": ["Two readers per condition."],
        "open_questions": ["Verify the record form."],
        "approximate_source_words": {"s1": 70, "s2": 100},
    })
    design_candidate.verify_candidate(slot, design)
    mismatched = design.matched[0].model_copy(update={
        "edit": design.matched[0].edit.model_copy(update={"source_id": "s1"}),
    })
    with pytest.raises(ValueError, match="baseline instruction"):
        design_candidate.verify_candidate(slot, design.model_copy(update={"matched": [mismatched]}))
