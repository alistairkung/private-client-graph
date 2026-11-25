"""Independently investigate an executed control that contradicted its committed expectation."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, audit_boundary, authorisation, joint_control_plan, science
from benchmark_v3.batch.contracts import MaskAssignment, Reading
from benchmark_v3.replay_manifest import BatchSourceFreeze, source_commitments
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.source import Source
from private_client_graph.research.retained_inputs import value_digest

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner


JOB = "executed-control-dispute"
RELEASE = "executed-control-dispute-audit"
SCOPE_JOB = "executed-control-scope-confirmation"
SCOPE_RELEASE = "executed-control-scope-audit"
CLARIFY = "executed-control-dispute-clarification"
FAILURE = re.compile(r"Independent observation (mask-[0-9]+) failed a required control\.")
CLARIFIED_JOB = re.compile(r"mask-([0-9]+)-clarified(?:-format-retry|-exact-format|-after-pause)?")
INSTRUCTIONS = (
    "Independently investigate the retained disagreement between a masked reader and a precommitted control. "
    "Use the exact same evidence standard on each related view. Distinguish a participant's report or prospective action, "
    "a witnessed event and an established relationship where the documents make these different. Decide whether the original "
    "masked response defeats the proposed proof, or whether the question and output scope mixed reported relationships with "
    "those demonstrated by the supplied evidence. Confirm or reject the exact precommitted expectations; keep every genuine "
    "documentary or scientific objection. If the scope was ambiguous, give one neutral question for fresh matched observations "
    "of the complete proof and each proper deletion. Do not disclose a correct edge, the excluded Source, or the expected "
    "outcome. If rewording cannot address the actual discrepancy without weakening the evidence requirement, return the case."
)
SCOPE_PROMPT = (
    "Independently determine whether the exact proposed wording preserves the original question, evidence threshold, "
    "Source views and each precommitted expectation. It must distinguish established relationships from unconfirmed "
    "reports without hinting which relationship or fact is absent from a particular view. Review the prior auditor's "
    "account and objections. Report ordinary limits on what a masked view shows separately from objections to the "
    "scientific validity of this comparison. Accept only if all the exact positive and deletion expectations remain "
    "defensible under one consistent standard and the wording is non-leading. Confirm the exact proposed question's SHA-256."
)
SCOPE_SUFFIX = (
    " Distinguish statements in the records from events and relationships that the supplied evidence establishes. "
    "Use structured relationship candidates only for established relationships. Place claims whose necessary facts "
    "remain uncertain in open_questions, and explain what remains uncertain."
)


class DisputeReview(Contract):
    verdict: Literal["scope_clarification", "control_refuted", "unresolved"]
    reasoning: Text
    limitations: list[Text]
    objections: list[Text]
    clarified_question: Text | None


class DisputeRelease(Contract):
    observation_job: Text
    observation_sha256: Digest
    inputs_sha256: Digest
    audit_sha256: Digest


class Clarification(Contract):
    question: Text
    dispute_receipt_sha256: Digest
    audit_receipt_sha256: Digest
    observation_sha256: Digest
    view_sha256s: dict[int, Digest]


class ScopeRelease(Contract):
    dispute_receipt_sha256: Digest
    inputs_sha256: Digest


class ScopeReview(Contract):
    verdict: Literal["accept", "return"]
    question_sha256: Digest
    reasoning: Text
    objections: list[Text]
    limitations: list[Text]


@dataclass(frozen=True)
class Dispute:
    release: DisputeRelease
    inputs: dict[str, str]
    assignments: dict[int, MaskAssignment]


def recorded(runner: "SessionRunner") -> DisputeRelease | None:
    return next((DisputeRelease.model_validate(row["details"])
                 for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", RELEASE)), None)


def reopen(runner: "SessionRunner", job: str) -> Dispute:
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    gate, = [row["details"] for row in events if (row["revision"], row["kind"], row["name"])
             == (runner.revision, "transition", "audit")]
    audit, request = _confirmed_audit(runner)
    audit_sha = authorisation.commitment(audit)
    if audit_sha != gate["outputs"]["audit"]:
        raise ValueError("A control dispute must preserve the exact independently accepted audit commit.")
    root = runner.directory / "family"
    bundles = TypeAdapter(dict[str, list[Source]]).validate_json(request["inputs"]["paired_bundles"])
    freeze = artifacts.read_contract(root / "freeze.json", BatchSourceFreeze)
    if bundles.keys() != freeze.order.keys():
        raise ValueError("The reviewer inputs differ from the exact frozen conditions.")
    for condition, sources in bundles.items():
        local = TypeAdapter(list[Source]).validate_json(artifacts.read_bytes(root / "sources" / f"{condition}.json"))
        if (local != sources or [source.id for source in sources] != freeze.order[condition]
                or value_digest([source.model_dump(mode="json") for source in sources]) != freeze.sources_sha256[condition]
                or source_commitments(sources) != freeze.source_commitments[condition]):
            raise ValueError("The reviewer inputs differ from the exact frozen Sources.")
    index = int(job.removeprefix("mask-"))
    target = audit.masks[index]
    sources = science.mask_sources(target, bundles[target.condition])
    observed, receipt, packet = runner.committed_result("masks", job, "masked", Reading)
    if (TypeAdapter(list[Source]).validate_json(packet["inputs"]["sources"]) != sources
            or packet["inputs"]["neutral_brief"] != f"{request['inputs']['neutral_brief']}\n\nReviewer question: {target.question}"):
        raise ValueError("The contradictory observation used a different masked view or question.")
    edges = science.check_reading(observed, sources).keys()
    disagreement = (set(target.present) - edges) | (set(target.absent) & edges)
    if not disagreement:
        raise ValueError("A conforming observation cannot open an executed control dispute.")
    assignments = {i: mask for i, mask in enumerate(audit.masks)
                   if (mask.condition, mask.risk, mask.question) == (target.condition, target.risk, target.question)}
    positives = {edge for mask in assignments.values() for edge in mask.present}
    negatives = {edge for mask in assignments.values() for edge in mask.absent}
    if target.risk != "joint_proof" or not disagreement <= positives & negatives:
        raise ValueError("A scope clarification requires a precommitted joint-proof comparison.")
    roles = dict(request["inputs"])
    roles["audit_rules"] = commissioning.json_text({
        "original_control": target.model_dump(mode="json"),
        "executed_control_response": observed.model_dump(mode="json"),
        "exact_shared_question_views": {str(i): mask.model_dump(mode="json") for i, mask in assignments.items()},
    })
    release = DisputeRelease(observation_job=job, observation_sha256=receipt["receipt_sha256"],
                             audit_sha256=audit_sha, inputs_sha256=_inputs_sha(roles))
    return Dispute(release, roles, assignments)


def permits(runner: "SessionRunner", inputs: dict[str, str]) -> bool:
    release = recorded(runner)
    return release is not None and release.inputs_sha256 == _inputs_sha(inputs)


def scope_release(runner: "SessionRunner") -> ScopeRelease | None:
    return next((ScopeRelease.model_validate(row["details"])
                 for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", SCOPE_RELEASE)), None)


def scope_packet(runner: "SessionRunner") -> tuple[ScopeRelease, dict[str, str], str, Dispute]:
    release = recorded(runner)
    if release is None:
        raise ValueError("A clarification requires a prior exact executed-control audit release.")
    dispute = reopen(runner, release.observation_job)
    review, receipt, request = runner.committed_result("audit", JOB, "audit", DisputeReview)
    if (release != dispute.release or request["inputs"] != dispute.inputs or review.verdict != "scope_clarification"
            or not review.clarified_question):
        raise ValueError("The independent reviewer has not identified an ambiguous reading scope.")
    question = next(iter(dispute.assignments.values())).question + SCOPE_SUFFIX
    rules = commissioning._read_json(dispute.inputs["audit_rules"])
    inputs = dispute.inputs | {"audit_rules": commissioning.json_text(rules | {
        "prior_independent_assessment": review.model_dump(mode="json"),
        "proposed_exact_question": question,
        "proposed_question_sha256": commissioning.digest(question.encode()),
    })}
    return ScopeRelease(dispute_receipt_sha256=receipt["receipt_sha256"], inputs_sha256=_inputs_sha(inputs)), inputs, question, dispute


def permits_scope(runner: "SessionRunner", inputs: dict[str, str]) -> bool:
    release = scope_release(runner)
    return release is not None and release.inputs_sha256 == _inputs_sha(inputs)


def make_clarification(runner: "SessionRunner") -> tuple[Clarification, Dispute, dict[str, Any]]:
    expected, inputs, question, dispute = scope_packet(runner)
    review, receipt, request = runner.committed_result("audit", SCOPE_JOB, "audit", ScopeReview)
    if (scope_release(runner) != expected or request["inputs"] != inputs or review.verdict != "accept"
            or review.objections or review.question_sha256 != commissioning.digest(question.encode())):
        raise ValueError("A fresh independent reviewer must confirm the exact clarified question and all expected comparisons.")
    return Clarification(question=question, dispute_receipt_sha256=expected.dispute_receipt_sha256,
                         audit_receipt_sha256=receipt["receipt_sha256"],
                         observation_sha256=dispute.release.observation_sha256,
                         view_sha256s={i: authorisation.commitment(mask) for i, mask in dispute.assignments.items()}), dispute, receipt


def clarification(runner: "SessionRunner") -> tuple[Clarification, Dispute, dict[str, Any]] | None:
    row = next((row for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", CLARIFY)), None)
    if row is None:
        return None
    result = make_clarification(runner)
    if Clarification.model_validate(row["details"]) != result[0]:
        raise ValueError("The clarification differs from the exact independent response or committed original tests.")
    return result


def require_observation_inputs(runner: "SessionRunner", job: str, inputs: dict[str, str]) -> None:
    matched = CLARIFIED_JOB.fullmatch(job)
    review = clarification(runner)
    if matched is None or review is None or int(matched[1]) not in review[1].assignments:
        raise ValueError("A clarified observation requires an independently approved view.")
    scope, dispute, _ = review
    view = dispute.assignments[int(matched[1])]
    bundles = TypeAdapter(dict[str, list[Source]]).validate_json(dispute.inputs["paired_bundles"])
    sources = science.mask_sources(view, bundles[view.condition])
    expected = {
        "sources": commissioning.json_text([source.model_dump(mode="json") for source in sources]),
        "neutral_brief": f"{dispute.inputs['neutral_brief']}\n\nReviewer question: {scope.question}",
        "ontology": commissioning.trusted_bytes("instructions/ontology.md").decode(),
        "annotation_rules": commissioning.trusted_bytes("instructions/annotation.md").decode(),
    }
    if inputs != expected:
        raise ValueError("The clarified mask packet changed its approved wording, scope or exact Source view.")


def _inputs_sha(inputs: dict[str, str]) -> str:
    return commissioning.digest(commissioning.json_text(inputs).encode())


def _confirmed_audit(runner: "SessionRunner") -> tuple[audit_boundary.RecheckedAudit, dict[str, Any]]:
    job = joint_control_plan.FOLLOWUP_JOB if joint_control_plan.followup(runner) else joint_control_plan.JOB
    confirmation, _, request = runner.committed_result("audit", job, "audit", joint_control_plan.Confirmation)
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    proposed = rules["additional_proposed_views_by_commitment"]
    if (confirmation.verdict != "accept" or confirmation.objections
            or len(confirmation.confirmed_views) != len(proposed) or set(confirmation.confirmed_views) != proposed.keys()):
        raise ValueError("A control dispute requires a complete accepted joint plan.")
    audit = audit_boundary.RecheckedAudit.model_validate(rules["full_control_plan"])
    return audit.model_copy(update={"limitations": [*audit.limitations, *confirmation.limitations]}), request
