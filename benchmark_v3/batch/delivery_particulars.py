"""Reopen only a participant's authorised direct-transmission particulars."""

from dataclasses import replace
from datetime import date

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import author_delivery
from benchmark_v3.batch.contracts import DesignOutput, SourceId
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.source import Source


class ReceiptParticular(Contract):
    source_id: SourceId
    sender: Text
    sent_on: date
    author_receipt_sha256: Digest


class IncomingParticulars(Contract):
    source_id: SourceId
    recipient_author: Text
    recipient_on: date
    records: list[ReceiptParticular]

    def source_ids(self) -> list[str]:
        return [record.source_id for record in self.records]

    def local_ticket(self) -> str:
        rows = "\n".join(f"{index}. {record.sender} | {record.sent_on.isoformat()}"
                         for index, record in enumerate(self.records, 1))
        return ("Use the checked direct transmission particulars below for the attached records, in attachment order. "
                "Each date records dispatch to you and delivery on that day. These particulars do not establish a "
                "separate office receipt, filing, storage or register entry.\n" + rows)

    def require_unchanged_senders(self, design: DesignOutput, affected: set[str]) -> None:
        recipient = next(row for row in design.inventory if row.source_id == self.source_id)
        if (self.source_id not in affected or recipient.author != self.recipient_author
                or recipient.created_on != self.recipient_on or recipient.received != self.source_ids()
                or affected.intersection(self.source_ids())):
            raise ValueError("Receipt particulars require an affected recipient and the same unchanged prior deliveries.")


def reopen(runner: SessionRunner, recipient: str) -> IncomingParticulars:
    """Check the exact earlier author request, Sources and original sender attestations."""
    _, _, request = runner.committed_result("author", f"author-{recipient}", "author", author_delivery.AttestedSource)
    inputs = request["inputs"]
    author_delivery.require_projection(runner, f"author-{recipient}", inputs)
    local = commissioning._read_json(inputs["author_brief"])
    received = TypeAdapter(list[Source]).validate_json(inputs["received_correspondence"])
    if not received or len({source.id for source in received}) != len(received):
        raise ValueError("A delivery-particulars repair requires distinct actual incoming direct transmissions.")
    revisions: dict[str, int] = {}
    for attempt in runner.ledger.attempts(runner.family):
        job, revision = attempt["job"], attempt["revision"]
        if job.startswith("author-") and revision <= runner.revision:
            revisions[job] = max(revisions.get(job, 0), revision)
    records = []
    for source in received:
        job = f"author-{source.id}"
        revision = revisions[job]
        origin = replace(runner, revision=revision, directory=runner.directory.with_name(str(revision)))
        _, receipt, original = origin.committed_result("author", job, "author", author_delivery.AttestedSource)
        brief = commissioning._read_json(original["inputs"]["author_brief"])
        sender = author_delivery._participant(brief["participant"])
        if any(character in sender for character in "\r\n|"):
            raise ValueError("The checked sender identity must fit one delivery row.")
        records.append(ReceiptParticular(source_id=source.id, sender=sender,
                                        sent_on=date.fromisoformat(brief["date"]), author_receipt_sha256=receipt["receipt_sha256"]))
    return IncomingParticulars(source_id=recipient, recipient_author=local["participant"],
                               recipient_on=date.fromisoformat(local["date"]), records=records)
