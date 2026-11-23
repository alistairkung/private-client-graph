"""Recover bounded mechanical defects from authenticated original design responses."""

from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import authorisation, science
from benchmark_v3.batch.contracts import DesignOutput
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot

CUTOFF_RECOVERY = "source-cutoff"
PREFIX_RECOVERY = "redundant-full-file-snapshot"
PREFIX_FAILURE = "Scaling snapshots must be increasing proper prefixes of the inventory."


def recorded_cutoff_recovery(runner: SessionRunner) -> dict[str, Any] | None:
    if not runner.manifest.requires_design_review or runner.revision != 1:
        return None
    return next((
        event["details"]
        for event in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if event["revision"] == 1 and event["kind"] == "reconcile" and event["name"] == CUTOFF_RECOVERY
    ), None)


def derive_cutoff_recovery(
    runner: SessionRunner, slot: FamilySlot, response_sha256: str,
) -> tuple[dict[str, Any], DesignOutput, dict[str, Any]]:
    attempt = next((
        row for row in runner.ledger.attempts(runner.family)
        if row["revision"] == 1 and row["job"] == "design" and row["stage"] == "design"
    ), None)
    if attempt is None:
        raise ValueError("Source cut-off recovery requires an original charged design attempt.")
    session = next((
        event["details"] for event in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if event["revision"] == 1 and event["kind"] == "session" and event["name"] == "design"
    ), None)
    if session is None or session.get("status") != "completed":
        raise ValueError("Source cut-off recovery requires a committed completed designer receipt.")
    request = commissioning._read_json(attempt["request"])
    output, receipt = runner.read_reserved("design", "design", request)
    if receipt != session or receipt["output_sha256"] != response_sha256 or request["role"] != "designer":
        raise ValueError("Source cut-off recovery requires the exact completed designer response.")
    design = DesignOutput.model_validate(commissioning._read_json(output))
    latest = max(source.created_on for source in design.inventory)
    if latest <= design.cutoff:
        raise ValueError("Source cut-off recovery requires a Source dated after the original cut-off.")
    # The full-file read is a required stage. A proper prefix cannot repeat it.
    corrected = _without_full_file_snapshot(design).model_copy(update={"cutoff": latest})
    snapshots = corrected.scaling_snapshots
    science.verify_design(slot, corrected)
    return {
        "output_sha256": response_sha256,
        "receipt_sha256": receipt["receipt_sha256"],
        "previous_cutoff": design.cutoff.isoformat(),
        "source_cutoff": latest.isoformat(),
        "previous_scaling_snapshots": design.scaling_snapshots,
        "scaling_snapshots": snapshots,
        "design_sha256": authorisation.commitment(corrected),
    }, corrected, receipt


def reopen_cutoff_recovery(
    runner: SessionRunner, slot: FamilySlot, recovery: dict[str, Any],
) -> tuple[DesignOutput, dict[str, Any]]:
    commitment, design, receipt = derive_cutoff_recovery(runner, slot, recovery["output_sha256"])
    if any(recovery.get(key) != value for key, value in commitment.items()):
        raise ValueError("The Source cut-off recovery differs from the recorded commitment.")
    return design, receipt


def _without_full_file_snapshot(design: DesignOutput) -> DesignOutput:
    snapshots = design.scaling_snapshots
    if not snapshots or snapshots[-1] != len(design.inventory):
        return design
    return design.model_copy(update={"scaling_snapshots": snapshots[:-1]})


def verify_milestone_design(runner: SessionRunner, slot: FamilySlot, design: DesignOutput) -> DesignOutput:
    corrected = _without_full_file_snapshot(design) if runner.revision == 1 else design
    science.verify_design(slot, corrected)
    if corrected is design:
        return design
    output, receipt, _ = runner.committed_packet("design", "design", "designer")
    if DesignOutput.model_validate(commissioning._read_json(output)) != design:
        raise ValueError("Snapshot recovery must match the immutable original design.")
    runner.ledger.event(
        runner.manifest.batch_id, runner.family, runner.revision, "reconcile", PREFIX_RECOVERY, "design", "design",
        {
            "output_sha256": receipt["output_sha256"], "receipt_sha256": receipt["receipt_sha256"],
            "previous_scaling_snapshots": design.scaling_snapshots,
            "scaling_snapshots": corrected.scaling_snapshots, "design_sha256": authorisation.commitment(corrected),
        },
    )
    return corrected


def recover_milestone_snapshot(runner: SessionRunner, slot: FamilySlot) -> None:
    raw, _, _ = runner.committed_packet("design", "design", "designer")
    original = DesignOutput.model_validate(commissioning._read_json(raw))
    if original is _without_full_file_snapshot(original):
        raise ValueError("The returned design contains no redundant terminal full-file snapshot.")
    verify_milestone_design(runner, slot, original)
