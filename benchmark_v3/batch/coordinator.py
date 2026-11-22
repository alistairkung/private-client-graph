"""Commission and resume independent development family workers."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, design_recovery, design_review
from benchmark_v3.batch.contracts import (
    BatchDecision, BatchManifest, Code, DesignReview, ExceptionRecord, SourceCutoffRecovery,
)
from benchmark_v3.batch.custody import namespace_directory
from benchmark_v3.batch.ledger import BudgetExhausted, Ledger, TaskHalted
from benchmark_v3.batch.sessions import Blocked, SessionRunner
from benchmark_v3.batch.workflow import FamilyWorkflow
from benchmark_v3.portfolio import FamilySlot, Portfolio


@dataclass(frozen=True)
class Commission:
    portfolio: Portfolio
    manifest: BatchManifest
    decision: BatchDecision

    def session_runner(self, ledger: Ledger, family: str, revision: int) -> SessionRunner:
        directory = ledger.root / "batches" / self.manifest.batch_id / family / str(revision)
        return SessionRunner(ledger, self.manifest, family, revision, directory, self.decision.owner)


def open_ledger(root: Path) -> Ledger:
    return Ledger(namespace_directory(root, "development"))


def commission_batch(ledger: Ledger, commission: Commission, boundary: bytes) -> None:
    with ledger.coordinator_lock():
        _commission(ledger, commission, boundary)


def _commission(ledger: Ledger, commission: Commission, boundary: bytes) -> None:
    portfolio, manifest, decision = commission.portfolio, commission.manifest, commission.decision
    existing = ledger.batch(manifest.batch_id)
    authorisation.verify_commission(portfolio, manifest, decision, boundary, resuming=existing is not None)
    metadata = {
        "portfolio": portfolio.model_dump(mode="json"), "manifest": manifest.model_dump(mode="json"),
        "decision": decision.model_dump(mode="json"),
    }
    identity = commissioning.digest(commissioning.json_text(metadata).encode())
    artifacts.write_bytes(ledger.root / "boundary" / f"{manifest.scope.os_boundary_evidence_sha256}.json", boundary)
    ledger.register(manifest, identity, metadata)


def load_commission(ledger: Ledger, batch_id: str) -> Commission:
    metadata = ledger.batch(batch_id)
    if metadata is None:
        raise ValueError("Commission this batch before running it.")
    return Commission(
        Portfolio.model_validate(metadata["portfolio"]), BatchManifest.model_validate(metadata["manifest"]),
        BatchDecision.model_validate(metadata["decision"]),
    )


def run_batch(ledger: Ledger, batch_id: str) -> None:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, batch_id)
        ledger.require_running()
        _verify_resume(ledger, commission)
        manifest = commission.manifest
        review = design_review.recorded_review(ledger, manifest, commission.decision.owner)
        design_only = manifest.requires_design_review and review is None
        slots = {slot.family_id: slot for slot in commission.portfolio.slots}
        with ThreadPoolExecutor(max_workers=manifest.max_parallel_families) as executor:
            list(executor.map(
                lambda family: _work_family(ledger, commission, slots[family.family_id], design_only=design_only),
                (family for family in manifest.families if review is None or review.accepts(family.family_id)),
            ))


def preview_design_review(ledger: Ledger, batch_id: str) -> dict[str, Any]:
    with ledger.coordinator_lock():
        ledger.require_running()
        manifest = load_commission(ledger, batch_id).manifest
        return {
            "batch_id": manifest.batch_id,
            "manifest_sha256": authorisation.commitment(manifest),
            "designs": [design.model_dump() for design in design_review.committed_designs(ledger, manifest)],
        }


def record_design_review(ledger: Ledger, review: DesignReview) -> None:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, review.batch_id)
        ledger.require_running()
        _verify_resume(ledger, commission)
        design_review.verify_review(ledger, commission.manifest, commission.decision.owner, review)
        existing = design_review.recorded_review(ledger, commission.manifest, commission.decision.owner)
        if existing is not None:
            if existing != review:
                raise ValueError("The recorded owner design review is immutable.")
            return
        with ledger.transaction() as connection:
            ledger._append(connection, review.batch_id, None, 0, "design_review", "owner", None, None,
                           review.model_dump(mode="json"))
            for row in review.designs:
                if row.disposition == "return":
                    ledger._append(connection, review.batch_id, row.family_id, 1, "design_return", "owner",
                                   "author", "pending_design_review", row.model_dump(mode="json"))



def recover_source_cutoffs(ledger: Ledger, decision: SourceCutoffRecovery) -> None:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, decision.batch_id)
        manifest = commission.manifest
        ledger.require_running()
        _verify_resume(ledger, commission)
        if decision.owner != commission.decision.owner or decision.manifest_sha256 != authorisation.commitment(manifest):
            raise ValueError("Source cut-off recovery requires the commissioning owner and exact manifest.")
        if not manifest.requires_design_review or design_review.recorded_review(ledger, manifest, decision.owner):
            raise ValueError("Recover Source cut-offs only before human design review.")
        workflows = _plan_cutoff_recoveries(ledger, commission, decision)
        with ledger.transaction() as connection:
            for workflow, record in workflows:
                ledger._append(
                    connection, decision.batch_id, workflow.slot.family_id, 1, "reconcile",
                    design_recovery.CUTOFF_RECOVERY, "design", "design", record,
                )
        for workflow, _ in workflows:
            workflow.design(recovery_only=True)


def _plan_cutoff_recoveries(
    ledger: Ledger, commission: Commission, decision: SourceCutoffRecovery,
) -> list[tuple[FamilyWorkflow, dict[str, Any]]]:
    slots = {slot.family_id: slot for slot in commission.portfolio.slots}
    commissioned = {family.family_id for family in commission.manifest.families}
    if not decision.responses.keys() <= commissioned:
        raise ValueError("Recover only families in the commissioned batch.")
    workflows = []
    for family, response in decision.responses.items():
        revision, state, blocking = family_status(ledger, decision.batch_id, family)
        runner = commission.session_runner(ledger, family, revision)
        existing = design_recovery.recorded_cutoff_recovery(runner)
        if existing is None:
            eligible = state == "design" and blocking is not None and blocking["code"] == "input_integrity"
        else:
            eligible = state in {"design", "author"} and blocking is None
        if revision != 1 or not eligible:
            raise ValueError(f"Family {family} does not have a recoverable initial design.")
        slot = slots[family]
        authorisation.verify_hypothesis(family, slot.hypothesis, decision.owner)
        record, _, _ = design_recovery.derive_cutoff_recovery(runner, slot, response)
        record["decision"] = decision.model_dump(mode="json")
        workflows.append((FamilyWorkflow(runner, slot, commission.portfolio.admission_criteria), record))
    return workflows


def _verify_resume(ledger: Ledger, commission: Commission) -> None:
    manifest = commission.manifest
    path = ledger.root / "boundary" / f"{manifest.scope.os_boundary_evidence_sha256}.json"
    try:
        authorisation.verify_boundary(manifest, artifacts.read_bytes(path))
    except (ValueError, OSError) as error:
        ledger.block(manifest.batch_id, 1, ExceptionRecord(
            stage="design", family_id=manifest.families[0].family_id, code="isolation",
            evidence=str(error), repair_permitted=False, human_action="Re-establish approved shared isolation.",
            remaining_work="task_halted",
        ))
        raise TaskHalted(str(error)) from error


def family_status(ledger: Ledger, batch_id: str, family: str) -> tuple[int, str, dict[str, Any] | None]:
    records = ledger.events(batch_id, family)
    if not records:
        raise ValueError(f"Family {family} is outside this batch.")
    revision = records[-1]["revision"]
    state = "design"
    blocking = None
    for record in records:
        if record["revision"] != revision:
            continue
        if record["kind"] in {"transition", "disposition", "human_decision", "operator_close", "design_return"}:
            state = record["next"] or state
        if record["kind"] in {"exception", "task_halt"}:
            blocking = record["details"]
        if record["kind"] == "reconcile":
            blocking = None
    return revision, state, blocking


def _work_family(
    ledger: Ledger, commission: Commission, slot: FamilySlot, *, design_only: bool = False,
) -> None:
    batch = commission.manifest.batch_id
    revision, state, blocking = family_status(ledger, batch, slot.family_id)
    if design_only and state != "design":
        return
    if state in {"admitted", "quarantined"} or state == "returned" and not _can_repair(
        ledger, commission, slot, revision,
    ):
        return
    if blocking and state != "returned":
        return
    if state == "returned":
        revision += 1
        ledger.event(batch, slot.family_id, revision, "transition", "repair", "returned", "design",
                     {"role": "batch_coordinator", "previous_revision": revision - 1,
                      "hypothesis_sha256": slot.hypothesis.hypothesis_sha256,
                      "gate": "previous review issued participant-scoped documentary repair tickets"})
    workflow = FamilyWorkflow(
        commission.session_runner(ledger, slot.family_id, revision), slot, commission.portfolio.admission_criteria,
    )
    try:
        ledger.require_running()
        if design_only:
            workflow.design()
        else:
            workflow.run()
    except TaskHalted:
        return
    except Blocked as error:
        _block(ledger, commission, workflow, error.code, str(error), error.job)
    except BudgetExhausted as error:
        _block(ledger, commission, workflow, "budget", str(error))
    except sqlite3.IntegrityError:
        _block(ledger, commission, workflow, "isolation", "A scientific session or thread identity was reused.")
    except (ValueError, OSError, KeyError, TypeError) as error:
        code: Code = (
            "technical_validation" if workflow.stage == "technical" else
            "input_integrity" if workflow.stage in {"design", "freeze", "admission_ready"} else "scientific_review"
        )
        _block(ledger, commission, workflow, code, str(error))
    if not design_only and _can_repair(ledger, commission, slot, revision):
        _work_family(ledger, commission, slot)


def _can_repair(ledger: Ledger, commission: Commission, slot: FamilySlot, revision: int) -> bool:
    return any(
        row["revision"] == revision and row["kind"] == "disposition"
        and row["details"]["repair_permitted"]
        for row in ledger.events(commission.manifest.batch_id, slot.family_id)
    )


def _block(
    ledger: Ledger, commission: Commission, workflow: FamilyWorkflow, code: Code, evidence: str,
    job: str | None = None,
) -> None:
    batch, family, revision = commission.manifest.batch_id, workflow.slot.family_id, workflow.runner.revision
    repair = _can_repair(ledger, commission, workflow.slot, revision)
    actions = {
        "isolation": "Investigate shared isolation before commissioning further work.",
        "uncertain_dispatch": "Reconcile the reserved job with a verified receipt or quarantine the family.",
        "budget": "Review the ceiling and remaining work. A reservation can never be refunded.",
        "failed_dispatch": "Review the rejected receipt and decide whether to quarantine.",
        "input_integrity": "Verify exact approved artifacts and decide whether to quarantine.",
    }
    ledger.block(batch, revision, ExceptionRecord(
        stage=workflow.stage, family_id=family, code=code, evidence=evidence, job=job,
        repair_permitted=repair,
        human_action=None if repair else actions.get(code, "Review the retained scientific objection."),
        remaining_work="task_halted" if code == "isolation" else "family_halted",
    ))


def reconcile_dispatch(ledger: Ledger, batch_id: str, family: str, reference: str) -> None:
    if not reference.strip():
        raise ValueError("Record an explicit custodian reconciliation reference.")
    with ledger.coordinator_lock():
        commission = load_commission(ledger, batch_id)
        ledger.require_running()
        revision, _, blocking = family_status(ledger, batch_id, family)
        if not blocking or blocking["code"] != "uncertain_dispatch":
            raise ValueError("Only a currently uncertain dispatch can be reconciled.")
        job = blocking["job"]
        attempt = next(row for row in ledger.attempts(family) if row["revision"] == revision and row["job"] == job)
        _, receipt = commission.session_runner(ledger, family, revision).read_reserved(
            attempt["stage"], job, commissioning._read_json(attempt["request"]),
        )
        ledger.event(batch_id, family, revision, "reconcile", job, attempt["stage"], attempt["stage"],
                     {"reference": reference, "receipt": receipt, "input_sha256": attempt["request_sha256"]})


def quarantine(ledger: Ledger, batch_id: str, family: str, reference: str) -> None:
    if not reference.strip():
        raise ValueError("Record an explicit quarantine reason or decision reference.")
    with ledger.coordinator_lock():
        revision, state, blocking = family_status(ledger, batch_id, family)
        if not blocking or state in {"admitted", "admission_ready", "quarantined"}:
            raise ValueError("Quarantine requires an unresolved exception before admission.")
        ledger.event(batch_id, family, revision, "operator_close", "quarantine", state, "quarantined",
                     {"reference": reference, "exception": blocking, "role": "custodian"})
