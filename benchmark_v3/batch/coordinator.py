"""Commission and resume independent development family workers."""

import sqlite3
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import (
    adjudication_contract, adjudication_recovery, annotation_recovery, artifacts, audit_boundary, audit_recovery, author_repair, authorisation,
    autonomous_realism, clean_redesign, construction, continuation, delivery_particulars, design_recovery, design_review, evidence_recovery, exception_review, frozen_rekey, joint_control_plan,
    milestone_repair, read_format_recovery, recipient_edit, repair_authority, science,
)
from benchmark_v3.batch.contracts import (
    Adjudication, AdjudicationQuoteRecovery, AnnotationRecovery, AuditRecovery, BatchDecision, BatchManifest, BudgetAmendment,
    ChildDesignMerits, Code, DeferredExceptionReview, DesignOutput, DesignReview, ExceptionRecord, FamilyContinuation, FreshAdjudication,
    MaskAssignment, MilestoneAudit, MilestoneEvidenceRepair, MilestoneRealismRepair, OwnerFamilyReview, Reading, RepairExecution, RepairScopeReview,
    SourceCutoffRecovery,
)
from benchmark_v3.batch.custody import namespace_directory
from benchmark_v3.batch.ledger import BudgetExhausted, Ledger, TaskHalted
from benchmark_v3.batch.pool import PooledLedger
from benchmark_v3.batch.sessions import Blocked, InvalidRoleOutput, SessionRunner
from benchmark_v3.batch.workflow import FamilyWorkflow, verify_dossier
from benchmark_v3.portfolio import FamilySlot, Portfolio
from benchmark_v3.research_contracts import Digest
from private_client_graph.models.source import Source


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
    construction.verify_designs(ledger.root, manifest, portfolio)
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


def run_batch(
    ledger: Ledger, batch_id: str, *, family_id: str | None = None,
    stop_after: Literal["audit", "masks"] | None = None, realism_amendment_reference: str | None = None,
) -> None:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, batch_id)
        ledger.require_running()
        _verify_resume(ledger, commission)
        manifest = commission.manifest
        if manifest.phase == "milestone":
            if family_id is not None or stop_after is not None:
                raise ValueError("A milestone runs in its commissioned roadmap order.")
            if realism_amendment_reference is not None:
                _record_realism_amendment(ledger, commission, realism_amendment_reference)
            review = design_review.recorded_review(ledger, manifest, commission.decision.owner)
            if manifest.requires_design_review and review is None:
                _design_roadmap(ledger, commission)
            else:
                _run_roadmap(ledger, commission, review)
            return
        if realism_amendment_reference is not None:
            raise ValueError("The realism amendment applies only to the milestone roadmap.")
        review = design_review.recorded_review(ledger, manifest, commission.decision.owner)
        design_only = manifest.requires_design_review and review is None
        slots = {slot.family_id: slot for slot in commission.portfolio.slots}
        selected = [family for family in manifest.families if family_id in (None, family.family_id)]
        if not selected:
            raise ValueError("The requested family is outside this batch.")
        if stop_after is not None and (family_id is None or not audit_recovery.recorded(
            commission.session_runner(ledger, family_id, family_status(ledger, batch_id, family_id)[0]),
        )):
            raise ValueError("Stop-after requires the exact released audit recovery family.")
        with ThreadPoolExecutor(max_workers=manifest.max_parallel_families) as executor:
            list(executor.map(
                lambda family: _work_family(
                    ledger, commission, slots[family.family_id], design_only=design_only, stop_after=stop_after,
                ),
                (family for family in selected if review is None or review.accepts(family.family_id)
                 or continuation.family_release(ledger.events(batch_id, family.family_id)) is not None),
            ))


def _record_realism_amendment(ledger: Ledger, commission: Commission, reference: str) -> None:
    manifest = commission.manifest
    if manifest.phase != "milestone" or not manifest.repair_cycles or not reference.strip():
        raise ValueError("Supply the owner's realism amendment reference for an approved milestone repair allocation.")
    ledger.event(manifest.batch_id, None, 0, repair_authority.AMENDMENT, "owner_scope", None, None, {
        "manifest_sha256": authorisation.commitment(manifest), "owner": commission.decision.owner,
        "reference": reference,
    })


def _returned_realism(
    ledger: Ledger, commission: Commission, family: str, revision: int, state: str,
) -> dict[str, Any] | None:
    if state not in {"returned", "quarantined"} or not repair_authority.enabled(ledger, commission.manifest):
        return None
    events = [row for row in ledger.events(commission.manifest.batch_id, family) if row["revision"] == revision]
    if any(row["kind"] in {"human_decision", "task_halt"} or row["name"] == "freeze" for row in events):
        return None
    disposition = next((row for row in events if row["kind"] == "disposition" and row["name"] == "realism"), None)
    if disposition and any(row["name"].startswith(repair_authority.STOP)
                           and row["sequence"] > disposition["sequence"] for row in events):
        return None
    return disposition


@dataclass(frozen=True)
class RoadmapProgress:
    qualified: list[str]
    active: list[str]
    reserve: list[str]


def roadmap_progress(ledger: Ledger, commission: Commission) -> RoadmapProgress:
    batch = commission.manifest.batch_id
    progress = RoadmapProgress([], [], [])
    for allocation in commission.manifest.families:
        family = allocation.family_id
        revision, state, blocking = family_status(ledger, batch, family)
        events = ledger.events(batch, family)
        if not any(row["kind"] == "roadmap_activation" for row in events):
            progress.reserve.append(family)
            continue
        ready = next((row["details"] for row in events
                      if row["revision"] == revision and row["kind"] == "transition" and row["name"] == "dossier"),
                     None)
        if blocking is None and state in {"admission_ready", "admitted"} and ready:
            verify_dossier(ledger, batch, family, revision, ready["family_sha256"])
            progress.qualified.append(family)
        elif (_returned_realism(ledger, commission, family, revision, state)
              or state == "returned" and _can_repair(ledger, commission, family, revision)):
            progress.active.append(family)
        elif blocking is None and state not in {"returned", "quarantined", "admitted", "pending_design_review"}:
            progress.active.append(family)
    return progress


def _design_roadmap(ledger: Ledger, commission: Commission) -> None:
    manifest = commission.manifest
    slots = {slot.family_id: slot for slot in commission.portfolio.slots}
    families = [allocation.family_id for allocation in manifest.families]
    _activate_roadmap_slots(ledger, commission, roadmap_progress(ledger, commission).reserve)
    _reopen_redundant_snapshots(ledger, commission, slots)
    with ThreadPoolExecutor(max_workers=manifest.max_parallel_families) as executor:
        list(executor.map(
            lambda family: _work_family(ledger, commission, slots[family], design_only=True), families,
        ))


def _run_roadmap(ledger: Ledger, commission: Commission, review: DesignReview | None = None) -> None:
    manifest = commission.manifest
    target = manifest.qualification_target
    assert target is not None
    slots = {slot.family_id: slot for slot in commission.portfolio.slots}
    _reopen_redundant_snapshots(ledger, commission, slots)
    _reopen_recovered_plans(ledger, commission, slots)
    with ThreadPoolExecutor(max_workers=manifest.max_parallel_families) as executor:
        workers: dict[Future[None], str] = {}
        snapshot_recovery_pending = False
        while True:
            ledger.require_running()
            if snapshot_recovery_pending and not workers:
                _reopen_redundant_snapshots(ledger, commission, slots)
                snapshot_recovery_pending = False
            progress = roadmap_progress(ledger, commission)
            needed = target - len(progress.qualified)
            open_workers = max(0, min(needed, manifest.max_parallel_families) - len(workers))
            in_progress = set(workers.values())
            active = [
                family for family in progress.active
                if family not in in_progress and (review is None or review.accepts(family))
            ]
            # Preserve the slot for an exact retained repair until its peers settle.
            new = [] if snapshot_recovery_pending else progress.reserve[:max(0, open_workers - len(active))]
            _activate_roadmap_slots(ledger, commission, new)
            for family in (active + new)[:open_workers]:
                workers[executor.submit(_work_family, ledger, commission, slots[family])] = family
            if not workers:
                return
            finished, _ = wait(workers, return_when=FIRST_COMPLETED)
            for worker in finished:
                family = workers.pop(worker)
                worker.result()
                snapshot_recovery_pending |= _redundant_snapshot_stop(family_status(ledger, manifest.batch_id, family))


def _activate_roadmap_slots(ledger: Ledger, commission: Commission, families: list[str]) -> None:
    if not families:
        return
    with ledger.transaction() as connection:
        ledger.check_halt(connection)
        for family in families:
            ledger._append(
                connection, commission.manifest.batch_id, family, 1, "roadmap_activation", "commissioned",
                "design", "design", {"manifest_sha256": commission.decision.manifest_sha256},
            )


def _redundant_snapshot_stop(status: tuple[int, str, dict[str, Any] | None]) -> bool:
    revision, state, blocking = status
    return ((revision, state) == (1, "design") and blocking is not None
            and (blocking["code"], blocking["evidence"]) == ("input_integrity", design_recovery.PREFIX_FAILURE))


def _reopen_redundant_snapshots(
    ledger: Ledger, commission: Commission, slots: dict[str, FamilySlot],
) -> None:
    batch = commission.manifest.batch_id
    for allocation in commission.manifest.families:
        family = allocation.family_id
        status = family_status(ledger, batch, family)
        if not _redundant_snapshot_stop(status):
            continue
        revision = status[0]
        runner = commission.session_runner(ledger, family, revision)
        try:
            remaining_defect = design_recovery.recover_milestone_snapshot(runner, slots[family])
        except (packet.PacketIsolationError, OSError, ValueError, KeyError, TypeError) as error:
            ledger.block(batch, revision, ExceptionRecord(
                stage="design", family_id=family, code="isolation", evidence=str(error),
                repair_permitted=False, human_action="Verify original design receipt custody.",
                remaining_work="task_halted",
            ), qualifier=design_recovery.PREFIX_RECOVERY)
            raise TaskHalted("The retained design failed its recovery integrity checks.") from error
        if remaining_defect is not None:
            ledger.block(batch, revision, ExceptionRecord(
                stage="design", family_id=family, code="input_integrity", evidence=remaining_defect,
                repair_permitted=False, human_action="Review the remaining design defect.",
                remaining_work="family_halted",
            ), qualifier=design_recovery.PREFIX_RECOVERY)


def _reopen_recovered_plans(ledger: Ledger, commission: Commission, slots: dict[str, FamilySlot]) -> None:
    manifest = commission.manifest
    if not repair_authority.enabled(ledger, manifest):
        return
    for allocation in manifest.families:
        family = allocation.family_id
        revision, state, blocking = family_status(ledger, manifest.batch_id, family)
        if state != "quarantined" or not blocking or blocking["stage"] != "design":
            continue
        format_failure = blocking["evidence"].startswith("repair-plan-format-retry failed its output contract:")
        capacity_failure = blocking["code"] == "budget"
        if not (format_failure or capacity_failure):
            continue
        runner = commission.session_runner(ledger, family, revision)
        release = autonomous_realism.release_event(runner)
        if any(row["revision"] == revision and row["name"] == repair_authority.PLAN_RECOVERY
               for row in ledger.events(manifest.batch_id, family)):
            continue
        if release is None:
            continue
        if capacity_failure:
            events = ledger.events(manifest.batch_id, family)
            jobs = {attempt["job"] for attempt in ledger.attempts(family) if attempt["revision"] == revision}
            if repair_authority.PLAN_JOB not in jobs or repair_authority.BUDGET_PLAN_JOB in jobs or any(
                row["revision"] == revision and row["kind"] == "transition" and row["name"] == "design"
                for row in events
            ):
                continue
            reason = "A retained pre-authoring budget stop can receive one independent capacity replan."
        elif autonomous_realism.recover_stopped_plan(runner, slots[family], release):
            reason = (
                "Verified unchanged local scope and prior Source contents for an ordinary counterpart term."
                if blocking["evidence"].endswith(autonomous_realism.PARTICIPANT_LITERAL_FAILURE)
                else "Validated exact current and retained historical objection IDs."
            )
        else:
            continue
        ledger.event(manifest.batch_id, family, revision, "reconcile", repair_authority.PLAN_RECOVERY,
                     state, "design", {"reason": reason})


def release_milestone_realism_repair(ledger: Ledger, plan: MilestoneRealismRepair) -> str:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, plan.batch_id)
        _verify_resume(ledger, commission)
        batch, family = plan.batch_id, plan.family_id
        slots = {slot.family_id: slot for slot in commission.portfolio.slots}
        original = commission.session_runner(ledger, family, 1)
        digest = milestone_repair.verify_plan(original, slots[family], plan)
        revision, state, blocking = family_status(ledger, batch, family)
        prior = next((row for row in ledger.events(batch, family) if row["name"] == milestone_repair.RELEASE), None)
        if prior is not None and prior["details"]["plan_sha256"] == digest:
            return digest
        if (revision, state) != (1, "returned") or not blocking or (
            blocking["code"], blocking["stage"]
        ) != ("documentary_realism", "realism"):
            raise ValueError("A common repair can reopen only the original paired documentary-realism return.")
        ledger.event(
            batch, family, 2, "transition", milestone_repair.RELEASE, "returned", "design",
            {"plan": plan.model_dump(mode="json"), "plan_sha256": digest, "role": "custodian"},
        )
        return digest


def release_milestone_evidence_repair(ledger: Ledger, plan: MilestoneEvidenceRepair) -> str:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, plan.batch_id)
        _verify_resume(ledger, commission)
        batch, family = plan.batch_id, plan.family_id
        revision, state, blocking = family_status(ledger, batch, family)
        prior = next((row for row in ledger.events(batch, family) if row["name"] == evidence_recovery.RELEASE), None)
        if prior is not None and prior["details"]["plan"] == plan.model_dump(mode="json"):
            return str(prior["details"]["plan_sha256"])
        if revision != 1 or state not in {"audit", "returned"} or not blocking or (
            blocking["code"], blocking["stage"]
        ) != ("scientific_review", "audit"):
            raise ValueError("Evidence repair requires the original independently returned scientific audit.")
        original = commission.session_runner(ledger, family, 1)
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        recovered = evidence_recovery.derive(original, slot, plan)
        possible_views = {evidence_recovery.observation_key(mask, science.mask_sources(
            mask, recovered.bundles[mask.condition],
        )) for mask in recovered.prior_audit.masks}
        ledger.require_capacity(family, 2, {"audit", *(f"mask-{index:03}" for index in range(len(possible_views)))})
        ledger.event(
            batch, family, 2, "transition", evidence_recovery.RELEASE, state, "adjudicate",
            {"plan": plan.model_dump(mode="json"), "plan_sha256": recovered.plan_sha256, "role": "custodian"},
        )
        return recovered.plan_sha256


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
            ledger._append(connection, review.batch_id, None, 0, "design_review",
                           "owner_scope" if commission.manifest.phase == "milestone" else "owner", None, None,
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
        construction.verify_designs(ledger.root, manifest, commission.portfolio)
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
        if record["kind"] in {"transition", "disposition", "human_decision", "operator_close", "design_return", "family_release"}:
            state = record["next"] or state
        if record["kind"] in {"exception", "task_halt"}:
            blocking = record["details"]
        if record["kind"] in {"reconcile", "family_release"}:
            blocking = None
            if record["kind"] == "reconcile" and record["name"] in {
                repair_authority.PLAN_RECOVERY, repair_authority.RETAINED_DESIGN_NOTE,
            }:
                state = "design"
            if record["kind"] == "reconcile" and (
                record["name"].startswith(("construction-followup", "pooled-release", read_format_recovery.RELEASE,
                                           read_format_recovery.MASK_RELEASE))
                or record["name"] in {audit_boundary.RECHECK, audit_boundary.FORMAT_RETRY,
                                      audit_boundary.LARGE_CONFIRMATION, author_repair.UNUSED_ATTESTATION,
                                      repair_authority.SCOPE_REVIEW_RETRY, joint_control_plan.RELEASE,
                                      joint_control_plan.FOLLOWUP_RELEASE}
            ):
                state = record["next"] or state
    return revision, state, blocking


def _work_family(
    ledger: Ledger, commission: Commission, slot: FamilySlot, *, design_only: bool = False,
    stop_after: Literal["audit", "masks"] | None = None,
) -> None:
    batch = commission.manifest.batch_id
    revision, state, blocking = family_status(ledger, batch, slot.family_id)
    if design_only and state != "design":
        return
    documentary_return = _returned_realism(ledger, commission, slot.family_id, revision, state)
    if documentary_return is not None:
        ledger.event(batch, slot.family_id, revision + 1, "transition", repair_authority.REVISION, state, "design", {
            "role": "batch_coordinator", "parent_revision": revision,
            "disposition_sequence": documentary_return["sequence"],
            "manifest_sha256": authorisation.commitment(commission.manifest),
            "family_sessions_remaining": ledger.effective_budget().families[slot.family_id]
            - len(ledger.attempts(slot.family_id)),
        })
        revision += 1
    elif state in {"admitted", "quarantined"} or state == "returned" and not _can_repair(
        ledger, commission, slot.family_id, revision,
    ):
        return
    elif blocking and state != "returned":
        return
    elif state == "returned":
        revision += 1
        ledger.event(batch, slot.family_id, revision, "transition", "repair", "returned", "design",
                     {"role": "batch_coordinator", "previous_revision": revision - 1,
                      "hypothesis_sha256": slot.hypothesis.hypothesis_sha256,
                      "gate": "previous review issued participant-scoped documentary repair tickets"})
    if commission.manifest.phase == "construction" and revision > 1:
        # Repair inputs are bound separately from the original construction command.
        return
    workflow = FamilyWorkflow(
        commission.session_runner(ledger, slot.family_id, revision), slot, commission.portfolio.admission_criteria,
    )
    try:
        ledger.require_running()
        if design_only:
            workflow.design()
        else:
            workflow.run(stop_after=stop_after)
    except TaskHalted:
        return
    except Blocked as error:
        _block(ledger, commission, workflow, error.code, str(error), error.job)
    except BudgetExhausted as error:
        _block(ledger, commission, workflow, "budget", str(error))
        if workflow.realism_release is not None:
            _stop_documentary_repair(ledger, commission, workflow, str(error))
    except InvalidRoleOutput as error:
        _block(ledger, commission, workflow, "scientific_review", str(error))
        if repair_authority.enabled(ledger, commission.manifest):
            _stop_documentary_repair(ledger, commission, workflow, str(error))
    except autonomous_realism.RepairStopped as error:
        _block(ledger, commission, workflow, "scientific_review", str(error))
        _stop_documentary_repair(ledger, commission, workflow, str(error))
    except packet.PacketIsolationError as error:
        _block(ledger, commission, workflow, "isolation", str(error))
    except sqlite3.IntegrityError:
        _block(ledger, commission, workflow, "isolation", "A scientific session or thread identity was reused.")
    except (ValueError, OSError, KeyError, TypeError) as error:
        code: Code = (
            "technical_validation" if workflow.stage == "technical" else
            "input_integrity" if workflow.stage in {"design", "freeze", "admission_ready"} else "scientific_review"
        )
        _block(ledger, commission, workflow, code, str(error))
    if commission.manifest.phase == "construction":
        _, state, blocking = family_status(ledger, batch, slot.family_id)
        if blocking and blocking["code"] in {"documentary_realism", "scientific_review", "failed_dispatch"}:
            if state != "quarantined":
                ledger.event(batch, slot.family_id, revision, "operator_close", "quarantine", state, "quarantined",
                             {"reference": "Commissioned unattended exception policy.", "exception": blocking})
    elif (not design_only and not repair_authority.enabled(ledger, commission.manifest)
          and _can_repair(ledger, commission, slot.family_id, revision)):
        _work_family(ledger, commission, slot)


def _stop_documentary_repair(ledger: Ledger, commission: Commission, workflow: FamilyWorkflow, reason: str) -> None:
    name = repair_authority.STOP
    if _plan_reopened(ledger, workflow):
        name += "_after_recovery"
    if ledger.pooled_revision(commission.manifest.batch_id, workflow.slot.family_id, workflow.runner.revision):
        name += "_pooled"
    previous = {row["name"] for row in ledger.events(commission.manifest.batch_id, workflow.slot.family_id)
                if row["revision"] == workflow.runner.revision and row["kind"] == "operator_close"}
    if name in previous:
        key = commissioning.digest(reason.encode())[:16]
        name += f"_{key}"
    ledger.event(
        commission.manifest.batch_id, workflow.slot.family_id, workflow.runner.revision,
        "operator_close", name, workflow.stage, "quarantined", {"reference": reason},
    )


def _plan_reopened(ledger: Ledger, workflow: FamilyWorkflow) -> bool:
    return any(
        row["revision"] == workflow.runner.revision and row["name"] == repair_authority.PLAN_RECOVERY
        for row in ledger.events(workflow.runner.manifest.batch_id, workflow.slot.family_id)
    )


def _can_repair(ledger: Ledger, commission: Commission, family: str, revision: int) -> bool:
    return any(
        row["revision"] == revision and row["kind"] == "disposition"
        and row["details"]["repair_permitted"]
        for row in ledger.events(commission.manifest.batch_id, family)
    )


def _block(
    ledger: Ledger, commission: Commission, workflow: FamilyWorkflow, code: Code, evidence: str,
    job: str | None = None,
) -> None:
    batch, family, revision = commission.manifest.batch_id, workflow.slot.family_id, workflow.runner.revision
    repair = _can_repair(ledger, commission, family, revision)
    actions = {
        "isolation": "Investigate shared isolation before commissioning further work.",
        "uncertain_dispatch": "Reconcile the reserved job with a verified receipt or quarantine the family.",
        "budget": "Review the ceiling and remaining work. A reservation can never be refunded.",
        "failed_dispatch": "Review the rejected receipt and decide whether to quarantine.",
        "input_integrity": "Verify exact approved artifacts and decide whether to quarantine.",
    }
    qualifier = None
    if workflow.stage == "audit" and joint_control_plan.released(workflow.runner) is not None:
        qualifier = (joint_control_plan.FOLLOWUP_RELEASE if joint_control_plan.followup(workflow.runner) is not None
                     else joint_control_plan.RELEASE)
    elif workflow.stage == "audit" and audit_boundary.release(workflow.runner) is not None:
        qualifier = next((row["name"] for row in reversed(ledger.events(batch, family))
                          if row["revision"] == revision and row["kind"] == "reconcile"
                          and row["name"] in {audit_boundary.FORMAT_RETRY, audit_boundary.LARGE_CONFIRMATION}),
                         audit_boundary.RECHECK)
    elif workflow.stage == "author" and any(
        row["revision"] == revision and row["name"] == repair_authority.SCOPE_REVIEW_RETRY
        for row in ledger.events(batch, family)
    ):
        qualifier = repair_authority.SCOPE_REVIEW_RETRY
    elif _plan_reopened(ledger, workflow):
        qualifier = repair_authority.PLAN_RECOVERY
    elif workflow.audit_recovery is not None:
        qualifier = audit_recovery.JOB
    elif workflow.release_action == "complete_evidence_adjudication":
        qualifier = "complete-evidence"
    reading_release_prefix = {
        "blind": read_format_recovery.RELEASE,
        "masks": read_format_recovery.MASK_RELEASE,
        "adjudicate": (adjudication_contract.PROOF_RETRY, adjudication_contract.QUOTE_RECOVERY),
    }.get(workflow.stage)
    if reading_release_prefix is not None:
        qualifier = next((row["name"] for row in reversed(ledger.events(batch, family))
                          if row["revision"] == revision and row["kind"] == "reconcile"
                          and row["name"].startswith(reading_release_prefix)), qualifier)
    ledger.block(batch, revision, ExceptionRecord(
        stage=workflow.stage, family_id=family, code=code, evidence=evidence, job=job,
        repair_permitted=repair,
        human_action=None if repair else actions.get(code, "Review the retained scientific objection."),
        remaining_work="task_halted" if code == "isolation" else "family_halted",
    ), continuation=workflow.release is not None, qualifier=qualifier)


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


def recover_scope_review_representation(ledger: Ledger, batch: str, family: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (not ledger.requires_delivery_attestation or state != "quarantined" or not issue
                or (issue["stage"], issue["code"]) != ("author", "scientific_review")
                or autonomous_realism.release_event(runner) is None
                or any(row["revision"] == revision and row["job"] == repair_authority.VERIFY_JOB + repair_authority.FORMAT_RETRY
                       for row in ledger.attempts(family))):
            raise ValueError("Only a retained ambiguous scope verification can get one independent retry.")
        review, receipt, _ = runner.committed_result("author", repair_authority.VERIFY_JOB, "audit",
                                                     autonomous_realism.ScopeReview)
        if review.verdict != "preserved" or not review.objections or issue["evidence"] != autonomous_realism.scope_failure(review):
            raise ValueError("The original scope receipt must have preserved scope with ambiguous objections.")
        ledger.event(batch, family, revision, "reconcile", repair_authority.SCOPE_REVIEW_RETRY, state, "author", {
            "receipt_sha256": receipt["receipt_sha256"],
            "reference": "Independent disposition clarification against the same exact frozen comparison.",
        })


def release_clean_redesign(ledger: PooledLedger, batch: str, family: str, reason: str) -> None:
    """Retain a failed lineage and commission one fresh independent replacement."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        events = ledger.events(batch, family)
        scoped = (commission.manifest.phase == "milestone" and ledger.requires_delivery_attestation
                  and not commission.manifest.requires_design_review)
        if (not scoped or not reason.strip() or state not in {"quarantined", "returned"}
                or not issue or issue["code"] not in {"scientific_review", "documentary_realism"}
                or any("documentary_redesign" in row["details"] for row in events)):
            raise ValueError("A clean redesign needs one retained scientific failure and a released non-giant hypothesis.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        if slot.tier == "giant" or slot.expected_sources >= 100:
            raise ValueError("The giant workload is outside clean redesign authority.")
        runner = commission.session_runner(ledger, family, revision + 1)
        record = clean_redesign.details(runner, revision, reason.strip())
        ledger.release(batch, family, revision + 1, "design", parent_sha256=authorisation.commitment(record),
                       reference="Fresh documentary design after a retained scientific failure.",
                       documentary_redesign=record.model_dump(mode="json"))


def release_frozen_evidence_review(ledger: PooledLedger, batch: str, family: str, rationale: str) -> None:
    """Preserve documentary and blind commitments before a fresh condition-local rekey."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        prior_reviews = [row for row in ledger.events(batch, family) if "frozen_evidence_review" in row["details"]]
        returned = state == "returned" or (
            state == "audit" and issue is not None and issue["evidence"] == science.AUDIT_COVERAGE_ERROR
        )
        if (not ledger.requires_delivery_attestation or not rationale.strip() or not returned
                or not issue or (issue["stage"], issue["code"]) != ("audit", "scientific_review")
                or len(prior_reviews) >= 2 or (prior_reviews and prior_reviews[0]["revision"] != revision)
                or any(row["revision"] == revision and row["stage"] == "masks" for row in ledger.attempts(family))):
            raise ValueError("A frozen evidence review requires an exact preserved audit return within the two-review bound.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        if commission.manifest.phase != "milestone" or slot.tier == "giant" or slot.expected_sources >= 100:
            raise ValueError("Frozen evidence review is scoped to non-giant milestone candidates.")
        record = frozen_rekey.make_release(commission.session_runner(ledger, family, revision), slot, rationale.strip())
        ledger.release(batch, family, revision + 1, "adjudicate", parent_sha256=authorisation.commitment(record),
                       reference="Independent condition-local evidence re-adjudication on the retained freeze.",
                       frozen_evidence_review=record.model_dump(mode="json"))


def recover_unused_attestation(ledger: Ledger, batch: str, family: str, source_id: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        if (state != "quarantined" or not issue or issue["stage"] != "author"
                or issue["evidence"] != (f"author-{source_id}-format-retry failed its output contract: "
                                         "The sending author must attest the exact ordered same-day grants.")):
            raise ValueError("The actual stopped author must have failed the exact attestation representation.")
        runner = commission.session_runner(ledger, family, revision)
        design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
        details = author_repair.verify_unused_attestation(runner, source_id, design)
        ledger.event(batch, family, revision, "reconcile", author_repair.UNUSED_ATTESTATION, state, "author", details)


def release_empty_sender_repair(ledger: PooledLedger, batch: str, family: str, source_id: str) -> None:
    """Reopen only the documented local sending act and its dependent authoring."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        expected = f"author-{source_id}-format-retry failed its output contract: {author_repair.ATTESTATION_ERROR}"
        if (state != "quarantined" or not issue or (issue["stage"], issue["code"], issue["evidence"])
                != ("author", "scientific_review", expected)
                or not ledger.pooled_revision(batch, family, revision)
                or any(row["name"] == author_repair.EMPTY_ATTESTATION_REPAIR for row in ledger.events(batch, family))):
            raise ValueError("Only one exactly retained missing sender attestation can receive a local remedy.")
        runner = commission.session_runner(ledger, family, revision)
        record, _, _ = author_repair.empty_sender_repair(runner, source_id)
        ledger.event(batch, family, revision + 1, "transition", author_repair.EMPTY_ATTESTATION_REPAIR, state, "design", record)


def clarify_pre_author_cover(ledger: PooledLedger, batch: str, family: str, source: str, wrong: str, right: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, stage, issue = family_status(ledger, batch, family)
        if (stage != "design" or not issue or issue["evidence"] != author_repair.PLAN_OUTSIDE_BRIEF
                or not ledger.pooled_revision(batch, family, revision)):
            raise ValueError("A verified preauthor scope return must identify the exact documentary custody error.")
        runner = commission.session_runner(ledger, family, revision + 1)
        details, _ = author_repair.cover_clarification(runner, source, wrong, right)
        ledger.event(batch, family, revision + 1, "transition", author_repair.PROVENANCE_CLARIFICATION,
                     stage, "design", details)


def release_unused_delivery_recheck(ledger: Ledger, batch: str, family: str, source_id: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        if (state != "quarantined" or not issue or issue["stage"] != "author"
                or any(row["name"] == author_repair.RECHECK_UNUSED_DELIVERY for row in ledger.events(batch, family))):
            raise ValueError("Only one unused-delivery clarification may follow a pre-author scope return.")
        details = author_repair.unused_delivery_return(commission.session_runner(ledger, family, revision), source_id)
        ledger.event(batch, family, revision + 1, "transition", author_repair.RECHECK_UNUSED_DELIVERY,
                     state, "design", details)


def release_audit_recheck(
    ledger: Ledger, batch: str, family: str, receipt_sha256: str, excerpts: list[audit_boundary.ExactExcerpt],
) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (not issue or (issue["stage"], issue["code"]) != ("audit", "scientific_review")
                or audit_boundary.release(runner) is not None):
            raise ValueError("A scientific recheck requires the first retained, exact audit repair request.")
        invalid_plan = state == "audit" and issue["evidence"] in {
            audit_boundary.MASK_RENDER_FAILURE, audit_boundary.MASK_QUOTE_FAILURE,
        }
        ambiguous_acceptance = state == "audit" and issue["evidence"] == audit_boundary.ACCEPTANCE_FORMAT_ERROR
        if state != "returned" and not invalid_plan and not ambiguous_acceptance:
            raise ValueError("Only documentary audit returns or exact unrenderable control plans are eligible.")
        path = runner.directory / "family" / "freeze.json"
        record = {"receipt_sha256": receipt_sha256, "freeze_sha256": commissioning.digest(artifacts.read_bytes(path)),
                  "excerpt_controls": [view.model_dump(mode="json") for view in excerpts],
                  **({"unrenderable_control_plan": True} if invalid_plan else {}),
                  **({"ambiguous_acceptance": True} if ambiguous_acceptance else {})}
        original = audit_boundary.returned_audit(runner, record)
        if not (invalid_plan or ambiguous_acceptance) and commissioning._read_json(issue["evidence"]) != original.model_dump(mode="json"):
            raise ValueError("The fresh audit does not bind the actual returned disposition.")
        if invalid_plan:
            from pydantic import TypeAdapter

            by_condition = {condition: TypeAdapter(list[Source]).validate_json(
                artifacts.read_bytes(path.parent / "sources" / f"{condition}.json"),
            ) for condition in original.completeness}
            exact, repairs = audit_boundary.exact_mask_quotes(original, by_condition)
            _, whole = audit_boundary.original_views(exact, by_condition)
            if not whole and not repairs:
                raise ValueError("An accepted control plan needs an exact whole-file or quotation representation defect.")
            if repairs:
                record["mask_quote_repairs"] = repairs
        ledger.event(batch, family, revision, "reconcile", audit_boundary.RECHECK, state, "audit", record)


def release_joint_control_confirmation(ledger: PooledLedger, batch: str, family: str, job: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (not ledger.requires_delivery_attestation or state != "quarantined" or not issue or issue["stage"] != "audit"
                or issue["evidence"] != f"{job} failed its output contract: {audit_boundary.JOINT_PLAN_FAILURE}"
                or joint_control_plan.released(runner) is not None
                or any(row["revision"] == revision and row["stage"] == "masks" for row in ledger.attempts(family))):
            raise ValueError("The exact incomplete joint plan must be held before any masked observations.")
        _, receipt, _ = runner.committed_packet("audit", job, "audit")
        if not any((row["revision"], row["kind"], row["name"]) == (revision, "rejected_output", job)
                   and row["details"] == {"reason": audit_boundary.JOINT_PLAN_FAILURE,
                                          "receipt_sha256": receipt["receipt_sha256"]}
                   for row in ledger.events(batch, family)):
            raise ValueError("The missing joint controls must bind the exact independent rejected plan.")
        record = {
            "job": job, "receipt_sha256": receipt["receipt_sha256"],
            "freeze_sha256": commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json")),
        }
        joint_control_plan.retained_audit(runner, record)
        ledger.event(batch, family, revision, "reconcile", joint_control_plan.RELEASE, state, "audit", record)


def release_joint_plan_followup(
    ledger: PooledLedger, batch: str, family: str, changes: dict[str, MaskAssignment],
) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (state != "quarantined" or not issue or issue["stage"] != "audit"
                or joint_control_plan.released(runner) is None or joint_control_plan.followup(runner) is not None
                or any(row["revision"] == revision and row["stage"] == "masks" for row in ledger.attempts(family))):
            raise ValueError("One independent joint-plan follow-up can precede all masked observations.")
        verdict, receipt, request = runner.committed_result(
            "audit", joint_control_plan.JOB, "audit", joint_control_plan.Confirmation,
        )
        if verdict.verdict != "return" or not verdict.objections or issue["evidence"] != verdict.model_dump_json():
            raise ValueError("A follow-up must bind the exact independently recorded return and objections.")
        rules = commissioning._read_json(request["inputs"]["audit_rules"])
        proposed = TypeAdapter(dict[str, MaskAssignment]).validate_python(rules["additional_proposed_views_by_commitment"])
        joint_control_plan.verify_replacements(proposed, changes)
        release = joint_control_plan.Followup(receipt_sha256=receipt["receipt_sha256"], replacements=changes)
        ledger.event(batch, family, revision, "reconcile", joint_control_plan.FOLLOWUP_RELEASE, state, "audit",
                     release.model_dump(mode="json"))


def release_joint_plan_recheck(ledger: PooledLedger, batch: str, family: str) -> None:
    """Independently complete all required joint observations before any mask is sent."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        job = "audit" + repair_authority.FORMAT_RETRY
        failure = f"{job} failed its output contract: {audit_boundary.JOINT_PLAN_FAILURE}"
        if (not ledger.requires_delivery_attestation or state != "quarantined" or not issue
                or issue["stage"] != "audit" or issue["evidence"] != failure or audit_boundary.release(runner) is not None
                or frozen_rekey.recorded(runner) is None
                or any(row["revision"] == revision and row["stage"] == "masks" for row in ledger.attempts(family))):
            raise ValueError("Only an exact jointly incomplete audit can get a fresh scientific control plan.")
        review, receipt, _ = runner.committed_result("audit", job, "audit", audit_boundary.RecheckedAudit)
        if review.verdict != "accept" or review.objections or not any(
            (row["revision"], row["kind"], row["name"]) == (revision, "rejected_output", job)
            and row["details"] == {"reason": audit_boundary.JOINT_PLAN_FAILURE,
                                   "receipt_sha256": receipt["receipt_sha256"]}
            for row in ledger.events(batch, family)
        ):
            raise ValueError("The retained scientific acceptance must bind its exact incomplete plan rejection.")
        digest = commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json"))
        ledger.event(batch, family, revision, "reconcile", audit_boundary.RECHECK, state, "audit", {
            "receipt_sha256": receipt["receipt_sha256"], "freeze_sha256": digest,
            "excerpt_controls": [view.model_dump(mode="json") for view in review.excerpt_controls],
            "incomplete_joint_control_plan": True,
        })


def release_fictional_dispatch_recheck(ledger: PooledLedger, batch: str, family: str) -> None:
    """Require independent reassessment when an audit confused a fictional question with a custody stop."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (not ledger.requires_delivery_attestation or state != "quarantined" or not issue
                or (issue["stage"], issue["code"]) != ("audit", "scientific_review")
                or audit_boundary.release(runner) is not None):
            raise ValueError("Only an exact audit disposition on fictional dispatch is eligible for independent recheck.")
        review, receipt, _ = runner.committed_result("audit", "audit", "audit", MilestoneAudit)
        if (review.verdict != "quarantine" or review.model_dump(mode="json") != commissioning._read_json(issue["evidence"])
                or not any("unresolved dispatch" in reason.casefold() and "audit-workflow dispatch" in reason.casefold()
                           for reason in review.objections)):
            raise ValueError("The original auditor must explicitly identify the distinction and its retained objection.")
        ledger_events = ledger.events(batch, family)
        terminal = {(row["revision"], row["name"]) for row in ledger_events
                    if row["kind"] == "session" and row["details"]["status"] in {"completed", "rejected"}}
        if any((attempt["revision"], attempt["job"]) not in terminal for attempt in ledger.attempts(family)):
            raise ValueError("An unsettled real scientific reservation prevents this scope recheck.")
        digest = commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json"))
        ledger.event(batch, family, revision, "reconcile", audit_boundary.RECHECK, state, "audit", {
            "receipt_sha256": receipt["receipt_sha256"], "freeze_sha256": digest,
            "excerpt_controls": [], "fictional_dispatch_only": True,
        })


def recover_large_confirmation(ledger: Ledger, batch: str, family: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (state != "audit" or (issue is not None and not issue["evidence"].endswith(audit_boundary.MASK_RENDER_FAILURE))
                or audit_boundary.release(runner) is None):
            raise ValueError("A large-file confirmation requires the exact unrenderable recheck exception.")
        job = audit_boundary.RECHECK + repair_authority.FORMAT_RETRY
        audit, receipt, request = runner.committed_result("audit", job, "audit", audit_boundary.RecheckedAudit)
        if not any(row["revision"] == revision and row["kind"] == "rejected_output" and row["name"] == job
                   and row["details"] == {"reason": audit_boundary.MASK_RENDER_FAILURE,
                                          "receipt_sha256": receipt["receipt_sha256"]}
                   for row in ledger.events(batch, family)):
            raise ValueError("The original independently accepted plan has no exact recorded render failure.")
        inputs = request["inputs"]
        by_condition = {name: TypeAdapter(list[Source]).validate_python(rows)
                        for name, rows in commissioning._read_json(inputs["paired_bundles"]).items()}
        targeted = audit_boundary.targeted_audit(audit, by_condition)
        if audit.verdict != "accept" or audit.objections or len(targeted.masks) >= len(audit.masks):
            raise ValueError("The independent auditor must have accepted a distinct large-file replication.")
        for mask in targeted.masks:
            science.mask_sources(mask, by_condition[mask.condition])
        ledger.event(batch, family, revision, "reconcile", audit_boundary.LARGE_CONFIRMATION, state, state, {
            "receipt_sha256": receipt["receipt_sha256"],
            "reference": "Preserve every independent control. Check the unmodified full file separately from targeted masks.",
        })


def recover_audit_recheck_representation(ledger: Ledger, batch: str, family: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        if (state != "audit" or not issue or issue["evidence"] != audit_boundary.ACCEPTANCE_FORMAT_ERROR
                or audit_boundary.release(runner) is None
                or any(row["revision"] == revision and row["job"] == audit_boundary.RECHECK + repair_authority.FORMAT_RETRY
                       for row in ledger.attempts(family))):
            raise ValueError("A fresh representation attempt requires an exhausted, explicitly accepting audit recheck.")
        review, receipt, _ = runner.committed_result("audit", audit_boundary.RECHECK, "audit", audit_boundary.RecheckedAudit)
        if review.verdict != "accept" or not review.objections:
            raise ValueError("The existing recheck did not return the exact ambiguous acceptance representation.")
        ledger.event(batch, family, revision, "reconcile", audit_boundary.FORMAT_RETRY, state, state,
                     {"receipt_sha256": receipt["receipt_sha256"], "reference": "One fresh bounded representation check."})


def release_returned_authored_scope_plan(
    ledger: PooledLedger, batch: str, family: str, *, incoming_particulars_source: str | None = None,
    natural_provenance_restoration: bool = False,
) -> None:
    """Open one documentary replan from an independently rejected authored repair."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        earlier = autonomous_realism.release_event(runner)
        previous_receipts = autonomous_realism._authored_scope_receipts(earlier or {})
        if (not ledger.requires_delivery_attestation or earlier is None
                or earlier.get("parent_revision") != revision - 1 - len(autonomous_realism._pre_author_returns(earlier))
                - len(previous_receipts)
                or (len(previous_receipts) != int(natural_provenance_restoration))
                or state != "quarantined" or not issue or (issue["stage"], issue["code"]) != ("author", "scientific_review")
                or not ledger.pooled_revision(batch, family, revision)):
            raise ValueError("An authored-scope replan requires an independently returned documentary revision.")
        review, receipt, _ = runner.committed_result("author", repair_authority.VERIFY_JOB, "audit",
                                                     autonomous_realism.ScopeReview)
        if review.verdict != "changed" or not review.objections or issue["evidence"] != autonomous_realism.scope_failure(review):
            raise ValueError("The exact retained scope review must establish the documentary objection.")
        release = {key: value for key, value in earlier.items()
                   if key not in {"scope_ticket_omission", "generated_attachment_ticket", "incoming_particulars"}} | {
            "scope_return_receipt_sha256": receipt["receipt_sha256"],
            "family_sessions_remaining": ledger.effective_budget().families[family] - len(ledger.attempts(family)),
        }
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        if natural_provenance_restoration:
            previous_particulars = (earlier.get("incoming_particulars") or {}).get("source_id")
            if (not incoming_particulars_source or incoming_particulars_source != previous_particulars
                    or len(science.condition_ids(slot)) != 1 or (runner.directory / "family").exists()):
                raise ValueError("One final natural-file restoration requires the same proven recipient and no key.")
            release.update(earlier_authored_scope_receipts=previous_receipts, natural_provenance_restoration=True)
        if incoming_particulars_source is not None:
            if not any(incoming_particulars_source in reason for reason in review.objections):
                raise ValueError("The returned scope must identify the specific recipient Source.")
            particulars = delivery_particulars.reopen(runner, incoming_particulars_source)
            release["incoming_particulars"] = {"source_id": particulars.source_id,
                                              "record_sha256": authorisation.commitment(particulars)}
        successor = commission.session_runner(ledger, family, revision + 1)
        autonomous_realism._read_return(successor, slot, release)
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design", release)


def reopen_delivery_body_repair(ledger: PooledLedger, batch: str, family: str) -> None:
    """Recover an exact plan stopped for revising the body of a still-authorised attachment."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        release = autonomous_realism.release_event(runner)
        if (not ledger.requires_delivery_attestation or state != "design" or not issue
                or issue["evidence"] != delivery_particulars.RETAINED_BODY_REPAIR_STOP
                or not release or "incoming_particulars" not in release
                or any(row["revision"] == revision and row["stage"] != "design" for row in ledger.attempts(family))):
            raise ValueError("Only the exact stopped, un-authored delivery body repair can reopen.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        parent = autonomous_realism._read_return(runner, slot, release)
        plan, receipt, _ = runner.committed_result("design", repair_authority.PLAN_JOB, "audit", autonomous_realism.RepairPlan)
        autonomous_realism._verify_classification(slot, parent, plan, attested=True)
        _, affected = autonomous_realism._verify_plan(slot, parent, plan, attested=True)
        particulars = parent.incoming_particulars
        if particulars is None or not affected.intersection(particulars.source_ids()):
            raise ValueError("The retained plan must revise at least one previously authorised attachment.")
        ledger.event(batch, family, revision, "reconcile", "delivery_body_repair", state, state, {
            "receipt_sha256": receipt["receipt_sha256"], "plan_sha256": authorisation.commitment(plan),
            "particulars_sha256": authorisation.commitment(particulars), "affected_sources": sorted(affected),
            "reference": "The same sender and transmission survive. The revised document needs a new sender attestation.",
        })


def release_realism_with_retained_delivery_facts(
    ledger: PooledLedger, batch: str, family: str, recipient: str, *,
    exact_edit: recipient_edit.ExactRecipientEdit | None = None,
) -> None:
    """Allow one local documentary repair while keeping unverified questions open."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, _ = family_status(ledger, batch, family)
        disposition = _returned_realism(ledger, commission, family, revision, state)
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        repairs = [row for row in ledger.events(batch, family) if row["details"].get("keep_documentary_limits")]
        permitted = not repairs if exact_edit is None else (
            exact_edit.source_id == recipient and state == "quarantined" and len(repairs) == 1
            and "exact_recipient_edit" not in repairs[0]["details"]
        )
        if (not ledger.requires_delivery_attestation or disposition is None or len(science.condition_ids(slot)) != 1
                or not permitted):
            raise ValueError("A bounded natural-file realism return must support the exact retained documentary scope.")
        parent = commission.session_runner(ledger, family, revision)
        autonomous_realism.require_verified_incoming_basis(parent, recipient)
        particulars = delivery_particulars.reopen(parent, recipient)
        release = {
            "role": "batch_coordinator", "parent_revision": revision, "disposition_sequence": disposition["sequence"],
            "manifest_sha256": authorisation.commitment(commission.manifest),
            "family_sessions_remaining": ledger.effective_budget().families[family] - len(ledger.attempts(family)),
            "keep_documentary_limits": True,
            "incoming_particulars": {"source_id": recipient, "reviewed_source_revision": revision,
                                     "record_sha256": authorisation.commitment(particulars)},
        }
        if exact_edit is not None:
            release["exact_recipient_edit"] = exact_edit.model_dump(mode="json")
        successor = commission.session_runner(ledger, family, revision + 1)
        autonomous_realism._read_return(successor, slot, release)
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design", release)


def release_returned_pre_author_plan(
    ledger: PooledLedger, batch: str, family: str, *,
    omit_reply_for: str | None = None, omit_future_reference: autonomous_realism.FutureReferenceOmission | None = None,
    incoming_particulars_source: str | None = None, exact_omission_assessment: str | None = None,
) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        original = autonomous_realism.release_event(runner)
        if (original is None or state != "quarantined" or not issue
                or (issue["stage"], issue["code"]) != ("author", "scientific_review")
                or not ledger.pooled_revision(batch, family, revision)):
            raise ValueError("A preauthor replan requires an exact retained scientific scope return.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        record, _ = autonomous_realism.pre_author_scope_return(runner, slot=slot)
        if commissioning._read_json(issue["evidence"]) != record["review"]:
            raise ValueError("The retained independent scope review differs from the current exception.")
        earlier = autonomous_realism._pre_author_returns(original)
        if "exact_recipient_edit" in original and exact_omission_assessment is None:
            raise ValueError("An exact recipient scope return requires an independent omission assessment.")
        if exact_omission_assessment is not None:
            if (earlier or "exact_recipient_edit" not in original or "exact_omission_assessment" in original
                    or any((omit_reply_for, omit_future_reference, incoming_particulars_source))):
                raise ValueError("One independent omission assessment may reopen only an exact recipient repair.")
            edit = recipient_edit.ExactRecipientEdit.model_validate(original["exact_recipient_edit"])
            edit.require_exact_omission_objections(record["objections"])
            TypeAdapter(Digest).validate_python(exact_omission_assessment)
        omission: dict[str, Any] | None
        if omit_future_reference is not None:
            if omit_reply_for is not None or len(earlier) > 2 or "scope_ticket_omission" in original:
                raise ValueError("Use only one exact unavailable-document omission in an un-authored repair chain.")
            omission = autonomous_realism.remove_future_reference(runner, slot, omit_future_reference)[0]
        elif len(earlier) >= 2 or (earlier and len(record["objections"]) >= len(earlier[-1]["objections"])):
            raise ValueError("A repeated un-authored scope repair requires tangible progress on earlier objections.")
        else:
            omission = autonomous_realism.remove_separate_reply_ticket(runner, slot, omit_reply_for)[0] if omit_reply_for else None
        release = original | {
            "pre_author_scope_return": record,
            **({"prior_pre_author_scope_returns": earlier} if earlier else {}),
            **({"scope_ticket_omission": omission} if omission is not None else {}),
            **({"exact_omission_assessment": exact_omission_assessment} if exact_omission_assessment is not None else {}),
            "family_sessions_remaining": ledger.effective_budget().families[family] - len(ledger.attempts(family)),
        }
        if incoming_particulars_source is not None:
            if omission is not None or autonomous_realism._authored_scope_receipts(original) or len(science.condition_ids(slot)) != 1:
                raise ValueError("Carried delivery facts require a fresh plan for the same previously reviewed natural file.")
            parent = commission.session_runner(ledger, family, original["parent_revision"])
            autonomous_realism.require_verified_incoming_basis(parent, incoming_particulars_source)
            particulars = delivery_particulars.reopen(parent, incoming_particulars_source)
            release["incoming_particulars"] = {
                "source_id": particulars.source_id, "record_sha256": authorisation.commitment(particulars),
                "reviewed_source_revision": parent.revision,
            }
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design", release)


def release_exact_plan_classification(ledger: PooledLedger, batch: str, family: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        failure = f"{repair_authority.PLAN_JOB}{repair_authority.FORMAT_RETRY} failed its output contract: "
        events = ledger.events(batch, family)
        if (not ledger.requires_delivery_attestation or not ledger.pooled_revision(batch, family, revision)
                or autonomous_realism.release_event(runner) is None or state != "quarantined" or not issue
                or (issue["stage"], issue["code"], issue["evidence"])
                != ("design", "scientific_review", failure + autonomous_realism.PLAN_REFERENCE_FAILURE)
                or any(row["revision"] == revision and row["name"] == repair_authority.PLAN_RECOVERY for row in events)
                or any(row["revision"] == revision and row["stage"] != "design" for row in ledger.attempts(family))):
            raise ValueError("One fresh classification requires a stopped pre-author documentary repair.")
        details, _ = autonomous_realism.classification_retry_details(runner)
        ledger.event(batch, family, revision, "reconcile", repair_authority.PLAN_RECOVERY, state, "design", {
            "exact_classification": details,
        })


def release_generated_attachment_ticket_recovery(ledger: PooledLedger, batch: str, family: str, source_id: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        original = autonomous_realism.release_event(runner)
        if (original is None or state != "quarantined" or not issue
                or (issue["stage"], issue["code"]) != ("author", "scientific_review")
                or "generated_attachment_ticket" in original or "scope_ticket_omission" in original
                or not ledger.pooled_revision(batch, family, revision)):
            raise ValueError("An automatic-ticket recovery requires the exact stopped un-authored scope review.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        proof, _, _ = autonomous_realism.generated_attachment_ticket(runner, slot, source_id)
        scope = proof["prior_scope"]
        if commissioning._read_json(issue["evidence"]) != scope["review"]:
            raise ValueError("The independently returned automatic ticket differs from the stopped packet.")
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design", original | {
            "pre_author_scope_return": scope, "prior_pre_author_scope_returns": autonomous_realism._pre_author_returns(original),
            "generated_attachment_ticket": proof,
            "family_sessions_remaining": ledger.effective_budget().families[family] - len(ledger.attempts(family)),
        })


def release_empty_attachment_ticket_recovery(ledger: Ledger, batch: str, family: str, source_id: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, blocking = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        parent = autonomous_realism.release_event(runner)
        if (state != "quarantined" or not blocking or blocking["stage"] != "author"
                or parent is None or parent.get("parent_revision") != revision - 1):
            raise ValueError("Only a freshly returned documentary revision can reopen the empty attachment ticket.")
        details = autonomous_realism.empty_attachment_ticket_return(runner, source_id)
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design",
                     parent | {"empty_ticket_return": details})


def release_unambiguous_review_note(ledger: PooledLedger, batch: str, family: str, note_key: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        release = autonomous_realism.release_event(runner)
        job = repair_authority.PLAN_JOB + repair_authority.FORMAT_RETRY
        reason = "The proposed repair changes committed targets, roster or contrast structure."
        if (not ledger.requires_delivery_attestation or not ledger.pooled_revision(batch, family, revision)
                or release is None or "pre_author_scope_return" not in release
                or state != "quarantined" or not issue or issue["stage"] != "design"
                or issue["evidence"] != f"{job} failed its output contract: {reason}"
                or any(row["revision"] == revision and row["stage"] != "design" for row in ledger.attempts(family))):
            raise ValueError("A review-note recovery requires the exact stopped un-authored repair lineage.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        parent = autonomous_realism._read_return(runner, slot, release)
        record, plan, receipt = autonomous_realism.recover_retained_design_note(runner, slot, parent, note_key)
        if not any(row["revision"] == revision and row["kind"] == "rejected_output" and row["name"] == job
                   and row["details"] == {"reason": reason, "receipt_sha256": receipt["receipt_sha256"]}
                   for row in ledger.events(batch, family)):
            raise ValueError("The recovery must bind the exact independent rejected plan.")
        autonomous_realism._verify_plan(slot, parent, plan, attested=True)
        ledger.event(batch, family, revision, "reconcile", repair_authority.RETAINED_DESIGN_NOTE, state, "design", record)


def recover_blind_whitespace(ledger: Ledger, batch: str, family: str, job: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        expected = f"{job}-exact-format failed its output contract: {read_format_recovery.QUOTE_ERROR}"
        if (state not in {"blind", "quarantined"} or not issue or issue["stage"] != "blind"
                or issue["code"] != "scientific_review" or issue["evidence"] != expected):
            raise ValueError("Only the exact retained blind quotation failure can reopen.")
        runner = commission.session_runner(ledger, family, revision)
        record, _, _, _ = read_format_recovery.whitespace_recovery(runner, job)
        ledger.event(batch, family, revision, "reconcile", read_format_recovery.WHITESPACE_RELEASE + job,
                     state, "blind", record)


def recover_mask_output(ledger: Ledger, batch: str, family: str, job: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        events = ledger.events(batch, family)
        errors = {f"{job}-format-retry failed its output contract: {error}" for error in read_format_recovery.ERRORS}
        if (state not in {"masks", "quarantined"} or not issue or issue["stage"] != "masks"
                or issue["code"] != "scientific_review" or issue["evidence"] not in errors
                or any(row["revision"] == revision and row["name"] in {
                    read_format_recovery.MASK_RELEASE + job, read_format_recovery.MASK_WHITESPACE_RELEASE + job,
                } for row in events)):
            raise ValueError("Only the exact retained masked output representation failure can reopen.")
        runner = commission.session_runner(ledger, family, revision)
        retained = read_format_recovery.release_details(runner, job, role="masked")
        try:
            record, _, _, _ = read_format_recovery.whitespace_recovery(runner, job, role="masked")
        except ValueError:
            prefix = read_format_recovery.MASK_RELEASE
            record = retained
            ledger.require_capacity(family, revision, {job + "-exact-format"})
        else:
            prefix = read_format_recovery.MASK_WHITESPACE_RELEASE
        ledger.event(batch, family, revision, "reconcile", prefix + job, state, "masks", record)


def reopen_paused_reading(ledger: PooledLedger, batch: str, family: str) -> None:
    """Allow one fresh isolated observation after a verified pause interrupted dispatch."""
    with ledger.coordinator_lock():
        ledger.require_running()
        revision, state, issue = family_status(ledger, batch, family)
        if (state not in {"blind", "masks"} or not issue or issue["stage"] != state
                or issue["code"] != "failed_dispatch" or issue["evidence"] != read_format_recovery.PAUSE_REASON
                or not issue["job"]):
            raise ValueError("Only a retained predispatch pause can reopen an unchanged reading.")
        job = issue["job"]
        runner = load_commission(ledger, batch).session_runner(ledger, family, revision)
        record, _ = read_format_recovery.paused_reading(runner, job, role="annotation" if state == "blind" else "masked")
        ledger.require_capacity(family, revision, {job + "-after-pause"})
        ledger.event(batch, family, revision, "reconcile", read_format_recovery.PAUSE_RELEASE + job, state, state, record)


def recover_adjudication_approval_ids(ledger: Ledger, batch: str, family: str, index: int) -> None:
    """Resume an unlocked key after proving an exact identity representation correction."""
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, blocking = family_status(ledger, batch, family)
        if (not ledger.requires_delivery_attestation or state != "adjudicate" or not blocking
                or blocking["code"] != "scientific_review"
                or blocking["evidence"] not in {adjudication_contract.SOURCE_APPROVAL_FAILURE,
                                                adjudication_contract.SOURCE_APPROVAL_QUOTE_FAILURE,
                                                adjudication_contract.KEY_REPLAY_FAILURE}):
            raise ValueError("Only the retained adjudication approval representation failure can reopen.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        condition = science.condition_ids(slot)[index]
        runner = commission.session_runner(ledger, family, revision)
        job = f"adjudicate-{index:03}"
        if (runner.directory / "family" / f"{condition}.json").exists():
            raise ValueError("A locked adjudication key cannot be relabelled.")
        original, receipt, request = runner.committed_result("adjudicate", job, "adjudication", Adjudication)
        result, edits = adjudication_contract.localize_key_presentation(original)
        ideal_edits = any(edit["path"].startswith("/key/ideal/relationships/") for edit in edits)
        if (not edits or original.key.condition != "local"
                or (blocking["evidence"] == adjudication_contract.KEY_REPLAY_FAILURE and not ideal_edits)):
            raise ValueError("The original response contains no unique local-ID correction.")
        inputs = request["inputs"]
        sources = [Source.model_validate(row) for row in commissioning._read_json(inputs["sources"])]
        first = Reading.model_validate_json(inputs["annotation_a"])
        second = Reading.model_validate_json(inputs["annotation_b"])
        result = result.model_copy(update={"key": result.key.model_copy(update={"condition": condition})})
        science.verify_adjudication(condition, result, sources, science.compare_readings(first, second, sources))
        ledger.event(batch, family, revision, "reconcile", f"{job}-local-approval-ids", state, state, {
            "receipt_sha256": receipt["receipt_sha256"], "changes": edits,
            "reference": "Unique existing local entity IDs verified by the unchanged evidence validator.",
        })


def release_incomplete_adjudication_proof(ledger: PooledLedger, batch: str, family: str, index: int) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        prior = frozen_rekey.recorded(runner)
        job = f"adjudicate-{index:03}"
        if (prior is None or state != "adjudicate" or not issue
                or issue["evidence"] != adjudication_contract.KEY_REPLAY_FAILURE
                or adjudication_contract.proof_retry(runner, job) is not None):
            raise ValueError("A fresh proof attempt requires the exact unlocked frozen-evidence failure.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        condition = science.condition_ids(slot)[index]
        case = frozen_rekey.reopen(runner, slot, prior)
        original, receipt, request = runner.committed_result("adjudicate", job, "adjudication", Adjudication)
        result, _ = adjudication_contract.localize_key_presentation(original)
        sources = case.bundles[condition]
        if (result.unresolved or result.key.condition != "local"
                or (runner.directory / "family" / f"{condition}.json").exists()
                or TypeAdapter(list[Source]).validate_json(request["inputs"]["sources"]) != sources
                or science.adjudication_replay_defects(result, sources) != (False, True)):
            raise ValueError("Only exact proof attachments may be incomplete in the rejected same-graph key.")
        frozen_rekey.verify_same_semantics(result, case.locked[condition])
        ledger.event(batch, family, revision, "reconcile", adjudication_contract.PROOF_RETRY + job, state, state, {
            "receipt_sha256": receipt["receipt_sha256"], "freeze_sha256": prior.freeze_sha256,
        })


def recover_adjudication_whitespace(ledger: PooledLedger, batch: str, family: str, index: int) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, issue = family_status(ledger, batch, family)
        runner = commission.session_runner(ledger, family, revision)
        job = f"adjudicate-{index:03}"
        if (not ledger.requires_delivery_attestation or state != "adjudicate" or not issue
                or issue["code"] != "scientific_review"
                or not issue["evidence"].endswith("supporting_text does not occur verbatim in source")
                or adjudication_contract.quote_recovery(runner, job) is not None):
            raise ValueError("Only the exact stopped adjudicated quotation can use whitespace recovery.")
        slot = next(row for row in commission.portfolio.slots if row.family_id == family)
        condition = science.condition_ids(slot)[index]
        if (runner.directory / "family" / f"{condition}.json").exists():
            raise ValueError("An already locked key cannot be changed by whitespace recovery.")
        original, receipt, request = runner.committed_result("adjudicate", job, "adjudication", Adjudication)
        sources = TypeAdapter(list[Source]).validate_json(request["inputs"]["sources"])
        derivative, edits = adjudication_contract.exact_whitespace_key(original, sources)
        if not edits or original.key.condition != "local":
            raise ValueError("The rejected key has no unique exact quotation derivative.")
        projected, local_id_edits = adjudication_contract.localize_key_presentation(derivative)
        if local_id_edits:
            raise ValueError("A quotation-only recovery cannot also change local endpoint presentation.")
        agreement = science.compare_readings(Reading.model_validate_json(request["inputs"]["annotation_a"]),
                                             Reading.model_validate_json(request["inputs"]["annotation_b"]), sources)
        locked = projected.model_copy(update={"key": projected.key.model_copy(update={"condition": condition})})
        science.verify_adjudication(condition, locked, sources, agreement)
        ledger.event(batch, family, revision, "reconcile", adjudication_contract.QUOTE_RECOVERY + job, state, state, {
            "receipt_sha256": receipt["receipt_sha256"], "derivative_sha256": authorisation.commitment(derivative), "edits": edits,
        })


def release_adjudication_documentary_repair(ledger: Ledger, batch: str, family: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, blocking = family_status(ledger, batch, family)
        if (state != "adjudicate" or not blocking
                or (blocking["code"], blocking["evidence"]) != ("scientific_review", autonomous_realism.ADJUDICATION_RETURN)
                or any(event["name"] == repair_authority.REVISION and "adjudication_return" in event["details"]
                       for event in ledger.events(batch, family))):
            raise ValueError("Only one bounded documentary repair can follow the first unlocked adjudication return.")
        runner = commission.session_runner(ledger, family, revision)
        if not repair_authority.enabled(ledger, commission.manifest):
            raise ValueError("This family has no autonomous documentary repair authority.")
        adjudication = autonomous_realism.document_adjudication_return(runner)
        ledger.event(batch, family, revision + 1, "transition", repair_authority.REVISION, state, "design", {
            "role": "batch_coordinator", "parent_revision": revision,
            "adjudication_return": adjudication, "manifest_sha256": authorisation.commitment(commission.manifest),
            "family_sessions_remaining": ledger.effective_budget().families[family] - len(ledger.attempts(family)),
        })


def recover_blind_representation(ledger: Ledger, batch: str, family: str, job: str) -> None:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, batch)
        revision, state, blocking = family_status(ledger, batch, family)
        if state not in {"blind", "quarantined"} or not blocking or (
            blocking["stage"], blocking["code"]
        ) != ("blind", "scientific_review"):
            raise ValueError("A fresh blind reading requires a held blind representation exception.")
        runner = commission.session_runner(ledger, family, revision)
        details = read_format_recovery.release_details(runner, job)
        ledger.event(batch, family, revision, "reconcile", read_format_recovery.RELEASE + job,
                     state, "blind", details)


def recover_annotation(ledger: Ledger, decision: AnnotationRecovery) -> str:
    with ledger.coordinator_lock():
        commission, slot, review = _owner_family_review(ledger, decision)
        revision, state, blocking = family_status(ledger, decision.batch_id, decision.family_id)
        runner = commission.session_runner(ledger, decision.family_id, revision)
        existing = annotation_recovery.recorded(runner)
        if existing is not None:
            if existing["decision"] != decision.model_dump(mode="json"):
                raise ValueError("Only one immutable mechanical blind correction is permitted per revision.")
            annotation_recovery.reopen(runner, existing)
            return str(existing["derivative_sha256"])
        if not review.accepts(slot.family_id) or state != "blind" or not blocking or (
            blocking["code"] != "scientific_review" or blocking["repair_permitted"]
        ):
            raise ValueError("Annotation recovery requires an accepted design halted at blind exact validation.")
        record, corrected, _, _ = annotation_recovery.derive(runner, decision)
        digest = artifacts.write_bytes(annotation_recovery.derivative_path(runner, decision.reader_job), corrected)
        ledger.event(decision.batch_id, decision.family_id, revision, "reconcile",
                     annotation_recovery.ANNOTATION_RECOVERY, "blind", "blind", record)
        return digest


def recover_adjudication_quote(ledger: Ledger, decision: AdjudicationQuoteRecovery) -> str:
    with ledger.coordinator_lock():
        commission, slot, review = _owner_family_review(ledger, decision)
        revision, state, blocking = family_status(ledger, decision.batch_id, decision.family_id)
        runner = commission.session_runner(ledger, decision.family_id, revision)
        existing = adjudication_recovery.recorded(runner)
        if existing is not None:
            if existing["decision"] != decision.model_dump(mode="json"):
                raise ValueError("Only one immutable adjudication quote correction is permitted per revision.")
            adjudication_recovery.reopen(runner, existing)
            return str(existing["derivative_sha256"])
        if (not review.accepts(slot.family_id) or state != "adjudicate" or not blocking
                or blocking["code"] != "scientific_review"
                or blocking["evidence"] != adjudication_recovery.QUOTE_SEMANTICS_ERROR):
            raise ValueError("Quote recovery requires the exact retained adjudication quote mismatch.")
        record, corrected, _, _ = adjudication_recovery.derive(runner, decision)
        digest = artifacts.write_bytes(adjudication_recovery.derivative_path(runner), corrected)
        ledger.event(decision.batch_id, decision.family_id, revision, "reconcile",
                     adjudication_recovery.ADJUDICATION_QUOTE_RECOVERY, "adjudicate", "adjudicate", record)
        return digest


def release_audit(ledger: Ledger, decision: AuditRecovery) -> str:
    with ledger.coordinator_lock():
        commission, slot, review = _owner_family_review(ledger, decision)
        revision, state, blocking = family_status(ledger, decision.batch_id, decision.family_id)
        runner = commission.session_runner(ledger, decision.family_id, revision)
        existing = audit_recovery.recorded(runner)
        audit_recovery.verify_authority(runner, decision)
        if existing is not None:
            if existing != decision:
                raise ValueError("The one-time audit recovery is immutable.")
            return authorisation.commitment(decision)
        budget = continuation.recorded_budget(ledger.events(decision.batch_id))
        if budget is None or authorisation.commitment(budget) != decision.budget_amendment_sha256:
            raise ValueError("Release requires the current approved budget amendment.")
        if (not review.accepts(slot.family_id) or state != "audit" or not blocking
                or blocking["code"] != "scientific_review" or blocking["evidence"] != audit_recovery.FAILURE):
            raise ValueError("Only the retained critical-map audit exception can enter this recovery.")
        recovery = adjudication_recovery.recorded(runner)
        if recovery is None:
            raise ValueError("Fresh audit requires the completed adjudication recovery.")
        adjudication_recovery.reopen(runner, recovery)
        jobs = {audit_recovery.JOB} | {f"mask-{number:03}" for number in range(len(decision.views))}
        if any(row["revision"] == revision and row["job"] in jobs for row in ledger.attempts(slot.family_id)):
            raise ValueError("Fresh audit requires unreserved recovery and mask jobs.")
        ledger.require_capacity(slot.family_id, revision, jobs)
        ledger.event(decision.batch_id, decision.family_id, revision, "reconcile", audit_recovery.JOB,
                     "audit", "audit", decision.model_dump(mode="json"))
        return authorisation.commitment(decision)


def record_deferred_review(ledger: Ledger, decision: DeferredExceptionReview) -> None:
    with ledger.coordinator_lock():
        commission, slot, review = _owner_family_review(ledger, decision)
        revision, state, blocking = family_status(ledger, decision.batch_id, decision.family_id)
        runner = commission.session_runner(ledger, decision.family_id, revision)
        disposition = decision.disposition
        if isinstance(disposition, RepairScopeReview):
            if state != "returned" or not review.accepts(slot.family_id):
                raise ValueError("Scope-only approval requires an accepted design returned at realism.")
            exception_review.verify_repair_scope(runner, slot, disposition, blocking)
        else:
            if state != "pending_design_review" or review.accepts(slot.family_id):
                raise ValueError("Child merits require a returned design still held at design review.")
            exception_review.verify_child_merits(runner, slot, disposition)
        ledger.event(decision.batch_id, decision.family_id, revision, "deferred_review", disposition.status,
                     state, state, decision.model_dump(mode="json"))


def _owner_family_review(
    ledger: Ledger, decision: OwnerFamilyReview,
) -> tuple[Commission, FamilySlot, DesignReview]:
    ledger.require_running()
    commission = load_commission(ledger, decision.batch_id)
    manifest = commission.manifest
    if decision.owner != commission.decision.owner or decision.manifest_sha256 != authorisation.commitment(manifest):
        raise ValueError("Scientific exception review requires the commissioning owner and exact manifest.")
    if decision.family_id not in {row.family_id for row in manifest.families}:
        raise ValueError("Review only families in the commissioned batch.")
    _verify_resume(ledger, commission)
    review = design_review.recorded_review(ledger, manifest, decision.owner)
    if review is None:
        raise ValueError("Scientific exception review requires a recorded design review.")
    slot = next(row for row in commission.portfolio.slots if row.family_id == decision.family_id)
    authorisation.verify_hypothesis(slot.family_id, slot.hypothesis, decision.owner)
    return commission, slot, review


def apply_budget_amendment(ledger: Ledger, decision: BudgetAmendment) -> str:
    with ledger.coordinator_lock():
        ledger.require_running()
        commission = load_commission(ledger, decision.batch_id)
        if (commission.manifest.phase != "pilot" or ledger.batch_ids() != [decision.batch_id]
                or decision.owner != commission.decision.owner
                or decision.manifest_sha256 != authorisation.commitment(commission.manifest)
                or decision.portfolio_sha256 != authorisation.commitment(commission.portfolio)
                or decision.original_approval_sha256 != authorisation.commitment(commission.decision)):
            raise ValueError("The amendment requires the original pilot, commissioning owner and exact commitments.")
        _verify_resume(ledger, commission)
        commitment = authorisation.commitment(decision)
        events = ledger.events(decision.batch_id)
        prior = continuation.recorded_budget(events, expected_sha256=commitment)
        if prior is None:
            if decision.schema_version == 1 and continuation.recorded_budget(events) is not None:
                raise ValueError("The recorded budget amendment is immutable.")
            _verify_completed_charges(ledger, commission, decision.completed_charges)
        ledger.amend_budget(decision)
        return commitment


def _verify_completed_charges(ledger: Ledger, commission: Commission, expected: dict[str, int]) -> None:
    attempts = {row.family_id: ledger.attempts(row.family_id) for row in commission.manifest.families}
    if expected != {family: len(rows) for family, rows in attempts.items()}:
        raise ValueError("The amendment must bind the exact completed charges for every family.")
    for family, rows in attempts.items():
        for row in rows:
            runner = commission.session_runner(ledger, family, row["revision"])
            role = commissioning._read_json(row["request"])["role"]
            runner.committed_packet(row["stage"], row["job"], role)


def continue_family(ledger: Ledger, decision: FamilyContinuation) -> None:
    with ledger.coordinator_lock():
        commission, slot, review = _owner_family_review(ledger, decision)
        events = ledger.events(decision.batch_id, decision.family_id)
        existing = continuation.family_release(events)
        payload = decision.model_dump(mode="json")
        prior = next((row["details"] for row in events if row["kind"] == "family_release"
                      and row["name"] == decision.release.action), None)
        if prior is not None:
            if prior["decision"] != payload:
                raise ValueError("The family continuation is immutable.")
            return
        budget = continuation.recorded_budget(ledger.events(decision.batch_id))
        if budget is None or authorisation.commitment(budget) != decision.budget_amendment_sha256:
            raise ValueError("The family release must bind the recorded budget amendment.")
        complete = decision.release.action == "complete_evidence_adjudication"
        if complete:
            if not existing or existing["decision"]["release"]["action"] != "fresh_adjudication":
                raise ValueError("Complete-evidence recovery requires the retained first continuation.")
        elif existing is not None:
            raise ValueError("The family continuation is immutable.")

        revision, state, blocking = family_status(ledger, decision.batch_id, decision.family_id)
        runner = commission.session_runner(ledger, decision.family_id, revision)
        commitment = next(row.design_sha256 for row in review.designs if row.family_id == decision.family_id)
        release = decision.release
        record: dict[str, Any] = {"decision": payload, "design_sha256": commitment}

        if isinstance(release, FreshAdjudication):
            reason = (adjudication_contract.SOURCE_APPROVAL_FAILURE if complete
                      else "Adjudication must resolve every graph or attached-evidence disagreement.")
            if (not review.accepts(slot.family_id) or state != "adjudicate" or not blocking
                    or blocking["code"] != "scientific_review" or blocking["evidence"] != reason):
                raise ValueError("A fresh adjudication requires its exact retained adjudication halt.")
            record["resolution_ids"] = continuation.fresh_resolution_ids(runner, release)
            next_revision, next_stage = revision, "adjudicate"
        else:
            next_revision, next_stage = revision + 1, "design"
            if isinstance(release, RepairExecution):
                held = continuation.deferred(events, revision, release.scope_review_sha256).disposition
                if (revision != 1 or state != "returned" or not review.accepts(slot.family_id)
                        or not isinstance(held, RepairScopeReview) or held.design_sha256 != commitment):
                    raise ValueError("Repair execution requires the first approved documentary scope.")
                exception_review.verify_repair_scope(runner, slot, held, blocking)
                record["repair_tickets"] = continuation.repair_tickets(runner, held, release.direct_sources)
            else:
                held = continuation.deferred(events, revision, release.merits_review_sha256).disposition
                if (state != "pending_design_review" or review.accepts(slot.family_id)
                        or not isinstance(held, ChildDesignMerits)
                        or held.child_design_sha256 != release.child_design_sha256):
                    raise ValueError("Activation requires the exact held child merits decision.")
                exception_review.verify_child_merits(runner, slot, held)
                record["design_sha256"] = held.child_design_sha256
        ledger.event(decision.batch_id, decision.family_id, next_revision, "family_release",
                     release.action, state, next_stage, record)
