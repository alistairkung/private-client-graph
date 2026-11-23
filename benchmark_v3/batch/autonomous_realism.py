"""Isolated documentary repair planning and revision lineage for milestone families."""

import re
from dataclasses import dataclass, replace
from typing import Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, author_context, author_delivery, authorisation, design_review, repair_authority, science
from benchmark_v3.batch.contracts import Adjudication, DesignOutput, MatchedCondition, RealismReview, SourceId
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
ADJUDICATION_RETURN = "Adjudication has unresolved scientific objections."
PLAN_REFERENCE_FAILURE = "Every additional classification must identify a retained earlier objection."
PARTICIPANT_LITERAL_FAILURE = "A participant instruction exposes a condition identifier or alternate literal."
CLASSIFICATION_LAYOUT = (
    " Classify the current audit_rules.objections using their exact keys. Discuss earlier documentary"
    " findings in the rationale, with revision numbers where needed."
)
LOCAL_ORIGIN = (
    " After a participant-scope return, derive each changed instruction from that participant's own acts and"
    " documented deliveries. Do not copy the reviewed case-wide file or a later Source into a brief under"
    " the name of a new worksheet. An honest working record may document what the participant actually checked"
    " and leave unverified fields open. Return infeasible if the commissioned mechanism requires unavailable"
    " participant knowledge."
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


class FutureReferenceOmission(Contract):
    source_id: SourceId
    later_source_id: SourceId
    reference: Text
    brief_sentence: Text
    ticket_sentence: Text


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
    prior_scope_return: dict[str, Any] | None = None
    earlier_scope_references: tuple[tuple[int, str], ...] = ()
    retained_literal_briefs: frozenset[SourceId] = frozenset()

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
    ticket_return = release.get("empty_ticket_return")
    note_recovery = retained_design_note(runner)
    omission = release.get("scope_ticket_omission")
    generated = release.get("generated_attachment_ticket")
    if generated is not None:
        prior = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
        actual, plan, receipt = generated_attachment_ticket(prior, slot, generated["source_id"])
        if actual != generated:
            raise packet.PacketIsolationError("The reviewed automatic ticket or its retained plan changed.")
        design, affected = _verify_plan(slot, replace(parent, previous_plan=None), plan, attested=True)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
        job = repair_authority.PLAN_JOB
    elif omission is not None:
        prior = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
        expected, plan, receipt = _reopen_scope_omission(prior, slot, omission)
        if expected != omission:
            raise packet.PacketIsolationError("The exact scoped ticket omission or its independent review changed.")
        design, affected = _verify_plan(slot, parent, plan, attested=True)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
        job = repair_authority.PLAN_JOB
    elif note_recovery is not None:
        actual, plan, receipt = recover_retained_design_note(runner, slot, parent, note_recovery["note_key"])
        if actual != note_recovery:
            raise packet.PacketIsolationError("A retained review note or un-authored design changed.")
        design, affected = _verify_plan(slot, parent, plan, attested=True)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
        job = repair_authority.PLAN_JOB
    elif ticket_return is None:
        plan, receipt, design, affected, job = _plan_from_objections(runner, slot, parent, release)
    else:
        plan, receipt, design, affected, job = _retained_plan_for_empty_ticket(runner, slot, parent, ticket_return)
    lineage = {
        "parent_revision": release["parent_revision"], "hypothesis_sha256": slot.hypothesis.hypothesis_sha256,
        "parent_design_sha256": authorisation.commitment(parent.design),
        "design_sha256": authorisation.commitment(design), "plan_sha256": authorisation.commitment(plan),
        "planner_receipt_sha256": receipt["receipt_sha256"],
        "original_source_commitments": parent.freeze.source_commitments,
        "original_review_receipts": parent.review_commitments, "affected_sources": sorted(affected),
    }
    if ticket_return is not None or release.get("pre_author_scope_return") is not None:
        lineage["rejected_author_context"] = ticket_return or release["pre_author_scope_return"]
    if note_recovery is not None:
        lineage["retained_plan_derivative"] = note_recovery
    if omission is not None:
        lineage["scoped_ticket_omission"] = omission
    if generated is not None:
        lineage["retired_automatic_ticket"] = generated
    if parent.prior_scope_return is not None:
        lineage["last_realism_revision"] = release["parent_revision"]
        lineage["parent_revision"] = parent.prior_scope_return["revision"]
        lineage["prior_scope_return_receipt_sha256"] = parent.prior_scope_return["receipt_sha256"]
        lineage["last_realism_source_commitments"] = parent.prior_scope_return["original_realism_source_commitments"]
    return Revision(parent, design, plan, affected, lineage, job), receipt


def retained_design_note(runner: SessionRunner) -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) ==
                 (runner.revision, "reconcile", repair_authority.RETAINED_DESIGN_NOTE)), None)


def recover_retained_design_note(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, note_key: str,
) -> tuple[dict[str, Any], RepairPlan, dict[str, Any]]:
    original_job = repair_authority.PLAN_JOB + repair_authority.FORMAT_RETRY
    original, receipt, _ = runner.committed_result("design", original_job, "audit", RepairPlan)
    plan = _separate_documentary_note(parent, original, note_key)
    _verify_classification(slot, parent, plan, attested=True)
    assert plan.revised_design is not None
    return {
        "receipt_sha256": receipt["receipt_sha256"], "original_job": original_job, "note_key": note_key,
        "retained_note": original.tickets[note_key], "original_plan_sha256": authorisation.commitment(original),
        "retained_design_sha256": authorisation.commitment(plan.revised_design),
        "derivative_sha256": authorisation.commitment(plan),
    }, plan, receipt


def _separate_documentary_note(parent: ReturnedFile, original: RepairPlan, note_key: str) -> RepairPlan:
    retained = parent.previous_plan.revised_design if parent.previous_plan is not None else None
    roster = {brief.source_id for brief in parent.design.inventory}
    if (original.disposition != "repair" or original.revised_design is not None or retained is None
            or "retain that revised design" not in original.rationale.casefold()
            or "follow-up is a review action, not a new source" not in original.rationale.casefold()
            or not note_key.endswith("_followup") or note_key in roster or note_key not in original.tickets
            or note_key.removesuffix("_followup") not in roster & original.tickets.keys()
            or not original.tickets.keys() - {note_key} <= roster):
        raise ValueError("A review note may only be separated from an explicit, unchanged prior design.")
    return original.model_copy(update={"revised_design": retained,
                                       "tickets": {key: text for key, text in original.tickets.items() if key != note_key}})



def _plan_from_objections(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, release: dict[str, Any],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
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
            **({"prior_scope_return": parent.prior_scope_return} if parent.prior_scope_return is not None else {}),
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
    return _select_plan(runner, slot, parent, inputs, release)

def _select_plan(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, inputs: dict[str, str], release: dict[str, Any],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
    attested = runner.ledger.requires_delivery_attestation

    def propose(job: str, prompt: str, packet_inputs: dict[str, str]) -> tuple[RepairPlan, dict[str, Any]]:
        result, receipt = runner.run(
            "design", job, "audit", packet_inputs,
            prompt + (" " + author_delivery.DESIGN_INSTRUCTION if attested else ""), RepairPlan,
            validate=lambda plan: _verify_classification(slot, parent, plan, attested=attested),
            allow_format_retry=job != repair_authority.EXACT_PLAN_JOB,
        )
        artifacts.write_json(runner.directory / f"{job}.json", result.model_dump(mode="json"))
        return result, receipt

    resumed = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                    if row["revision"] == runner.revision and row["kind"] == "reconcile"
                    and row["name"] == repair_authority.CAPACITY_SUCCESSOR), None)
    if resumed is not None:
        if not runner.ledger.pooled_revision(runner.manifest.batch_id, runner.family, runner.revision):
            raise ValueError("A capacity successor requires the active pooled release.")
        prior, prior_receipt, _ = runner.committed_result("design", repair_authority.PLAN_JOB, "audit", RepairPlan)
        if prior.disposition != "infeasible" or prior_receipt["receipt_sha256"] != resumed["prior_receipt_sha256"]:
            raise ValueError("Capacity re-review must bind the exact previously declined plan.")
        rules = commissioning._read_json(inputs["audit_rules"])
        rules["superseded_capacity_return"] = prior.model_dump(mode="json")
        rules["capacity"]["family_sessions_before_planning"] = resumed["available_sessions"]
        job = repair_authority.BUDGET_PLAN_JOB
        plan, receipt = propose(job, PLAN_PROMPT + " Reassess feasibility under the recorded new shared capacity. "
                                "Independently confirm the documentary repair or retain the scientific return.",
                                inputs | {"audit_rules": commissioning.json_text(rules)})
        design, affected = _verify_plan(slot, parent, plan, attested=attested)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
        _record_plan_selection(runner, job, receipt)
        return plan, receipt, design, affected, job
    prompt = PLAN_PROMPT
    if parent.prior_scope_return is not None:
        prompt += (" The exact scoped return is the immediate documentary draft. Address the new scope objections "
                   "and preserve all unaffected records. Retain prior documentary objections for context and arrange "
                   "fresh independent realism on the revised full conditions.")
    if exact := repair_authority.recorded_classification_retry(runner):
        expected, previous_inputs = classification_retry_details(runner)
        if exact != expected or inputs != previous_inputs:
            raise packet.PacketIsolationError("A fresh classification must preserve both retained repair packets.")
        job = repair_authority.EXACT_PLAN_JOB
        runner.ledger.require_capacity(runner.family, runner.revision, {
            job, "author-minimum", *mandatory_jobs(parent.design, set(), verification=True, assume_whole_file=True),
        })
        plan, receipt = propose(job, prompt + (
            " Copy the current keys from audit_rules.objections into your objections map exactly. "
            "Discuss earlier findings in the rationale with revision numbers. Keep their documentary "
            "substance in the plan, and use the objections map for the current keys only."
        ), inputs)
        design, affected = _verify_plan(slot, parent, plan, attested=attested)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
        _record_plan_selection(runner, job, receipt)
        return plan, receipt, design, affected, job
    if attested:
        if _include_plan_instruction(runner, CLASSIFICATION_LAYOUT):
            prompt += CLASSIFICATION_LAYOUT
        if _pre_author_returns(release) and _include_plan_instruction(runner, LOCAL_ORIGIN):
            prompt += LOCAL_ORIGIN
    plan, receipt = propose(repair_authority.PLAN_JOB, prompt, inputs)
    design, affected = _verify_plan(slot, parent, plan, attested=attested)
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
    design, affected = _verify_plan(slot, parent, plan, attested=attested)
    runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
    _record_plan_selection(runner, budget_job, receipt)
    return plan, receipt, design, affected, budget_job


def _include_plan_instruction(runner: SessionRunner, instruction: str) -> bool:
    attempt = next((row for row in runner.ledger.attempts(runner.family)
                    if row["revision"] == runner.revision and row["job"] == repair_authority.PLAN_JOB), None)
    return attempt is None or instruction in commissioning._read_json(attempt["request"])["prompt"]


def _record_plan_selection(runner: SessionRunner, job: str, receipt: dict[str, Any]) -> None:
    runner.ledger.event(runner.manifest.batch_id, runner.family, runner.revision, "repair_plan_selection",
                        "chosen", "design", "design", {"job": job, "receipt_sha256": receipt["receipt_sha256"]})


def classification_retry_details(runner: SessionRunner) -> tuple[dict[str, Any], dict[str, str]]:
    rejected = {row["name"]: row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                if row["revision"] == runner.revision and row["kind"] == "rejected_output"}
    receipts = {}
    prior_inputs: dict[str, str] | None = None
    for job in (repair_authority.PLAN_JOB, repair_authority.PLAN_JOB + repair_authority.FORMAT_RETRY):
        _, receipt, request = runner.committed_packet("design", job, "audit")
        expected = {"receipt_sha256": receipt["receipt_sha256"], "reason": PLAN_REFERENCE_FAILURE}
        inputs = request["inputs"]
        if rejected.get(job) != expected or (prior_inputs is not None and prior_inputs != inputs):
            raise ValueError("A fresh classification requires two exact historical-reference failures on the same input.")
        receipts[job] = receipt["receipt_sha256"]
        prior_inputs = inputs
    assert prior_inputs is not None
    return {
        "manifest_sha256": authorisation.commitment(runner.manifest), "receipts": receipts,
        "inputs_sha256": commissioning.digest(commissioning.json_text(prior_inputs).encode()),
    }, prior_inputs


def _read_return(runner: SessionRunner, slot: FamilySlot, release: dict[str, Any]) -> ReturnedFile:
    revision = release["parent_revision"]
    ledger, batch, family = runner.ledger, runner.manifest.batch_id, runner.family
    authored_return = bool(release.get("scope_return_receipt_sha256"))
    preauthor_returns = _pre_author_returns(release)
    empty_ticket = bool(release.get("empty_ticket_return"))
    if (revision != runner.revision - 1 - int(authored_return or empty_ticket) - len(preauthor_returns)
            or (empty_ticket and (authored_return or preauthor_returns))
            or ((authored_return or preauthor_returns or empty_ticket)
                and not ledger.pooled_revision(batch, family, runner.revision))):
        raise ValueError("A repair must bind each of its verified intervening scope returns.")
    previous = SessionRunner(ledger, runner.manifest, family, revision, runner.directory.parent / str(revision), runner.owner)
    history = ledger.events(batch, family)
    events = [row for row in history if row["revision"] == revision]
    disposition = next((row for row in events if row["kind"] == "disposition" and row["name"] == "realism"), None)
    adjudication = release.get("adjudication_return")
    if (release["manifest_sha256"] != authorisation.commitment(runner.manifest)
            or (adjudication is None and (
                disposition is None or release["disposition_sequence"] != disposition["sequence"]
            ))):
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
    if adjudication is not None:
        if objections or disposition is not None or adjudication != document_adjudication_return(previous):
            raise ValueError("The documentary repair must bind passing realism and the exact uncommitted adjudication.")
        first_condition = science.condition_ids(slot)[0]
        _, _, request = previous.committed_result("adjudicate", "adjudicate-000", "adjudication", Adjudication)
        read_sources = TypeAdapter(list[Source]).validate_json(request["inputs"]["sources"])
        if read_sources != supplied[first_condition]:
            raise ValueError("The adjudication did not receive the reviewed documentary file.")
        objections = {f"adjudication:{index}": reason
                      for index, reason in enumerate(adjudication["objections"], 1)}
    elif disposition is None or reviews != commissioning._read_json(disposition["details"]["evidence"]) or not objections:
        raise ValueError("The realism responses differ from the returned disposition.")
    natural = supplied[science.condition_ids(slot)[0]]
    authored = next(row for row in events if row["kind"] == "transition" and row["name"] == "author")
    reviewed_design = authored["details"]["inputs"].get("design_review_derivative")
    if reviewed_design is not None:
        design = design_review.verified_authoring_design(previous, design, reviewed_design)
    bundles, freeze = science.freeze_bundles(slot, design, natural)
    expected = commissioning.digest(commissioning.json_text(
        [source.model_dump(mode="json") for source in natural],
    ).encode())
    if supplied != bundles or authored["details"]["outputs"]["natural"] != expected:
        raise ValueError("The reviewed Sources differ from the immutable authored inventory.")
    prior = None
    previous_release = release_event(previous)
    if previous_release is not None:
        prior = _committed_prior_plan(previous, slot, previous_release, history)
    earlier = [
        {"revision": row["revision"], "reviews": commissioning._read_json(row["details"]["evidence"])}
        for row in history if row["revision"] < revision and row["kind"] == "disposition" and row["name"] == "realism"
    ]
    scope_references = _earlier_pre_author_references(runner, history, revision, slot=slot)
    result = ReturnedFile(design, bundles, freeze, objections, reviews, receipts, prior, earlier,
                          earlier_scope_references=scope_references,
                          retained_literal_briefs=_retained_literal_briefs(previous, design, natural, events))
    if authored_return:
        result = _scope_repair_parent(runner, slot, result, release["scope_return_receipt_sha256"],
                                      rejected_revision=revision + 1)
    for expected_revision, expected_return in enumerate(preauthor_returns, runner.revision - len(preauthor_returns)):
        skipped = replace(runner, revision=expected_revision, directory=runner.directory.with_name(str(expected_revision)))
        record, rejected = pre_author_scope_return(skipped, slot=slot)
        if record != expected_return:
            raise ValueError("The rejected un-authored scope proposal changed after review.")
        scope_objections = {f"pre-author:{index}": issue for index, issue in enumerate(record["objections"], 1)}
        if expected_revision == runner.revision - 1:
            result = replace(result, objections=result.objections | scope_objections, previous_plan=rejected)
        else:
            references = tuple((expected_revision, key) for key in scope_objections)
            result = replace(result, earlier_scope_references=(*result.earlier_scope_references, *references))
    return result


def _retained_literal_briefs(
    runner: SessionRunner, design: DesignOutput, natural: list[Source], events: list[dict[str, Any]],
) -> frozenset[SourceId]:
    """Prove a counterpart's ordinary use of an unchanged term independently of the matched edit."""
    alternate = _hidden_literals(design)
    if not alternate or not runner.ledger.requires_delivery_attestation:
        return frozenset()
    edited = {control.edit.source_id for control in design.matched if control.edit is not None}
    completed = {row["name"] for row in events if row["kind"] == "session" and row["details"]["status"] == "completed"}
    selected = {row["name"]: row["details"]["selected_job"] for row in events if row["kind"] == "output_selection"}
    sources = {source.id: source for source in natural}
    approved = set()
    for brief in design.inventory:
        identity = brief.source_id
        ordinary = {word for word in alternate if word.casefold() in brief.participant_brief.casefold()}
        job = f"author-{identity}"
        chosen = selected.get(job, job)
        if not ordinary or identity in edited or chosen not in completed:
            continue
        document, _, request = runner.committed_result("author", job, "author", author_delivery.AttestedSource)
        local = commissioning._read_json(request["inputs"]["author_brief"])
        if (local["brief"] != brief.participant_brief or local["participant"] != brief.author
                or local["date"] != brief.created_on.isoformat()
                or (document.title, document.text) != (sources[identity].title, sources[identity].text)
                or any(word.casefold() not in document.text.casefold() for word in ordinary)):
            continue
        author_delivery.require_prompt(chosen, request["prompt"])
        author_delivery.require_projection(runner, job, request["inputs"])
        approved.add(identity)
    return frozenset(approved)


def _committed_prior_plan(
    previous: SessionRunner, slot: FamilySlot, release: dict[str, Any], history: list[dict[str, Any]],
) -> RepairPlan:
    note = retained_design_note(previous)
    if note is not None:
        parent = _read_return(previous, slot, release)
        actual, plan, _ = recover_retained_design_note(previous, slot, parent, note["note_key"])
        if actual != note:
            raise ValueError("The prior review-note derivative differs from its retained evidence.")
        return plan
    omission = release.get("scope_ticket_omission")
    if omission is not None:
        older = replace(previous, revision=previous.revision - 1, directory=previous.directory.with_name(str(previous.revision - 1)))
        actual, plan, _ = _reopen_scope_omission(older, slot, omission)
        if actual != omission:
            raise ValueError("The prior scoped ticket omission differs from its retained evidence.")
        return plan
    generated = release.get("generated_attachment_ticket")
    if generated is not None:
        older = replace(previous, revision=previous.revision - 1, directory=previous.directory.with_name(str(previous.revision - 1)))
        actual, plan, _ = generated_attachment_ticket(older, slot, generated["source_id"])
        if actual != generated:
            raise ValueError("The prior automatic ticket recovery differs from its retained evidence.")
        return plan
    revision = previous.revision - int("empty_ticket_return" in release)
    planner = replace(previous, revision=revision, directory=previous.directory.with_name(str(revision)))
    selection = next((row["details"] for row in history if row["revision"] == revision
                      and row["kind"] == "repair_plan_selection"), None)
    job = selection["job"] if selection else repair_authority.PLAN_JOB
    stored = artifacts.read_contract(planner.directory / f"{job}.json", RepairPlan)
    committed, receipt, _ = planner.committed_result("design", job, "audit", RepairPlan)
    if stored != committed or selection and receipt["receipt_sha256"] != selection["receipt_sha256"]:
        raise ValueError("The prior repair plan differs from its charged original.")
    return stored


def _pre_author_returns(release: dict[str, Any]) -> list[dict[str, Any]]:
    records = list(release.get("prior_pre_author_scope_returns", []))
    if "pre_author_scope_return" in release:
        records.append(release["pre_author_scope_return"])
    return records


def pre_author_scope_return(runner: SessionRunner, *, slot: FamilySlot | None = None) -> tuple[dict[str, Any], RepairPlan]:
    batch, family = runner.manifest.batch_id, runner.family
    parent = release_event(runner)
    if (not runner.ledger.requires_delivery_attestation or parent is None or len(_pre_author_returns(parent)) > 2
            or parent["parent_revision"] != runner.revision - 1 - len(_pre_author_returns(parent))
            - int(bool(parent.get("scope_return_receipt_sha256")))
            or any(row["revision"] == runner.revision and row["stage"] == "author"
                   and row["job"] not in {author_context.JOB, author_context.JOB + repair_authority.FORMAT_RETRY}
                   for row in runner.ledger.attempts(family))):
        raise ValueError("A new preauthor plan requires a bounded independently returned repair before any author dispatch.")
    note = retained_design_note(runner)
    if note is not None:
        if slot is None:
            raise ValueError("A retained review-note plan requires the exact approved workload.")
        actual, plan, planner = recover_retained_design_note(runner, slot, _read_return(runner, slot, parent), note["note_key"])
        if actual != note:
            raise ValueError("The independently rejected scope must bind the exact retained plan derivative.")
        chosen = note
    else:
        chosen = next(row["details"] for row in runner.ledger.events(batch, family)
                      if row["revision"] == runner.revision and row["kind"] == "repair_plan_selection")
        plan, planner, _ = runner.committed_result("design", chosen["job"], "audit", RepairPlan)
    review, receipt, _ = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    if review.verdict != "return" or not review.objections or planner["receipt_sha256"] != chosen["receipt_sha256"]:
        raise ValueError("A new preauthor plan must bind the exact independently rejected documentary proposal.")
    return {
        "revision": runner.revision, "planner_receipt_sha256": planner["receipt_sha256"],
        "scope_receipt_sha256": receipt["receipt_sha256"], "objections": review.objections,
        "review": review.model_dump(mode="json"),
    }, plan


def _earlier_pre_author_references(
    runner: SessionRunner, history: list[dict[str, Any]], parent_revision: int, *, slot: FamilySlot | None = None,
) -> tuple[tuple[int, str], ...]:
    exact: list[tuple[int, str]] = []
    for row in history:
        if row["revision"] > parent_revision or row["kind"] != "transition" or row["name"] != repair_authority.REVISION:
            continue
        retained = row["details"].get("pre_author_scope_return")
        if retained is None:
            continue
        revision = row["revision"] - 1
        former = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
        proof, _ = pre_author_scope_return(former, slot=slot)
        if retained != proof:
            raise ValueError("The historical preauthor objection differs from its immutable receipts.")
        exact.extend((revision, f"pre-author:{index}")
                     for index in range(1, len(proof["objections"]) + 1))
    return tuple(exact)


def remove_separate_reply_ticket(
    runner: SessionRunner, slot: FamilySlot, source_id: str,
) -> tuple[dict[str, Any], RepairPlan, dict[str, Any]]:
    record, prior = pre_author_scope_return(runner, slot=slot)
    review, receipt, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    proposed = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"][source_id]
    ticket = prior.tickets[source_id]
    if (len(review.objections) != 1 or not review.objections[0].startswith(f"{source_id}: Remove the instruction to produce a separate ")
            or proposed["revision_ticket"] != ticket):
        raise ValueError("The exact independent scope return must identify one unsupported separate reply.")
    sentences = re.findall(r"(?<= )In a separate reply,[^.]+\. ", ticket)
    if len(sentences) != 1 or ticket.count(sentences[0]) != 1:
        raise ValueError("A separately requested reply must occupy one exact uniquely identifiable sentence.")
    removed, = sentences
    revised = ticket.replace(removed, "", 1)
    plan = prior.model_copy(update={"tickets": prior.tickets | {source_id: revised}, "progress": "improved"})
    return {
        "source_id": source_id, "scope_receipt_sha256": receipt["receipt_sha256"], "reviewed_pre_author_return": record,
        "prior_plan_sha256": authorisation.commitment(prior), "removed_sentence": removed,
        "derivative_sha256": authorisation.commitment(plan),
    }, plan, receipt


def _reopen_scope_omission(
    runner: SessionRunner, slot: FamilySlot, record: dict[str, Any],
) -> tuple[dict[str, Any], RepairPlan, dict[str, Any]]:
    if "future_reference" in record:
        return remove_future_reference(runner, slot, FutureReferenceOmission.model_validate(record["future_reference"]))
    return remove_separate_reply_ticket(runner, slot, record["source_id"])


def remove_future_reference(
    runner: SessionRunner, slot: FamilySlot, omission: FutureReferenceOmission,
) -> tuple[dict[str, Any], RepairPlan, dict[str, Any]]:
    retained, prior = pre_author_scope_return(runner, slot=slot)
    review, receipt, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    inventory = {brief.source_id: brief for brief in design.inventory}
    local = inventory[omission.source_id]
    future = inventory[omission.later_source_id]
    ticket = prior.tickets[local.source_id]
    projected = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"][local.source_id]
    objection = review.objections[0] if len(review.objections) == 1 else ""
    if (
        prior.revised_design != design or local.created_on >= future.created_on or future.source_id in local.received
        or projected != author_delivery.projection(design, prior.tickets)[local.source_id]
        or receipt["receipt_sha256"] != retained["scope_receipt_sha256"]
        or not re.match(rf"^{re.escape(local.source_id)}\s*[:—-]\s*Remove\b", objection)
        or omission.reference.casefold() not in objection.casefold()
        or not set(omission.reference.casefold().split()) <= set(re.findall(r"\w+", future.participant_brief.casefold()))
    ):
        raise ValueError("The retained scope return must identify one exact unavailable later document.")
    revised_brief = _omit_unavailable_reference(local.participant_brief, omission.brief_sentence, omission.reference)
    revised_ticket = _omit_unavailable_reference(ticket, omission.ticket_sentence, omission.reference)
    if "further act" in omission.ticket_sentence and "Require no further acceptance or act." not in revised_brief:
        raise ValueError("The remaining participant brief must retain its no-further-act condition.")
    updated = design.model_copy(update={"inventory": [
        brief.model_copy(update={"participant_brief": revised_brief}) if brief == local else brief
        for brief in design.inventory
    ]})
    plan = prior.model_copy(update={
        "revised_design": updated, "tickets": prior.tickets | {local.source_id: revised_ticket}, "progress": "improved",
    })
    return {
        "future_reference": omission.model_dump(mode="json"), "receipt_sha256": receipt["receipt_sha256"],
        "planner_receipt_sha256": retained["planner_receipt_sha256"], "original_plan_sha256": authorisation.commitment(prior),
        "derivative_sha256": authorisation.commitment(plan),
    }, plan, receipt


def _omit_unavailable_reference(value: str, sentence: str, reference: str) -> str:
    text = " " + sentence
    if (not re.fullmatch(rf"Do not refer to (?:a|the) {re.escape(reference)}(?: in this instrument"
                         r"(?: or make issuance, receipt or a further act a condition)?)?\.", sentence)
            or not value.endswith(text) or value.count(text) != 1):
        raise ValueError("Omit only one exact trailing instruction about the unavailable document.")
    return value.removesuffix(text)


def generated_attachment_ticket(
    runner: SessionRunner, slot: FamilySlot, source_id: str,
) -> tuple[dict[str, Any], RepairPlan, dict[str, Any]]:
    record, plan = pre_author_scope_return(runner, slot=slot)
    review, receipt, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    prior = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"][source_id]
    if (source_id in plan.tickets or len(review.objections) != 1 or not review.objections[0].startswith(source_id + ":")
            or repair_authority.LEGACY_REVISED_ATTACHMENTS not in review.objections[0]
            or prior.get("revision_ticket") != repair_authority.LEGACY_REVISED_ATTACHMENTS or not prior["received_ids"]):
        raise ValueError("The independently returned instruction must be one automatic attachment ticket.")
    return {"source_id": source_id, "prior_scope": record, "plan_sha256": authorisation.commitment(plan)}, plan, receipt


def empty_attachment_ticket_return(runner: SessionRunner, source_id: str) -> dict[str, Any]:
    """Authenticate a pre-author return of the factory's boilerplate attachment wording."""
    if not runner.ledger.requires_delivery_attestation or any(
        row["revision"] == runner.revision and row["stage"] == "author"
        and row["job"] not in {author_context.JOB, author_context.JOB + repair_authority.FORMAT_RETRY}
        for row in runner.ledger.attempts(runner.family)
    ):
        raise ValueError("The boilerplate correction must precede all affected author turns.")
    review, receipt, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    projected = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"][source_id]
    if (review.verdict != "return" or len(review.objections) != 1
            or not review.objections[0].startswith(source_id)
            or "received correspondence" not in review.objections[0]
            or projected["received_ids"] != []
            or projected.get("revision_ticket") != "Write this record using its revised instructions and received correspondence."):
        raise ValueError("The retained scope return is not the exact empty-attachment ticket case.")
    return {"source_id": source_id, "review_receipt_sha256": receipt["receipt_sha256"]}


def _retained_plan_for_empty_ticket(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, return_details: dict[str, Any],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
    previous = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    if empty_attachment_ticket_return(previous, return_details["source_id"]) != return_details:
        raise ValueError("The pre-author ticket return failed its commitment.")
    choice = next(row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                  if row["revision"] == previous.revision and row["kind"] == "repair_plan_selection")
    job = choice["job"]
    plan, receipt, _ = previous.committed_result("design", job, "audit", RepairPlan)
    if receipt["receipt_sha256"] != choice["receipt_sha256"] or return_details["source_id"] in plan.tickets:
        raise ValueError("The selected plan must be unchanged and the returned ticket machine-generated.")
    design, affected = _verify_plan(slot, parent, plan, attested=True)
    if design != artifacts.read_contract(previous.directory / "design.json", DesignOutput):
        raise ValueError("The retained un-authored revision has a different design.")
    return plan, receipt, design, affected, job


def document_adjudication_return(runner: SessionRunner) -> dict[str, Any]:
    if not runner.ledger.requires_delivery_attestation:
        raise ValueError("Documentary adjudication repair requires the attested isolation release.")
    if any((runner.directory / "family").glob(f"{runner.family}[0-9][0-9][0-9].json")):
        raise ValueError("A documentary return cannot supersede an already locked provisional key.")
    review, receipt, _ = runner.committed_result("adjudicate", "adjudicate-000", "adjudication", Adjudication)
    if not review.unresolved:
        raise ValueError("No independently recorded adjudication objection supports documentary repair.")
    return {"receipt_sha256": receipt["receipt_sha256"], "objections": review.unresolved}


def _scope_repair_parent(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, expected_receipt: str, *, rejected_revision: int,
) -> ReturnedFile:
    rejected = replace(runner, revision=rejected_revision, directory=runner.directory.with_name(str(rejected_revision)))
    finding, receipt, request = rejected.committed_result("author", repair_authority.VERIFY_JOB, "audit", ScopeReview)
    if receipt["receipt_sha256"] != expected_receipt or not finding.objections:
        raise ValueError("Scope repair requires the exact independent material scope return.")
    files = commissioning._read_json(request["inputs"]["paired_bundles"])
    if files["original"] != commissioning._read_json(_bundles(parent.bundles)):
        raise ValueError("The rejected scope comparison names different parent Sources.")
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    rejected_design = artifacts.read_contract(rejected.directory / "design.json", DesignOutput)
    if rules["revised_design"] != rejected_design.model_dump(mode="json"):
        raise ValueError("The rejected scope comparison has a different revised design.")
    rejected_natural = TypeAdapter(list[Source]).validate_python(files["revised"][parent.freeze.natural])
    bundles, freeze = science.freeze_bundles(slot, rejected_design, rejected_natural)
    if files["revised"] != commissioning._read_json(_bundles(bundles)):
        raise ValueError("The rejected scope comparison failed source and matched replay.")
    scope_record = {"revision": rejected_revision, "receipt_sha256": expected_receipt,
                    "original_realism_source_commitments": parent.freeze.source_commitments,
                    "original_realism_review_receipts": parent.review_commitments,
                    "original_realism_sources": files["original"],
                    "independent_finding": finding.model_dump(mode="json")}
    earlier = [*parent.earlier_objections, {"revision": rejected_revision - 1, "reviews": parent.reviews}]
    return replace(parent, design=rejected_design, bundles=bundles, freeze=freeze, retained_literal_briefs=frozenset(),
                   objections={f"scope:{index}": issue for index, issue in enumerate(finding.objections, start=1)},
                   earlier_objections=earlier, prior_scope_return=scope_record)


def _verify_classification(
    slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan, *, attested: bool = False,
) -> None:
    historical_sources = {
        (row["revision"], f"{condition}:{index}"): set(review["source_findings"])
        for row in parent.earlier_objections
        for condition, review in row["reviews"].items()
        if review["verdict"] != "pass" or review["objections"]
        for index in range(1, len(review["objections"] or [review["summary"]]) + 1)
    }
    earlier = historical_sources.keys() | set(parent.earlier_scope_references)
    roster = set(parent.freeze.order[parent.freeze.natural])
    reference_aliases: dict[tuple[int, str], str] = {}
    for key in plan.objections.keys() - parent.objections.keys():
        match = re.fullmatch(r"(?:earlier[_ -]|historical:)?revision[_ -]?([1-9][0-9]*):(.+)", key)
        if match is not None:
            candidates = {(int(match[1]), match[2])} & earlier
        elif parent.prior_scope_return is not None and key.startswith(("original:", "realism:")):
            original_realism = parent.prior_scope_return["revision"] - 1
            candidates = {(original_realism, key.split(":", 1)[1])} & earlier
        elif key.startswith("prior_repair:"):
            candidates = {reference for reference in parent.earlier_scope_references if reference[1] == key.split(":", 1)[1]}
        else:
            candidates = {reference for reference in earlier if reference[1] == key.removeprefix("earlier:")}
        if len(candidates) != 1:
            raise ValueError(PLAN_REFERENCE_FAILURE)
        reference, = candidates
        classification = plan.objections[key]
        if not set(classification.sources) <= roster | historical_sources.get(reference, set()):
            raise ValueError("A historical classification must use the referenced or current Source inventory.")
        previous_key = reference_aliases.setdefault(reference, key)
        previous = plan.objections[previous_key]
        if (classification.cause, set(classification.sources)) != (previous.cause, set(previous.sources)):
            raise ValueError("Repeated classifications of a retained objection must agree on cause and Sources.")
    if not parent.objections.keys() <= plan.objections.keys() or any(
        not set(plan.objections[key].sources) <= roster for key in parent.objections.keys() & plan.objections.keys()
    ):
        raise ValueError("Classify every exact supplied objection using only supplied Source identifiers.")
    if plan.disposition == "repair":
        design = _verify_design_change(slot, parent, plan)
        if attested:
            author_delivery.projection(design, plan.tickets)


def recover_stopped_plan(runner: SessionRunner, slot: FamilySlot, release: dict[str, Any]) -> bool:
    """Recognize a retained valid plan after a formerly strict historical-key check."""
    parent = _read_return(runner, slot, release)
    attempted = {row["job"] for row in runner.ledger.attempts(runner.family) if row["revision"] == runner.revision}
    if repair_authority.PLAN_JOB not in attempted:
        return False
    try:
        plan, receipt, _ = runner.committed_result("design", repair_authority.PLAN_JOB, "audit", RepairPlan)
        _verify_classification(slot, parent, plan, attested=runner.ledger.requires_delivery_attestation)
    except (ValueError, OSError, KeyError):
        return False
    if parent.retained_literal_briefs and any(
        row["revision"] == runner.revision and row["kind"] == "rejected_output"
        and row["name"] == repair_authority.PLAN_JOB
        and row["details"] == {"reason": PARTICIPANT_LITERAL_FAILURE, "receipt_sha256": receipt["receipt_sha256"]}
        for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
    ):
        try:
            _verify_plan(slot, parent, plan, attested=True)
        except ValueError:
            return False
        return True
    return bool(plan.objections.keys() - parent.objections.keys())


def _verify_plan(
    slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan, *, attested: bool = False,
) -> tuple[DesignOutput, set[str]]:
    if plan.disposition != "repair":
        raise RepairStopped(f"Independent repair planning returned {plan.disposition}: {plan.rationale}")
    if parent.previous_plan and (
        plan.progress == "none" and parent.previous_plan.progress == "none"
        or plan.tickets == parent.previous_plan.tickets and plan.revised_design == parent.previous_plan.revised_design
    ):
        raise RepairStopped("The same repair or two consecutive planning assessments showed no meaningful progress.")
    old = parent.design
    design = _verify_design_change(slot, parent, plan)
    old_briefs = {brief.source_id: brief for brief in old.inventory}
    affected: set[str] = set()
    if attested:
        earlier, revised = author_delivery.projection(old, {}), author_delivery.projection(design, {})
        affected.update(identity for identity in revised if earlier[identity] != revised[identity])
    for brief in design.inventory:
        identity = brief.source_id
        if (
            identity in plan.tickets or brief != old_briefs[identity] or affected.intersection(brief.received)
        ):
            affected.add(identity)
    for left, right in zip(old.matched, design.matched, strict=True):
        if left.edit != right.edit and right.edit and right.edit.source_id not in affected:
            raise RepairStopped("A revised matched literal must regenerate its affected Source.")
    if not affected:
        raise RepairStopped("The repair proposes no change to any authored Source.")
    return design, affected


def _verify_design_change(slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan) -> DesignOutput:
    old = parent.design
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
    if _exposes_hidden_text(design, plan, parent.retained_literal_briefs):
        raise ValueError(PARTICIPANT_LITERAL_FAILURE)
    return design


def _hidden_literals(design: DesignOutput) -> set[str]:
    return {condition.edit.after for condition in design.matched
            if condition.edit and condition.edit.after not in condition.edit.before}


def _exposes_hidden_text(
    design: DesignOutput, plan: RepairPlan, retained_literal_briefs: frozenset[SourceId],
) -> bool:
    affected = set(plan.tickets)
    alternate = _hidden_literals(design)
    for ticket in plan.tickets.values():
        if any(hidden.casefold() in ticket.casefold() for hidden in (*design.required, *alternate)):
            return True
    for brief in design.inventory:
        subject = brief.participant_brief.casefold()
        if affected.intersection(brief.received):
            affected.add(brief.source_id)
        retained = (plan.revised_design is None and brief.source_id in retained_literal_briefs
                    and brief.source_id not in affected)
        if any(identifier.casefold() in subject for identifier in design.required) or (
            not retained and any(literal.casefold() in subject for literal in alternate)
        ):
            return True
    return False


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
    def verify_layout(result: ScopeReview) -> None:
        if result.verdict == "preserved" and result.objections:
            raise ValueError("Preserved scope requires resolved objections in the disposition.")

    result, receipt = runner.run(
        "author", repair_authority.VERIFY_JOB, "audit", inputs, VERIFY_PROMPT, ScopeReview,
        validate=verify_layout if runner.ledger.requires_delivery_attestation else None,
    )
    if result.verdict != "preserved" or result.objections:
        raise RepairStopped(scope_failure(result))
    return receipt


def scope_failure(result: ScopeReview) -> str:
    return "Independent scope review did not confirm preservation of the comparison: " + result.model_dump_json()


def _bundles(bundles: dict[str, list[Source]]) -> str:
    return commissioning.json_text({
        condition: [source.model_dump(mode="json") for source in sources]
        for condition, sources in bundles.items()
    })
