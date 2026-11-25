"""Bind a bounded pre-author large-design repair to independent review."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, author_context, authorisation, clean_redesign
from benchmark_v3.batch.contracts import AuthorBrief, DesignOutput
from benchmark_v3.research_contracts import Contract, Text

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner
    from benchmark_v3.batch.workflow import FamilyWorkflow

RELEASE = "clean-large-design-merits-repair"
JOB = "clean-design-merits-plan"


class MeritsRepairPlan(Contract):
    revised_records: dict[str, AuthorBrief]
    rationale: Text


def recorded(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if row["revision"] == runner.revision and row["kind"] == "transition"
                 and row["name"] == RELEASE), None)


def requires_review(runner: "SessionRunner") -> bool:
    if repair := recorded(runner):
        reopen(runner, repair)
        return True
    fresh = clean_redesign.recorded(runner)
    return runner.ledger.requires_workload_merits or (fresh is not None and fresh.audited_replacement is not None)


def returned(runner: "SessionRunner") -> tuple[DesignOutput, author_context.AuthorContextReview, str]:
    replacement = clean_redesign.recorded(runner)
    reviews = {clean_redesign.MERITS_JOB}
    if runner.ledger.requires_workload_merits:
        reviews.add(author_context.JOB)
    if (not runner.ledger.requires_workload_merits
            and (replacement is None or replacement.audited_replacement is None)) or any(
        attempt["revision"] == runner.revision and attempt["stage"] == "author"
        and attempt["job"].removesuffix("-format-retry") not in reviews
        for attempt in runner.ledger.attempts(runner.family)
    ):
        raise ValueError("A large merits repair requires one independently returned design with no participant dispatch.")
    review, receipt, request = runner.committed_result("author", clean_redesign.MERITS_JOB, "audit",
                                                      author_context.AuthorContextReview)
    permitted_labels = {"_design"}
    if runner.ledger.requires_workload_merits and review.verdict == "accept" and not review.objections:
        clean_redesign.require_merits(runner)
        review, receipt, request = runner.committed_result("author", author_context.JOB, "audit",
                                                          author_context.AuthorContextReview)
        permitted_labels = set()
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    if (review.verdict != "return" or not review.objections
            or DesignOutput.model_validate_json(request["inputs"]["intended_intervention"]) != design
            or review.findings.keys() - permitted_labels != {row.source_id for row in design.inventory}):
        raise ValueError("A merits repair requires the exact independently returned complete design.")
    return design, review, str(receipt["receipt_sha256"])


def reopen(runner: "SessionRunner", record: dict[str, Any]) -> tuple[DesignOutput, author_context.AuthorContextReview]:
    revision = runner.revision - 1
    previous = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
    design, review, receipt = returned(previous)
    if (record.get("parent_revision") != revision or record.get("review_sha256") != receipt
            or record.get("design_sha256") != authorisation.commitment(design)):
        raise ValueError("The retained merits return changed before the replacement plan.")
    return design, review


def apply(design: DesignOutput, plan: MeritsRepairPlan, permitted: set[str]) -> DesignOutput:
    original = {row.source_id: row for row in design.inventory}
    if not plan.revised_records or not plan.revised_records.keys() <= (permitted & original.keys()):
        raise ValueError("The merits repair must stay within the exact released Source scope.")
    for key, current in plan.revised_records.items():
        prior = original[key]
        if ((current.source_id, current.author, current.created_on) != (key, prior.author, prior.created_on)
                or current == prior):
            raise ValueError("A pre-author merits repair must preserve all record IDs, authors and dates.")
    return design.model_copy(update={"inventory": [plan.revised_records.get(row.source_id, row)
                                                   for row in design.inventory]})


def repair(workflow: "FamilyWorkflow", record: dict[str, Any]) -> DesignOutput:
    design, review = reopen(workflow.runner, record)
    permitted = set(record["source_ids"])

    def validate(plan: MeritsRepairPlan) -> None:
        workflow._verify_fresh_design(apply(design, plan, permitted))

    plan = workflow.job(JOB, "audit", {
        "intended_intervention": design.model_dump_json(),
        "audit_rules": commissioning.json_text({"review": review.model_dump(mode="json"),
                                                "released_source_ids": sorted(permitted)}),
    }, "Independently repair the exact scoped large-file design before any participant writes. Address every "
       "retained objection through the smallest documentary and custody revision. Keep all intended positive "
       "and unsupported claims, independent controls, dates, participant identities, authorised scope, record "
       "purposes, sections and scientific workload. Change only the necessary released participant briefs, "
       "documented possession or transmissions. Give each participant only their own facts or exact earlier "
       "records they actually receive. Make operative historic capacity and qualifying receipt visible in "
       "contemporaneous records. Do not add a retrospective explanation, unverified enclosure, different "
       "document version or hidden answer. Return an empty revision if a defensible bounded fix is impossible.",
       MeritsRepairPlan, validate=validate)
    revised = apply(design, plan, permitted)
    workflow.transition_inputs["large_merits_repair"] = artifacts.write_json(
        workflow.directory / "large-merits-repair.json", {
            "retained_review_sha256": record["review_sha256"],
            "design_sha256": authorisation.commitment(revised),
            "plan_sha256": authorisation.commitment(plan),
        },
    )
    return revised
