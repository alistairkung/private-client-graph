"""Verify scope-only owner reviews without releasing a scientific gate."""

from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, science
from benchmark_v3.batch.contracts import ChildDesignMerits, DesignOutput, RealismReview, RepairScopeReview
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot


def verify_repair_scope(
    runner: SessionRunner, slot: FamilySlot, decision: RepairScopeReview, blocking: dict[str, Any] | None,
) -> None:
    if not blocking or blocking["code"] != "documentary_realism" or blocking["repair_permitted"]:
        raise ValueError("Scope-only approval requires a blocked documentary realism return.")
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    if authorisation.commitment(design) != decision.design_sha256:
        raise ValueError("The repair scope requires the exact committed design.")
    returns = commissioning._read_json(blocking["evidence"])
    conditions = science.condition_ids(slot)
    if set(decision.realism_output_sha256) != set(conditions) or set(returns) != set(conditions):
        raise ValueError("Bind the realism outputs for all returned conditions.")
    for index, condition in enumerate(conditions):
        output, receipt, _ = runner.committed_packet("realism", f"realism-{index:03}", "realism")
        if (receipt["output_sha256"] != decision.realism_output_sha256[condition]
                or RealismReview.model_validate_json(output).model_dump(mode="json") != returns[condition]):
            raise ValueError("The documentary realism output differs from the returned condition.")


def verify_child_merits(runner: SessionRunner, slot: FamilySlot, decision: ChildDesignMerits) -> None:
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    returned = _revision_event(events, runner.revision, "design_return", "owner")
    if returned is None or returned["design_sha256"] != decision.parent_design_sha256:
        raise ValueError("Child merits require the exact returned parent design.")
    child_revision = runner.revision + 1
    child = runner.directory.with_name(str(child_revision))
    proposal = _revision_event(events, runner.revision, "design_clarification", f"child-{child_revision}")
    if (proposal is None or proposal["parent_revision"] != runner.revision
            or proposal["child_revision"] != child_revision or proposal["status"] != "pending_design_review"
            or proposal["parent_design_sha256"] != decision.parent_design_sha256
            or proposal["design_sha256"] != decision.child_design_sha256
            or proposal["manifest_sha256"] != authorisation.commitment(runner.manifest)
            or proposal["hypothesis_sha256"] != slot.hypothesis.hypothesis_sha256
            or commissioning._read_json(artifacts.read_bytes(child / "design-proposal.json")) != proposal):
        raise ValueError("Child merits require the exact recorded proposal and lineage.")
    design = artifacts.read_contract(child / "design.json", DesignOutput)
    if authorisation.commitment(design) != decision.child_design_sha256:
        raise ValueError("The child design differs from its recorded commitment.")
    science.verify_design(slot, design)


def _revision_event(events: list[dict[str, Any]], revision: int, kind: str, name: str) -> dict[str, Any] | None:
    return next((row["details"] for row in events
                 if (row["revision"], row["kind"], row["name"]) == (revision, kind, name)), None)
