"""Recover one isolated reading from its exact retained representation failures."""

import re
from typing import TYPE_CHECKING, Any, Literal

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, repair_authority, science
from benchmark_v3.batch.contracts import Reading
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

RELEASE = "blind-representation-"
MASK_RELEASE = "masked-representation-"
PAUSE_RELEASE = "reading-after-shared-pause-"
PAUSE_REASON = "A custody member has an unresolved shared integrity stop."
ReadingRole = Literal["annotation", "masked"]
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
_MASK_JOB = re.compile(r"mask-[0-9]{3}(?:-clarified)?")


def _stage(role: ReadingRole) -> Literal["blind", "masks"]:
    return "blind" if role == "annotation" else "masks"


def _release(role: ReadingRole) -> str:
    return RELEASE if role == "annotation" else MASK_RELEASE


def release_details(
    runner: "SessionRunner", job: str, *, role: ReadingRole = "annotation",
) -> dict[str, Any]:
    pattern = _JOB if role == "annotation" else _MASK_JOB
    if not runner.ledger.requires_delivery_attestation or pattern.fullmatch(job) is None:
        raise ValueError("A local representation recovery requires an isolated reading.")
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    rejected = {event["name"]: event["details"] for event in events if
                event["revision"] == runner.revision and event["kind"] == "rejected_output"}
    receipts = {}
    for attempt in (job, job + repair_authority.FORMAT_RETRY):
        _, receipt, _ = runner.committed_packet(_stage(role), attempt, role)
        failure = rejected.get(attempt)
        if (failure is None or failure["reason"] not in ERRORS
                or failure["receipt_sha256"] != receipt["receipt_sha256"]):
            raise ValueError("A fresh reading requires both original exact representation failures.")
        receipts[attempt] = receipt["receipt_sha256"]
    return {"job": job, "receipts": receipts, "manifest_sha256": authorisation.commitment(runner.manifest)}


def selected_job(
    runner: "SessionRunner", job: str, inputs: dict[str, str], *, role: ReadingRole = "annotation",
) -> str:
    releases = {event["name"]: event["details"] for event in runner.ledger.events(runner.manifest.batch_id, runner.family)
                if event["revision"] == runner.revision and event["kind"] == "reconcile"}
    if paused := releases.get(PAUSE_RELEASE + job):
        exact, original = paused_reading(runner, job, role=role)
        if paused != exact or inputs != original:
            raise ValueError("The resumed reading must have the identical frozen input and interrupted receipt.")
        return job + "-after-pause"
    record = releases.get(_release(role) + job)
    if record is None:
        return job
    if record != release_details(runner, job, role=role):
        raise ValueError("The blind representation release differs from the retained receipts.")
    for attempt in record["receipts"]:
        _, _, request = runner.committed_packet(_stage(role), attempt, role)
        if request["inputs"] != inputs:
            raise ValueError("A fresh blind reading requires the identical frozen input.")
    return job + "-exact-format"


def paused_reading(
    runner: "SessionRunner", job: str, *, role: ReadingRole,
) -> tuple[dict[str, Any], dict[str, str]]:
    pattern = _JOB if role == "annotation" else _MASK_JOB
    if not runner.ledger.requires_delivery_attestation or pattern.fullmatch(job) is None:
        raise ValueError("A paused reading requires an exact isolated reader role.")
    attempt = next(item for item in runner.ledger.attempts(runner.family)
                   if (item["revision"], item["stage"], item["job"]) == (runner.revision, _stage(role), job))
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    session = next(item["details"] for item in events
                   if (item["revision"], item["kind"], item["name"]) == (runner.revision, "session", job))
    folder = runner.directory / "packets" / job
    request = commissioning._read_json(artifacts.read_bytes(folder / "request.json"))
    handoff_bytes = artifacts.read_bytes(folder / "handoff.json")
    handoff = commissioning._read_json(handoff_bytes)
    receipt_bytes = artifacts.read_bytes(folder / "receipt.json")
    receipt = commissioning._read_json(receipt_bytes)
    receipt_sha = commissioning.digest(receipt_bytes)
    if (request["role"] != role or handoff["role"] != role or session["role"] != role
            or request != commissioning._read_json(attempt["request"])
            or commissioning.digest(commissioning.json_text(request).encode()) != attempt["request_sha256"]
            or receipt["status"] != "rejected" or receipt["reason"] != PAUSE_REASON or "submitted_at" in receipt
            or "output" in receipt or (folder / "output.txt").exists()
            or session["status"] != "rejected" or session["receipt_sha256"] != receipt_sha
            or receipt["handoff_sha256"] != commissioning.digest(handoff_bytes)
            or session["packet_sha256"] != receipt["packet_sha256"] or handoff["packet_sha256"] != receipt["packet_sha256"]):
        raise ValueError("A paused reading must have its original unsubmitted request and rejected receipt.")
    return {"request_sha256": attempt["request_sha256"], "receipt_sha256": receipt_sha}, request["inputs"]


WHITESPACE_RELEASE = RELEASE + "whitespace-"
MASK_WHITESPACE_RELEASE = MASK_RELEASE + "whitespace-"


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
    runner: "SessionRunner", job: str, *, role: ReadingRole = "annotation",
) -> tuple[dict[str, Any], Reading, dict[str, Any], dict[str, str]]:
    release_details(runner, job, role=role)
    original_job = job + repair_authority.FORMAT_RETRY
    output, receipt, request = runner.committed_packet(_stage(role), original_job, role)
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
    runner: "SessionRunner", job: str, inputs: dict[str, str], *, role: ReadingRole = "annotation",
) -> tuple[Reading, dict[str, Any]] | None:
    prefix = WHITESPACE_RELEASE if role == "annotation" else MASK_WHITESPACE_RELEASE
    record = next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                   if (row["revision"], row["kind"], row["name"]) ==
                   (runner.revision, "reconcile", prefix + job)), None)
    if record is None:
        return None
    expected, reading, receipt, original_inputs = whitespace_recovery(runner, job, role=role)
    if expected != record or original_inputs != inputs:
        raise ValueError("The exact-quote derivative requires its original committed role and frozen input.")
    return reading, receipt
