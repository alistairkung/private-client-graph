"""Release one fresh blind reading when both original turns failed representation."""

import re
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import authorisation, repair_authority, science
from benchmark_v3.batch.contracts import Reading
from private_client_graph.models.source import Source

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


WHITESPACE_RELEASE = RELEASE + "whitespace-"


def exact_whitespace_span(quotation: str, source: str) -> str:
    """Recover an exact contiguous span only when non-whitespace bytes are unchanged."""
    terms = quotation.split()
    if not terms:
        raise ValueError("A quotation needs non-whitespace text.")
    pattern = r"\s+".join(re.escape(term) for term in terms)
    matches = list(re.finditer(f"(?=({pattern}))", source))
    if len(matches) != 1:
        raise ValueError("Whitespace recovery requires one exact span in the attributed Source.")
    return matches[0].group(1)


def whitespace_recovery(
    runner: "SessionRunner", job: str,
) -> tuple[dict[str, Any], Reading, dict[str, Any], dict[str, str]]:
    release_details(runner, job)
    original_job = job + repair_authority.FORMAT_RETRY
    output, receipt, request = runner.committed_packet("blind", original_job, "annotation")
    reading = Reading.model_validate_json(output)
    sources = TypeAdapter(list[Source]).validate_json(request["inputs"]["sources"])
    by_id = {source.id: source.text for source in sources}
    relationships = []
    recovered = []
    for index, candidate in enumerate(reading.candidates.relationships):
        source = by_id.get(candidate.source_id)
        if source is None:
            raise ValueError("Whitespace recovery cannot change Source attribution.")
        old = candidate.supporting_text
        if old not in source:
            quote = exact_whitespace_span(old, source)
            candidate = candidate.model_copy(update={"supporting_text": quote})
            recovered.append({
                "candidate_index": index, "source_id": candidate.source_id,
                "before_sha256": commissioning.digest(old.encode()),
                "after_sha256": commissioning.digest(quote.encode()),
            })
        relationships.append(candidate)
    if not recovered:
        raise ValueError("The retained reading has no safely recoverable whitespace difference.")
    corrected = reading.model_copy(update={"candidates": reading.candidates.model_copy(
        update={"relationships": relationships},
    )})
    science.check_reading(corrected, sources)
    record = {
        "original_job": original_job, "receipt_sha256": receipt["receipt_sha256"],
        "manifest_sha256": authorisation.commitment(runner.manifest),
        "derivative_sha256": authorisation.commitment(corrected), "repairs": recovered,
    }
    return record, corrected, receipt, request["inputs"]


def reopen_whitespace(
    runner: "SessionRunner", job: str, inputs: dict[str, str],
) -> tuple[Reading, dict[str, Any]] | None:
    record = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                   if (row["revision"], row["kind"], row["name"]) ==
                   (runner.revision, "reconcile", WHITESPACE_RELEASE + job)), None)
    if record is None:
        return None
    expected, reading, receipt, original_inputs = whitespace_recovery(runner, job)
    if expected != record or original_inputs != inputs:
        raise ValueError("The exact-quote derivative requires its original committed role and frozen input.")
    return reading, receipt
