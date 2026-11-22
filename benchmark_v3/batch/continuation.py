"""Verify and reopen exact owner releases for previously blocked families."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import adjudication_contract, annotation_recovery, artifacts, authorisation, science
from benchmark_v3.batch.contracts import (
    Adjudication, BudgetAmendment, DeferredExceptionReview, DesignOutput, FamilyContinuation, FreshAdjudication,
    Reading, RealismReview, RepairScopeReview,
)
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner


def family_release(events: list[dict[str, Any]], revision: int | None = None) -> dict[str, Any] | None:
    return next((row["details"] for row in events if row["kind"] == "family_release"
                 and (revision is None or row["revision"] == revision)), None)


def recorded(runner: "SessionRunner") -> dict[str, Any] | None:
    return family_release(runner.ledger.events(runner.manifest.batch_id, runner.family), runner.revision)


def recorded_budget(events: list[dict[str, Any]]) -> BudgetAmendment | None:
    return next((BudgetAmendment.model_validate(row["details"]) for row in events
                 if row["kind"] == "budget_amendment"), None)


def verify_authority(runner: "SessionRunner", release: dict[str, Any]) -> None:
    decision = FamilyContinuation.model_validate(release["decision"])
    budget = recorded_budget(runner.ledger.events(runner.manifest.batch_id))
    if (decision.owner != runner.owner or decision.family_id != runner.family
            or decision.batch_id != runner.manifest.batch_id
            or decision.manifest_sha256 != authorisation.commitment(runner.manifest)
            or budget is None or decision.budget_amendment_sha256 != authorisation.commitment(budget)):
        raise ValueError("The family release does not bind its commissioning owner, manifest and budget.")
    path = runner.ledger.root / "boundary" / f"{runner.manifest.scope.os_boundary_evidence_sha256}.json"
    try:
        authorisation.verify_boundary(runner.manifest, artifacts.read_bytes(path))
    except (ValueError, OSError) as error:
        raise packet.PacketIsolationError(str(error)) from error
    path = runner.directory / "design.json"
    if decision.release.action == "repair_execution" and not path.exists():
        path = runner.directory.with_name(str(runner.revision - 1)) / "design.json"
    content = artifacts.read_bytes(path)
    if not content.endswith(b"\n") or commissioning.digest(content[:-1]) != release["design_sha256"]:
        raise ValueError("The active design differs from its exact family release.")
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    freeze: dict[str, str] = next((row["details"]["outputs"] for row in events if row["revision"] == runner.revision
                   and row["name"] == "freeze" and row["kind"] == "transition"), {})
    for name, expected in freeze.items():
        value = artifacts.read_bytes(runner.directory / "family" / name)
        if commissioning.digest(value) != expected:
            raise ValueError("A released family's frozen Sources no longer match their commitment.")


def previous_runner(runner: "SessionRunner") -> "SessionRunner":
    return replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))


def deferred(events: list[dict[str, Any]], revision: int, expected: str) -> DeferredExceptionReview:
    review = next((DeferredExceptionReview.model_validate(row["details"]) for row in events
                   if row["kind"] == "deferred_review" and row["revision"] == revision), None)
    if review is None or authorisation.commitment(review) != expected:
        raise ValueError("The release must bind the prior deferred owner decision.")
    return review


def fresh_resolution_ids(runner: "SessionRunner", release: FreshAdjudication) -> list[str]:
    output, receipt, request = runner.committed_packet("adjudicate", "adjudicate-000", "adjudication")
    if (receipt["output_sha256"], receipt["receipt_sha256"]) != (release.output_sha256, release.receipt_sha256):
        raise ValueError("The fresh adjudication must bind the failed output and receipt.")
    recovery = annotation_recovery.recorded(runner)
    if not recovery or recovery["derivative_sha256"] != release.annotation_derivative_sha256:
        raise ValueError("The fresh adjudication requires the approved blind derivative.")
    derivative, _ = annotation_recovery.reopen(runner, recovery)
    recovery_decision = recovery["decision"]
    if recovery_decision["reader_job"] != "reading-000-b-full":
        raise ValueError("The released adjudication requires the corrected second reading for condition zero.")
    reader_a, _, request_a = runner.committed_packet("blind", "reading-000-a-full", "annotation")
    inputs = request["inputs"]
    first = Reading.model_validate(commissioning._read_json(reader_a))
    if (Reading.model_validate_json(inputs["annotation_a"]) != first
            or Reading.model_validate_json(inputs["annotation_b"]) != derivative
            or inputs["sources"] != request_a["inputs"]["sources"]):
        raise ValueError("The failed packet did not use the two committed blind readings and frozen Sources.")
    sources = [Source.model_validate(row) for row in commissioning._read_json(inputs["sources"])]
    ids = adjudication_contract.resolution_ids(science.compare_readings(first, derivative, sources)["disagreements"])
    old_resolutions = Adjudication.model_validate(commissioning._read_json(output)).disagreement_resolutions
    if len(ids) != release.disagreement_count or set(old_resolutions) == set(ids):
        raise ValueError("The failed packet must reproduce the exact authorised disagreement contract failure.")
    return ids


def released_design(runner: "SessionRunner", record: dict[str, Any]) -> DesignOutput:
    path = runner.directory if record["decision"]["release"]["action"] == "child_activation" else previous_runner(runner).directory
    content = artifacts.read_bytes(path / "design.json")
    if not content.endswith(b"\n") or commissioning.digest(content[:-1]) != record["design_sha256"]:
        raise ValueError("The released design file differs from its committed digest.")
    return DesignOutput.model_validate(commissioning._read_json(content))


def repair_tickets(runner: "SessionRunner", scope: RepairScopeReview, direct_sources: list[str]) -> dict[str, str]:
    output, receipt, _ = runner.committed_packet("realism", "realism-000", "realism")
    if receipt["output_sha256"] not in scope.realism_output_sha256.values():
        raise ValueError("Repair tickets must come from the retained natural realism output.")
    tickets = RealismReview.model_validate(commissioning._read_json(output)).repair_tickets
    if len(direct_sources) != len(set(direct_sources)) or set(direct_sources) != tickets.keys():
        raise ValueError("The authorised direct Sources must match the participant-safe natural repair tickets.")
    return tickets
