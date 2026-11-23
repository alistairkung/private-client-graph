"""Isolated documentary repair planning and revision lineage for milestone families."""

import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, authorisation, repair_authority, science
from benchmark_v3.batch.contracts import DesignOutput, MatchedCondition, RealismReview, SourceId
from benchmark_v3.batch.ledger import BudgetExhausted
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchSourceFreeze
from benchmark_v3.research_contracts import Contract, Text
from private_client_graph.models.source import Source

PLAN_PROMPT = (
    "Independently diagnose the returned fictional Matter before it has a key. Classify each supplied objection "
    "by its cause and affected Sources. Plan the smallest coherent repair. Address the material objections of "
    "every reviewer. Output a full revised design only when author briefs, possession, chronology or another "
    "design detail must change. Keep the approved hypothesis, contrast, critical graph declarations and scope. "
    "Incidental section assignments may change only if they do not test a scientific property. Keep all "
    "declared proper-prefix views. Judge progress against the previously attempted repair when supplied. "
    "Write each ticket as instructions addressed to its own participant using only knowledge available to them. "
    "Keep private history, matched alternatives, reviewers' findings, research purpose and planned answers "
    "out of the tickets and participant briefs. Return infeasible or scope_change with reasons when warranted."
)
VERIFY_PROMPT = (
    "Independently compare the original and revised fictional files with their designs and the approved hypothesis. "
    "Check that the intended contrast, scoped relationships, cut-off question, invariant evidence, participant "
    "knowledge and planned scientific controls have been preserved. Check that the revised design has not "
    "made the comparison easier by revealing answers. Revisions to incidental documentary details are allowed. "
    "Give explicit findings on scope, provenance and contrast. Reject a material change or compromised isolation. "
    "Separate scientific scope from documentary polish, which fresh realism reviewers assess independently."
)


class Objection(Contract):
    cause: Literal["documentary", "provenance", "chronology", "participant_knowledge", "design"]
    sources: list[SourceId]
    diagnosis: Text


class RepairPlan(Contract):
    disposition: Literal["repair", "infeasible", "scope_change"]
    objections: dict[Text, Objection]
    revised_design: DesignOutput | None = None
    tickets: dict[SourceId, Text]
    progress: Literal["initial", "improved", "none"]
    rationale: Text


class ScopeReview(Contract):
    verdict: Literal["preserved", "changed"]
    scope: Text
    provenance: Text
    contrast: Text
    objections: list[Text]


class RepairStopped(ValueError):
    """A documented refusal to advance a repair under the current scope."""


@dataclass(frozen=True)
class ReturnedFile:
    design: DesignOutput
    bundles: dict[str, list[Source]]
    freeze: BatchSourceFreeze
    objections: dict[str, str]
    reviews: dict[str, Any]
    review_commitments: dict[str, str]
    previous_plan: RepairPlan | None
    earlier_objections: list[dict[str, Any]]

    def inputs(self, slot: FamilySlot) -> dict[str, str]:
        key = f"{slot.hypothesis.hypothesis_id}@{slot.hypothesis.revision}"
        hypothesis, ref, _ = commissioning.proposal_history()[key]
        if ref != slot.hypothesis:
            raise ValueError("The approved hypothesis commitment changed.")
        return {
            "paired_bundles": _bundles(self.bundles),
            "intended_intervention": commissioning.json_text({
                "hypothesis": hypothesis.model_dump(mode="json"),
                "original_design": self.design.model_dump(mode="json"),
            }),
        }


@dataclass(frozen=True)
class Revision:
    parent: ReturnedFile
    design: DesignOutput
    plan: RepairPlan
    affected: set[str]
    lineage: dict[str, Any]
    planner_job: str


def release_event(runner: SessionRunner) -> dict[str, Any] | None:
    return next((
        row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if row["revision"] == runner.revision and row["kind"] == "transition"
        and row["name"] == repair_authority.REVISION
    ), None)


def plan_revision(
    runner: SessionRunner, slot: FamilySlot, release: dict[str, Any],
) -> tuple[Revision, dict[str, Any]]:
    try:
        parent = _read_return(runner, slot, release)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        raise packet.PacketIsolationError("The original realism inputs and receipts failed their commitments.") from error
    if not any(row["revision"] == runner.revision and row["job"] == repair_authority.PLAN_JOB
               for row in runner.ledger.attempts(runner.family)):
        runner.ledger.require_capacity(
            runner.family, runner.revision,
            mandatory_jobs(parent.design, set(), planning=True, verification=True, assume_whole_file=True),
        )

    inputs = parent.inputs(slot) | {
        "audit_rules": commissioning.json_text({
            "objections": parent.objections, "condition_local_reviews": parent.reviews,
            "prior_repair": parent.previous_plan.model_dump(mode="json") if parent.previous_plan else None,
            "earlier_documentary_objections": parent.earlier_objections,
            "capacity": {
                "family_sessions_before_planning": release["family_sessions_remaining"],
                "mandatory_at_existing_topology_before_regenerated_authors_and_masks": len(
                    mandatory_jobs(parent.design, set(), planning=True, verification=True),
                ) - 1,
                "mandatory_at_whole_file_topology_before_regenerated_authors_and_masks": len(
                    mandatory_jobs(parent.design, set(), planning=True, verification=True, assume_whole_file=True),
                ) - 1,
            },
        }),
    }
    plan, receipt, design, affected, job = _select_plan(runner, slot, parent, inputs, release)
    lineage = {
        "parent_revision": runner.revision - 1, "hypothesis_sha256": slot.hypothesis.hypothesis_sha256,
        "parent_design_sha256": authorisation.commitment(parent.design),
        "design_sha256": authorisation.commitment(design), "plan_sha256": authorisation.commitment(plan),
        "planner_receipt_sha256": receipt["receipt_sha256"],
        "original_source_commitments": parent.freeze.source_commitments,
        "original_review_receipts": parent.review_commitments, "affected_sources": sorted(affected),
    }
    return Revision(parent, design, plan, affected, lineage, job), receipt


def _select_plan(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, inputs: dict[str, str], release: dict[str, Any],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
    def propose(job: str, prompt: str, packet_inputs: dict[str, str]) -> tuple[RepairPlan, dict[str, Any]]:
        result, receipt = runner.run(
            "design", job, "audit", packet_inputs, prompt, RepairPlan,
            validate=lambda plan: _verify_classification(slot, parent, plan),
        )
        artifacts.write_json(runner.directory / f"{job}.json", result.model_dump(mode="json"))
        return result, receipt

    plan, receipt = propose(repair_authority.PLAN_JOB, PLAN_PROMPT, inputs)
    design, affected = _verify_plan(slot, parent, plan)
    original_jobs = mandatory_jobs(design, affected, verification=True)
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    selected = next((row["details"]["job"] for row in events if row["revision"] == runner.revision
                     and row["kind"] == "repair_plan_selection"), None)
    if selected != repair_authority.BUDGET_PLAN_JOB:
        try:
            runner.ledger.require_capacity(runner.family, runner.revision, original_jobs)
        except BudgetExhausted:
            if selected == repair_authority.PLAN_JOB:
                raise
        else:
            _record_plan_selection(runner, repair_authority.PLAN_JOB, receipt)
            return plan, receipt, design, affected, repair_authority.PLAN_JOB

    attempts = [row for row in runner.ledger.attempts(runner.family) if row["revision"] == runner.revision]
    original_charges = sum(row["job"] in {repair_authority.PLAN_JOB, repair_authority.PLAN_JOB + repair_authority.FORMAT_RETRY}
                           for row in attempts)
    budget_job = repair_authority.BUDGET_PLAN_JOB
    if not any(row["job"] == budget_job for row in attempts):
        runner.ledger.require_capacity(runner.family, runner.revision, {
            budget_job, "author-minimum",
            *mandatory_jobs(parent.design, set(), verification=True, assume_whole_file=True),
        })
    rules = commissioning._read_json(inputs["audit_rules"])
    rules["unaffordable_plan"] = {
        "proposal": plan.model_dump(mode="json"), "required_remaining_sessions_before_masks": len(original_jobs),
        "available_before_replanning": release["family_sessions_remaining"] - original_charges,
    }
    plan, receipt = propose(
        budget_job, PLAN_PROMPT + " Independently assess a lower-cost lawful repair. "
        "Account for the additional planning turn. Preserve every scientific requirement or return infeasible.",
        inputs | {"audit_rules": commissioning.json_text(rules)},
    )
    design, affected = _verify_plan(slot, parent, plan)
    runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
    _record_plan_selection(runner, budget_job, receipt)
    return plan, receipt, design, affected, budget_job


def _record_plan_selection(runner: SessionRunner, job: str, receipt: dict[str, Any]) -> None:
    runner.ledger.event(runner.manifest.batch_id, runner.family, runner.revision, "repair_plan_selection",
                        "chosen", "design", "design", {"job": job, "receipt_sha256": receipt["receipt_sha256"]})


def _read_return(runner: SessionRunner, slot: FamilySlot, release: dict[str, Any]) -> ReturnedFile:
    revision = runner.revision - 1
    ledger, batch, family = runner.ledger, runner.manifest.batch_id, runner.family
    previous = SessionRunner(ledger, runner.manifest, family, revision, runner.directory.parent / str(revision), runner.owner)
    history = ledger.events(batch, family)
    events = [row for row in history if row["revision"] == revision]
    disposition = next(row for row in events if row["kind"] == "disposition" and row["name"] == "realism")
    if (release["parent_revision"] != revision or release["disposition_sequence"] != disposition["sequence"]
            or release["manifest_sha256"] != authorisation.commitment(runner.manifest)):
        raise ValueError("The repair must bind the exact previous realism disposition and approved manifest.")
    design = artifacts.read_contract(previous.directory / "design.json", DesignOutput)
    locked_design = next(row for row in events if row["kind"] == "transition" and row["name"] == "design")
    if locked_design["details"]["outputs"]["design"] != authorisation.commitment(design):
        raise ValueError("The prior design commitment changed.")
    reviews, supplied, receipts = {}, {}, {}
    objections = {}
    for index, condition in enumerate(science.condition_ids(slot)):
        job = f"realism-{index:03}"
        review, receipt, request = previous.committed_result("realism", job, "realism", RealismReview)
        reviews[condition] = review.model_dump(mode="json")
        receipts[condition] = receipt["receipt_sha256"]
        supplied[condition] = TypeAdapter(list[Source]).validate_json(request["inputs"]["sources"])
        if review.verdict != "pass" or review.objections:
            issues = review.objections or [review.summary]
            objections.update({f"{condition}:{i}": issue for i, issue in enumerate(issues, start=1)})
    if reviews != commissioning._read_json(disposition["details"]["evidence"]) or not objections:
        raise ValueError("The realism responses differ from the returned disposition.")
    natural = supplied[science.condition_ids(slot)[0]]
    bundles, freeze = science.freeze_bundles(slot, design, natural)
    authored = next(row for row in events if row["kind"] == "transition" and row["name"] == "author")
    expected = commissioning.digest(commissioning.json_text(
        [source.model_dump(mode="json") for source in natural],
    ).encode())
    if supplied != bundles or authored["details"]["outputs"]["natural"] != expected:
        raise ValueError("The reviewed Sources differ from the immutable authored inventory.")
    prior = None
    if any(row["kind"] == "transition" and row["name"] == repair_authority.REVISION for row in events):
        selection = next((row["details"] for row in events if row["kind"] == "repair_plan_selection"), None)
        job = selection["job"] if selection else repair_authority.PLAN_JOB
        prior = artifacts.read_contract(previous.directory / f"{job}.json", RepairPlan)
        committed, receipt, _ = previous.committed_result("design", job, "audit", RepairPlan)
        if prior != committed or selection and receipt["receipt_sha256"] != selection["receipt_sha256"]:
            raise ValueError("The prior repair plan differs from its charged original.")
    earlier = [
        {"revision": row["revision"], "reviews": commissioning._read_json(row["details"]["evidence"])}
        for row in history if row["revision"] < revision and row["kind"] == "disposition" and row["name"] == "realism"
    ]
    return ReturnedFile(design, bundles, freeze, objections, reviews, receipts, prior, earlier)


def _verify_classification(slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan) -> None:
    earlier = {
        (row["revision"], f"{condition}:{index}")
        for row in parent.earlier_objections
        for condition, review in row["reviews"].items()
        if review["verdict"] != "pass" or review["objections"]
        for index in range(1, len(review["objections"] or [review["summary"]]) + 1)
    }
    reference_aliases = set()
    for key in plan.objections.keys() - parent.objections.keys():
        match = re.fullmatch(r"revision[_ -]?([1-9][0-9]*):(.+)", key)
        if match is None:
            raise ValueError("Every additional classification must identify a retained earlier objection.")
        reference = (int(match[1]), match[2])
        if reference not in earlier or reference in reference_aliases:
            raise ValueError("Earlier classifications must bind unique retained objections.")
        reference_aliases.add(reference)
    roster = set(parent.freeze.order[parent.freeze.natural])
    if not parent.objections.keys() <= plan.objections.keys() or any(
        not set(finding.sources) <= roster for finding in plan.objections.values()
    ):
        raise ValueError("Classify every exact supplied objection using only supplied Source identifiers.")
    if plan.disposition == "repair":
        _verify_design_change(slot, parent.design, plan)


def recover_stopped_plan(runner: SessionRunner, slot: FamilySlot, release: dict[str, Any]) -> bool:
    """Recognize a retained valid plan after a formerly strict historical-key check."""
    parent = _read_return(runner, slot, release)
    attempted = {row["job"] for row in runner.ledger.attempts(runner.family) if row["revision"] == runner.revision}
    if repair_authority.PLAN_JOB not in attempted:
        return False
    try:
        plan, _, _ = runner.committed_result("design", repair_authority.PLAN_JOB, "audit", RepairPlan)
        _verify_classification(slot, parent, plan)
    except (ValueError, OSError, KeyError):
        return False
    return bool(plan.objections.keys() - parent.objections.keys())


def _verify_plan(slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan) -> tuple[DesignOutput, set[str]]:
    if plan.disposition != "repair":
        raise RepairStopped(f"Independent repair planning returned {plan.disposition}: {plan.rationale}")
    if parent.previous_plan and (
        plan.progress == "none" and parent.previous_plan.progress == "none"
        or plan.tickets == parent.previous_plan.tickets and plan.revised_design == parent.previous_plan.revised_design
    ):
        raise RepairStopped("The same repair or two consecutive planning assessments showed no meaningful progress.")
    old = parent.design
    design = _verify_design_change(slot, old, plan)
    old_briefs = {brief.source_id: brief for brief in old.inventory}
    affected: set[str] = set()
    for brief in design.inventory:
        identity = brief.source_id
        if (
            identity in plan.tickets or brief != old_briefs[identity]
            or design.documentary_references != old.documentary_references
            or affected.intersection(brief.received)
        ):
            affected.add(identity)
    for left, right in zip(old.matched, design.matched, strict=True):
        if left.edit != right.edit and right.edit and right.edit.source_id not in affected:
            raise RepairStopped("A revised matched literal must regenerate its affected Source.")
    if not affected:
        raise RepairStopped("The repair proposes no change to any authored Source.")
    return design, affected


def _verify_design_change(slot: FamilySlot, old: DesignOutput, plan: RepairPlan) -> DesignOutput:
    design = plan.revised_design or old
    science.verify_design(slot, design)
    roster = {brief.source_id for brief in old.inventory}
    if (
        design.candidates != old.candidates or design.required != old.required
        or design.scaling_snapshots != old.scaling_snapshots
        or {brief.source_id for brief in design.inventory} != roster
        or not plan.tickets.keys() <= roster
        or any(_control_identity(left) != _control_identity(right)
               for left, right in zip(old.matched, design.matched, strict=True))
    ):
        raise ValueError("The proposed repair changes committed targets, roster or contrast structure.")
    hidden_literals = {
        condition.edit.after for condition in design.matched
        if condition.edit and condition.edit.after not in condition.edit.before
    }
    participant_texts = [brief.participant_brief for brief in design.inventory] + list(plan.tickets.values())
    if any(
        any(hidden.casefold() in text.casefold() for hidden in (*design.required, *hidden_literals))
        for text in participant_texts
    ):
        raise ValueError("A participant instruction exposes a condition identifier or alternate literal.")
    return design


def _control_identity(control: MatchedCondition) -> tuple[str, str | None, list[str] | None]:
    return control.kind, control.edit.source_id if control.edit else None, control.order


def mandatory_jobs(
    design: DesignOutput, affected: set[str], *, planning: bool = False, verification: bool = False,
    assume_whole_file: bool = False,
) -> set[str]:
    jobs = {f"author-{source_id}" for source_id in affected} | {"audit"}
    if planning:
        jobs.update({repair_authority.PLAN_JOB, "author-minimum"})
    if verification:
        jobs.add(repair_authority.VERIFY_JOB)
    for index in range(len(design.required)):
        jobs.update({f"realism-{index:03}", f"adjudicate-{index:03}"})
        for reader in ("a", "b"):
            prefix = f"reading-{index:03}-{reader}"
            jobs.add(f"{prefix}-full")
            if not assume_whole_file:
                jobs.update(f"{prefix}-part-{part:03}" for part in range(len(design.sections)))
    return jobs


def verify_revision(
    runner: SessionRunner, slot: FamilySlot, revision: Revision, bundles: dict[str, list[Source]],
) -> dict[str, Any]:
    if bundles == revision.parent.bundles and revision.design == revision.parent.design:
        raise RepairStopped("The regenerated family has identical Source bytes and design.")
    inputs = revision.parent.inputs(slot)
    inputs["paired_bundles"] = commissioning.json_text({
        "original": commissioning._read_json(inputs["paired_bundles"]),
        "revised": commissioning._read_json(_bundles(bundles)),
    })
    inputs["audit_rules"] = commissioning.json_text({
        "revised_design": revision.design.model_dump(mode="json"), "affected_sources": sorted(revision.affected),
    })
    result, receipt = runner.run("author", repair_authority.VERIFY_JOB, "audit", inputs, VERIFY_PROMPT, ScopeReview)
    if result.verdict != "preserved" or result.objections:
        raise RepairStopped("Independent scope review did not confirm preservation of the comparison: "
                            + result.model_dump_json())
    return receipt


def _bundles(bundles: dict[str, list[Source]]) -> str:
    return commissioning.json_text({
        condition: [source.model_dump(mode="json") for source in sources]
        for condition, sources in bundles.items()
    })
