"""Recover bounded mechanical defects from authenticated original design responses."""

from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, science
from benchmark_v3.batch.contracts import DesignOutput
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot

CUTOFF_RECOVERY = "source-cutoff"
PREFIX_RECOVERY = "redundant-full-file-snapshot"
PREFIX_FAILURE = "Scaling snapshots must be increasing proper prefixes of the inventory."
INITIAL_RUNTIME_RETRY = "initial-design-runtime-retry"
CONNECTION_FAILURE = "The Codex app-server closed its connection."


def initial_runtime_retry(runner: SessionRunner) -> dict[str, Any] | None:
    """Reopen only an initial runtime rejection that preceded every scientific turn."""
    if runner.revision != 2 or not runner.ledger.requires_delivery_attestation:
        return None
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    release = next((row["details"] for row in events
                    if (row["revision"], row["kind"], row["name"]) == (2, "reconcile", INITIAL_RUNTIME_RETRY)), None)
    if release is None:
        return None
    prior = runner.directory.with_name("1")
    rejected = prior / "packets" / "design"
    raw = artifacts.read_bytes(rejected / "receipt.json")
    receipt = commissioning._read_json(raw)
    charged = [row for row in runner.ledger.attempts(runner.family) if row["revision"] == 1]
    sessions = [row["details"] for row in events if row["revision"] == 1 and row["kind"] == "session"]
    if (len(charged) != 1 or (charged[0]["stage"], charged[0]["job"]) != ("design", "design")
            or len(sessions) != 1 or sessions[0]["role"] != "designer" or sessions[0]["status"] != "rejected"
            or sessions[0]["receipt_sha256"] != release["rejected_packet_sha256"]
            or commissioning.digest(raw) != sessions[0]["receipt_sha256"]
            or receipt["status"] != "rejected" or receipt["reason"] != CONNECTION_FAILURE
            or receipt.get("failure_kind") == "isolation" or "submitted_at" in receipt
            or (rejected / "output.txt").exists() or (prior / "design.json").exists()
            or not runner.ledger.pooled_revision(runner.manifest.batch_id, runner.family, 2)):
        raise ValueError("An initial runtime retry requires the exact rejected, unsubmitted design packet.")
    return release


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


def verify_milestone_design(
    runner: SessionRunner, slot: FamilySlot, design: DesignOutput, *, fresh_replacement: bool = False,
) -> DesignOutput:
    corrected = _without_full_file_snapshot(design) if runner.revision == 1 or fresh_replacement else design
    science.verify_design(slot, corrected)
    if corrected is design:
        return design
    selected, selected_receipt, _ = runner.committed_result("design", "design", "designer", DesignOutput)
    if selected != design:
        raise ValueError("Snapshot recovery must match the immutable original design.")
    _record_snapshot_recovery(runner, design, corrected, selected_receipt)
    return corrected


def recover_milestone_snapshot(runner: SessionRunner, slot: FamilySlot) -> str | None:
    raw, receipt, _ = runner.committed_packet("design", "design", "designer")
    original = DesignOutput.model_validate(commissioning._read_json(raw))
    corrected = _without_full_file_snapshot(original)
    if original is corrected:
        raise ValueError("The returned design contains no redundant terminal full-file snapshot.")
    try:
        science.verify_design(slot, corrected)
    except ValueError as error:
        return str(error)
    _record_snapshot_recovery(runner, original, corrected, receipt)
    return None


def _record_snapshot_recovery(
    runner: SessionRunner, original: DesignOutput, corrected: DesignOutput, receipt: dict[str, Any],
) -> None:
    runner.ledger.event(
        runner.manifest.batch_id, runner.family, runner.revision, "reconcile", PREFIX_RECOVERY, "design", "design",
        {
            "output_sha256": receipt["output_sha256"], "receipt_sha256": receipt["receipt_sha256"],
            "previous_scaling_snapshots": original.scaling_snapshots,
            "scaling_snapshots": corrected.scaling_snapshots, "design_sha256": authorisation.commitment(corrected),
        },
    )


ISOLATED_CUTOFF = "isolation-restart-cutoff"


def isolated_cutoff_recovery(runner: SessionRunner, slot: FamilySlot) -> tuple[DesignOutput, dict[str, Any], str] | None:
    """Recover the documentary assembly date from a rejected, un-authored design."""
    from dataclasses import replace

    release = next((event["details"] for event in runner.ledger.events(runner.manifest.batch_id, runner.family)
                    if event["revision"] == runner.revision and event["kind"] == "transition"
                    and event["name"] == ISOLATED_CUTOFF), None)
    if release is None:
        return None
    previous = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    if not runner.ledger.requires_author_context or any(
        row["revision"] == previous.revision and row["stage"] != "design"
        for row in runner.ledger.attempts(runner.family)
    ):
        raise ValueError("A cutoff derivative requires an un-authored design in the verified isolated custody.")
    job = release["job"]
    if job not in {"design", "design-format-retry"}:
        raise ValueError("A cutoff derivative requires an actual retained designer attempt.")
    output, receipt, _ = previous.committed_packet("design", job, "designer")
    if receipt["receipt_sha256"] != release["receipt_sha256"]:
        raise ValueError("The retained designer receipt changed.")
    original = DesignOutput.model_validate(commissioning._read_json(output))
    cutoff = max(brief.created_on for brief in original.inventory)
    if (original.cutoff >= cutoff or cutoff.isoformat() != release["assembly_date"]
            or original.cutoff.isoformat() != release["exact_relationship_snapshot"]
            or authorisation.commitment(original) != release["original_design_sha256"]):
        raise ValueError("The exact documentary assembly date or relationship snapshot differs from the review.")
    revised = _without_full_file_snapshot(original).model_copy(update={"cutoff": cutoff})
    science.verify_design(slot, revised)
    return revised, receipt, authorisation.commitment(revised)
