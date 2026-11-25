"""Isolated documentary repair planning and revision lineage for milestone families."""

import re
from dataclasses import dataclass, replace
from typing import Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, audit_boundary, author_context, author_delivery, author_repair, authorisation, clean_redesign, delivery_particulars, design_review, recipient_edit, repair_authority, science, ticket_authority
from benchmark_v3.batch.contracts import Adjudication, AuthorBrief, DesignOutput, MatchedCondition, MilestoneAudit, RealismReview, SourceId
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
PLAN_SCOPE_FAILURE = "The proposed repair changes committed targets, roster or contrast structure."
INTAKE_ATTACHMENT_FAILURE = "The repair cites additional intake records without their authenticated participant attachments."
LINEAGE_REOPEN_FAILURE = "The original realism inputs and receipts failed their commitments."
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


class LocalRepairPlan(Contract):
    disposition: Literal["repair", "infeasible", "scope_change"]
    objections: dict[Text, Objection]
    revised_records: dict[SourceId, AuthorBrief]
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
    incoming_particulars: delivery_particulars.IncomingParticulars | None = None
    exact_recipient_edit: recipient_edit.ExactRecipientEdit | None = None
    prior_owned_source: Source | None = None
    owned_records: dict[SourceId, Source] | None = None
    audit_repair_sources: frozenset[SourceId] = frozenset()

    def expected_local_source(self) -> Source | None:
        if self.exact_recipient_edit is None:
            return None
        if self.prior_owned_source is None:
            raise ValueError("The exact recipient edit requires its authenticated earlier Source.")
        return self.exact_recipient_edit.revise_source(self.prior_owned_source)

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

    def participant_tickets(self) -> dict[SourceId, str]:
        if (expected := self.parent.expected_local_source()) is not None:
            return {expected.id: (
                "Use the exact local retained record supplied below as the revised copy of your own inventory. "
                "Copy its title and text exactly. Your own earlier transmissions and the status of this retained "
                "record are unchanged.\nTitle: " + expected.title + "\n\n" + expected.text
            )}
        particulars = self.parent.incoming_particulars
        if particulars is None:
            return self.plan.tickets
        source_id = particulars.source_id
        basis = self.plan.tickets.get(source_id)
        ticket = particulars.local_ticket()
        tickets = self.plan.tickets | {source_id: f"{basis}\n\n{ticket}" if basis else ticket}
        for identity, record in (self.parent.owned_records or {}).items():
            direction = (
                "Use your own exact previous retained record below when preserving its original wording and annotation."
                if identity == source_id else
                "Copy your own original title and complete text exactly. Attest only the separately supplied transmissions."
            )
            tickets[identity] = f"{tickets.get(identity, '')}\n\n{direction}\nTitle: {record.title}\n\n{record.text}"
        return tickets


def release_event(runner: SessionRunner) -> dict[str, Any] | None:
    return next((
        row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if row["revision"] == runner.revision and row["kind"] == "transition"
        and row["name"] == repair_authority.REVISION
    ), None)


def retained_draft_tickets(runner: SessionRunner, revision: Revision, tickets: dict[SourceId, str]) -> dict[SourceId, str]:
    """Give a participant their own verified draft for a strictly local documentary edit."""
    parent = revision.parent
    if (not runner.ledger.requires_workload_merits or not runner.ledger.requires_delivery_attestation
            or revision.design.matched or parent.audit_repair_sources or parent.owned_records is not None
            or parent.prior_scope_return is not None or parent.incoming_particulars is not None
            or parent.exact_recipient_edit is not None):
        return tickets
    path = runner.directory / "own-draft-author-lineage.json"
    attempts = runner.ledger.attempts(runner.family)
    if not path.exists() and any(row["revision"] == runner.revision and row["job"] == author_context.JOB for row in attempts):
        return tickets
    index = revision.lineage["parent_revision"]
    old = {brief.source_id: brief for brief in parent.design.inventory}
    drafts = {source.id: source for source in parent.bundles[parent.freeze.natural]}
    local = {identity for item in revision.plan.objections.values() if item.cause == "documentary" for identity in item.sources}
    other = {identity for item in revision.plan.objections.values() if item.cause != "documentary" for identity in item.sources}
    augmented = dict(tickets)
    commitments = {}
    for brief in revision.design.inventory:
        identity = brief.source_id
        previous = old[identity]
        if (identity not in tickets or identity not in local or identity in other
                or revision.affected.intersection(previous.received)
                or previous.model_dump(exclude={"participant_brief"}) != brief.model_dump(exclude={"participant_brief"})):
            continue
        job = f"author-{identity}"
        authored = max((row["revision"] for row in attempts if row["job"] == job and row["revision"] <= index), default=0)
        if authored == 0:
            continue
        origin = replace(runner, revision=authored, directory=runner.directory.with_name(str(authored)))
        document, receipt, request = origin.committed_result("author", job, "author", author_delivery.AttestedSource)
        source = drafts[identity]
        owned = commissioning._read_json(request["inputs"]["author_brief"])
        if ((owned["participant"], owned["date"]) != (brief.author, brief.created_on.isoformat())
                or (document.title, document.text) != (source.title, source.text)):
            raise packet.PacketIsolationError("The local draft differs from the participant's own retained author receipt.")
        author_delivery.require_projection(origin, job, request["inputs"])
        author_delivery.verify_attestation(document, request["inputs"]["author_brief"])
        commitments[identity] = receipt["receipt_sha256"]
        augmented[identity] += ("\n\nBelow is your own earlier draft of this record. Preserve the existing document and its known "
            "facts outside the specific repair. Use only your approved earlier attachments and own knowledge. "
            "Retain the original record type, purpose and issue date.\nTitle: " + source.title + "\n\n" + source.text)
    if commitments or path.exists():
        artifacts.write_json(path, {"parent_revision": index, "author_receipts": commitments})
    return augmented


def unavailable_ticket_literals(revision: Revision, projected: dict[str, Any]) -> dict[SourceId, list[str]]:
    """Check new instructions against the participant brief and already selected earlier records."""
    parent = revision.parent
    prior = {brief.source_id: brief for brief in parent.design.inventory}
    documents = {document.id: document for document in parent.bundles[parent.freeze.natural]}
    unsupported = {}
    for row in revision.design.inventory:
        identity = row.source_id
        ticket = revision.plan.tickets.get(identity)
        if not ticket:
            continue
        earlier = prior[identity]
        approved = {anchor for anchor in row.received if anchor in earlier.received} if earlier.author == row.author else set()
        evidence = [projected[identity]["author_brief"], row.created_on.strftime("%B")]
        evidence.extend(f"{documents[anchor].title}\n{documents[anchor].text}" for anchor in sorted(approved))
        if missing := ticket_authority.unsupported_literals(revision.design, ticket, "\n".join(evidence)):
            unsupported[identity] = missing
    return unsupported


def plan_revision(
    runner: SessionRunner, slot: FamilySlot, release: dict[str, Any],
) -> tuple[Revision, dict[str, Any]]:
    try:
        parent = _read_return(runner, slot, release)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        raise packet.PacketIsolationError(LINEAGE_REOPEN_FAILURE) from error
    ticket_return = release.get("empty_ticket_return")
    sender_return = release.get("audit_sender_return")
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
    elif sender_return is not None:
        plan, receipt, design, affected, job = _retained_audit_sender_plan(runner, slot, parent, sender_return)
        runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
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
    if parent.incoming_particulars is not None:
        lineage["incoming_particulars"] = release["incoming_particulars"]
    if parent.owned_records is not None:
        lineage["owned_source_revisions"] = release["owned_source_revisions"]
    if parent.audit_repair_sources:
        lineage["documentary_audit_return"] = release["documentary_audit_return"]
    if sender_return is not None:
        lineage["audit_sender_return"] = sender_return
    if release.get("natural_provenance_restoration"):
        lineage["natural_provenance_restoration"] = True
    if release.get("verified_recipient_scope_restoration"):
        lineage["verified_recipient_scope_restoration"] = True
    if parent.exact_recipient_edit is not None:
        lineage["exact_recipient_edit"] = release["exact_recipient_edit"]
        if "exact_omission_assessment" in release:
            lineage["exact_omission_assessment"] = release["exact_omission_assessment"]
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
            **({"keep_documentary_limits": True} if release.get("keep_documentary_limits") else {}),
            **({"exact_recipient_edit": release["exact_recipient_edit"]} if parent.exact_recipient_edit is not None else {}),
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
    if repair_authority.recorded_local_retry(runner) is not None:
        return _select_local_plan(runner, slot, parent, inputs)

    def propose(job: str, prompt: str, packet_inputs: dict[str, str]) -> tuple[RepairPlan, dict[str, Any]]:
        def validate(plan: RepairPlan) -> None:
            _verify_classification(slot, parent, plan, attested=attested)
            _verify_intake_basis(runner, parent, plan)

        result, receipt = runner.run(
            "design", job, "audit", packet_inputs,
            prompt + (" " + author_delivery.DESIGN_INSTRUCTION if attested else ""), RepairPlan,
            validate=validate,
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
    if parent.audit_repair_sources:
        prompt += (" The scope is a new documentary revision after an independent audit return. Only change the "
                   "participant briefs or add repair tickets for these exact originating Sources: "
                   + commissioning.json_text(sorted(parent.audit_repair_sources))
                   + ". Review whether the existing trust identity or operative fact can ordinarily be made explicit "
                     "in the record body without changing who knew it or its business purpose. Do not rely on titles "
                     "as proof members, withdraw an authentic evidence route, or change the graph or a frozen artifact. "
                     "Fresh realism, both blind lanes, adjudication and controls are required. Return infeasible if necessary.")
    if parent.prior_scope_return is not None:
        prompt += (" The exact scoped return is the immediate documentary draft. Address the new scope objections "
                   "and preserve all unaffected records. Retain prior documentary objections for context and arrange "
                   "fresh independent realism on the revised full conditions.")
    if parent.incoming_particulars is not None:
        prompt += (f" The original authorised direct-transmission particulars for {parent.incoming_particulars.source_id}"
                   " will be appended in full, in attachment order, after your local instructions. Do not embed"
                   " lists of delivery facts, quote the review, or single out a relationship proof. Preserve the exact"
                   " set of incoming attachments and every one of their original sending acts and Sources.")
    if parent.owned_records is not None:
        prompt += (" The following affected participants will receive their own exact earlier authored record only: "
                   + commissioning.json_text(sorted(parent.owned_records))
                   + ". Issue a separate safe repair ticket for each. The inventory-note author will use that record's "
                     "original wording and the verified current receipt details. For other participants, retain the exact "
                     "prior issued record while verifying the original sending act. Do not expose those records to other authors.")
    if release.get("keep_documentary_limits"):
        prompt += (
            " Separate actual defects in the retained documents from substantive questions the historical"
            " file properly leaves open. Do not invent replies, valuation workings, missing mandates,"
            " attachments or later acts. Prefer deleting unsupported summary detail to making up a crosswalk."
            " Repair ambiguous terminology using only documented local facts. Treat any suggested future"
            " enquiry as practitioner follow-up, not as an author instruction to supply new evidence."
        )
    if parent.exact_recipient_edit is not None:
        if parent.exact_recipient_edit.brief_omission is None:
            prompt += (
                " Independently assess the exact correction to one entry in the same recipient's authenticated"
                " earlier record. The verified counterpart is retained from the authored revision."
                " Classify every objection. Return a single ticket for the recipient and no revised design, or"
                " return infeasible if the exact edit would lose evidence, invent a fact or alter scientific scope."
            )
        else:
            prompt += (
                " Independently assess the exact locally owned edit. Classify every current objection. If feasible,"
                " return only a ticket for that recipient and no revised design. The validated derivative removes the"
                " conflicting original brief instruction and implements the exact record changes. Return infeasible if"
                " anything beyond these edits is materially necessary. Preserve all existing verified evidence and limits."
            )
    if release.get("exact_omission_assessment"):
        prompt += (
            " Classify the retained pre-author objections, including whether the omitted tally was required for"
            " the recipient's ordinary task. The exact two edits are within this release's allowed scope."
            " Independently reject a loss of necessary evidence, a change to the scientific question or an"
            " unsupported possession claim. The record is a new authoring revision of the same inventory."
        )
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
        intake = _intake_attachments(parent)
        if runner.ledger.requires_workload_merits and intake:
            instruction = (" Add these exact earlier records to their recipient's received slice, preserving already "
                           "authorised attachments and chronological order: " + commissioning.json_text(intake)
                           + ". Do not substitute a case-wide reconstructed intake list in the brief or ticket. "
                           "Ask the recipient to account for the locally available received records and preserve their "
                           "own exact original note and annotation. If the authorised receipt path cannot be shown, return infeasible.")
            if _include_plan_instruction(runner, instruction):
                prompt += instruction
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


def local_retry_details(runner: SessionRunner) -> tuple[dict[str, Any], dict[str, str]]:
    rejected = {row["name"]: row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                if row["revision"] == runner.revision and row["kind"] == "rejected_output"}
    failures = {}
    inputs: dict[str, str] | None = None
    for job in (repair_authority.PLAN_JOB, repair_authority.PLAN_JOB + repair_authority.FORMAT_RETRY):
        _, receipt, request = runner.committed_packet("design", job, "audit")
        rejection = rejected.get(job)
        if (rejection is None or rejection.get("receipt_sha256") != receipt["receipt_sha256"]
                or (inputs is not None and inputs != request["inputs"])):
            raise ValueError("A local replan requires both exact rejected outputs on the same inputs.")
        failures[job] = rejection
        inputs = request["inputs"]
    if not any(rejection["reason"] == PLAN_SCOPE_FAILURE for rejection in failures.values()):
        raise ValueError("A local replan requires a demonstrated whole-design contract failure.")
    assert inputs is not None
    return {"prior_rejections": failures, "manifest_sha256": authorisation.commitment(runner.manifest),
            "inputs_sha256": commissioning.digest(commissioning.json_text(inputs).encode())}, inputs


def _select_local_plan(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, inputs: dict[str, str],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
    details, original_inputs = local_retry_details(runner)
    if details != repair_authority.recorded_local_retry(runner) or original_inputs != inputs:
        raise packet.PacketIsolationError("The local replan must preserve the two original review packets.")
    job = repair_authority.LOCAL_PLAN_JOB
    def validate(local: LocalRepairPlan) -> None:
        plan = _local_derivative(parent, local)
        _verify_classification(slot, parent, plan, attested=True)
        _verify_intake_basis(runner, parent, plan)

    result, receipt = runner.run("design", job, "audit", inputs, PLAN_PROMPT + (
        " Use exact current objection keys. Return revised_records as a map of changed author records only, keyed "
        "by their exact Source IDs. Ticket only Sources identified by the returning reviewers. Preserve the author, issue date, "
        "overall design, targets and contrast. Use the earliest contemporaneous local basis for each change. "
        "Keep observations and follow-up enquiries in rationale, outside participant instructions. If a repair needs "
        "changes outside these local records and their dependency closure, return infeasible or scope_change."
    ) + " " + author_delivery.DESIGN_INSTRUCTION, LocalRepairPlan,
        validate=validate,
        allow_format_retry=False)
    plan = _local_derivative(parent, result)
    design, affected = _verify_plan(slot, parent, plan, attested=True)
    runner.ledger.require_capacity(runner.family, runner.revision, mandatory_jobs(design, affected, verification=True))
    artifacts.write_json(runner.directory / f"{job}.json", plan.model_dump(mode="json"))
    _record_plan_selection(runner, job, receipt)
    return plan, receipt, design, affected, job


def _local_derivative(parent: ReturnedFile, local: LocalRepairPlan) -> RepairPlan:
    original = parent.design
    records = {row.source_id: row for row in original.inventory}
    named = {source for objection in local.objections.values() for source in objection.sources}
    permitted = {source for review in parent.reviews.values() for source in review["repair_tickets"]}
    permitted.update(source for source in records if any(
        re.search(rf"(?<!\w){re.escape(source)}(?!\w)", objection, re.IGNORECASE)
        for objection in parent.objections.values()
    ))
    if not (local.revised_records.keys() | local.tickets.keys()) <= records.keys() & permitted & named:
        raise ValueError("A local repair must target Sources named by the returning reviewer and the classification.")
    for identity, current in local.revised_records.items():
        prior = records[identity]
        if (current.source_id, current.author, current.created_on) != (identity, prior.author, prior.created_on):
            raise ValueError("A local repair must preserve the affected Source's identity, author and date.")
    revised = original.model_copy(update={"inventory": [local.revised_records.get(row.source_id, row)
                                                         for row in original.inventory]})
    return RepairPlan(**local.model_dump(exclude={"revised_records"}), revised_design=revised)


def _intake_attachments(parent: ReturnedFile) -> dict[SourceId, list[SourceId]]:
    """Read an independent review's explicit list of missing arrivals to a named recipient."""
    if parent.prior_scope_return is None:
        return {}
    documents = {row.source_id: row for row in parent.design.inventory}
    requirements: dict[SourceId, list[SourceId]] = {}
    for objection in parent.prior_scope_return["independent_finding"]["objections"]:
        matched = re.search(r"\bRevised (\w+) lists only\b.*?\badditional arrivals to ([^:]+): ([^.]+)\.", objection)
        if matched is None:
            continue
        target, recipient, names = matched.groups()
        if target not in documents or author_delivery._participant(documents[target].author).split()[0] != recipient:
            continue
        ids = [source for source in documents if re.search(rf"(?<!\w){re.escape(source)}(?!\w)", names)]
        if ids:
            requirements[target] = ids
    return requirements


def _intake_gaps(parent: ReturnedFile, design: DesignOutput) -> dict[SourceId, list[SourceId]]:
    received = {row.source_id: set(row.received) for row in design.inventory}
    return {target: missing for target, expected in _intake_attachments(parent).items()
            if (missing := sorted(set(expected) - received.get(target, set())))}


def _verify_intake_basis(runner: SessionRunner, parent: ReturnedFile, plan: RepairPlan) -> None:
    if (runner.ledger.requires_workload_merits and plan.disposition == "repair"
            and _intake_gaps(parent, plan.revised_design or parent.design)):
        raise ValueError(INTAKE_ATTACHMENT_FAILURE)


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
    authored_receipts = _authored_scope_receipts(release)
    preauthor_returns = _pre_author_returns(release)
    skipped_ticket = bool(release.get("empty_ticket_return") or release.get("audit_sender_return"))
    if (revision != runner.revision - 1 - len(authored_receipts) - int(skipped_ticket) - len(preauthor_returns)
            or (skipped_ticket and (authored_receipts or preauthor_returns))
            or (len(authored_receipts) > 1 and not release.get("natural_provenance_restoration"))
            or ((authored_receipts or preauthor_returns or skipped_ticket)
                and not ledger.historical_pooled_revision(batch, family, runner.revision))):
        raise ValueError("A repair must bind each of its verified intervening scope returns.")
    previous = SessionRunner(ledger, runner.manifest, family, revision, runner.directory.parent / str(revision), runner.owner)
    history = ledger.events(batch, family)
    events = [row for row in history if row["revision"] == revision]
    disposition = next((row for row in events if row["kind"] == "disposition" and row["name"] == "realism"), None)
    adjudication = release.get("adjudication_return")
    audit = release.get("documentary_audit_return")
    if (release["manifest_sha256"] != authorisation.commitment(runner.manifest)
            or (adjudication is None and audit is None and (
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
    elif audit is not None:
        if objections or disposition is not None or audit != document_audit_return(previous, set(audit["source_ids"])):
            raise ValueError("An audit repair must retain passing realism and the exact returned audit.")
        objections = {f"audit:{i}": reason for i, reason in enumerate(audit["objections"], 1)}
    elif disposition is None or reviews != commissioning._read_json(disposition["details"]["evidence"]) or not objections:
        raise ValueError("The realism responses differ from the returned disposition.")
    natural = supplied[science.condition_ids(slot)[0]]
    authored = next(row for row in events if row["kind"] == "transition" and row["name"] == "author")
    reviewed_design = authored["details"]["inputs"].get("design_review_derivative")
    if reviewed_design is not None:
        design = design_review.verified_authoring_design(previous, design, reviewed_design)
    bundles, freeze = science.freeze_bundles(slot, design, natural)
    if audit is not None and artifacts.read_contract(previous.directory / "family" / "freeze.json", BatchSourceFreeze) != freeze:
        raise ValueError("The passed documentary review differs from the audit's frozen Sources.")
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
                          audit_repair_sources=frozenset(audit["source_ids"]) if audit is not None else frozenset(),
                          retained_literal_briefs=_retained_literal_briefs(previous, design, natural, events))
    authored_returns, preauthor = _scope_returns_by_revision(history, authored_receipts, preauthor_returns)
    if not skipped_ticket and sorted((*authored_returns, *preauthor)) != list(range(revision + 1, runner.revision)):
        raise ValueError("Each intervening revision needs its own authenticated scope return.")
    if release.get("natural_provenance_restoration") and (len(authored_returns) != 2 or design.matched):
        raise ValueError("Provenance restoration requires one natural condition and two authenticated scope returns.")
    for rejected_revision in sorted((*authored_returns, *preauthor)):
        if rejected_revision in authored_returns:
            result = _scope_repair_parent(runner, slot, result, authored_returns[rejected_revision],
                                          rejected_revision=rejected_revision, original_revision=revision)
        else:
            result = _append_pre_author_return(runner, slot, result, rejected_revision, preauthor[rejected_revision])
    if details := release.get("incoming_particulars"):
        source_revision = details.get("reviewed_source_revision", runner.revision - 1)
        retained_natural = (not authored_returns and source_revision == revision and not design.matched
                            and ledger.historical_pooled_revision(batch, family, runner.revision))
        if not (retained_natural or (authored_returns and source_revision == max(authored_returns))):
            raise ValueError("Delivery particulars require the exact reviewed draft revision.")
        previous_draft = replace(runner, revision=source_revision,
                                 directory=runner.directory.with_name(str(source_revision)))
        if retained_natural:
            require_verified_incoming_basis(previous_draft, details["source_id"])
        particulars = delivery_particulars.reopen(previous_draft, details["source_id"])
        if authorisation.commitment(particulars) != details["record_sha256"]:
            raise ValueError("The participant's original delivery particulars changed.")
        result = replace(result, incoming_particulars=particulars)
    if owned := release.get("owned_source_revisions"):
        if result.incoming_particulars is None or not release.get("natural_provenance_restoration"):
            raise ValueError("Earlier participant records require an exact natural-file provenance restoration.")
        current = {row.source_id: row for row in result.design.inventory}
        retained = {}
        for identity, original_revision in owned.items():
            if not revision <= original_revision < max(authored_returns) or identity not in current:
                raise ValueError("An owned record must precede the exact returned repair and stay in its roster.")
            origin = replace(runner, revision=original_revision,
                             directory=runner.directory.with_name(str(original_revision)))
            document, _, request = origin.committed_result("author", f"author-{identity}", "author", author_delivery.AttestedSource)
            local = commissioning._read_json(request["inputs"]["author_brief"])
            if (local["participant"], local["date"]) != (current[identity].author, current[identity].created_on.isoformat()):
                raise ValueError("An earlier owned record must have the same author and issue date.")
            author_delivery.require_projection(origin, f"author-{identity}", request["inputs"])
            retained[identity] = Source(id=identity, title=document.title, text=document.text)
        result = replace(result, owned_records=retained)
    if edit := release.get("exact_recipient_edit"):
        exact = recipient_edit.ExactRecipientEdit.model_validate(edit)
        if "exact_omission_assessment" in release:
            if len(preauthor_returns) != 1:
                raise ValueError("An omission assessment must bind one exact pre-author scope return.")
            exact.require_exact_omission_objections(preauthor_returns[0]["objections"])
        if result.incoming_particulars is None or result.incoming_particulars.source_id != exact.source_id:
            raise ValueError("The exact edit must belong to the same independently verified receiving participant.")
        own, _, request = previous.committed_result("author", f"author-{exact.source_id}", "author", author_delivery.AttestedSource)
        source = next(item for item in natural if item.id == exact.source_id)
        if (own.title, own.text) != (source.title, source.text):
            raise ValueError("The exact edit must reopen the verified Source authored by the participant.")
        author_delivery.require_projection(previous, f"author-{exact.source_id}", request["inputs"])
        exact.revise_source(source)
        exact.revise_design(design)
        result = replace(result, exact_recipient_edit=exact, prior_owned_source=source)
    return result


def _scope_returns_by_revision(
    events: list[dict[str, Any]], authored_receipts: list[str], preauthor_returns: list[dict[str, Any]],
) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
    authored = {}
    for receipt in authored_receipts:
        revisions = [row["revision"] for row in events if row["kind"] == "session" and row["name"] in {
            repair_authority.VERIFY_JOB, repair_authority.VERIFY_JOB + repair_authority.FORMAT_RETRY,
        } and row["details"].get("receipt_sha256") == receipt]
        if len(revisions) != 1 or revisions[0] in authored:
            raise ValueError("Each authored scope return needs one unique charged receipt.")
        authored[revisions[0]] = receipt
    preauthor = {row["revision"]: row for row in preauthor_returns}
    if (list(authored) != sorted(authored) or len(preauthor) != len(preauthor_returns)
            or list(preauthor) != sorted(preauthor) or authored.keys() & preauthor.keys()):
        raise ValueError("Scope returns must retain their original distinct revisions.")
    return authored, preauthor


def _append_pre_author_return(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, revision: int, expected: dict[str, Any],
) -> ReturnedFile:
    skipped = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
    record, rejected = pre_author_scope_return(skipped, slot=slot)
    if record != expected:
        raise ValueError("The rejected un-authored scope proposal changed after review.")
    objections = {f"pre-author:{index}": issue for index, issue in enumerate(record["objections"], 1)}
    if revision == runner.revision - 1:
        return replace(parent, objections=parent.objections | objections, previous_plan=rejected)
    references = tuple((revision, key) for key in objections)
    return replace(parent, earlier_scope_references=(*parent.earlier_scope_references, *references))


def require_verified_incoming_basis(runner: SessionRunner, source_id: str) -> None:
    while True:
        release = release_event(runner) or {}
        review, _, _ = runner.committed_result("author", repair_authority.VERIFY_JOB, "audit", ScopeReview)
        details = release.get("incoming_particulars", {})
        if details.get("source_id") != source_id or review.verdict != "preserved" or review.objections:
            raise ValueError("Incoming particulars can carry only the recipient's independently verified natural-file facts.")
        if release.get("natural_provenance_restoration"):
            return
        earlier = details.get("reviewed_source_revision", 0)
        if not 0 < earlier < runner.revision:
            raise ValueError("Carried delivery particulars require an authentic earlier natural-file review.")
        runner = replace(runner, revision=earlier, directory=runner.directory.with_name(str(earlier)))


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
    if sender_return := release.get("audit_sender_return"):
        plan, _, _, _, _ = _retained_audit_sender_plan(previous, slot, _read_return(previous, slot, release), sender_return)
        return plan
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
    if job == repair_authority.LOCAL_PLAN_JOB:
        parent = _read_return(planner, slot, release)
        local, receipt, _ = planner.committed_result("design", job, "audit", LocalRepairPlan)
        committed = _local_derivative(parent, local)
    else:
        committed, receipt, _ = planner.committed_result("design", job, "audit", RepairPlan)
    if stored != committed or selection and receipt["receipt_sha256"] != selection["receipt_sha256"]:
        raise ValueError("The prior repair plan differs from its charged original.")
    return stored


def _pre_author_returns(release: dict[str, Any]) -> list[dict[str, Any]]:
    records = list(release.get("prior_pre_author_scope_returns", []))
    if "pre_author_scope_return" in release:
        records.append(release["pre_author_scope_return"])
    return records


def pre_author_progress(previous: list[dict[str, Any]], current: dict[str, Any], identities: set[SourceId]) -> bool:
    """Recognize a new exact scope objection after earlier objects cleared."""
    if not previous:
        return True
    if any(set(record["objections"]) == set(current["objections"]) for record in previous):
        return False
    if len(current["objections"]) < len(previous[-1]["objections"]):
        return True

    def leading_sources(record: dict[str, Any]) -> set[SourceId]:
        names = {objection.split(maxsplit=1)[0].rstrip(":") for objection in record["objections"] if objection.strip()}
        if names <= identities:
            return names
        if record.get("review_job") == clean_redesign.MERITS_JOB:
            citations = [set(re.findall(r"[\w-]+", objection)) & identities for objection in record["objections"]]
            if citations and all(citations):
                return set().union(*citations)
        return set()

    current_sources = leading_sources(current)
    previous_sources = [leading_sources(record) for record in previous]
    return bool(current_sources and all(previous_sources) and current_sources.isdisjoint(set().union(*previous_sources)))


def _authored_scope_receipts(release: dict[str, Any]) -> list[str]:
    receipts = list(release.get("earlier_authored_scope_receipts", []))
    if "scope_return_receipt_sha256" in release:
        receipts.append(release["scope_return_receipt_sha256"])
    return receipts


def _pre_author_review_jobs(runner: SessionRunner) -> set[str]:
    from benchmark_v3.batch import clean_redesign

    jobs = {author_context.JOB}
    if runner.ledger.requires_workload_merits:
        jobs.add(clean_redesign.MERITS_JOB)
    return {name for job in jobs for name in (job, job + repair_authority.FORMAT_RETRY)}


def pre_author_scope_return(runner: SessionRunner, *, slot: FamilySlot | None = None) -> tuple[dict[str, Any], RepairPlan]:
    batch, family = runner.manifest.batch_id, runner.family
    parent = release_event(runner)
    if (not runner.ledger.requires_delivery_attestation or parent is None
            or (not runner.ledger.requires_workload_merits and len(_pre_author_returns(parent)) > 2)
            or parent["parent_revision"] != runner.revision - 1 - len(_pre_author_returns(parent))
            - len(_authored_scope_receipts(parent))
            or any(row["revision"] == runner.revision and row["stage"] == "author"
                   and row["job"] not in _pre_author_review_jobs(runner)
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
        history = runner.ledger.events(batch, family)
        chosen = next(row["details"] for row in history
                      if row["revision"] == runner.revision and row["kind"] == "repair_plan_selection")
        if chosen["job"] == repair_authority.LOCAL_PLAN_JOB:
            if slot is None:
                raise ValueError("A local record plan requires the exact approved workload.")
            plan = _committed_prior_plan(runner, slot, parent, history)
            _, planner, _ = runner.committed_packet("design", chosen["job"], "audit")
        else:
            plan, planner, _ = runner.committed_result("design", chosen["job"], "audit", RepairPlan)
    review_job = author_context.JOB
    merits_job = clean_redesign.MERITS_JOB
    if runner.ledger.requires_workload_merits and any(
        row["revision"] == runner.revision and row["job"] == merits_job for row in runner.ledger.attempts(family)
    ):
        merits, receipt, request = runner.committed_result("author", merits_job, "audit", author_context.AuthorContextReview)
        if merits.verdict == "return":
            design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
            if (DesignOutput.model_validate_json(request["inputs"]["intended_intervention"]) != design
                    or merits.findings.keys() - {"_design"} != {row.source_id for row in design.inventory}):
                raise ValueError("The independent merits return differs from the exact held design.")
            review_job = merits_job
    review, receipt, request = runner.committed_result("author", review_job, "audit", author_context.AuthorContextReview)
    objections = review.objections
    intake: dict[SourceId, list[SourceId]] = {}
    unsupported: dict[SourceId, list[str]] = {}
    if (review.verdict == "accept" and not objections and runner.ledger.requires_workload_merits and slot is not None):
        original = _read_return(runner, slot, parent)
        design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
        if DesignOutput.model_validate_json(request["inputs"]["intended_intervention"]) != design:
            raise ValueError("The accepted scope review differs from the exact held design.")
        rules = commissioning._read_json(request["inputs"]["audit_rules"])
        if rules.get("ticket_basis_version") == 1:
            revised, affected = _verify_plan(slot, original, plan, attested=True)
            if revised != design:
                raise ValueError("A ticket-basis return must match the independently reviewed scoped design.")
            check = Revision(original, revised, plan, affected, {}, repair_authority.PLAN_JOB)
            unsupported = unavailable_ticket_literals(check, rules["participant_packets"])
            if unsupported != rules.get("unavailable_ticket_literals"):
                raise ValueError("The retained local ticket authority check changed.")
        if unsupported:
            objections = [f"{source}: Repair instructions add names or periods without a local documentary basis. "
                          f"Remove or authorise the exact facts about {', '.join(terms)}."
                          for source, terms in unsupported.items()]
        else:
            intake = _intake_gaps(original, design)
            objections = [f"{source}: {INTAKE_ATTACHMENT_FAILURE} Include the actual earlier correspondence for "
                          f"{', '.join(missing)} in the participant's received slice." for source, missing in intake.items()]
    if (not objections or (review.verdict != "return" and not intake and not unsupported)
            or planner["receipt_sha256"] != chosen["receipt_sha256"]):
        raise ValueError("A new preauthor plan must bind the exact independently rejected documentary proposal.")
    return {
        "revision": runner.revision, "planner_receipt_sha256": planner["receipt_sha256"],
        "scope_receipt_sha256": receipt["receipt_sha256"], "objections": objections,
        "review": review.model_dump(mode="json"),
        **({"review_job": review_job} if review_job == merits_job else {}),
        **({"mechanically_missing_intake_attachments": intake} if intake else {}),
        **({"mechanically_unsupported_ticket_literals": unsupported} if unsupported else {}),
    }, plan


def _earlier_pre_author_references(
    runner: SessionRunner, history: list[dict[str, Any]], parent_revision: int, *, slot: FamilySlot | None = None,
) -> tuple[tuple[int, str], ...]:
    exact: list[tuple[int, str]] = []
    verified: dict[int, dict[str, Any]] = {}
    for row in history:
        if row["revision"] > parent_revision or row["kind"] != "transition" or row["name"] != repair_authority.REVISION:
            continue
        for retained in _pre_author_returns(row["details"]):
            revision = retained["revision"]
            if not 0 < revision < row["revision"]:
                raise ValueError("A preauthor objection must reference an earlier revision.")
            if revision not in verified:
                former = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
                proof, _ = pre_author_scope_return(former, slot=slot)
                verified[revision] = proof
                exact.extend((revision, f"pre-author:{index}") for index in range(1, len(proof["objections"]) + 1))
            if retained != verified[revision]:
                raise ValueError("The historical preauthor objection differs from its immutable receipts.")
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
        and row["job"] not in _pre_author_review_jobs(runner)
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


def document_audit_sender_return(runner: SessionRunner, source_id: str) -> dict[str, Any]:
    release = release_event(runner)
    if (release is None or release["parent_revision"] != runner.revision - 1
            or source_id not in release.get("documentary_audit_return", {}).get("source_ids", [])
            or not runner.ledger.requires_delivery_attestation or (runner.directory / "family").exists()):
        raise ValueError("A retained sender retry requires an exact un-frozen audit documentary revision.")
    events = [row for row in runner.ledger.events(runner.manifest.batch_id, runner.family) if row["revision"] == runner.revision]
    failures = author_repair._missing_sender_receipts(runner, source_id, events)
    _, _, request = runner.committed_packet("author", f"author-{source_id}", "author")
    _, receipt, retry = runner.committed_packet("author", f"author-{source_id}-format-retry", "author")
    grants = commissioning._read_json(request["inputs"]["author_brief"])["outgoing_deliveries"]
    if request["inputs"] != retry["inputs"] or not grants or not request["inputs"].get("revision_ticket"):
        raise ValueError("A retained sender retry requires the same approved local ticket and existing transmissions.")
    return {"source_id": source_id, "failures": failures, "grants": grants, "receipt_sha256": receipt["receipt_sha256"]}


def _retained_audit_sender_plan(
    runner: SessionRunner, slot: FamilySlot, parent: ReturnedFile, details: dict[str, Any],
) -> tuple[RepairPlan, dict[str, Any], DesignOutput, set[str], str]:
    previous = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    identity = details["source_id"]
    if details != document_audit_sender_return(previous, identity):
        raise ValueError("The two independently omitted sender attestations changed.")
    history = runner.ledger.events(runner.manifest.batch_id, runner.family)
    choice = next(row["details"] for row in history if row["revision"] == previous.revision and row["kind"] == "repair_plan_selection")
    job = choice["job"]
    plan, receipt, _ = previous.committed_result("design", job, "audit", RepairPlan)
    design, affected = _verify_plan(slot, parent, plan, attested=True)
    _, _, request = previous.committed_packet("author", f"author-{identity}", "author")
    if (receipt["receipt_sha256"] != choice["receipt_sha256"] or plan.tickets.get(identity) != request["inputs"]["revision_ticket"]
            or design != artifacts.read_contract(previous.directory / "design.json", DesignOutput)):
        raise ValueError("The retained sender ticket differs from the accepted documentary plan.")
    declared = " and ".join(f"{grant['recipient']} on {grant['sent_on']}" for grant in details["grants"])
    clarification = (f" Record the original documented delivery to {declared} in the deliveries field. "
                     "This is an attestation of the original sending act. Do not make a new delivery.")
    revised = plan.model_copy(update={"tickets": plan.tickets | {identity: plan.tickets[identity] + clarification}})
    return revised, receipt, design, affected, job


def document_audit_return(runner: SessionRunner, source_ids: set[str]) -> dict[str, Any]:
    recheck = audit_boundary.release(runner) is not None
    job = audit_boundary.RECHECK if recheck else "audit"
    contract = audit_boundary.RecheckedAudit if recheck else MilestoneAudit
    review, receipt, _ = runner.committed_result("audit", job, "audit", contract)
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    if (review.verdict not in {"return", "repair"} or not review.objections or not source_ids
            or not source_ids <= {row.source_id for row in design.inventory}
            or any(not any(re.search(rf"(?<!\w){re.escape(source)}(?!\w)", reason) for reason in review.objections)
                   for source in source_ids)):
        raise ValueError("A documentary release requires named Sources in an independent audit return.")
    return {"job": job, "receipt_sha256": receipt["receipt_sha256"], "source_ids": sorted(source_ids),
            "objections": review.objections,
            "freeze_sha256": commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json"))}


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
    original_revision: int,
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
    earlier_scope = parent.prior_scope_return or {}
    scope_record = {"revision": rejected_revision, "receipt_sha256": expected_receipt,
                    "original_realism_source_commitments": earlier_scope.get("original_realism_source_commitments",
                                                                          parent.freeze.source_commitments),
                    "original_realism_review_receipts": parent.review_commitments,
                    "original_realism_sources": earlier_scope.get("original_realism_sources", files["original"]),
                    "independent_finding": finding.model_dump(mode="json")}
    if original_revision != rejected_revision - 1:
        scope_record["original_realism_revision"] = original_revision
    earlier_objections = parent.earlier_objections
    references = parent.earlier_scope_references
    if earlier_scope:
        earlier_finding = earlier_scope["independent_finding"]
        scope_record["earlier_authored_scope"] = earlier_finding
        authored_references = tuple((earlier_scope["revision"], f"scope:{index}")
                                    for index, _ in enumerate(earlier_finding["objections"], 1))
        references = (*references, *authored_references)
    else:
        earlier_objections = [*earlier_objections, {"revision": original_revision, "reviews": parent.reviews}]
    return replace(parent, design=rejected_design, bundles=bundles, freeze=freeze, retained_literal_briefs=frozenset(),
                   objections={f"scope:{index}": issue for index, issue in enumerate(finding.objections, start=1)},
                   earlier_objections=earlier_objections, earlier_scope_references=references, prior_scope_return=scope_record)


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
            original_realism = parent.prior_scope_return.get("original_realism_revision", parent.prior_scope_return["revision"] - 1)
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
    if parent.incoming_particulars is not None:
        parent.incoming_particulars.require_preserved_deliveries(old, design, affected)
    if parent.owned_records is not None and not parent.owned_records.keys() <= plan.tickets.keys():
        raise ValueError("Every independently designated owned Source needs its own localized repair ticket.")
    if parent.exact_recipient_edit is not None and affected != {parent.exact_recipient_edit.source_id}:
        raise ValueError("An exact recipient edit cannot alter another document or require a descendant repair.")
    return design, affected


def _verify_design_change(slot: FamilySlot, parent: ReturnedFile, plan: RepairPlan) -> DesignOutput:
    old = parent.design
    edit = parent.exact_recipient_edit
    if edit is not None:
        if plan.revised_design is not None or set(plan.tickets) != {edit.source_id}:
            raise ValueError("The exact recipient edit requires one participant ticket and the retained design.")
        design = edit.revise_design(old)
    else:
        design = plan.revised_design or old
    science.verify_design(slot, design)
    if parent.audit_repair_sources:
        if (not plan.tickets.keys() <= parent.audit_repair_sources or any(
            revised != original and (original.source_id not in parent.audit_repair_sources
                or revised.model_dump(exclude={"participant_brief"}) != original.model_dump(exclude={"participant_brief"}))
            for original, revised in zip(old.inventory, design.inventory, strict=True)
        ) or design.model_dump(exclude={"inventory"}) != old.model_dump(exclude={"inventory"})):
            raise ValueError("An audit-origin repair must preserve the documentary design outside its exact local briefs.")
    roster = {brief.source_id for brief in old.inventory}
    if (
        design.candidates != old.candidates or design.required != old.required
        or design.scaling_snapshots != old.scaling_snapshots
        or {brief.source_id for brief in design.inventory} != roster
        or not plan.tickets.keys() <= roster
        or any(_control_identity(left) != _control_identity(right)
               for left, right in zip(old.matched, design.matched, strict=True))
    ):
        raise ValueError(PLAN_SCOPE_FAILURE)
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
    rules: dict[str, Any] = {
        "revised_design": revision.design.model_dump(mode="json"), "affected_sources": sorted(revision.affected),
    }
    prompt = VERIFY_PROMPT
    if (revision.lineage.get("natural_provenance_restoration")
            or revision.lineage.get("verified_recipient_scope_restoration")):
        rules["retained_scope_return"] = revision.parent.prior_scope_return
        prompt += (
            " This commissioned design has one natural condition. The previous draft was returned and has no key."
            " Independently decide whether revised documentary evidence recovers facts already established by the"
            " authorised histories and deliveries. A corrected documentary premise may change what the rejected"
            " draft could prove. Reject any new event, altered research hypothesis, narrowed participant question,"
            " unjustified proof or hidden answer. Preserve the exact authorised cut-off, targets, controls and"
            " workload. There is no licence for a matched or fixed-evidence comparison. Require fresh realism,"
            " blind reconstruction and audit for the revised natural file."
        )
    inputs["audit_rules"] = commissioning.json_text(rules)
    if revision.lineage.get("exact_omission_assessment"):
        prompt += (
            " Review the omission of the aggregate and the local label correction as the two authorised edits."
            " Compare the preserved original with the independent authored revision. Check that no required"
            " intake fact, enclosure, evidence, possession, date, scope or scientific signal changed. A returned"
            " earlier version remains in custody. Give an independent verdict on materiality."
        )
    def verify_layout(result: ScopeReview) -> None:
        if result.verdict == "preserved" and result.objections:
            raise ValueError("Preserved scope requires resolved objections in the disposition.")

    result, receipt = runner.run(
        "author", repair_authority.VERIFY_JOB, "audit", inputs, prompt, ScopeReview,
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
