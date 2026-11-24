"""Release one participant-safe common documentary repair in an approved roadmap."""

from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.contracts import DesignOutput, MilestoneRealismRepair, RealismReview
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot

RELEASE = "milestone_realism_repair"


def verify_plan(runner: SessionRunner, slot: FamilySlot, plan: MilestoneRealismRepair) -> str:
    manifest = runner.manifest
    if (
        manifest.phase != "milestone" or manifest.repair_cycles != 1 or runner.revision != 1
        or plan.batch_id != manifest.batch_id or plan.family_id != runner.family
        or plan.manifest_sha256 != authorisation.commitment(manifest)
    ):
        raise ValueError("A common repair requires the approved milestone and original family revision.")
    design_bytes = artifacts.read_bytes(runner.directory / "design.json")
    design = DesignOutput.model_validate(commissioning._read_json(design_bytes))
    canonical = commissioning.json_text(design.model_dump(mode="json")) + "\n"
    if design_bytes != canonical.encode():
        raise ValueError("The common repair requires the original committed design bytes.")
    transition = next(row for row in runner.ledger.events(manifest.batch_id, runner.family)
                      if row["revision"] == 1 and row["kind"] == "transition" and row["name"] == "design")
    if plan.design_sha256 != authorisation.commitment(design) or plan.design_sha256 != (
        transition["details"]["outputs"]["design"]
    ):
        raise ValueError("A common repair must preserve the exact committed design and matched interventions.")
    expected = {f"realism-{index:03}" for index in range(1 + len(slot.matched_conditions))}
    if len(expected) < 2 or plan.realism_outputs.keys() != expected:
        raise ValueError("A common repair requires the original independent review for every matched condition.")
    for job in sorted(expected):
        raw, receipt, _ = runner.committed_packet("realism", job, "realism")
        review = RealismReview.model_validate(commissioning._read_json(raw))
        if (
            plan.realism_outputs[job] != receipt["output_sha256"] or review.verdict != "repair"
            or review.repair_tickets.keys() != plan.repair_tickets.keys()
        ):
            raise ValueError("Every condition must independently request repair of the same named Sources.")
    return authorisation.commitment(plan)


def recorded_tickets(runner: SessionRunner, slot: FamilySlot) -> dict[str, str] | None:
    if runner.manifest.phase != "milestone" or runner.revision != 2:
        return None
    batch = runner.manifest.batch_id
    row = next((row for row in runner.ledger.events(batch, runner.family)
                if row["revision"] == 2 and row["kind"] == "transition" and row["name"] == RELEASE), None)
    if row is None:
        return None
    record: dict[str, Any] = row["details"]
    plan = MilestoneRealismRepair.model_validate(record["plan"])
    previous = SessionRunner(runner.ledger, runner.manifest, runner.family, 1, runner.directory.parent / "1", runner.owner)
    if verify_plan(previous, slot, plan) != record["plan_sha256"]:
        raise ValueError("The recorded common realism repair failed its immutable commitment.")
    return plan.repair_tickets
