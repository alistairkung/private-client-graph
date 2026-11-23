"""Bind participant author packets to an independent review and exact deliveries."""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch.contracts import AuthoredSource, DesignOutput
from benchmark_v3.research_contracts import Contract, Text
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

JOB = "author-context"
INSTRUCTIONS = ("Write this one fictional record from the participant's dated perspective. "
                "Return its title and complete text without editorial notes.")


def require_prompt(job: str, prompt: str) -> None:
    expected = INSTRUCTIONS
    if job.endswith("-format-retry"):
        expected += " Return only the exact requested JSON object."
    expected += "\nReturn one JSON object. Output schema: " + commissioning.json_text(AuthoredSource.model_json_schema())
    if prompt != expected:
        raise packet.PacketIsolationError("The author task instructions differ from the fixed documentary prompt.")


class AuthorContextReview(Contract):
    verdict: Literal["accept", "return"]
    findings: dict[str, Text]
    objections: list[Text]


def projection(design: DesignOutput, tickets: dict[str, str]) -> dict[str, Any]:
    """Build the author projection independently of the private design prose."""
    rows: dict[str, Any] = {}
    dates = {brief.source_id: brief.created_on for brief in design.inventory}
    edits = [control.edit for control in design.matched if control.edit]
    for brief in design.inventory:
        identity = brief.source_id
        allowed = {identity, *brief.received}
        text = "\n".join((brief.author, brief.participant_brief, tickets.get(identity, "")))
        for other in dates.keys() - allowed:
            if len(other) >= 4 and re.search(rf"(?<![\w-]){re.escape(other)}(?![\w-])", text, re.IGNORECASE):
                raise ValueError(f"Author {identity} has an undeclared documentary reference.")
        for alternate in edits:
            before, after = alternate.before.casefold(), alternate.after.casefold()
            if len(after) >= 12 and after not in before and after in text.casefold():
                raise ValueError(f"Author {identity} receives the matched alternate wording.")
        if any(delivery not in rows or dates[delivery] > brief.created_on for delivery in brief.received):
            raise ValueError(f"Author {identity} depends on unavailable or future correspondence.")
        rows[identity] = {
            "author_brief": commissioning.json_text({"participant": brief.author,
                "date": brief.created_on.isoformat(), "brief": brief.participant_brief}),
            "received_ids": brief.received,
            **({"revision_ticket": tickets[identity]} if identity in tickets else {}),
        }
    return rows


def require_projection(runner: "SessionRunner", job: str, inputs: dict[str, str]) -> None:
    """Authenticate the independent review and compare the actual request before dispatch."""
    identity = job.removesuffix("-format-retry").removeprefix("author-")
    review, _, request = runner.committed_result("author", JOB, "audit", AuthorContextReview)
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    approved = rules["participant_packets"]
    if review.verdict != "accept" or review.objections or review.findings.keys() != approved.keys():
        raise packet.PacketIsolationError("The independent participant context review did not clear the inventory.")
    validate_inputs(inputs, approved[identity], lambda source: _committed_source(runner, source))


def validate_inputs(inputs: dict[str, str], approved: dict[str, Any], verify_source: Callable[[Source], None]) -> None:
    """Reject nested changes as well as extra fields in the author input envelope."""
    supplied = {key: value for key, value in inputs.items() if key != "received_correspondence"}
    if supplied != {key: value for key, value in approved.items() if key != "received_ids"}:
        raise packet.PacketIsolationError("The author brief or revision ticket differs from the reviewed projection.")
    deliveries = commissioning._read_json(inputs["received_correspondence"])
    if not isinstance(deliveries, list) or any(
        not isinstance(item, dict) or item.keys() != {"id", "title", "text"} for item in deliveries
    ):
        raise packet.PacketIsolationError("The author delivery payload has an unexpected nested field.")
    if [item["id"] for item in deliveries] != approved["received_ids"]:
        raise packet.PacketIsolationError("The author delivery list differs from its reviewed prior inventory.")
    for item in deliveries:
        verify_source(Source.model_validate(item))


def _committed_source(runner: "SessionRunner", source: Source) -> None:
    from dataclasses import replace

    # A repair may reuse an unchanged Source, but only within this fresh custody.
    for revision in range(runner.revision, 0, -1):
        origin = replace(runner, revision=revision, directory=runner.directory.parent / str(revision))
        if not (origin.directory / "packets" / JOB / "receipt.json").is_file():
            continue
        if not any(row["revision"] == revision and row["job"] == f"author-{source.id}"
                   for row in runner.ledger.attempts(runner.family)):
            continue
        document, _, _ = origin.committed_result("author", f"author-{source.id}", "author", AuthoredSource)
        if source.title == document.title and source.text == document.text:
            return
        break
    raise packet.PacketIsolationError("A delivered Source differs from its independently authored receipt.")
