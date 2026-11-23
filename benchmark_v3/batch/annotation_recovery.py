"""Bind a one-line-feed transcription correction to an immutable blind receipt."""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, science
from benchmark_v3.batch.contracts import AnnotationRecovery, Reading
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

ANNOTATION_RECOVERY = "annotation-newline"


def recorded(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((
        row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if row["revision"] == runner.revision and row["kind"] == "reconcile" and row["name"] == ANNOTATION_RECOVERY
    ), None)


def derive(
    runner: "SessionRunner", decision: AnnotationRecovery,
) -> tuple[dict[str, Any], bytes, Reading, dict[str, Any]]:
    original, receipt, request = runner.committed_packet("blind", decision.reader_job, "annotation")
    if (receipt["output_sha256"], receipt["receipt_sha256"]) != (decision.output_sha256, decision.receipt_sha256):
        raise ValueError("Annotation recovery requires the exact original output and receipt.")
    sources = _frozen_sources(runner, decision, request)
    source = next((item for item in sources if item.id == decision.source_id), None)
    if source is None:
        raise ValueError("Annotation recovery requires the cited Source in its frozen bundle.")
    value = commissioning._read_json(original)
    original_reading = Reading.model_validate(value)
    index = int(decision.candidate_path.split("[")[1].split("]")[0])
    relationships = value["candidates"]["relationships"]
    if index >= len(relationships) or relationships[index]["source_id"] != source.id:
        raise ValueError("The candidate path must cite the approved Source.")
    candidate = relationships[index]
    start, stop = decision.byte_interval
    source_bytes = source.text.encode()
    if not 0 <= start < stop <= len(source_bytes):
        raise ValueError("The replacement byte interval is outside the cited Source.")
    quote = candidate["supporting_text"]
    replacement = source_bytes[start:stop]
    _verify_unique_newline(quote.encode(), source_bytes, start, replacement)
    _verify_original_failure(runner, decision, original_reading, sources)

    token = commissioning.json_text(quote).encode()
    if original.count(token) != 1:
        raise ValueError("The original quotation must be one unique JSON string token.")
    corrected = original.replace(token, commissioning.json_text(replacement.decode()).encode(), 1)
    candidate["supporting_text"] = replacement.decode()
    if commissioning._read_json(corrected) != value or len(corrected) != len(original) + 2:
        raise ValueError("Only the approved line feed may change in the blind output.")
    reading = Reading.model_validate(value)
    science.check_reading(reading, sources)
    return {
        "decision": decision.model_dump(mode="json"),
        "original_quote_sha256": commissioning.digest(quote.encode()),
        "corrected_quote_sha256": commissioning.digest(replacement),
        "source_text_sha256": commissioning.digest(source_bytes),
        "derivative_sha256": commissioning.digest(corrected),
        "difference": {"operation": "insert", "hex": "0a", "count": 1},
        "validation": "Original fails verbatim validation. Unique frozen span and derivative pass exact validation.",
    }, corrected, reading, receipt


def _frozen_sources(
    runner: "SessionRunner", decision: AnnotationRecovery, request: dict[str, Any],
) -> list[Source]:
    outputs: dict[str, str] = next((
        row["details"]["outputs"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if row["revision"] == runner.revision and row["kind"] == "transition" and row["name"] == "freeze"
    ), {})
    bundles = [name for name, sha in outputs.items() if name.startswith("sources/") and sha == decision.bundle_sha256]
    if len(bundles) != 1:
        raise ValueError("Annotation recovery requires an exact committed frozen bundle.")
    bundle = bundles[0]
    content = artifacts.read_bytes(runner.directory / "family" / bundle)
    if commissioning.digest(content) != decision.bundle_sha256:
        raise ValueError("The frozen bundle differs from its committed bytes.")
    values = commissioning._read_json(content)
    if values != commissioning._read_json(request["inputs"]["sources"]):
        raise ValueError("The completed reader did not receive the approved frozen bundle.")
    return [Source.model_validate(value) for value in values]


def _verify_unique_newline(quote: bytes, source: bytes, start: int, replacement: bytes) -> None:
    # Every possible repair doubles one existing LF. Match by byte, including overlapping occurrences.
    variants = {quote[:index] + b"\n" + quote[index:] for index, byte in enumerate(quote) if byte == 10}
    matches = {
        (hit.start(), candidate) for candidate in variants
        for hit in re.finditer(b"(?=" + re.escape(candidate) + b")", source)
    }
    if matches != {(start, replacement)}:
        raise ValueError("The interval must be the unique frozen match for a single missing line feed.")


def _verify_original_failure(
    runner: "SessionRunner", decision: AnnotationRecovery, reading: Reading, sources: list[Source],
) -> None:
    retained = [
        row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
        if row["revision"] == runner.revision and row["kind"] == "exception"
        and row["name"] == "blind-scientific_review"
    ]
    try:
        science.check_reading(reading, sources)
    except ValueError as error:
        if ("supporting_text does not occur verbatim in source" in str(error)
                and any(row["evidence"] == str(error) and row["job"] in (None, decision.reader_job) for row in retained)):
            return
    raise ValueError("The original reading must reproduce the recorded verbatim-quotation failure.")


def derivative_path(runner: "SessionRunner", reader_job: str) -> Path:
    return runner.directory / "recoveries" / reader_job / "output.json"


def reopen(runner: "SessionRunner", record: dict[str, Any]) -> tuple[Reading, dict[str, Any]]:
    decision = AnnotationRecovery.model_validate(record["decision"])
    if (decision.owner != runner.owner or decision.batch_id != runner.manifest.batch_id
            or decision.family_id != runner.family
            or decision.manifest_sha256 != authorisation.commitment(runner.manifest)):
        raise ValueError("Annotation recovery belongs to another owner or family.")
    expected, content, reading, receipt = derive(runner, decision)
    if expected != record or content != artifacts.read_bytes(derivative_path(runner, decision.reader_job)):
        raise ValueError("Annotation derivative differs from its committed lineage.")
    return reading, receipt | {"mechanical_derivative_sha256": record["derivative_sha256"]}
