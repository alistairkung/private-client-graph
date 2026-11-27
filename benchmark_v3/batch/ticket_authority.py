"""Check documentary repair instructions for facts outside the participant's local basis."""

import re
from calendar import month_name
from typing import TYPE_CHECKING

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import author_context
from benchmark_v3.batch.contracts import DesignOutput

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner


def unsupported_literals(design: DesignOutput, ticket: str, local_text: str) -> list[str]:
    """Identify case names and documented periods a ticket adds without local context."""
    authors = (brief.author.split(",", 1)[0].split() for brief in design.inventory)
    names = {parts[0] for parts in authors if len(parts) >= 2 and parts[-1].istitle()}
    periods = set(month_name[1:]) - {"May"}
    mentioned = {value for value in names | periods if re.search(rf"(?<!\w){re.escape(value)}(?!\w)", ticket)}
    if re.search(r"\b(?:\d{1,2} May|May \d{4}|in May)\b", ticket):
        mentioned.add("May")
    return sorted(value for value in mentioned if not re.search(rf"(?<!\w){re.escape(value)}(?!\w)", local_text))


def require_cleared(runner: "SessionRunner") -> None:
    if not runner.ledger.requires_workload_merits:
        return
    _, _, request = runner.committed_result("author", author_context.JOB, "audit", author_context.AuthorContextReview)
    rules = commissioning._read_json(request["inputs"]["audit_rules"])
    if rules.get("unavailable_ticket_literals"):
        raise packet.PacketIsolationError("The local authority gate did not clear the participant repair tickets.")
