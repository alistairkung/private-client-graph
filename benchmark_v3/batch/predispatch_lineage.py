"""Verify an undispatched attachment lookup that selected a discarded authoring branch."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, author_context, author_delivery, autonomous_realism, delivery_audience
from benchmark_v3.batch.contracts import DesignOutput
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner
    from benchmark_v3.portfolio import FamilySlot


MISMATCH = "The exact attachment lacks an earlier sender receipt for this participant."


def verify_return(runner: "SessionRunner", slot: "FamilySlot", job: str) -> dict[str, Any]:
    release = autonomous_realism.release_event(runner)
    discarded = (release or {}).get("partial_packet_return", {}).get("revision")
    reservations = runner.ledger.attempts(runner.family)
    if (release is None or not discarded or not job.startswith("author-")
            or any(row["revision"] == runner.revision and row["job"] == job for row in reservations)
            or (runner.directory / "packets" / job).exists() or (runner.directory / "family").exists()):
        raise ValueError("The exact new attachment failure must precede any reservation for that participant.")
    parent = autonomous_realism._read_return(runner, slot, release)
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    inventory = {row.source_id: row for row in design.inventory}
    local = inventory[job.removeprefix("author-")]
    review, review_receipt, request = runner.committed_result(
        "author", author_context.JOB, "audit", author_context.AuthorContextReview,
    )
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    approved = rules["participant_packets"]
    expected = approved[local.source_id]
    if (review.verdict != "accept" or review.objections or review.findings.keys() != approved.keys()
            or expected["received_ids"] != local.received):
        raise ValueError("The refused attachment must match the exact independent participant scope.")
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    earliest = max((row["revision"] for row in events if row["revision"] <= runner.revision
                    and "documentary_redesign" in row["details"]), default=1)
    authoritative = {row.id: row for row in parent.bundles[parent.freeze.natural]}
    affected = set(commissioning._read_json(artifacts.read_bytes(runner.directory / "repair-lineage.json"))["affected_sources"])
    attachments = []
    discarded_receipts = {}
    allowed_receipts = {}
    for identity in local.received:
        name = f"author-{identity}"
        revisions = sorted({row["revision"] for row in reservations if row["job"] == name
                            and earliest <= row["revision"] <= runner.revision}, reverse=True)
        if not revisions or (identity in affected and revisions[0] != runner.revision):
            raise ValueError("The unfinished repair has no verified source for the refused participant packet.")
        chosen = revisions[0]
        if chosen == runner.revision:
            primary, _, _ = _receipt(runner, chosen, name)
            source = Source(id=identity, title=primary.title, text=primary.text)
        else:
            source = authoritative[identity]
        attachments.append(source)
        for revision in revisions:
            origin, receipt, previous = _receipt(runner, revision, name)
            if (origin.title, origin.text) != (source.title, source.text):
                if revision == chosen:
                    if revision != discarded:
                        raise ValueError("Only a demonstrably discarded intermediate receipt can explain this stop.")
                    discarded_receipts[identity] = receipt["receipt_sha256"]
                continue
            origin_brief = commissioning._read_json(previous["inputs"]["author_brief"])
            author = inventory[identity]
            if ((origin_brief["participant"], origin_brief["date"]) != (author.author, author.created_on.isoformat())
                    or author.created_on > local.created_on
                    or not any(grant.recipient == local.author.split(",", 1)[0].strip()
                               and grant.sent_on == author.created_on for grant in origin.deliveries)):
                raise ValueError("The authoritative attachment lacks an exact same-participant delivery receipt.")
            authority = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
            author_delivery.require_projection(authority, name, previous["inputs"])
            allowed_receipts[identity] = receipt["receipt_sha256"]
            break
        else:
            raise ValueError("The authoritative attachment has no exact retained issuing receipt.")

    inputs = {key: value for key, value in expected.items() if key != "received_ids"}
    inputs["received_correspondence"] = commissioning.json_text([row.model_dump(mode="json") for row in attachments])
    delivery_audience.verify_packet(inputs)
    try:
        author_delivery.require_projection(runner, job, inputs)
    except packet.PacketIsolationError as error:
        if str(error) != MISMATCH or not discarded_receipts:
            raise ValueError("The unchanged transport must reproduce the exact closed rejection.") from error
    else:
        raise ValueError("An ordinary passing packet cannot authorize recovery from this stop.")
    return {
        "discarded_author_receipts": discarded_receipts, "authoritative_receipts": allowed_receipts,
        "review_receipt_sha256": review_receipt["receipt_sha256"], "job": job,
        "rejected_inputs_sha256": commissioning.digest(commissioning.json_text(inputs).encode()),
        "blocked_job_reserved": False, "discarded_revision": discarded,
    }


def _receipt(runner: "SessionRunner", revision: int, name: str) -> tuple[author_delivery.AttestedSource, dict[str, Any], dict[str, Any]]:
    origin = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
    source, receipt, request = origin.committed_result("author", name, "author", author_delivery.AttestedSource)
    author_delivery.verify_attestation(source, request["inputs"]["author_brief"])
    return source, receipt, request
