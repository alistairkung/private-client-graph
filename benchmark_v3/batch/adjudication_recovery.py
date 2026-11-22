"""Recover a Source ID serialized into its own approved quotation field."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import adjudication_contract, annotation_recovery, artifacts, authorisation, continuation, science
from benchmark_v3.batch.contracts import Adjudication, AdjudicationQuoteRecovery, Reading
from private_client_graph.evaluation import _edge
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

ADJUDICATION_QUOTE_RECOVERY = "adjudication-quote"
PARENT_JOB = adjudication_contract.RELEASE_JOBS["complete_evidence_adjudication"]
QUOTE_SEMANTICS_ERROR = "Source-aware approval must retain existing approved-quote semantics"


def recorded(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if row["revision"] == runner.revision and row["kind"] == "reconcile"
                 and row["name"] == ADJUDICATION_QUOTE_RECOVERY), None)


def derivative_path(runner: "SessionRunner") -> Path:
    return runner.directory / "recoveries" / PARENT_JOB / "output.json"


def derive(
    runner: "SessionRunner", decision: AdjudicationQuoteRecovery,
) -> tuple[dict[str, Any], bytes, Adjudication, dict[str, Any]]:
    if (decision.owner != runner.owner or decision.family_id != runner.family
            or decision.batch_id != runner.manifest.batch_id
            or decision.manifest_sha256 != authorisation.commitment(runner.manifest)):
        raise ValueError("The quote recovery requires the commissioning owner and exact family and manifest.")
    release = continuation.recorded(runner)
    if release is None or release["decision"]["release"]["action"] != "complete_evidence_adjudication":
        raise ValueError("Quote recovery requires the retained complete-evidence adjudication.")
    continuation.verify_authority(runner, release)
    raw, receipt, request = runner.committed_packet("adjudicate", PARENT_JOB, "adjudication")
    if (receipt["output_sha256"], receipt["receipt_sha256"]) != (decision.output_sha256, decision.receipt_sha256):
        raise ValueError("Quote recovery requires the exact adjudication output and receipt.")

    condition = f"{runner.family}000"
    content = artifacts.read_bytes(runner.directory / "family" / "sources" / f"{condition}.json")
    if commissioning.digest(content) != decision.bundle_sha256:
        raise ValueError("Quote recovery requires the exact frozen Source bundle.")
    values = commissioning._read_json(content)
    inputs = request["inputs"]
    if values != commissioning._read_json(inputs["sources"]):
        raise ValueError("The retained adjudication did not receive the frozen Sources.")
    sources = [Source.model_validate(value) for value in values]
    first, second = _verified_readings(runner, inputs)
    agreement = science.compare_readings(first, second, sources)
    if adjudication_contract.resolution_ids(agreement["disagreements"]) != release["resolution_ids"]:
        raise ValueError("The blind readings no longer reproduce the authorised disputes.")

    parsed = commissioning._read_json(raw)
    original = Adjudication.model_validate(parsed)
    _verify_original_failure(condition, original, sources, agreement)
    donor, edge, quote = _selected_quote(decision, original, sources, (first, second))
    corrected = _substitute(raw, parsed, decision, quote)
    review = Adjudication.model_validate(commissioning._read_json(corrected))
    science.verify_adjudication(condition, _local_key(review, condition), sources, agreement)
    return {
        "decision": decision.model_dump(mode="json"),
        "parent_job": PARENT_JOB,
        "parent_packet_sha256": receipt["packet_sha256"],
        "parent_condition": condition,
        "destination": f"/key/truth/relationships/{decision.truth_relationship_index}/approved_evidence/0",
        "donor": f"/key/source_approval/relationships/{donor}/approved_evidence/0/supporting_text",
        "edge": list(edge),
        "replaced_source_id": decision.source_id,
        "derivative_sha256": commissioning.digest(corrected),
        "validation": {"original": QUOTE_SEMANTICS_ERROR, "derivative": "full adjudication validation passed"},
    }, corrected, review, receipt


def _verified_readings(runner: "SessionRunner", inputs: dict[str, str]) -> tuple[Reading, Reading]:
    raw, _, request = runner.committed_packet("blind", "reading-000-a-full", "annotation")
    first = Reading.model_validate(commissioning._read_json(raw))
    recovery = annotation_recovery.recorded(runner)
    if recovery is None or recovery["decision"]["reader_job"] != "reading-000-b-full":
        raise ValueError("Quote recovery requires the retained second-reading derivative.")
    second, _ = annotation_recovery.reopen(runner, recovery)
    if (Reading.model_validate_json(inputs["annotation_a"]) != first
            or Reading.model_validate_json(inputs["annotation_b"]) != second
            or inputs["sources"] != request["inputs"]["sources"]):
        raise ValueError("Quote recovery requires the exact inputs of both verified readings.")
    return first, second


def _local_key(review: Adjudication, condition: str) -> Adjudication:
    if review.key.condition != "local":
        raise ValueError("Quote recovery requires a condition-local adjudication.")
    return review.model_copy(update={"key": review.key.model_copy(update={"condition": condition})})


def _verify_original_failure(
    condition: str, review: Adjudication, sources: list[Source], agreement: dict[str, Any],
) -> None:
    try:
        science.verify_adjudication(condition, _local_key(review, condition), sources, agreement)
    except ValueError as error:
        if str(error) != QUOTE_SEMANTICS_ERROR:
            raise ValueError("The original does not reproduce its approved-quote mismatch.") from error
    else:
        raise ValueError("The original adjudication already passes.")


def _selected_quote(
    decision: AdjudicationQuoteRecovery, review: Adjudication, sources: list[Source],
    readings: tuple[Reading, Reading],
) -> tuple[int, tuple[str, str, str], str]:
    key = review.key
    index = decision.truth_relationship_index
    if index >= len(key.truth.relationships):
        raise ValueError("The approved truth relationship index is absent.")
    row = key.truth.relationships[index]
    if row.approved_evidence != [decision.source_id]:
        raise ValueError("The approved truth quote must be the single erroneous Source ID.")
    donors = [(i, item) for i, item in enumerate(key.source_approval.relationships)
              if _edge(item.source, item.type, item.target) == _edge(row.source, row.type, row.target)]
    if len(donors) != 1 or len(donors[0][1].approved_evidence) != 1:
        raise ValueError("The same edge must have one unambiguous Source-aware quote.")
    donor, entry = donors[0]
    pair = entry.approved_evidence[0]
    quote = pair.supporting_text
    source = next((item for item in sources if item.id == decision.source_id), None)
    start, stop = decision.source_quote_interval
    exact = quote.encode()
    if (source is None or pair.source_id != decision.source_id or stop > len(source.text.encode())
            or source.text.encode()[start:stop] != exact or source.text.encode().count(exact) != 1
            or commissioning.digest(exact) != decision.quote_sha256):
        raise ValueError("The donor quote must equal the authorised unique frozen byte span.")

    names = {entity.id: entity.name for entity in key.truth.entities}
    edge = _edge(names[row.source], row.type, names[row.target])
    proofs = [item for item in key.sufficient_evidence if _edge(*item.edge) == edge]
    attached = {(item.source_id, item.supporting_text) for item in key.ideal.relationships
                if _edge(item.source_name, item.relationship_type, item.target_name) == edge}
    if (len(proofs) != 1 or proofs[0].joint_only or proofs[0].alternatives != [[pair]]
            or attached != {(pair.source_id, quote)}
            or any(not attached <= science.check_reading(reading, sources).get(edge, set()) for reading in readings)):
        raise ValueError("The settled proof, ideal, and both blind readings must select that same single quote.")
    return donor, edge, quote


def _substitute(raw: bytes, parsed: dict[str, Any], decision: AdjudicationQuoteRecovery, quote: str) -> bytes:
    start, stop = decision.output_token_interval
    if stop > len(raw) or raw[start:stop] != commissioning.json_text(decision.source_id).encode():
        raise ValueError("The approved original byte interval must contain exactly the erroneous JSON string.")
    corrected = raw[:start] + commissioning.json_text(quote).encode() + raw[stop:]
    parsed["key"]["truth"]["relationships"][decision.truth_relationship_index]["approved_evidence"][0] = quote
    if commissioning._read_json(corrected) != parsed or commissioning.digest(corrected) != decision.derivative_sha256:
        raise ValueError("The substitution must change only the approved field and match the authorised derivative.")
    return corrected


def reopen(runner: "SessionRunner", record: dict[str, Any]) -> tuple[Adjudication, dict[str, Any]]:
    decision = AdjudicationQuoteRecovery.model_validate(record["decision"])
    expected, content, review, receipt = derive(runner, decision)
    if expected != record or content != artifacts.read_bytes(derivative_path(runner)):
        raise ValueError("The adjudication derivative differs from its committed lineage.")
    return review, receipt | {"mechanical_derivative_sha256": record["derivative_sha256"]}
