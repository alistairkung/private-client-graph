"""Plan a bounded brief correction before any document is authored."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, author_context, authorisation
from benchmark_v3.batch.contracts import DesignOutput
from benchmark_v3.research_contracts import Contract, Text

if TYPE_CHECKING:
    from benchmark_v3.batch.workflow import FamilyWorkflow
    from benchmark_v3.batch.sessions import SessionRunner

RELEASE = "author-context-repair"
JOB = "author-context-repair-plan"


class Plan(Contract):
    briefs: dict[str, Text]
    rationale: Text


def recorded(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if row["revision"] == runner.revision and row["kind"] == "transition"
                 and row["name"] == RELEASE), None)


def repair(work: "FamilyWorkflow", release: dict[str, Any]) -> DesignOutput:
    runner = work.runner
    prior = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    review, receipt, _ = prior.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    original = artifacts.read_contract(prior.directory / "design.json", DesignOutput)
    if (not runner.ledger.requires_author_context or review.verdict != "return" or not review.objections
            or receipt["receipt_sha256"] != release["receipt_sha256"]
            or authorisation.commitment(original) != release["original_design_sha256"]
            or any(row["revision"] == prior.revision and row["job"].startswith("author-")
                   and row["job"] not in {author_context.JOB, author_context.JOB + "-format-retry"}
                   for row in runner.ledger.attempts(runner.family))):
        raise ValueError("A brief repair requires an exact rejected scope receipt before any author turn.")
    plan = work.job(JOB, "audit", {"intended_intervention": original.model_dump_json(),
                                  "audit_rules": review.model_dump_json()},
                    "Repair only the participant-brief wording that caused this independent pre-author return. "
                    "Preserve every scientific objective, documentary function and delivery relationship. "
                    "Return a map from each affected Source ID to its complete revised brief, and explain why "
                    "the revision limits knowledge to the participant's own dated record. Return an empty map "
                    "if the repair needs a change outside the brief text.", Plan)
    expected = {row.source_id for row in original.inventory}
    if not plan.briefs or not plan.briefs.keys() <= expected:
        raise ValueError("The scope return needs a different scientific plan or valid author IDs.")
    revised = original.model_copy(update={"inventory": [
        row.model_copy(update={"participant_brief": plan.briefs[row.source_id]}) if row.source_id in plan.briefs else row
        for row in original.inventory
    ]})
    if revised == original:
        raise ValueError("The proposed author scope repair has no effect.")
    author_context.projection(revised, {})
    work.transition_inputs["author_scope_repair"] = artifacts.write_json(runner.directory / "author-context-lineage.json", {
        "prior_review_sha256": receipt["receipt_sha256"], "parent_design_sha256": authorisation.commitment(original),
        "design_sha256": authorisation.commitment(revised), "changes": sorted(plan.briefs),
    })
    return revised


RECHECK_UNUSED_DELIVERY = "author-context-unused-delivery-recheck"
SELECTED_DELIVERY_SCOPE = (
    " The outgoing delivery list is limited to transfers used as attachments by downstream author packets. "
    "Fictional transmissions recorded in the sender's own instructions and provenance can occur outside this selection. "
    "Do not require an attestation for an unused transmission. Require sender attestation for every actual author attachment."
)


def unused_delivery_return(runner: "SessionRunner", source_id: str) -> dict[str, Any]:
    if not runner.ledger.requires_delivery_attestation or any(
        row["stage"] == "author" and row["job"] not in {author_context.JOB, author_context.JOB + "-format-retry"}
        for row in runner.ledger.attempts(runner.family)
    ):
        raise ValueError("An unused-delivery recheck requires a wholly un-authored lineage.")
    review, receipt, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    original = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    packets = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"]
    if (review.verdict != "return" or len(review.objections) != 1 or not review.objections[0].startswith(source_id)
            or "outgoing delivery" not in review.objections[0].lower()
            or commissioning._read_json(packets[source_id]["author_brief"])["outgoing_deliveries"]
            or any(source_id in packet["received_ids"] for packet in packets.values())):
        raise ValueError("The returned Source must have no outgoing author attachment in the exact projection.")
    return {"source_id": source_id, "discussion_receipt_sha256": receipt["receipt_sha256"],
            "design_sha256": authorisation.commitment(original)}


def reopen_unused_delivery(runner: "SessionRunner") -> DesignOutput | None:
    event = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                  if row["revision"] == runner.revision and row["kind"] == "transition"
                  and row["name"] == RECHECK_UNUSED_DELIVERY), None)
    if event is None:
        return None
    previous = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    if unused_delivery_return(previous, event["source_id"]) != event:
        raise ValueError("The exact earlier scope return or original design has changed.")
    return artifacts.read_contract(previous.directory / "design.json", DesignOutput)
