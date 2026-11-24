import json
from datetime import datetime, UTC
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmark_v3 import commissioning, packet
from benchmark_v3.coverage import render_coverage
from benchmark_v3.research_contracts import (
    Hypothesis,
    HypothesisRef,
    OwnerDecision,
    PlanningRecord,
    PlanningResult,
    ReconciliationContext,
    ReconciliationRecord,
    ReconciliationResult,
    SessionProvenance,
)

_ROOT = Path(__file__).resolve().parents[1] / "benchmark_v3"
_PROVENANCE = SessionProvenance(
    session="test-session",
    packet_sha256="a" * 64,
    prompt_sha256="b" * 64,
    output_sha256="c" * 64,
    model="test-model",
    effort="medium",
    completed_at=datetime(2026, 11, 22, 3, tzinfo=UTC),
)


@pytest.fixture
def hypothesis():
    return {
        "schema_version": 1,
        "hypothesis_id": "amendment-scope",
        "revision": 1,
        "previous_revision_sha256": None,
        "family_id": "D",
        "title": "Scoped corrections",
        "status": "proposed",
        "grounding": {
            "legal_workflow": "Private-client file reconciliation.",
            "retainer": "Review an existing trust file.",
            "meeting_purpose": "Confirm what the instruments establish.",
            "documentary_situation": "A supplemental instrument has a bounded scope.",
            "confidence": "provisional",
            "references": [],
            "assumptions": ["A custodian can supply the amendment with its parent instrument."],
            "practitioner_unknowns": ["Actual distribution of such records."],
        },
        "objective": {
            "primary_axis": "versions-and-amendments",
            "secondary_axes": ["documentary-authority"],
            "failure_mechanism": "Treat the latest supplement as a full replacement.",
            "falsifiable_hypothesis": "Only relationships governed by the amended clause should change.",
            "coverage_gap": "Existing variants do not test the scope of an override.",
        },
        "design": {
            "scenario": "Reconcile a certified amendment and parent instrument.",
            "genres_and_provenance": ["Original instrument and archive-supplied supplement."],
            "intervention": "Vary which provision is amended.",
            "invariants": ["Hold unrelated authority and relationships fixed."],
            "expected_sensitivity_or_invariance": "Change only the affected relationship.",
            "negative_controls": ["Hold a separately supported edge invariant."],
            "evidence_dependencies": ["Require the scope clause and original role evidence."],
            "shortcut_heuristics": ["Picking the newest document alone."],
            "success_criteria": ["Independent readers agree and a scope mask defeats the target decision."],
        },
        "feasibility": {
            "conditions": 2,
            "documentary_complexity": "Two governing Sources and one administrative record.",
            "authoring_and_review_effort": "Three perspectives and four blind readings plus masking.",
            "ontology_compatibility": "Existing named person-to-trust relationships.",
            "infrastructure_reuse": "Matched fixture replay and same-edge proof.",
            "risks_and_limits": ["An unintended complete restatement could bypass the test."],
        },
    }


@pytest.fixture
def custody(tmp_path, monkeypatch):
    monkeypatch.setattr(commissioning, "_ROOT", tmp_path)
    for directory in ("rounds", "decisions", "reconciliations"):
        (tmp_path / "planning" / directory).mkdir(parents=True)
    register = json.loads((_ROOT / "coverage.json").read_bytes())
    register["families"] = []
    _write_json(tmp_path / "coverage.json", register)
    for prompt in (commissioning.ARCHITECT_PROMPT, commissioning.DESIGNER_PROMPT, "instructions/ontology.md"):
        path = tmp_path / prompt
        path.parent.mkdir(exist_ok=True)
        path.write_bytes((_ROOT / prompt).read_bytes())
    return tmp_path


def _write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _register_proposal(custody, hypothesis, provenance=_PROVENANCE):
    proposal = Hypothesis.model_validate(hypothesis)
    plan = PlanningRecord(
        schema_version=1,
        provenance=provenance,
        result=PlanningResult(
            schema_version=1, portfolio_summary="A controlled amendment comparison.",
            family_assessments=[], gaps=[], proposals=[proposal], stopping_criteria=["Stop after one audit."],
        ),
    )
    (custody / "planning/rounds" / f"r{proposal.revision}.json").write_text(plan.model_dump_json())
    return commissioning.hypothesis_ref(proposal, provenance)


def _record_decision(custody, ref, status="approved", **changes):
    decision = OwnerDecision.model_validate({
        **ref.model_dump(), "schema_version": 1, "status": status,
        "owner": "Test owner", "decided_on": "2026-11-22", "decision_reference": "Test owner message",
    } | changes)
    path = custody / "planning/decisions" / f"{ref.hypothesis_id}@{ref.revision}.json"
    path.write_text(decision.model_dump_json(), encoding="utf-8")


def _designer_request(tmp_path, key, **changes):
    directory = tmp_path / "packet"
    directory.mkdir(exist_ok=True)
    _write_json(directory / "request.json", {
        "role": "designer", "model": "test-model", "effort": "medium",
        "rationale": "Only record the allocation outside the model turn.", "parent": None,
        "inputs": {"hypothesis_revision": key}, "prompt": "commissioned-designer-v1",
    } | changes)
    return directory


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("grounding", "assumptions", []),
        ("grounding", "confidence", "documented"),
        ("objective", "falsifiable_hypothesis", " "),
        ("design", "intervention", ""),
        ("design", "success_criteria", []),
        ("design", "source_quotes", ["private text"]),
        ("feasibility", "conditions", 1),
    ],
)
def test_hypothesis_requires_grounding_contrasts_and_feasibility(hypothesis, section, field, value):
    hypothesis[section][field] = value
    with pytest.raises(ValidationError):
        Hypothesis.model_validate(hypothesis)


def test_designer_accepts_only_an_exact_owner_approved_revision(custody, hypothesis):
    ref = _register_proposal(custody, hypothesis)
    directory = _designer_request(custody, "amendment-scope@1")

    with pytest.raises(packet.PacketError, match="human-approved hypothesis"):
        packet.run_packet(directory)
    assert set(item.name for item in directory.iterdir()) == {"request.json"}

    _record_decision(custody, ref, "returned")
    with pytest.raises(packet.PacketError, match="human-approved hypothesis"):
        packet.run_packet(directory)

    _record_decision(custody, ref, hypothesis_sha256="0" * 64)
    with pytest.raises(packet.PacketError, match="exact hypothesis revision digest"):
        packet.run_packet(directory)

    _record_decision(custody, ref)
    request = packet._read_request(directory)
    brief = json.loads(request["inputs"]["capability_brief"])
    assert set(request["inputs"]) == {"capability_brief"}
    assert brief["commission"] == ref.model_dump()
    assert brief["family_id"] == "D"
    assert brief["capability_question"] == hypothesis["objective"]["falsifiable_hypothesis"]
    assert hypothesis["objective"]["coverage_gap"] not in json.dumps(brief)
    assert _PROVENANCE.session not in json.dumps(brief)
    assert not (custody / "family_d").exists()

    _designer_request(custody, "amendment-scope@1", prompt="Attach the research deliberation.")
    with pytest.raises(packet.PacketError, match="versioned prompt"):
        packet.run_packet(directory)


def test_revision_preserves_provenance_and_does_not_inherit_approval(custody, hypothesis):
    original = _register_proposal(custody, hypothesis)
    _record_decision(custody, original)
    revised = {**hypothesis, "revision": 2, "previous_revision_sha256": original.hypothesis_sha256}
    ref = _register_proposal(
        custody, revised, _PROVENANCE.model_copy(update={"session": "new-session"}),
    )

    history = commissioning.proposal_history()
    assert history["amendment-scope@1"][1] == original
    assert history["amendment-scope@2"][1] == ref
    assert commissioning.hypothesis_ref(Hypothesis.model_validate(revised), _PROVENANCE) != ref
    with pytest.raises(ValueError, match="human-approved"):
        commissioning.designer_brief("amendment-scope@2")

    _record_decision(custody, ref)
    assert commissioning.designer_brief("amendment-scope@2")["commission"] == ref.model_dump()

    _register_proposal(custody, {**revised, "previous_revision_sha256": "d" * 64})
    (custody / "planning/decisions/amendment-scope@2.json").unlink()
    with pytest.raises(ValueError, match="Invalid revision lineage"):
        commissioning.proposal_history()


def test_approval_lookup_rejects_path_and_symlink(custody, hypothesis):
    ref = _register_proposal(custody, hypothesis)
    with pytest.raises(ValueError, match="revision identifier"):
        commissioning.designer_brief("../../sealed@1")
    outside = custody.parent / "sealed-sentinel.json"
    outside.write_text("must remain unread", encoding="utf-8")
    (custody / "planning/decisions/amendment-scope@1.json").symlink_to(outside)
    with pytest.raises(ValueError, match="Unsafe custodian artifact"):
        commissioning.designer_brief(f"{ref.hypothesis_id}@{ref.revision}")


def test_planning_validates_citations_axes_family_and_zero_proposals(custody, hypothesis):
    _, context = commissioning.prepare_architect({
        "research_specification": "Prebaseline scope.", "development_findings": "No admissions yet.",
        "practice_references": "[]",
    })
    result = {
        "schema_version": 1, "portfolio_summary": "A narrow gap.", "family_assessments": [],
        "gaps": [], "proposals": [hypothesis], "stopping_criteria": ["One defensible contrast."],
    }
    assert commissioning.validate_architect_result(json.dumps(result), context)
    result["proposals"] = []
    assert commissioning.validate_architect_result(json.dumps(result), context).proposals == []

    result["proposals"] = [hypothesis]
    hypothesis["grounding"]["references"] = [
        {"title": "Unsupplied reference", "url": "https://example.org", "relevance": "Claim"},
    ]
    with pytest.raises(ValueError, match="supplied public references"):
        commissioning.validate_architect_result(json.dumps(result), context)
    hypothesis["grounding"]["references"] = []
    hypothesis["objective"]["primary_axis"] = "unknown-axis"
    with pytest.raises(ValueError, match="unregistered difficulty"):
        commissioning.validate_architect_result(json.dumps(result), context)
    hypothesis["objective"]["primary_axis"] = "versions-and-amendments"
    hypothesis["family_id"] = "A"
    with pytest.raises(ValueError, match="admitted family ID"):
        commissioning.validate_architect_result(json.dumps(result), context)


def test_historical_admissions_and_rendered_register_match(v3_legacy_custody):
    register = commissioning.coverage_register()
    historical = [family for family in register.families if family.protocol == "historical"]
    assert {family.family_id for family in historical} == {"A", "B", "C"}
    for family in historical:
        commissioning.verify_coverage_family(family)
        assert family.hypothesis is None
        assert family.verified_findings
    assert (_ROOT / "COVERAGE.md").read_text() == render_coverage()


def test_reconciliation_is_post_admission_and_separate_from_intent(custody, hypothesis):
    ref = _register_proposal(custody, hypothesis)
    _record_decision(custody, ref)
    inputs = {
        "hypothesis_revision": "amendment-scope@1", "admission_dossier": "Admitted dossier excerpt.",
        "technical_findings": "The audit found a singleton proof.",
    }
    with pytest.raises(ValueError, match="admission.json"):
        commissioning.prepare_architect(inputs)
    directory = custody / "family_d"
    directory.mkdir()
    manifest = b'{"synthetic_manifest":"fixture"}'
    (directory / "manifest.json").write_bytes(manifest)
    admission = {
        "family": "D", "split": "development", "status": "pending_human_admission",
        "owner_decision": None,
        "manifest_sha256": commissioning.digest(manifest), "hypothesis": ref.model_dump(),
        "signature": {
            "source": "Owner decision", "recorded_at": "2026-11-22", "reviewed_commit": "a" * 40,
        },
    }
    _write_json(directory / "admission.json", admission)
    with pytest.raises(ValueError, match="recorded human admission"):
        commissioning.prepare_architect(inputs)
    admission.update(status="admitted", owner_decision="accept")
    _write_json(directory / "admission.json", admission)
    original_admission = (directory / "admission.json").read_bytes()
    visible, metadata = commissioning.prepare_architect(inputs)
    assert set(visible) == {"approved_hypothesis", "admission_dossier", "technical_findings", "coverage_register"}
    assert json.loads(visible["approved_hypothesis"]) == {
        "proposal": hypothesis, "approved_revision": ref.model_dump(),
    }
    assert metadata["admission"]["hypothesis"] == ref.model_dump()
    with pytest.raises(ValueError, match="reserves this Matter family ID"):
        commissioning.designer_brief("amendment-scope@1")
    assessment = {
        "schema_version": 1, "operationalisation": "invalidated_by_shortcut",
        "achieved_vs_intended": "A singleton established the target. The approved scope claim failed.",
        "verified_findings": [{
            "axis": "graph-completeness", "finding": "Unaffected relationships survive.",
            "evidence": ["Comparative audit, unchanged relationships"],
        }],
        "additional_coverage": "Invariant graph reconstruction only.",
        "redundancy": "Other families already verify retained relationships.",
        "remaining_gaps": [{"axes": ["versions-and-amendments"], "finding": "Still open."}],
        "recommendation": "refine_future_designs", "rationale": "Retain the admission and record the failed contrast.",
    }
    result = commissioning.validate_architect_result(json.dumps(assessment), metadata)
    assert isinstance(result, ReconciliationResult)
    record = ReconciliationRecord(
        schema_version=1, provenance=_PROVENANCE,
        context=ReconciliationContext.model_validate(metadata["admission"]), result=result,
    )
    (custody / "planning/reconciliations/D.json").write_text(record.model_dump_json())
    register_path = custody / "coverage.json"
    register = json.loads(register_path.read_bytes())
    register["families"] = [{
        "family_id": "D", "name": "Test family", "title": "Test family", "protocol": "architect_v1",
        "admission_sha256": commissioning.digest(original_admission), "hypothesis": ref.model_dump(),
        "primary_axis": hypothesis["objective"]["primary_axis"],
        "secondary_axes": hypothesis["objective"]["secondary_axes"],
        "intended_difficulty": hypothesis["objective"]["falsifiable_hypothesis"],
        "verified_findings": [], "incidental_challenges": ["Incidental context."],
        "matched_controls": ["Scope-only comparison."], "known_shortcuts_and_limits": ["Singleton proof."],
        "documentary_genres": ["Instruments"], "overlap": "Same invariant retention check.",
    }]
    _write_json(register_path, register)

    summary = render_coverage()
    assert "| versions and amendments |" in summary
    assert "**Graph completeness.** Unaffected relationships survive." in summary
    assert "**Versions and amendments.**" not in summary.split("## Difficulty taxonomy")[0]
    assert (directory / "admission.json").read_bytes() == original_admission

    _write_json(directory / "admission.json", admission | {"split": "held_out"})
    with pytest.raises(ValueError, match="recorded human admission"):
        commissioning.prepare_architect(inputs)

    admission["hypothesis"] = HypothesisRef(
        hypothesis_id=ref.hypothesis_id, revision=ref.revision, hypothesis_sha256="f" * 64,
    ).model_dump()
    _write_json(directory / "admission.json", admission)
    with pytest.raises(ValueError, match="approved hypothesis revision and digest"):
        commissioning.prepare_architect(inputs)


def test_legacy_custody_is_external_and_limited_to_fixture_paths(tmp_path, monkeypatch):
    fixture = tmp_path / "family_a" / "manifest.json"
    fixture.parent.mkdir()
    fixture.write_text("{}")
    monkeypatch.setenv("PCG_V3_LEGACY_CUSTODY", str(tmp_path))
    assert commissioning.development_artifact_path("family_a/manifest.json") == fixture
    assert commissioning.development_artifact_path("coverage.json") == _ROOT / "coverage.json"
    with pytest.raises(ValueError, match="Unsafe"):
        commissioning.development_artifact_path("family_a/../../other")
    monkeypatch.setenv("PCG_V3_LEGACY_CUSTODY", str(_ROOT))
    with pytest.raises(ValueError, match="external"):
        commissioning.development_artifact_path("family_a/manifest.json")


def test_existing_admissions_are_reserved_without_reading_legacy_keys(monkeypatch):
    monkeypatch.delenv("PCG_V3_LEGACY_CUSTODY", raising=False)
    assert commissioning._historical_or_admitted("D")
    assert commissioning._historical_or_admitted("DB")
    assert not commissioning._historical_or_admitted("V")
    with pytest.raises(ValueError, match="Missing custodian artifact"):
        commissioning.trusted_bytes("family_a/manifest.json")
