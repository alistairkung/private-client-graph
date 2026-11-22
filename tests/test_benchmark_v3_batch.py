"""Exercise the coordinator with the real packet projection and a deterministic transport."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import adjudication_contract, admission, artifacts, authorisation, coordinator, custody, science
from benchmark_v3.batch.contracts import (
    AdmissionDecisions, AnnotationRecovery, AuthoredSource, BatchDecision, BatchManifest, BudgetAmendment,
    DeferredExceptionReview, DesignOutput, DesignReview, FamilyContinuation, PilotDecision, SourceCutoffRecovery,
)
from benchmark_v3.batch.ledger import BudgetExhausted, TaskHalted
from benchmark_v3.batch.sessions import Blocked
from benchmark_v3.portfolio import Portfolio
from benchmark_v3.replay_manifest import BatchSourceFreeze, load_family, source_commitments
from private_client_graph.models.source import Source
from private_client_graph.research.retained_inputs import value_digest
from test_benchmark_v3_architect import _record_decision, _register_proposal, custody as architect_root, hypothesis


OWNER = "Test owner"
TODAY = date(2026, 11, 22)
ROOT = Path(commissioning.__file__).parent
EDGE = ["Test Parent", "parent_of", "Test Child"]
QUOTE = "Test Parent is the parent of Test Child."
BOUNDARY = b'{"inside":{"returncode":0,"denied":false,"matched_inside_count":true},' \
           b'"outside":{"denied":true,"matched_inside_count":false},' \
           b'"repository":{"denied":true,"matched_inside_count":false}}'


@pytest.fixture
def approved(architect_root, hypothesis, tmp_path):
    for name in ("batch-designer-v1.md", "batch-portfolio-v1.md", "annotation.md"):
        (architect_root / "instructions" / name).write_bytes((ROOT / "instructions" / name).read_bytes())
    refs = []
    slots = []
    for family, revision in (("G", 1), ("H", 2), ("I", 3), ("J", 4)):
        # Register v2 natural-only proposals in independent planning rounds.
        proposal = hypothesis | {
            "schema_version": 2, "hypothesis_id": f"test-{family.lower()}", "family_id": family,
            "feasibility": hypothesis["feasibility"] | {"conditions": 1},
        }
        ref = _register_proposal(architect_root, proposal)
        round_path = architect_root / "planning" / "rounds"
        (round_path / "r1.json").rename(round_path / f"test-{revision}.json")
        _record_decision(architect_root, ref)
        refs.append({"family_id": family, "hypothesis": ref, "sessions": 10})
        slots.append({
            "family_id": family, "hypothesis": ref,
            "primary_axis": proposal["objective"]["primary_axis"],
            "secondary_axes": proposal["objective"]["secondary_axes"],
            "tier": "routine", "expected_sources": 2,
            "natural_condition": "Natural record.", "matched_conditions": [],
            "retainer": proposal["grounding"]["retainer"], "workflow": proposal["grounding"]["legal_workflow"],
            "estimated_sessions": 9, "estimated_cost_usd": None, "independent_authoring": ["Separate roles."],
        })
    coverage, existing = authorisation.admitted_coverage()
    portfolio = Portfolio.model_validate({
        "schema_version": 1, "portfolio_id": "test-portfolio", "revision": 1, "previous_revision_sha256": None,
        "namespace": "development", "target_families": 20, "architect_session": "fake-architect",
        "coverage_sha256": coverage, "existing": existing, "slots": slots, "admission_criteria": ["Independent review."],
        "stopping_criteria": ["Stop at allocation."], "gaps": [],
    })
    manifest = BatchManifest.model_validate({
        "schema_version": 1, "task_id": "test-task", "batch_id": "test-pilot", "namespace": "development",
        "phase": "pilot", "portfolio_sha256": authorisation.commitment(portfolio), "families": refs[:3],
        "task_session_ceiling": 37,
        "scope": {
            "profile": "benchmark_packet", "packet_implementation_sha256": commissioning.digest(
                Path(packet.__file__).read_bytes(),
            ),
            "os_boundary_evidence_sha256": commissioning.digest(BOUNDARY), "custodian": OWNER,
            "scope_reference": "Fixture OS checks.",
        },
        "models": {role: {"model": "test-only", "effort": "medium", "rationale": "Saved output fixture."}
                   for role in ("designer", "author", "realism", "annotation", "adjudication", "audit", "masked")},
        "stop_conditions": ["Stop at the approved allowance."],
    })
    decision = _approval(portfolio, manifest)
    return coordinator.open_ledger(tmp_path / "task"), coordinator.Commission(portfolio, manifest, decision)


def _approval(portfolio, manifest):
    return BatchDecision.model_validate({
        "schema_version": 1, "manifest_sha256": authorisation.commitment(manifest),
        "portfolio": {
            "schema_version": 1, "portfolio_sha256": authorisation.commitment(portfolio), "status": "approved",
            "owner": OWNER, "decided_on": TODAY, "decision_reference": "Fixture owner portfolio approval.",
        },
        "owner": OWNER, "decided_on": TODAY, "decision_reference": "Fixture owner budget approval.",
    })


class Interrupted(BaseException):
    pass


@pytest.fixture
def transport(monkeypatch, tmp_path):
    calls = []
    behavior = {}
    local = threading.local()
    run_packet = packet.run_packet

    def run(directory, *, before_turn):
        request = json.loads((directory / "request.json").read_bytes())
        local.request = request
        local.job = directory.name
        family = request["parent"].split("@")[0]
        key = (family, local.job)
        mode = behavior.get(key)
        if mode == "uncertain":
            raise OSError("Interrupted before receiving a terminal receipt.")
        run_packet(directory, before_turn=before_turn)
        if mode == "interrupt_after_receipt":
            raise Interrupted()

    def isolation(_codex, _workspace, request):
        family = request["parent"].split("@")[0]
        if behavior.get((family, local.job)) == "isolation":
            raise packet.PacketIsolationError("Fixture sandbox negative control failed.")
        return {
            "thread_id": uuid4().hex, "codex_session_id": uuid4().hex,
            "model": request["model"], "effort": request["effort"], "provider": "openai",
            "ephemeral": True, "empty_workspace": True, "approval_policy": "never",
            "permission_profile": {"id": "benchmark_packet", "extends": None},
            "sandbox": {"type": "readOnly", "networkAccess": False},
            "instruction_sources": [], "thread_environments": [], "runtime_workspace_roots": [],
        }

    def turn(_codex, _thread, message, _effort):
        request = local.request
        family = request["parent"].split("@")[0]
        mode = behavior.get((family, local.job))
        inputs = json.loads(message)["inputs"]
        calls.append((family, request["parent"], local.job, inputs))
        if mode == "failed":
            raise packet.PacketError("Fixture provider did not complete.")
        if callable(mode):
            result = mode(inputs)
        elif mode == "return" or mode == "repair" and request["parent"].endswith("@1"):
            result = {
                "verdict": mode, "summary": "Fixture documentary objection.",
                "source_findings": {"src1": "Needs provenance.", "src2": "Plausible."},
                "objections": ["Fixture issue."],
                "repair_tickets": {"src1": "Clarify the sender's role."} if mode == "repair" else {},
            }
        else:
            result = _output(request["role"], family, local.job, inputs)
        return {"text": json.dumps(result), "turn_id": uuid4().hex, "observed_tool_actions": [],
                "usage": {"total": {"totalTokens": 12}}}

    monkeypatch.setattr(packet, "run_packet", run)
    monkeypatch.setattr(packet, "_create_runtime", lambda: TemporaryDirectory(dir=tmp_path))
    monkeypatch.setattr(packet, "_server_command", lambda *_: [])
    monkeypatch.setattr(packet, "_Codex", lambda *_: nullcontext())
    monkeypatch.setattr(packet, "_start_checked_thread", isolation)
    monkeypatch.setattr(packet, "_run_turn", turn)
    return calls, behavior, run


def _design(family, count=2):
    return {
        "neutral_brief": "Review a synthetic record.", "cutoff": TODAY.isoformat(),
        "documentary_references": [], "private_history": "Private fixture history marker.",
        "inventory": [
            {"source_id": f"src{index}", "author": f"Writer {index}", "created_on": TODAY.isoformat(),
             "provenance": "Direct synthetic handoff.", "participant_brief": f"Write record {index}.", "received": []}
            for index in range(1, count + 1)
        ],
        "matched": [], "candidates": [EDGE], "required": {f"{family}000": [EDGE]},
    }


def _output(role, family, job, inputs):
    if role == "designer":
        assert json.loads(inputs["capability_brief"])["approved_workload"]["expected_sources"] == 2
        return _design(family)
    if role == "author":
        assert "Private fixture history marker." not in str(inputs)
        return {"title": "Test record", "text": QUOTE if job == "author-src1" else "Ordinary synthetic note."}
    condition = f"{family}000"
    edge_key = commissioning.json_text(EDGE)
    candidate = {"source_name": EDGE[0], "target_name": EDGE[2], "relationship_type": EDGE[1],
                 "source_id": "src1", "supporting_text": QUOTE}
    proof = {"source_id": "src1", "supporting_text": QUOTE}
    if role in {"annotation", "masked"}:
        assert "intended_intervention" not in inputs
        assert "Private fixture history marker." not in str(inputs)
        sources = json.loads(inputs["sources"])
        return {"candidates": {"relationships": [candidate] if any(QUOTE in s["text"] for s in sources) else []},
                "reviewed_sources": [source["id"] for source in sources], "open_questions": []}
    if role == "realism":
        return {"verdict": "pass", "summary": "Fixture realism pass.",
                "source_findings": {"src1": "Purpose recorded.", "src2": "Ordinary note."}}
    if role == "adjudication":
        assert "intended_intervention" not in inputs
        return {
            "key": {
                "condition": "local",
                "truth": {
                    "entities": [{"id": "p1", "type": "person", "name": EDGE[0]},
                                 {"id": "p2", "type": "person", "name": EDGE[2]}],
                    "relationships": [{"source": "p1", "type": EDGE[1], "target": "p2",
                                       "approved_evidence": [QUOTE]}],
                },
                "source_approval": {
                    "schema_version": 1, "relationships": [
                        {"source": "p1", "type": EDGE[1], "target": "p2", "approved_evidence": [proof]},
                    ],
                },
                "ideal": {"relationships": [candidate]},
                "sufficient_evidence": [{"edge": EDGE, "alternatives": [[proof]]}],
            },
            "disagreement_resolutions": {}, "source_audit": {"src1": "One edge.", "src2": "Neutral."},
            "unresolved": [],
        }
    assert role == "audit"
    return {
        "verdict": "accept", "summary": "Fixture audit pass.", "objections": [], "limitations": ["Fixture only."],
        "completeness": {condition: {"src1": "Edge accounted for.", "src2": "No assertion."}},
        "sufficiency": {condition: {edge_key: "Direct exact proof."}},
        "negative_controls": {condition: "No sibling edge."},
        "shortcuts": {condition: "None observed in this fixture."},
        "matched_controls": {condition: "Natural condition only."}, "risks": [], "masks": [],
    }


def _run(approved):
    ledger, commission = approved
    coordinator.commission_batch(ledger, commission, BOUNDARY)
    coordinator.run_batch(ledger, commission.manifest.batch_id)
    return ledger, commission.manifest.batch_id


def _status(ledger, batch):
    return {row: coordinator.family_status(ledger, batch, row)[1] for row in "GHI"}


def test_admitted_starting_coverage_is_five_families_and_twelve_conditions():
    _, coverage = authorisation.admitted_coverage()
    assert [item.family_id for item in coverage] == list("ABCDF")
    assert sum(len(item.conditions) for item in coverage) == 12
    assert json.loads((ROOT / "family_e" / "admission.json").read_bytes())["status"] == "returned"


def test_commission_requires_exact_owner_approvals_and_scope(approved, architect_root):
    ledger, commission = approved
    changed = commission.portfolio.model_copy(update={"stopping_criteria": ["Different."]})
    with pytest.raises(ValueError, match="exact portfolio"):
        coordinator.commission_batch(ledger, coordinator.Commission(changed, commission.manifest, commission.decision), BOUNDARY)
    with pytest.raises(ValueError, match="isolation evidence"):
        coordinator.commission_batch(ledger, commission, b"{}")
    (architect_root / "planning" / "decisions" / "test-g@1.json").unlink()
    with pytest.raises(ValueError, match="exact hypothesis approval"):
        coordinator.commission_batch(ledger, commission, BOUNDARY)


def test_batch_demo_resume_package_and_consolidated_admission(approved, transport):
    calls, behavior, _ = transport
    behavior["H", "realism-000"] = "return"
    ledger, batch = _run(approved)
    assert _status(ledger, batch) == {"G": "admission_ready", "H": "returned", "I": "admission_ready"}
    assert len(calls) == 20
    coordinator.run_batch(ledger, batch)
    assert len(calls) == 20
    path, summary_digest = admission.package_batch(ledger, batch)
    assert "[G](" in path.read_text()
    rows = {row["family_id"]: row for row in json.loads(path.with_name("summary.json").read_bytes())["families"]}
    assert rows["G"]["charged_attempts"] == rows["G"]["unpriced_attempts"] == 8
    pilot = PilotDecision(schema_version=1, pilot_batch_id=batch, summary_sha256=summary_digest,
                          status="continue", owner=OWNER, decision_reference="Fixture decision.", decided_on=TODAY)
    admission.record_pilot_review(ledger, pilot)
    decisions = AdmissionDecisions.model_validate({
        "schema_version": 1, "batch_id": batch, "owner": OWNER, "decided_on": TODAY,
        "source": "Explicit fixture decision.", "reviewed_commit": "a" * 40,
        "decisions": [
            {"family_id": family, "family_sha256": rows[family]["family_sha256"], "disposition": disposition,
             "reason": "Fixture disposition."}
            for family, disposition in (("G", "accept"), ("I", "return"))
        ],
    })
    bad = decisions.decisions[1].model_copy(update={"family_sha256": "0" * 64})
    with pytest.raises(ValueError, match="exact technically reviewed dossier"):
        admission.record_admissions(ledger, decisions.model_copy(update={"decisions": [decisions.decisions[0], bad]}))
    assert _status(ledger, batch)["G"] == "admission_ready"
    records = admission.record_admissions(ledger, decisions)
    assert [json.loads(record.read_bytes())["status"] for record in records] == ["admitted", "returned"]
    assert admission.record_admissions(ledger, decisions) == records


@pytest.fixture
def design_gated(approved):
    ledger, initial = approved
    manifest = initial.manifest.model_copy(update={"schema_version": 2, "max_parallel_families": 3})
    commission = coordinator.Commission(initial.portfolio, manifest, _approval(initial.portfolio, manifest))
    coordinator.commission_batch(ledger, commission, BOUNDARY)
    return ledger, commission


def _design_approval(ledger, commission):
    preview = coordinator.preview_design_review(ledger, commission.manifest.batch_id)
    return DesignReview.model_validate(preview | {
        "schema_version": 1, "owner": OWNER, "decided_on": TODAY,
        "decision_reference": "Explicit fixture design review.",
    })


def test_stock_run_pauses_for_all_designs_and_reuses_them_after_review(design_gated, transport):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, _, _ = transport
    coordinator.run_batch(ledger, batch)
    assert set((family, job) for family, _, job, _ in calls) == {(family, "design") for family in "GHI"}
    assert all(len(ledger.attempts(family)) == 1 for family in "GHI")

    coordinator.run_batch(ledger, batch)
    assert len(calls) == 3
    runner = commission.session_runner(ledger, "G", 1)
    with pytest.raises(Blocked, match="accept this exact design"):
        runner.run("author", "author-src1", "author", {}, "Fixture author.", AuthoredSource)
    assert len(ledger.attempts("G")) == 1

    review = _design_approval(ledger, commission)
    with pytest.raises(ValueError, match="commissioning owner and exact manifest"):
        coordinator.record_design_review(ledger, review.model_copy(update={"owner": "Other owner"}))
    with pytest.raises(ValueError, match="commissioning owner and exact manifest"):
        coordinator.record_design_review(ledger, review.model_copy(update={"manifest_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="every exact committed design"):
        coordinator.record_design_review(ledger, review.model_copy(update={"designs": review.designs[:2]}))
    altered = review.designs[0].model_copy(update={"design_sha256": "0" * 64})
    with pytest.raises(ValueError, match="every exact committed design"):
        coordinator.record_design_review(ledger, review.model_copy(update={"designs": [altered, *review.designs[1:]]}))
    assert not ledger.events(batch)

    coordinator.record_design_review(ledger, review)
    coordinator.record_design_review(ledger, review)
    assert len(ledger.events(batch)) == 1
    coordinator.run_batch(ledger, batch)
    assert sum(job == "design" for _, _, job, _ in calls) == 3
    assert _status(ledger, batch) == dict.fromkeys("GHI", "admission_ready")


def test_mixed_design_review_releases_only_accepted_families(design_gated, transport):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, _, _ = transport
    coordinator.run_batch(ledger, batch)
    approval = _design_approval(ledger, commission)
    payload = approval.model_dump(mode="json")
    payload["schema_version"] = 2
    with pytest.raises(ValueError, match="returned design requires"):
        DesignReview.model_validate(payload | {
            "designs": [*payload["designs"][:2], payload["designs"][2] | {"disposition": "return"}],
        })
    payload["designs"][2].update(disposition="return", reason="Clarify the proof chain.")
    with pytest.raises(ValueError, match="every disposition to be explicit"):
        DesignReview.model_validate(payload | {
            "designs": [{k: v for k, v in payload["designs"][0].items() if k != "disposition"},
                        *payload["designs"][1:]],
        })
    review = DesignReview.model_validate(payload)
    coordinator.record_design_review(ledger, review)
    coordinator.record_design_review(ledger, review)
    with pytest.raises(ValueError, match="immutable"):
        coordinator.record_design_review(ledger, approval)
    for revision in (1, 2):
        runner = commission.session_runner(ledger, "I", revision)
        with pytest.raises(Blocked, match="accept this exact design"):
            runner.run("author", "author-src1", "author", {}, "Fixture author.", AuthoredSource)
    coordinator.run_batch(ledger, batch)
    assert _status(ledger, batch) == {
        "G": "admission_ready", "H": "admission_ready", "I": "pending_design_review",
    }
    assert [(family, job) for family, _, job, _ in calls if family == "I"] == [("I", "design")]
    assert len(ledger.attempts("I")) == 1
    [returned] = [row for row in ledger.events(batch, "I") if row["kind"] == "design_return"]
    assert returned["details"] == payload["designs"][2]


def test_design_review_rechecks_committed_bytes_before_any_author(design_gated, transport):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, _, _ = transport
    coordinator.run_batch(ledger, batch)
    review = _design_approval(ledger, commission)
    coordinator.record_design_review(ledger, review)
    design = commission.session_runner(ledger, "I", 1).directory / "design.json"
    design.chmod(0o600)
    design.write_bytes(design.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="committed design bytes changed"):
        coordinator.run_batch(ledger, batch)
    assert len(calls) == 3
    assert all(len(ledger.attempts(family)) == 1 for family in "GHI")


def test_design_only_resume_reopens_completed_receipts_without_authoring(design_gated, transport):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, behavior, _ = transport
    behavior["G", "design"] = "interrupt_after_receipt"
    with pytest.raises(Interrupted):
        coordinator.run_batch(ledger, batch)
    with pytest.raises(ValueError, match="no committed design"):
        _design_approval(ledger, commission)
    coordinator.run_batch(ledger, batch)
    assert len(_design_approval(ledger, commission).designs) == 3
    assert len(calls) == 3 and all(job == "design" for _, _, job, _ in calls)


def test_source_cutoff_recovery_preserves_packets_and_pauses_for_review(design_gated, transport, monkeypatch):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, _, _ = transport
    mock_turn = packet._run_turn

    def design_with_late_sources(codex, thread, message, effort):
        result = mock_turn(codex, thread, message, effort)
        brief = json.loads(message)["inputs"].get("capability_brief")
        if brief and json.loads(brief)["family_id"] in "HI":
            design = json.loads(result["text"])
            as_of = (TODAY - timedelta(days=1)).isoformat()
            design.update(
                cutoff=as_of, neutral_brief=f"Review what the file establishes as of {as_of}.",
                scaling_snapshots=[1, len(design["inventory"])],
            )
            result["text"] = json.dumps(design)
        return result

    monkeypatch.setattr(packet, "_run_turn", design_with_late_sources)
    coordinator.run_batch(ledger, batch)
    original_design = commission.session_runner(ledger, "G", 1).directory / "design.json"
    original_bytes = original_design.read_bytes()
    raw_packets = {
        path: path.read_bytes()
        for family in "GHI"
        for path in (commission.session_runner(ledger, family, 1).directory / "packets" / "design").iterdir()
    }
    responses = {
        family: commissioning.digest(raw_packets[
            commission.session_runner(ledger, family, 1).directory / "packets" / "design" / "output.txt"
        ])
        for family in "HI"
    }
    decision = SourceCutoffRecovery(
        schema_version=1, batch_id=batch, manifest_sha256=authorisation.commitment(commission.manifest),
        owner=OWNER, decided_on=TODAY, decision_reference="Fixture owner authorized cut-off recovery only.",
        responses=responses,
    )
    with pytest.raises(ValueError, match="exact completed designer response"):
        coordinator.recover_source_cutoffs(ledger, decision.model_copy(update={
            "responses": responses | {"I": "0" * 64},
        }))
    assert all(coordinator.family_status(ledger, batch, family)[2] for family in "HI")

    def no_dispatch(*_args, **_kwargs):
        pytest.fail("Offline recovery cannot dispatch a session.")

    with monkeypatch.context() as recovery:
        recovery.setattr(packet, "run_packet", no_dispatch)
        coordinator.recover_source_cutoffs(ledger, decision)
        coordinator.recover_source_cutoffs(ledger, decision)
        coordinator.run_batch(ledger, batch)
    assert len(calls) == 3
    assert all(len(ledger.attempts(family)) == 1 for family in "GHI")
    assert original_design.read_bytes() == original_bytes
    assert all(path.read_bytes() == original for path, original in raw_packets.items())
    for family in "HI":
        directory = commission.session_runner(ledger, family, 1).directory
        original = DesignOutput.model_validate_json(raw_packets[directory / "packets" / "design" / "output.txt"])
        assert json.loads((directory / "design.json").read_bytes()) == (
            original.model_dump(mode="json") | {"cutoff": TODAY.isoformat(), "scaling_snapshots": [1]}
        )
    assert not ledger.events(batch)
    coordinator.record_design_review(ledger, _design_approval(ledger, commission))
    coordinator.run_batch(ledger, batch)
    assert sum(job == "design" for _, _, job, _ in calls) == 3
    assert _status(ledger, batch) == dict.fromkeys("GHI", "admission_ready")


def test_dispatch_receipt_survives_interruption_without_repeat(approved, transport):
    calls, behavior, _ = transport
    behavior["G", "author-src1"] = "interrupt_after_receipt"
    with pytest.raises(Interrupted):
        _run(approved)
    ledger, commission = approved
    coordinator.run_batch(ledger, commission.manifest.batch_id)
    assert sum(family == "G" and job == "author-src1" for family, _, job, _ in calls) == 1
    assert _status(ledger, commission.manifest.batch_id)["G"] == "admission_ready"


def test_uncertain_dispatch_is_charged_and_requires_explicit_recovery(approved, transport):
    calls, behavior, original = transport
    behavior["G", "author-src1"] = "uncertain"
    ledger, batch = _run(approved)
    assert coordinator.family_status(ledger, batch, "G")[2]["code"] == "uncertain_dispatch"
    assert len(ledger.attempts("G")) == 2
    coordinator.run_batch(ledger, batch)
    assert not any(family == "G" and job == "author-src1" for family, _, job, _ in calls)
    with pytest.raises(ValueError, match="terminal receipt"):
        coordinator.reconcile_dispatch(ledger, batch, "G", "Fixture recovery request.")
    # Simulate a delayed receipt from the already reserved dispatch.
    del behavior["G", "author-src1"]
    runner = approved[1].session_runner(ledger, "G", 1)
    original(runner.directory / "packets" / "author-src1", before_turn=lambda: None)
    coordinator.run_batch(ledger, batch)
    assert _status(ledger, batch)["G"] == "author"
    coordinator.reconcile_dispatch(ledger, batch, "G", "Located the original terminal receipt.")
    coordinator.run_batch(ledger, batch)
    assert _status(ledger, batch)["G"] == "admission_ready"
    assert sum(family == "G" and job == "author-src1" for family, _, job, _ in calls) == 1


def test_shared_isolation_failure_stops_pending_workers(approved, transport):
    calls, behavior, _ = transport
    ledger, batch = approved
    manifest = batch.manifest.model_copy(update={"max_parallel_families": 1})
    behavior["G", "design"] = "isolation"
    coordinator.commission_batch(ledger, coordinator.Commission(batch.portfolio, manifest,
                                  _approval(batch.portfolio, manifest)), BOUNDARY)
    coordinator.run_batch(ledger, manifest.batch_id)
    assert len(ledger.attempts("G")) == 1
    assert not calls and not ledger.attempts("H") and not ledger.attempts("I")
    with pytest.raises(TaskHalted, match="isolation"):
        coordinator.run_batch(ledger, manifest.batch_id)


def test_altered_source_and_blind_output_cannot_dispatch_adjudicator(approved, transport, monkeypatch):
    calls, _, run = transport

    def change_after_blind(directory, *, before_turn):
        run(directory, before_turn=before_turn)
        if directory.name == "reading-000-b-full" and "G" in directory.parts:
            output = directory / "output.txt"
            output.chmod(0o600)
            output.write_text("{}")

    monkeypatch.setattr(packet, "run_packet", change_after_blind)
    ledger, batch = _run(approved)
    assert coordinator.family_status(ledger, batch, "G")[2]["code"] == "input_integrity"
    assert not any(family == "G" and job.startswith("adjudicate") for family, _, job, _ in calls)
    assert _status(ledger, batch)["H"] == "admission_ready"
    source = approved[1].session_runner(ledger, "H", 1).directory / "family" / "sources" / "H000.json"
    source.chmod(0o600)
    source.write_text("[]")
    with pytest.raises(ValueError, match="reviewed artifact bytes changed"):
        admission.package_batch(ledger, batch)


def test_global_and_family_ceilings_are_atomic(approved):
    ledger, commission = approved
    coordinator.commission_batch(ledger, commission, BOUNDARY)
    barrier = threading.Barrier(12)

    def reserve(index):
        barrier.wait(timeout=5)
        try:
            return ledger.reserve("G", 1, f"job-{index}", "design", {}, "digest")
        except BudgetExhausted:
            return False

    with ThreadPoolExecutor(max_workers=12) as executor:
        assert sum(executor.map(reserve, range(12))) == 10
    assert not ledger.reserve("G", 1, ledger.attempts("G")[0]["job"], "design", {}, "digest")
    for family in "HI":
        for index in range(10):
            assert ledger.reserve(family, 1, f"job-{index}", "design", {}, "digest")
    expansion = commission.manifest.model_copy(update={
        "batch_id": "expansion", "phase": "expansion",
        "families": [commission.manifest.families[0].model_copy(
            update={"family_id": "J", "hypothesis": commission.portfolio.slots[3].hypothesis},
        )],
    })
    commission2 = coordinator.Commission(commission.portfolio, expansion, _approval(commission.portfolio, expansion))
    with pytest.raises(ValueError, match="pilot review"):
        coordinator.commission_batch(ledger, commission2, BOUNDARY)
    ledger.event(commission.manifest.batch_id, None, 0, "pilot_decision", "owner", None, "continue", {})
    coordinator.commission_batch(ledger, commission2, BOUNDARY)
    for index in range(7):
        assert ledger.reserve("J", 1, f"job-{index}", "design", {}, "digest")
    with pytest.raises(BudgetExhausted, match="Task-wide"):
        ledger.reserve("J", 1, "overflow", "design", {}, "digest")
    assert len(coordinator.open_ledger(ledger.root).attempts("J")) == 7


def test_failed_dispatch_can_be_quarantined_without_affecting_other_workers(approved, transport):
    _, behavior, _ = transport
    behavior["G", "author-src1"] = "failed"
    ledger, batch = _run(approved)
    assert coordinator.family_status(ledger, batch, "G")[2]["code"] == "failed_dispatch"
    coordinator.quarantine(ledger, batch, "G", "Fixture failure disposition.")
    assert _status(ledger, batch) == {"G": "quarantined", "H": "admission_ready", "I": "admission_ready"}


def test_documentary_repair_reuses_unaffected_author_and_respects_allowance(approved, transport):
    calls, behavior, _ = transport
    behavior["G", "realism-000"] = "repair"
    ledger, batch = _run(approved)
    revision, _, exception = coordinator.family_status(ledger, batch, "G")
    assert revision == 2 and exception is None
    assert len(ledger.attempts("G")) == 10
    assert sum(family == "G" and job == "author-src2" for family, _, job, _ in calls) == 1
    assert sum(family == "G" and job == "realism-000" for family, _, job, _ in calls) == 2


def test_giant_inventory_requires_sections_and_full_file_coverage(approved):
    _, commission = approved
    slot = commission.portfolio.slots[0].model_copy(update={"expected_sources": 125, "tier": "giant"})
    payload = _design("G", 125)
    payload["sections"] = {"early": [f"src{i}" for i in range(1, 61)], "late": [f"src{i}" for i in range(61, 126)]}
    payload["scaling_snapshots"] = [20, 60, 100]
    design = DesignOutput.model_validate(payload)
    science.verify_design(slot, design)
    sources = [Source(id=row.source_id, title="Fixture", text="Test only.") for row in design.inventory]
    bundles, freeze = science.freeze_bundles(slot, design, sources)
    assert len(bundles["G000"]) == len(freeze.source_commitments["G000"]) == 125
    with pytest.raises(ValueError, match="complete dated inventory"):
        science.freeze_bundles(slot, design, sources[:-1])
    with pytest.raises(ValueError, match="section assignments"):
        science.verify_design(slot, design.model_copy(update={"sections": {}}))


def test_evaluation_custody_projects_only_public_taxonomy(tmp_path):
    brief = custody.EvaluationBrief(schema_version=1, namespace="evaluation", target_families=20,
                                    workloads={"routine": 20}, difficulty_axes=["entity-identity"],
                                    distribution="independent_matter_families")
    development, evaluation = tmp_path / "development", tmp_path / "sealed"
    projected = custody.evaluation_handoff(brief, development=development, evaluation=evaluation,
                                           role="evaluation_commissioner")
    assert set(projected) == set(custody.EvaluationBrief.model_fields)
    with pytest.raises(ValueError, match="Only the evaluation commissioner"):
        custody.evaluation_handoff(brief, development=development, evaluation=evaluation, role="development_author")
    with pytest.raises(ValueError, match="disjoint"):
        custody.evaluation_handoff(brief, development=development, evaluation=development / "sealed",
                                   role="evaluation_commissioner")
    with pytest.raises(ValueError, match="registered difficulty axes"):
        custody.evaluation_handoff(brief.model_copy(update={"difficulty_axes": ["private-answers"]}),
                                   development=development, evaluation=evaluation, role="evaluation_commissioner")
    with pytest.raises(ValueError, match="outside Git"):
        custody.private_directory(ROOT / "sealed")


def test_architect_portfolio_projection_binds_current_coverage_and_registered_revisions(approved):
    _, commission = approved
    inputs, metadata = commissioning.prepare_architect({
        "portfolio_specification": "Plan the development portfolio.",
        "development_findings": "Independently reviewed fixture findings.",
        "practice_references": "[]",
    })
    assert metadata["profile"] == "portfolio"
    assert json.loads(inputs["admitted_snapshot"])["coverage_sha256"] == commission.portfolio.coverage_sha256
    draft = commission.portfolio.model_dump(mode="json", exclude={"architect_session"})
    assert commissioning.validate_architect_result(json.dumps(draft), metadata).portfolio_id == "test-portfolio"
    draft["coverage_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="current admitted"):
        commissioning.validate_architect_result(json.dumps(draft), metadata)


def test_freeze_is_explicit_irreversible_and_binds_exact_snapshot(approved, transport):
    from benchmark_v3.batch import freeze

    _, behavior, _ = transport
    for family in "GHI":
        behavior[family, "realism-000"] = "return"
    ledger, batch = _run(approved)
    snapshot, digest = freeze.preview(ledger, batch)
    assert json.loads(snapshot.read_bytes())["admitted_families"] == 0
    decision = freeze.FreezeDecision(
        schema_version=1, batch_id=batch, snapshot_sha256=digest, disposition="freeze", owner=OWNER,
        decided_on=TODAY, decision_reference="Fixture freeze.", stopping_rationale="No eligible fixture families.",
    )
    with pytest.raises(ValueError, match="exact current"):
        freeze.record(ledger, decision.model_copy(update={"snapshot_sha256": "0" * 64}))
    frozen = freeze.record(ledger, decision)
    assert freeze.record(ledger, decision) == frozen
    with pytest.raises(TaskHalted, match="frozen"):
        coordinator.run_batch(ledger, batch)


def test_same_account_cannot_open_sealed_evaluation_ledger(tmp_path):
    import os

    with pytest.raises(ValueError, match="own OS account"):
        custody.evaluation_ledger_path(tmp_path / "sealed", development_uid=os.getuid(),
                                        role="evaluation_custodian")
    sealed = custody.evaluation_ledger_path(tmp_path / "sealed", development_uid=os.getuid() + 1,
                                             role="evaluation_custodian")
    assert sealed.name == "evaluation-ledger-v1.sqlite"
    with pytest.raises(ValueError, match="Immutable artifact changed"):
        coordinator.open_ledger(sealed.parent)


def test_new_manifest_replays_precommitted_literal_and_order_only_controls(tmp_path):
    from benchmark_v3 import replay
    from benchmark_v3.batch import artifacts
    from benchmark_v3.replay_manifest import BatchFamilyManifest

    root = tmp_path / "test-fixture"
    saved = ROOT / "family_f"
    family = replay.load_family(saved / "manifest.json")
    original, variant = family.conditions.values()
    bundles = {"TEST000": original.sources, "TEST001": list(reversed(original.sources)), "TEST002": variant.sources}
    freeze = BatchSourceFreeze(
        natural="TEST000", variants={"TEST001": None, "TEST002": family.edits["F1"]},
        candidates=sorted(family.candidates),
        required={"TEST000": family.required["F0"], "TEST001": family.required["F0"], "TEST002": family.required["F1"]},
        order={condition: [item.id for item in sources] for condition, sources in bundles.items()},
        sources_sha256={condition: value_digest([item.model_dump(mode="json") for item in sources])
                        for condition, sources in bundles.items()},
        source_commitments={condition: source_commitments(sources) for condition, sources in bundles.items()},
    )
    freeze_sha256 = artifacts.write_json(root / "freeze.json", freeze.model_dump(mode="json"))
    keys = {}
    for condition, sources in bundles.items():
        artifacts.write_json(root / "sources" / f"{condition}.json", [item.model_dump(mode="json") for item in sources])
        specimen = variant if condition == "TEST002" else original
        keys[condition] = artifacts.write_json(root / f"{condition}.json",
                                               specimen.saved.model_dump(mode="json") | {"condition": condition})
    manifest = BatchFamilyManifest(schema_version=4, family="TEST", freeze_sha256=freeze_sha256, conditions=keys)
    path = root / "manifest.json"
    artifacts.write_json(path, manifest.model_dump(mode="json"))
    report = replay.preflight(path, tmp_path / "replay")
    assert report["paid_attempts"] == 0 and report["aggregate"]["coverage"]["scored"] == 3
    assert set(report["matches"]) == {"TEST001", "TEST002"}
    damaged = root / "sources" / "TEST002.json"
    damaged.chmod(0o600)
    damaged.write_text("[]")
    with pytest.raises(ValueError, match="Digest mismatch"):
        replay.load_family(path)


def test_v4_admission_is_compatible_with_architect_and_detects_changed_review_bytes(
    approved, transport, architect_root,
):
    from shutil import copytree

    ledger, batch = _run(approved)
    path, _ = admission.package_batch(ledger, batch)
    row = json.loads(path.with_name("summary.json").read_bytes())["families"][0]
    decision = AdmissionDecisions.model_validate({
        "schema_version": 1, "batch_id": batch, "owner": OWNER, "decided_on": TODAY,
        "source": "Explicit fixture decision.", "reviewed_commit": "a" * 40,
        "decisions": [{"family_id": "G", "family_sha256": row["family_sha256"], "disposition": "accept",
                       "reason": "Fixture disposition."}],
    })
    record, = admission.record_admissions(ledger, decision)
    destination = architect_root / "family_g"
    copytree(record.parent, destination)
    inputs, context = commissioning.prepare_architect({
        "hypothesis_revision": "test-g@1", "admission_dossier": "Review fixture dossier.",
        "technical_findings": "Confirmed saved fixture replay.",
    })
    assert "approved_hypothesis" in inputs and context["admission"]["family_id"] == "G"
    with pytest.raises(ValueError, match="coverage register disagree"):
        authorisation.admitted_coverage()
    dossier = destination / "DOSSIER.md"
    dossier.chmod(0o600)
    dossier.write_text("Changed review.")
    with pytest.raises(ValueError, match="exact reviewed dossier"):
        commissioning.admitted_family_ids()


def test_audit_requires_fresh_masks_for_joint_proof():
    from benchmark_v3.batch.contracts import Adjudication, AuditReview, MaskAssignment

    family = load_family(ROOT / "family_f" / "manifest.json")
    condition = family.conditions["F0"]
    review = Adjudication(key=condition.saved, disagreement_resolutions={}, source_audit={}, unresolved=[])
    payload = _output("audit", "F", "audit", {})
    payload = {
        key: {"F0": next(iter(value.values()))} if isinstance(value, dict) else value
        for key, value in payload.items()
    }
    payload["completeness"] = {"F0": {source.id: "Reviewed." for source in condition.sources}}
    payload["sufficiency"] = {"F0": {commissioning.json_text(edge): "Joint proof." for edge in family.required["F0"]}}
    freeze = BatchSourceFreeze(natural="F0", variants={}, candidates=sorted(family.candidates),
                               required={"F0": family.required["F0"]}, order={}, sources_sha256={},
                               source_commitments={})

    def verify(masks):
        audit = AuditReview.model_validate(payload | {"masks": masks})
        science.verify_audit(audit, {"F0": condition.sources}, freeze, {"joint_proof"}, {"F0": review})

    with pytest.raises(ValueError, match="independent masks"):
        verify([])
    masks = []
    for proof in review.key.sufficient_evidence:
        for alternative in proof.alternatives:
            chosen = sorted({part.source_id for part in alternative})
            if len(chosen) < 2:
                continue
            public = {"condition": "F0", "risk": "joint_proof", "reason": "Independent proof check.",
                      "question": "Is the edge supported when the file is limited?"}
            masks.append(MaskAssignment.model_validate(public | {"included": chosen, "present": [proof.edge], "absent": []}))
            for omit in chosen:
                masks.append(MaskAssignment.model_validate(public | {
                    "included": [source for source in chosen if source != omit], "present": [], "absent": [proof.edge],
                }))
    with pytest.raises(ValueError, match="one deletion per Source"):
        verify(masks[:-1])
    verify(masks)


@pytest.fixture
def annotation_exception(design_gated, transport, request):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, behavior, _ = transport
    coordinator.run_batch(ledger, batch)
    review = _design_approval(ledger, commission).model_dump(mode="json")
    for item in review["designs"][1:]:
        item.update(disposition="return", reason="Hold other families at design review.")
    coordinator.record_design_review(ledger, DesignReview.model_validate(review | {"schema_version": 2}))

    exact = QUOTE.replace(" is ", "\n\nis ")
    submitted = exact.replace("\n\n", "\n")
    text = f"Synthetic record:\n{exact}" + (f"\n\n{exact}" if getattr(request, "param", False) is True else "")
    behavior["G", "author-src1"] = lambda _: {"title": "Test record", "text": text}

    def annotation(inputs, quote):
        return {
            "candidates": {"relationships": [{"source_name": EDGE[0], "target_name": EDGE[2],
                "relationship_type": EDGE[1], "source_id": "src1", "supporting_text": quote}]},
            "reviewed_sources": [item["id"] for item in json.loads(inputs["sources"])], "open_questions": [],
        }

    first_quote = f"Synthetic record:\n{exact}" if getattr(request, "param", False) == "disagreed" else exact
    behavior["G", "reading-000-a-full"] = lambda inputs: annotation(inputs, first_quote)
    behavior["G", "reading-000-b-full"] = lambda inputs: annotation(inputs, submitted)
    behavior["G", "adjudicate-000"] = lambda inputs: json.loads(json.dumps(
        _output("adjudication", "G", "fixture", inputs),
    ).replace(QUOTE, json.dumps(exact)[1:-1]))
    coordinator.run_batch(ledger, batch)
    assert coordinator.family_status(ledger, batch, "G")[2]["code"] == "scientific_review"
    runner = commission.session_runner(ledger, "G", 1)
    reader = runner.directory / "packets" / "reading-000-b-full"
    bundle = runner.directory / "family" / "sources" / "G000.json"
    decision = _exception_owner(commission, "G") | {
        "reader_job": reader.name, "output_sha256": commissioning.digest((reader / "output.txt").read_bytes()),
        "receipt_sha256": commissioning.digest((reader / "receipt.json").read_bytes()),
        "bundle_sha256": commissioning.digest(bundle.read_bytes()), "source_id": "src1",
        "candidate_path": "candidates.relationships[0].supporting_text",
        "byte_interval": [text.encode().index(exact.encode()), text.encode().index(exact.encode()) + len(exact.encode())],
    }
    return ledger, batch, runner, calls, decision, exact, [reader / "output.txt", reader / "receipt.json", bundle]


def _exception_owner(commission, family):
    return {"schema_version": 1, "batch_id": commission.manifest.batch_id,
            "manifest_sha256": authorisation.commitment(commission.manifest), "family_id": family,
            "owner": OWNER, "decided_on": TODAY.isoformat(), "decision_reference": "Fixture owner exception decision."}


def test_exact_annotation_recovery_is_immutable_and_resumes_at_adjudication(annotation_exception):
    ledger, batch, runner, calls, draft, exact, originals = annotation_exception
    original_bytes = [file.read_bytes() for file in originals]
    decision = AnnotationRecovery.model_validate(draft)
    cursor = len(calls)
    digest = coordinator.recover_annotation(ledger, decision)
    assert coordinator.recover_annotation(ledger, decision) == digest
    assert len(calls) == cursor
    assert coordinator.family_status(ledger, batch, "G") == (1, "blind", None)
    derivative = (runner.directory / "recoveries" / decision.reader_job / "output.json").read_bytes()
    assert commissioning.digest(derivative) == digest
    assert derivative == original_bytes[0].replace(b"Parent\\nis", b"Parent\\n\\nis")
    with pytest.raises(ValueError, match="one immutable"):
        coordinator.recover_annotation(ledger, AnnotationRecovery.model_validate(draft | {
            "decision_reference": "A second owner decision cannot overwrite the first.",
        }))
    with pytest.raises(ValueError, match="cannot reserve an earlier"):
        runner.run("author", "late-author", "author", {}, "Fixture author.", AuthoredSource)
    coordinator.run_batch(ledger, batch)
    assert coordinator.family_status(ledger, batch, "G") == (1, "admission_ready", None)
    assert [job for _, _, job, _ in calls[cursor:]] == ["adjudicate-000", "audit"]
    adjudication = calls[cursor][3]
    assert json.loads(adjudication["annotation_b"])["candidates"]["relationships"][0]["supporting_text"] == exact
    assert [file.read_bytes() for file in originals] == original_bytes
    assert coordinator.recover_annotation(ledger, decision) == digest


@pytest.mark.parametrize(("change", "error"), [
    ({"owner": "Another owner"}, "commissioning owner"),
    ({"owner": None}, "owner"),
    ({"manifest_sha256": "0" * 64}, "exact manifest"),
    ({"output_sha256": "0" * 64}, "exact original output and receipt"),
    ({"receipt_sha256": "0" * 64}, "exact original output and receipt"),
    ({"bundle_sha256": "0" * 64}, "exact committed frozen bundle"),
    ({"source_id": "src2"}, "candidate path"),
    ({"candidate_path": "candidates.relationships[1].supporting_text"}, "candidate path"),
    ({"candidate_path": "candidates.relationships[0].target_name"}, "candidate_path"),
    ({"byte_interval": [0, 2]}, "unique frozen match"),
    ({"byte_interval": [2, 1]}, "byte interval"),
    ({"relationship_type": "child_of"}, "relationship_type"),
])
def test_annotation_recovery_fails_closed(annotation_exception, change, error):
    ledger, batch, runner, calls, draft, _, originals = annotation_exception
    original_bytes = [file.read_bytes() for file in originals]
    cursor = len(calls)
    with pytest.raises(ValueError, match=error):
        coordinator.recover_annotation(ledger, AnnotationRecovery.model_validate(draft | change))
    assert not (runner.directory / "recoveries").exists()
    assert coordinator.family_status(ledger, batch, "G")[2]["code"] == "scientific_review"
    assert len(calls) == cursor and [file.read_bytes() for file in originals] == original_bytes


@pytest.mark.parametrize("annotation_exception", [True], indirect=True)
def test_annotation_recovery_rejects_nonunique_source_span(annotation_exception):
    ledger, _, _, _, decision, _, _ = annotation_exception
    with pytest.raises(ValueError, match="unique frozen match"):
        coordinator.recover_annotation(ledger, AnnotationRecovery.model_validate(decision))


def test_deferred_owner_reviews_do_not_release_either_family(design_gated, transport):
    ledger, commission = design_gated
    batch = commission.manifest.batch_id
    calls, behavior, _ = transport
    coordinator.run_batch(ledger, batch)
    payload = _design_approval(ledger, commission).model_dump(mode="json") | {"schema_version": 2}
    payload["designs"][2].update(disposition="return", reason="Check the chain.")
    coordinator.record_design_review(ledger, DesignReview.model_validate(payload))
    behavior["H", "realism-000"] = lambda inputs: _output("realism", "H", "fixture", inputs) | {
        "verdict": "return", "objections": ["Clarify one record."], "repair_tickets": {"src1": "Use native wording."},
    }
    coordinator.run_batch(ledger, batch)
    original_status = _status(ledger, batch)
    assert original_status == {"G": "admission_ready", "H": "returned", "I": "pending_design_review"}
    h = commission.session_runner(ledger, "H", 1)
    realism = h.directory / "packets" / "realism-000" / "output.txt"
    scope = _exception_owner(commission, "H") | {"disposition": {
        "status": "repair_scope_approved_pending_execution", "design_sha256": payload["designs"][1]["design_sha256"],
        "realism_output_sha256": {"H000": commissioning.digest(realism.read_bytes())}, "scope": ["Fixture clarification."],
    }}
    i = commission.session_runner(ledger, "I", 1)
    parent = payload["designs"][2]["design_sha256"]
    design = artifacts.read_contract(i.directory / "design.json", DesignOutput).model_copy(update={
        "private_history": "Clarified fixture chain.",
    })
    child = authorisation.commitment(design)
    directory = i.directory.with_name("2")
    proposal = {"parent_revision": 1, "child_revision": 2, "status": "pending_design_review",
                "parent_design_sha256": parent, "design_sha256": child,
                "manifest_sha256": authorisation.commitment(commission.manifest),
                "hypothesis_sha256": commission.manifest.families[2].hypothesis.hypothesis_sha256}
    artifacts.write_json(directory / "design.json", design.model_dump(mode="json"))
    artifacts.write_json(directory / "design-proposal.json", proposal)
    ledger.event(batch, "I", 1, "design_clarification", "child-2", "pending_design_review", "pending_design_review", proposal)
    merits = _exception_owner(commission, "I") | {"disposition": {
        "status": "design_merits_accepted_pending_activation", "parent_design_sha256": parent,
        "child_design_sha256": child,
    }}
    with pytest.raises(ValueError, match="exact recorded proposal"):
        coordinator.record_deferred_review(ledger, DeferredExceptionReview.model_validate(merits | {
            "disposition": merits["disposition"] | {"child_design_sha256": "0" * 64},
        }))
    for draft in (scope, merits):
        decision = DeferredExceptionReview.model_validate(draft)
        coordinator.record_deferred_review(ledger, decision)
        coordinator.record_deferred_review(ledger, decision)
    cursor = len(calls)
    attempts = [ledger.attempts(family) for family in "HI"]
    for family in "HI":
        with pytest.raises(Blocked, match="defers this family"):
            commission.session_runner(ledger, family, 2).run(
                "author", "author-new", "author", {}, "Fixture author.", AuthoredSource,
            )
    coordinator.run_batch(ledger, batch)
    assert _status(ledger, batch) == original_status
    assert len(calls) == cursor and [ledger.attempts(family) for family in "HI"] == attempts
    assert [event["details"] for family in "HI" for event in ledger.events(batch, family)
            if event["kind"] == "deferred_review"] == [scope, merits]

    amended = _amendment(ledger, commission)
    budget_digest = coordinator.apply_budget_amendment(ledger, amended)
    for family, draft, release in (
        ("H", scope, {"action": "repair_execution", "direct_sources": ["src1"],
                      "scope_review_sha256": authorisation.commitment(DeferredExceptionReview.model_validate(scope))}),
        ("I", merits, {"action": "child_activation", "child_design_sha256": child,
                       "merits_review_sha256": authorisation.commitment(DeferredExceptionReview.model_validate(merits))}),
    ):
        decision = FamilyContinuation.model_validate(_exception_owner(commission, family) | {
            "budget_amendment_sha256": budget_digest, "release": release,
        })
        with pytest.raises(ValueError, match="bind the recorded budget"):
            coordinator.continue_family(ledger, decision.model_copy(update={"budget_amendment_sha256": "0" * 64}))
        coordinator.continue_family(ledger, decision)
        coordinator.continue_family(ledger, decision)
    behavior.pop(("H", "realism-000"))
    coordinator.run_batch(ledger, batch)
    assert _status(ledger, batch) == dict.fromkeys("GHI", "admission_ready")
    new_authors = [(family, parent, job, inputs) for family, parent, job, inputs in calls[cursor:] if job.startswith("author")]
    assert {(family, parent, job) for family, parent, job, _ in new_authors} == {
        ("H", "H@2", "author-src1"), ("I", "I@2", "author-src1"), ("I", "I@2", "author-src2"),
    }
    assert new_authors and all("revision_ticket" in inputs if f == "H" else "revision_ticket" not in inputs
                               for f, _, _, inputs in new_authors)
    assert all(job != "design" for _, _, job, _ in calls[cursor:])
    assert coordinator.apply_budget_amendment(ledger, amended) == budget_digest
    assert authorisation.commitment(artifacts.read_contract(directory / "design.json", DesignOutput)) == child



def test_recovery_stops_before_a_mask_plan_exceeds_remaining_slots(annotation_exception, transport):
    ledger, batch, _, calls, draft, _, _ = annotation_exception
    _, behavior, _ = transport
    mask = {"risk": "shortcut", "condition": "G000", "included": ["src2"], "present": [], "absent": [EDGE],
            "reason": "Check whether the administrative note leaks the assertion.", "question": "What holds?"}
    behavior["G", "audit"] = lambda inputs: _output("audit", "G", "audit", inputs) | {
        "risks": ["shortcut"], "masks": [mask] * 3,
    }
    cursor = len(calls)
    coordinator.recover_annotation(ledger, AnnotationRecovery.model_validate(draft))
    coordinator.run_batch(ledger, batch)
    _, stage, error = coordinator.family_status(ledger, batch, "G")
    assert stage == "masks" and error["code"] == "budget"
    assert "3 new sessions with 2 available" in error["evidence"]
    assert [job for _, _, job, _ in calls[cursor:]] == ["adjudicate-000", "audit"]
    assert len(ledger.attempts("G")) == 8


def _amendment(ledger, commission):
    return BudgetAmendment.model_validate({
        "schema_version": 1, "batch_id": commission.manifest.batch_id,
        "manifest_sha256": authorisation.commitment(commission.manifest),
        "portfolio_sha256": authorisation.commitment(commission.portfolio),
        "original_approval_sha256": authorisation.commitment(commission.decision),
        "owner": OWNER, "decided_on": TODAY, "decision_reference": "Fixture owner amendment.",
        "reason": "Additional isolated reading sections.",
        "previous": {"shared": 37, "families": dict.fromkeys("GHI", 10)},
        "allocation": {"shared": 39, "families": {"G": 12, "H": 13, "I": 14}},
        "completed_charges": {family: len(ledger.attempts(family)) for family in "GHI"},
    })


def test_budget_amendment_is_append_only_and_no_transfer(approved, transport):
    ledger, commission = approved
    coordinator.commission_batch(ledger, commission, BOUNDARY)
    decision = _amendment(ledger, commission)
    with pytest.raises(ValueError, match="commissioning owner"):
        coordinator.apply_budget_amendment(ledger, decision.model_copy(update={"owner": "Other"}))
    with pytest.raises(ValueError, match="exact completed charges"):
        coordinator.apply_budget_amendment(ledger, decision.model_copy(update={
            "completed_charges": {"G": 1, "H": 0, "I": 0},
        }))
    with pytest.raises(ValueError, match="without moving"):
        lower = decision.allocation.model_copy(update={"families": {"G": 9, "H": 16, "I": 14}})
        coordinator.apply_budget_amendment(ledger, decision.model_copy(update={"allocation": lower}))
    before = ledger.batch(commission.manifest.batch_id)
    coordinator.apply_budget_amendment(ledger, decision)
    assert ledger.batch(commission.manifest.batch_id) == before
    with ledger.connect() as connection:
        assert connection.execute("SELECT ceiling FROM task").fetchone()[0] == 37
        assert dict(connection.execute("SELECT id, allowance FROM families")) == dict.fromkeys("GHI", 10)
    assert ledger.effective_budget() == decision.allocation
    for number in range(12):
        assert ledger.reserve("G", 1, f"fixture-{number}", "design", {}, str(number))
    with pytest.raises(BudgetExhausted, match="Family"):
        ledger.reserve("G", 1, "surplus", "design", {}, "x")
    coordinator.apply_budget_amendment(ledger, decision)
    with pytest.raises(ValueError, match="immutable"):
        coordinator.apply_budget_amendment(ledger, decision.model_copy(update={"reason": "Overwrite."}))


@pytest.mark.parametrize("annotation_exception", ["disagreed"], indirect=True)
@pytest.mark.parametrize("fresh_valid", [True, False])
def test_fresh_adjudication_uses_only_actual_disputes_and_is_single_attempt(annotation_exception, transport, fresh_valid):
    ledger, batch, runner, calls, draft, _, _ = annotation_exception
    _, behavior, _ = transport
    coordinator.recover_annotation(ledger, AnnotationRecovery.model_validate(draft))
    fixture_reply = behavior["G", "adjudicate-000"]
    disputed = commissioning.json_text(EDGE)
    surplus = '["Agreed","parent_of","Edge"]'
    behavior["G", "adjudicate-000"] = lambda inputs: fixture_reply(inputs) | {
        "disagreement_resolutions": {disputed: "Resolve the proof.", surplus: "Already agreed."},
    }
    coordinator.run_batch(ledger, batch)
    assert coordinator.family_status(ledger, batch, "G")[2]["evidence"] == (
        "Adjudication must resolve every graph or attached-evidence disagreement."
    )
    commission = coordinator.load_commission(ledger, batch)
    digest = coordinator.apply_budget_amendment(ledger, _amendment(ledger, commission))
    _, failed, _ = runner.committed_packet("adjudicate", "adjudicate-000", "adjudication")
    recovery = next(event["details"] for event in ledger.events(batch, "G") if event["name"] == "annotation-newline")
    release = FamilyContinuation.model_validate(_exception_owner(commission, "G") | {
        "budget_amendment_sha256": digest, "release": {
            "action": "fresh_adjudication", "output_sha256": failed["output_sha256"],
            "receipt_sha256": failed["receipt_sha256"], "annotation_derivative_sha256": recovery["derivative_sha256"],
            "disagreement_count": 1,
        },
    })
    coordinator.continue_family(ledger, release)
    behavior["G", "adjudicate-000-fresh"] = lambda inputs: fixture_reply(inputs) | {
        "disagreement_resolutions": {disputed: "Resolve the proof."} if fresh_valid else {},
    }
    if fresh_valid:
        behavior["G", "audit"] = lambda inputs: _output("audit", "G", "fixture", inputs) | {
            "risks": ["reader_disagreement"], "masks": [{
                "risk": "reader_disagreement", "condition": "G000", "included": ["src2"],
                "present": [], "absent": [EDGE], "reason": "Check disputed proof.", "question": "What holds?",
            }],
        }
    cursor = len(calls)
    coordinator.run_batch(ledger, batch)
    coordinator.run_batch(ledger, batch)
    assert [v[2] for v in calls[cursor:]] == (
        ["adjudicate-000-fresh", "audit", "mask-000"] if fresh_valid else ["adjudicate-000-fresh"]
    )
    old = runner.committed_packet("adjudicate", "adjudicate-000", "adjudication")[1]
    assert old == failed
    request = next(a for a in ledger.attempts("G") if a["job"] == "adjudicate-000-fresh")
    inputs = json.loads(request["request"])
    assert set(inputs["inputs"]) == {"sources", "neutral_brief", "ontology", "annotation_rules",
                                      "annotation_a", "annotation_b"}
    assert "Already agreed." not in request["request"]
    schema = json.loads(inputs["prompt"].split("Output schema: ", 1)[1])
    assert schema["properties"]["disagreement_resolutions"] == {
        "type": "object", "properties": {disputed: {"type": "string", "minLength": 1}},
        "required": [disputed], "additionalProperties": False, "minProperties": 1, "maxProperties": 1,
    }
    assert coordinator.family_status(ledger, batch, "G")[1] == ("admission_ready" if fresh_valid else "adjudicate")


def test_three_disagreement_ids_are_order_stable_and_duplicate_json_is_rejected():
    edges = [tuple(EDGE), ("Tina", "parent_of", "Mina"), ("Eleanor", "parent_of", "Eva")]
    ids = adjudication_contract.resolution_ids(edges)
    assert len(ids) == 3 and ids == adjudication_contract.resolution_ids(list(reversed(edges)))
    assert adjudication_contract.output_schema(ids)["properties"]["disagreement_resolutions"]["required"] == ids
    with pytest.raises(ValueError, match="unique disagreement IDs"):
        adjudication_contract.resolution_ids([*edges, edges[0]])
    with pytest.raises(ValueError, match="unique JSON keys"):
        commissioning._read_json('{"disagreement_resolutions":{"same":"first","same":"duplicate"}}')
