"""Plan a bounded brief correction before any document is authored."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

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
