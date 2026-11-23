"""Release one fresh blind reading when both original turns failed representation."""

import re
from typing import TYPE_CHECKING, Any

from benchmark_v3.batch import authorisation, repair_authority

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

RELEASE = "blind-representation-"
QUOTE_ERROR = "The reading must quote the exact attributed Source."
INVENTORY_ERROR = "The reading must account for the exact Source inventory."
ERRORS = {QUOTE_ERROR, INVENTORY_ERROR}
INSTRUCTIONS = (
    " Write one candidate row per actual Source and exact contiguous quotation. A supported edge that needs "
    "several Sources may appear in several candidate rows with the same endpoints and type. Preserve all "
    "needed passages without claiming that one conjunct is independently sufficient. Use the real Source ID "
    "in every row. Do not use N/A, virtual evidence, joined quotations or a scoring-policy label as a Source ID. "
    "Copy the quotation, including any line breaks, from that one Source. Prefer a short complete verbatim passage. "
    "Use open_questions for unsupported propositions or caveats."
)
_JOB = re.compile(r"reading-[0-9]{3}-[ab]-(?:full|part-[0-9]{3})")


def release_details(runner: "SessionRunner", job: str) -> dict[str, Any]:
    if not runner.ledger.requires_delivery_attestation or _JOB.fullmatch(job) is None:
        raise ValueError("A local representation recovery requires an isolated blind reading.")
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    rejected = {event["name"]: event["details"] for event in events if
                event["revision"] == runner.revision and event["kind"] == "rejected_output"}
    receipts = {}
    for attempt in (job, job + repair_authority.FORMAT_RETRY):
        _, receipt, _ = runner.committed_packet("blind", attempt, "annotation")
        failure = rejected.get(attempt)
        if (failure is None or failure["reason"] not in ERRORS
                or failure["receipt_sha256"] != receipt["receipt_sha256"]):
            raise ValueError("A fresh reading requires both original exact representation failures.")
        receipts[attempt] = receipt["receipt_sha256"]
    return {"job": job, "receipts": receipts, "manifest_sha256": authorisation.commitment(runner.manifest)}


def selected_job(runner: "SessionRunner", job: str, inputs: dict[str, str]) -> str:
    record = next((event["details"] for event in runner.ledger.events(runner.manifest.batch_id, runner.family)
                   if event["revision"] == runner.revision and event["kind"] == "reconcile"
                   and event["name"] == RELEASE + job), None)
    if record is None:
        return job
    if record != release_details(runner, job):
        raise ValueError("The blind representation release differs from the retained receipts.")
    for attempt in record["receipts"]:
        _, _, request = runner.committed_packet("blind", attempt, "annotation")
        if request["inputs"] != inputs:
            raise ValueError("A fresh blind reading requires the identical frozen input.")
    return job + "-exact-format"
