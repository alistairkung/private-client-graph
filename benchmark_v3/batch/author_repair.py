"""Plan and verify bounded participant-local authoring repairs."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, author_context, author_delivery, authorisation, clean_redesign, repair_authority
from benchmark_v3.batch.contracts import DesignOutput
from benchmark_v3.research_contracts import Contract, Text
from private_client_graph.models.source import Source

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
        raise ValueError(PLAN_OUTSIDE_BRIEF)
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


UNUSED_ATTESTATION = "author-unneeded-attestation"
EMPTY_ATTESTATION_REPAIR = "author-empty-attestation-repair"
ATTESTATION_ERROR = "The sending author must attest the exact ordered same-day grants."


def empty_sender_repair(
    runner: "SessionRunner", source_id: str,
) -> tuple[dict[str, Any], DesignOutput, dict[str, Source]]:
    """Bind an omitted grant to its approved sender's existing act, with no derived attestation."""
    if not runner.ledger.requires_delivery_attestation or (runner.directory / "family").exists():
        raise ValueError("A missing sender attestation must precede the family freeze.")
    events = [row for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
              if row["revision"] == runner.revision]
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    design_hash = authorisation.commitment(design)
    transition = next(row["details"] for row in events if (row["kind"], row["name"]) == ("transition", "design"))
    if transition["outputs"]["design"] != design_hash:
        raise ValueError("A sender repair requires the exact original design commitment.")
    review, scope_receipt, scope_request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    original_packets = commissioning._read_json(scope_request["inputs"]["audit_rules"])["participant_packets"]
    if review.verdict != "accept" or review.objections or original_packets != author_delivery.projection(design, {}):
        raise ValueError("A sender reminder requires an independently approved original unticketed projection.")
    outgoing = commissioning._read_json(original_packets[source_id]["author_brief"])["outgoing_deliveries"]
    if not outgoing:
        raise ValueError("A sender reminder requires documented outgoing attachment grants.")
    failure_receipts = _missing_sender_receipts(runner, source_id, events)
    revised = _explicit_sender_design(design, source_id, outgoing)
    original_retained, retained = _retained_sender_sources(runner, design, source_id, events)
    record = {"source_id": source_id, "scope_receipt_sha256": scope_receipt["receipt_sha256"],
              "design_sha256": design_hash, "revised_design_sha256": authorisation.commitment(revised),
              "rejected_author_receipts": failure_receipts, "retained_sources": original_retained}
    return record, revised, retained


def _missing_sender_receipts(runner: "SessionRunner", source_id: str, events: list[dict[str, Any]]) -> dict[str, str]:
    rejected = {row["name"]: row["details"] for row in events if row["kind"] == "rejected_output"}
    job = f"author-{source_id}"
    found = {}
    prior_inputs = None
    partial = None
    for name in (job, job + repair_authority.FORMAT_RETRY):
        output, receipt, request = runner.committed_packet("author", name, "author")
        inputs = request["inputs"]
        author_delivery.require_projection(runner, name, inputs)
        author_delivery.require_prompt(name, request["prompt"])
        supplied = [item.model_dump(mode="json") for item in author_delivery.AttestedSource.model_validate_json(output).deliveries]
        expected = commissioning._read_json(inputs["author_brief"])["outgoing_deliveries"]
        if ((supplied and not runner.ledger.requires_workload_merits)
                or supplied != [grant for grant in expected if grant in supplied] or supplied == expected
                or (prior_inputs is not None and (inputs != prior_inputs or supplied != partial))
                or rejected.get(name) != {"receipt_sha256": receipt["receipt_sha256"], "reason": ATTESTATION_ERROR}):
            raise ValueError("Both original authors must have omitted the same existing grants under the same cleared scope.")
        prior_inputs, partial = inputs, supplied
        found[name] = receipt["receipt_sha256"]
    return found


def _explicit_sender_design(design: DesignOutput, source_id: str, outgoing: list[dict[str, str]]) -> DesignOutput:
    declared = " and ".join(f"{item['recipient']} on {item['sent_on']}" for item in outgoing)
    source = next(brief for brief in design.inventory if brief.source_id == source_id)
    brief = source.participant_brief + f" Personally send this record to {declared} as part of this documented act."
    revised = design.model_copy(update={"inventory": [
        row.model_copy(update={"participant_brief": brief}) if row.source_id == source_id else row for row in design.inventory
    ]})
    author_delivery.projection(revised, {})
    return revised


def _retained_sender_sources(
    runner: "SessionRunner", design: DesignOutput, source_id: str, events: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, Source]]:
    affected = {source_id}
    selected = {row["name"]: row["details"]["selected_job"] for row in events if row["kind"] == "output_selection"}
    rejected = {row["name"] for row in events if row["kind"] == "rejected_output"}
    verified = {row["name"] for row in events if row["kind"] == "session" and row["details"]["status"] == "completed"}
    commitments: dict[str, str] = {}
    sources: dict[str, Source] = {}
    for row in design.inventory:
        if row.source_id in affected or affected.intersection(row.received):
            affected.add(row.source_id)
            continue
        job = f"author-{row.source_id}"
        actual = selected.get(job, job)
        if actual not in verified or actual in rejected or not set(row.received) <= sources.keys():
            continue
        author, receipt, request = runner.committed_result("author", job, "author", author_delivery.AttestedSource)
        author_delivery.require_projection(runner, actual, request["inputs"])
        author_delivery.require_prompt(actual, request["prompt"])
        author_delivery.verify_attestation(author, request["inputs"]["author_brief"])
        commitments[row.source_id] = receipt["receipt_sha256"]
        sources[row.source_id] = Source(id=row.source_id, title=author.title, text=author.text)
    return commitments, sources


def reopen_empty_sender_repair(runner: "SessionRunner") -> tuple[DesignOutput, dict[str, Source], dict[str, Any]] | None:
    record = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                   if (row["revision"], row["kind"], row["name"]) == (runner.revision, "transition", EMPTY_ATTESTATION_REPAIR)), None)
    if record is None:
        return None
    previous = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    deferred = record.get("deferred_redesign")
    if deferred is not None:
        if deferred != deferred_sender_redesign(previous):
            raise ValueError("The deferred clean design no longer matches its retained receipts.")
        previous = replace(previous, revision=previous.revision - 1, directory=previous.directory.with_name(str(previous.revision - 1)))
    expected, design, retained = empty_sender_repair(previous, record["source_id"])
    if expected | ({"deferred_redesign": deferred} if deferred is not None else {}) != record:
        raise ValueError("The sender reminder differs from the original independently held receipts.")
    return design, retained, record


def deferred_sender_redesign(runner: "SessionRunner") -> dict[str, Any]:
    """Keep a design-only replacement separate when a stronger prior lineage becomes recoverable."""
    batch, family, revision = runner.manifest.batch_id, runner.family, runner.revision
    replacement = clean_redesign.recorded(runner)
    if replacement is None or replacement.parent_revision != revision - 1 or not runner.ledger.requires_workload_merits:
        raise ValueError("Only the direct design-only replacement may be deferred for sender recovery.")
    attempts = [row for row in runner.ledger.attempts(family) if row["revision"] == revision]
    results = {row["name"]: row["details"] for row in runner.ledger.events(batch, family)
               if row["revision"] == revision and row["kind"] == "session"}
    if (not attempts or any(row["stage"] != "design" or row["job"] not in results for row in attempts)):
        raise ValueError("A replacement with active reservations or post-design work may not be deferred.")
    receipts = {}
    for attempt in attempts:
        job = attempt["job"]
        receipt = artifacts.read_bytes(runner.directory / "packets" / job / "receipt.json")
        digest = commissioning.digest(receipt)
        if digest != results[job]["receipt_sha256"]:
            raise ValueError("A deferred replacement must retain every exact designer receipt.")
        receipts[job] = digest
    return {"revision": revision, "replacement_sha256": authorisation.commitment(replacement), "receipts": receipts}


def verify_unused_attestation(runner: "SessionRunner", source_id: str, design: DesignOutput) -> dict[str, Any]:
    from benchmark_v3.batch import author_delivery

    own = next(brief for brief in design.inventory if brief.source_id == source_id)
    if not runner.ledger.requires_delivery_attestation or any(
        source_id in brief.received for brief in design.inventory
    ):
        raise ValueError("A local-only attestation cannot repair a delivery consumed by another author.")
    job = f"author-{source_id}"
    author, receipt, request = runner.committed_result("author", job, "author", author_delivery.AttestedSource)
    local = commissioning._read_json(request["inputs"]["author_brief"])
    declared = author_delivery._declared_grants(own.provenance, own.created_on)
    supplied = {(item.recipient, item.sent_on) for item in author.deliveries}
    if local.get("outgoing_deliveries") != [] or not supplied or len(supplied) != len(author.deliveries) or not supplied <= declared:
        raise ValueError("The exact extra local grants are not authorised own-record facts.")
    return {"source_id": source_id, "receipt_sha256": receipt["receipt_sha256"],
            "author_output_sha256": receipt["output_sha256"], "design_sha256": authorisation.commitment(design),
            "unused_outgoing_attestations": [item.model_dump(mode="json") for item in author.deliveries]}


def unused_attestation(runner: "SessionRunner", source_id: str, design: DesignOutput) -> bool:
    recorded = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                     if row["revision"] == runner.revision and row["kind"] == "reconcile"
                     and row["name"] == UNUSED_ATTESTATION and row["details"].get("source_id") == source_id), None)
    if recorded is None:
        return False
    if verify_unused_attestation(runner, source_id, design) != recorded:
        raise ValueError("The exact local-only attestation proof has changed.")
    return True


PROVENANCE_CLARIFICATION = "preauthor-provenance-clarification"
PLAN_OUTSIDE_BRIEF = "The scope return needs a different scientific plan or valid author IDs."


def cover_clarification(
    runner: "SessionRunner", source_id: str, wrong_cover: str, correct_cover: str,
) -> tuple[dict[str, Any], DesignOutput]:
    """Resolve a uniquely attested custody cross-reference before any author turn."""
    from benchmark_v3.batch import author_delivery

    family, batch = runner.family, runner.manifest.batch_id
    if not runner.ledger.requires_delivery_attestation or runner.revision < 3:
        raise ValueError("The clarification requires a charged independent preauthor scope plan.")
    planner = replace(runner, revision=runner.revision - 1, directory=runner.directory.with_name(str(runner.revision - 1)))
    prior = replace(runner, revision=runner.revision - 2, directory=runner.directory.with_name(str(runner.revision - 2)))
    review, review_receipt, _ = prior.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    plan, plan_receipt, _ = planner.committed_result("design", JOB, "audit", Plan)
    if (review.verdict != "return" or plan.briefs or not review.objections
            or not any(all(token in issue for token in (source_id, wrong_cover, correct_cover)) for issue in review.objections)
            or not all(token in plan.rationale for token in (source_id, wrong_cover, correct_cover))
            or any(prior.revision <= row["revision"] < runner.revision and row["stage"] == "author"
                   and row["job"] not in {author_context.JOB, author_context.JOB + "-format-retry"}
                   for row in runner.ledger.attempts(family))):
        raise ValueError("Both independent reports must identify the same exact unapplied cover-reference correction.")
    design = artifacts.read_contract(prior.directory / "design.json", DesignOutput)
    inventory = {item.source_id: item for item in design.inventory}
    origin, wrong, correct = (inventory[item] for item in (source_id, wrong_cover, correct_cover))
    if (wrong_cover == correct_cover or origin.provenance.count(wrong_cover) != 1
            or correct_cover in origin.provenance or source_id not in correct.received or source_id in wrong.received
            or sum(source_id in item.received for item in design.inventory) != 1
            or correct.created_on < origin.created_on or source_id not in correct.provenance):
        raise ValueError("The independently identified record must be the unique actual forwarding cover.")
    fixed = origin.model_copy(update={"provenance": origin.provenance.replace(wrong_cover, correct_cover, 1)})
    effect = design.model_copy(update={"inventory": [fixed if row.source_id == source_id else row for row in design.inventory]})
    if author_delivery.projection(design, {}) != author_delivery.projection(effect, {}):
        raise ValueError("A custody cross-reference clarification must preserve every exact participant projection.")
    return ({
        "batch": batch, "source_id": source_id, "wrong_cover": wrong_cover, "correct_cover": correct_cover,
        "scope_receipt_sha256": review_receipt["receipt_sha256"], "plan_receipt_sha256": plan_receipt["receipt_sha256"],
        "original_design_sha256": authorisation.commitment(design), "corrected_design_sha256": authorisation.commitment(effect),
    }, effect)


def reopen_cover_clarification(runner: "SessionRunner") -> DesignOutput | None:
    chosen = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                   if (row["revision"], row["kind"], row["name"]) ==
                   (runner.revision, "transition", PROVENANCE_CLARIFICATION)), None)
    if chosen is None:
        return None
    details, design = cover_clarification(runner, chosen["source_id"], chosen["wrong_cover"], chosen["correct_cover"])
    if details != chosen:
        raise ValueError("The exact independently verified custody clarification changed.")
    return design
