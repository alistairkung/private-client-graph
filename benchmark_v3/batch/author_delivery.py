"""Require receipt-backed sender attestations for participant attachments."""

import re
from dataclasses import replace
from datetime import date
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import author_context
from benchmark_v3.batch.contracts import AuthoredSource, DesignOutput
from benchmark_v3.research_contracts import Contract, Text
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

INSTRUCTIONS = (
    author_context.INSTRUCTIONS + " In deliveries, attest only the supplied same-day transmissions you personally "
    "made of this record. Record each exact recipient and sent_on date in the separate deliveries field. "
    "Omit a delivery if it conflicts with your own documented actions or requires another person to forward it. "
    "Do not put the attestation in the record text. Return an empty list when you made no supplied transmission."
)
DESIGN_INSTRUCTION = (
    "For each earlier Source used as an attachment, the originating Source's provenance must include a separate exact "
    "line 'Delivered YYYY-MM-DD to Full Name' for that person. The date must equal the sending Source's created_on. "
    "Use the named participant before the first comma in author. The sender must personally transmit this version on "
    "that date. A signature, familiarity with the contents, an institutional file or an intended route is insufficient. "
    "Use a separate dated cover record for later forwarding and keep the same-day sender grant and the recipient's "
    "received list consistent. Use the authorised earlier attachments only where the author needs them. Show no "
    "experimental rationale in documentary instructions."
)
REVIEW_INSTRUCTION = (
    "For every attachment, independently verify the explicitly named sender-to-person transmission in its originating "
    "provenance and the matching date. Require the actual author to be the sender for that record. Do not infer "
    "delivery from being a signer or witness, being in the same workstream, a copy addressed only to an institution, "
    "or a later routing statement. Return any material conflict between a delivery declaration and the origin, role, "
    "date or participant's knowledge. The sender will independently attest the same-day grants outside Source text."
)
_DELIVERY = re.compile(r"Delivered (\d{4}-\d{2}-\d{2}) to ([^\r\n]+)")


class Delivery(Contract):
    recipient: Text
    sent_on: date


class AttestedSource(AuthoredSource):
    deliveries: list[Delivery]


def _participant(author: str) -> str:
    return author.split(",", 1)[0].strip()


def _declared_grants(provenance: str, created_on: date) -> set[tuple[str, date]]:
    grants = set()
    for line in provenance.splitlines():
        if not line.lstrip().startswith("Delivered "):
            continue
        match = _DELIVERY.fullmatch(line)
        if match is None:
            raise ValueError("A sender grant must name one exact person and the record's date.")
        day, person = match.groups()
        grant = (person, date.fromisoformat(day))
        if not person.strip() or person != person.strip() or grant in grants or grant[1] != created_on:
            raise ValueError("A sender grant must be unique, named and dated on the sending record's day.")
        grants.add(grant)
    return grants


def projection(design: DesignOutput, tickets: dict[str, str]) -> dict[str, Any]:
    """Bind incoming links to a directly named, dated grant on the sending side."""
    packets = author_context.projection(design, tickets)
    inventory = {brief.source_id: brief for brief in design.inventory}
    declared = {identity: _declared_grants(brief.provenance, brief.created_on) for identity, brief in inventory.items()}
    outgoing: dict[str, set[tuple[str, date]]] = {identity: set() for identity in packets}
    for identity, brief in inventory.items():
        for source in brief.received:
            grant = (_participant(brief.author), inventory[source].created_on)
            if not grant[0] or grant not in declared[source]:
                raise ValueError(f"Attachment {source} has no same-day sender grant to the participant for {identity}.")
            outgoing[source].add(grant)
    for identity, grants in outgoing.items():
        local = commissioning._read_json(packets[identity]["author_brief"])
        local["outgoing_deliveries"] = [
            {"recipient": recipient, "sent_on": day.isoformat()} for recipient, day in sorted(grants)
        ]
        packets[identity]["author_brief"] = commissioning.json_text(local)
    return packets


def verify_attestation(source: AttestedSource, author_brief: str) -> None:
    expected = commissioning._read_json(author_brief)["outgoing_deliveries"]
    if [delivery.model_dump(mode="json") for delivery in source.deliveries] != expected:
        raise ValueError("The sending author must attest the exact ordered same-day grants.")


def require_prompt(job: str, prompt: str) -> None:
    expected = INSTRUCTIONS
    if job.endswith("-format-retry"):
        expected += " Return only the exact requested JSON object."
    expected += "\nReturn one JSON object. Output schema: " + commissioning.json_text(AttestedSource.model_json_schema())
    if prompt != expected:
        raise packet.PacketIsolationError("The author task does not use the fixed attestation prompt.")


def require_projection(runner: "SessionRunner", job: str, inputs: dict[str, str]) -> None:
    identity = job.removesuffix("-format-retry").removeprefix("author-")
    review, _, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    approved = rules["participant_packets"]
    if (rules.get("delivery_attestation") != 1 or review.verdict != "accept"
            or review.objections or review.findings.keys() != approved.keys()):
        raise packet.PacketIsolationError("The independent review did not clear the attested participant inventory.")
    recipient = commissioning._read_json(approved[identity]["author_brief"])
    author_context.validate_inputs(inputs, approved[identity], lambda source: _verify_delivery(
        runner, source, _participant(recipient["participant"]), date.fromisoformat(recipient["date"]),
    ))


def _verify_delivery(runner: "SessionRunner", source: Source, recipient: str, received_by: date) -> None:
    job = f"author-{source.id}"
    revision = max((row["revision"] for row in runner.ledger.attempts(runner.family)
                    if row["job"] == job and row["revision"] <= runner.revision), default=0)
    if not revision:
        raise packet.PacketIsolationError("The attachment has no prior scientific author receipt.")
    earlier = replace(runner, revision=revision, directory=runner.directory.parent / str(revision))
    document, _, request = earlier.committed_result("author", job, "author", AttestedSource)
    origin_brief = commissioning._read_json(request["inputs"]["author_brief"])
    issued_on = date.fromisoformat(origin_brief["date"])
    verify_attestation(document, request["inputs"]["author_brief"])
    if (source.title != document.title or source.text != document.text or issued_on > received_by
            or not any(grant.recipient == recipient and grant.sent_on == issued_on for grant in document.deliveries)):
        raise packet.PacketIsolationError("The exact attachment lacks an earlier sender receipt for this participant.")
