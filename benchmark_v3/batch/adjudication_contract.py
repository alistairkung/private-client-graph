"""Explicit output keys for a condition-local adjudication."""

from typing import TYPE_CHECKING, Any

from benchmark_v3.batch.contracts import Adjudication
from benchmark_v3.batch.read_format_recovery import exact_whitespace_span
from benchmark_v3.commissioning import json_text
from private_client_graph.evaluation import _edge
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner


RELEASE_JOBS = {
    "fresh_adjudication": "adjudicate-000-fresh",
    "complete_evidence_adjudication": "adjudicate-000-evidence",
}
SOURCE_APPROVAL_FAILURE = "Source approvals require each ground-truth relationship exactly once"
SOURCE_APPROVAL_QUOTE_FAILURE = "Source-aware approval must retain existing approved-quote semantics"
COMPLETE_EVIDENCE_INSTRUCTIONS = (
    " Before submitting, check the entire key, including agreed edges. "
    "key.ideal.relationships must represent every edge in key.truth.relationships and attach exact "
    "Source ID and verbatim quotation pairs to those same edges. "
    "For each ordinary-eligible edge use matching nonempty truth approved_evidence and "
    "source_approval approved_evidence. For a genuinely joint-only edge, keep that truth edge with "
    "empty ordinary approved_evidence and omit its row from source_approval entirely. "
    "Keep it in the ideal and attach every pair from at least one of its complete sufficient "
    "alternatives to that edge, using multiple candidate rows where needed. "
    "A declaration in sufficient_evidence does not attach evidence to the ideal."
)


def resolution_ids(disagreements: list[SemanticEdge]) -> list[str]:
    ids = sorted(json_text(edge) for edge in disagreements)
    if len(ids) != len(set(ids)):
        raise ValueError("Adjudication requires unique disagreement IDs.")
    return ids


def output_schema(ids: list[str], *, complete_evidence: bool = False) -> dict[str, Any]:
    schema = Adjudication.model_json_schema()
    schema["properties"]["disagreement_resolutions"] = {
        "type": "object",
        "properties": {key: {"type": "string", "minLength": 1} for key in ids},
        "required": ids,
        "additionalProperties": False,
        "minProperties": len(ids),
        "maxProperties": len(ids),
    }
    if complete_evidence:
        definitions = schema["$defs"]
        definitions["SourceEvidenceRelationship"]["properties"]["approved_evidence"]["minItems"] = 1
        definitions["SourceEvidenceApproval"]["required"] = ["relationships"]
        definitions["SufficientEvidence"]["properties"]["alternatives"]["items"]["minItems"] = 1
    return schema


LOCAL_APPROVAL_IDS = (
    " In key.source_approval.relationships use the exact local entity IDs from key.truth for source and target. "
    "Keep full canonical names in key.ideal.relationships and in sufficient_evidence edge triples."
)


def localize_source_approval(review: Adjudication) -> tuple[Adjudication, list[dict[str, Any]]]:
    """Resolve exact display representations using only the adjudicator’s own committed data."""
    names: dict[str, list[str]] = {}
    known_ids = {entity.id for entity in review.key.truth.entities}
    for entity in review.key.truth.entities:
        names.setdefault(entity.name, []).append(entity.id)
    changes: list[dict[str, Any]] = []
    relationships = []
    for index, relationship in enumerate(review.key.source_approval.relationships):
        endpoints = {"source": relationship.source, "target": relationship.target}
        for field, value in endpoints.items():
            if value in known_ids:
                continue
            matches = names.get(value, [])
            if len(matches) != 1:
                raise ValueError("An adjudicated approval endpoint does not name a unique local entity.")
            endpoints[field] = matches[0]
            changes.append({"path": f"/key/source_approval/relationships/{index}/{field}",
                            "before": value, "after": matches[0]})
        relationships.append(relationship.model_copy(update=endpoints))
    by_edge = {_edge(row.source, row.type, row.target): row.approved_evidence for row in relationships}
    truth_rows = []
    if len(by_edge) != len(relationships):
        raise ValueError("Repeated approval identities cannot be repaired as representation.")
    for index, row in enumerate(review.key.truth.relationships):
        evidence = by_edge.get(_edge(row.source, row.type, row.target), [])
        source_ids = {item.source_id for item in evidence}
        texts = list(dict.fromkeys(item.supporting_text for item in evidence))
        if (row.approved_evidence and len(row.approved_evidence) == len(source_ids)
                and set(row.approved_evidence) == source_ids and not source_ids.intersection(texts)):
            changes.append({"path": f"/key/truth/relationships/{index}/approved_evidence",
                            "before": row.approved_evidence, "after": texts})
            row = row.model_copy(update={"approved_evidence": texts})
        truth_rows.append(row)
    if not changes:
        return review, []
    approval = review.key.source_approval.model_copy(update={"relationships": relationships})
    truth = review.key.truth.model_copy(update={"relationships": truth_rows})
    return review.model_copy(update={"key": review.key.model_copy(update={"source_approval": approval, "truth": truth})}), changes


TRUTH_QUOTATIONS = (
    " In key.truth.relationships, approved_evidence contains verbatim quotation strings, not Source IDs. "
    "The same quotation strings appear verbatim in the Source-aware approval, with their named Source IDs there."
)


KEY_REPLAY_FAILURE = "Provisional key fails canonical replay or the existing evidence policies."
PROOF_RETRY = "independent-proof-retry-"
QUOTE_RECOVERY = "adjudication-whitespace-"


def proof_retry(runner: "SessionRunner", job: str) -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", PROOF_RETRY + job)), None)


def quote_recovery(runner: "SessionRunner", job: str) -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", QUOTE_RECOVERY + job)), None)


def exact_whitespace_key(review: Adjudication, sources: list[Source]) -> tuple[Adjudication, list[dict[str, Any]]]:
    """Normalize uniquely attributable whitespace without changing the independent key's substance."""
    body = {source.id: source.text for source in sources}
    key = review.key.model_dump(mode="json")
    edits: list[dict[str, Any]] = []
    approved: dict[tuple[SemanticEdge, str], set[str]] = {}

    def quote(pair: dict[str, str], path: str) -> tuple[str, str]:
        original = pair["supporting_text"]
        if pair["source_id"] not in body:
            raise ValueError("Exact quotation recovery cannot change Source attribution.")
        repaired = (original if original in body[pair["source_id"]]
                    else exact_whitespace_span(original, body[pair["source_id"]]))
        if repaired != original:
            edits.append({"path": path, "source_id": pair["source_id"], "before": original, "after": repaired})
            pair["supporting_text"] = repaired
        return original, repaired

    for index, row in enumerate(key["ideal"]["relationships"]):
        quote(row, f"/ideal/relationships/{index}/supporting_text")
    for index, row in enumerate(key["source_approval"]["relationships"]):
        edge = _edge(row["source"], row["type"], row["target"])
        for number, pair in enumerate(row["approved_evidence"]):
            original, repaired = quote(pair, f"/source_approval/relationships/{index}/approved_evidence/{number}/supporting_text")
            approved.setdefault((edge, original), set()).add(repaired)
    for index, row in enumerate(key["sufficient_evidence"]):
        for alternative, group in enumerate(row["alternatives"]):
            for number, pair in enumerate(group):
                quote(pair, f"/sufficient_evidence/{index}/alternatives/{alternative}/{number}/supporting_text")
        row["alternatives"] = _retain_minimal_sets(row["alternatives"], index, edits)
    for index, row in enumerate(key["truth"]["relationships"]):
        edge = _edge(row["source"], row["type"], row["target"])
        for number, original in enumerate(row["approved_evidence"]):
            choices = approved.get((edge, original), {original})
            if len(choices) != 1:
                raise ValueError("A truth quotation needs one exact replacement in its approved Sources.")
            restored, = choices
            if restored != original:
                path = f"/truth/relationships/{index}/approved_evidence/{number}"
                edits.append({"path": path, "before": original, "after": restored})
                row["approved_evidence"][number] = restored
    return Adjudication.model_validate(review.model_dump(mode="json") | {"key": key}), edits


def _retain_minimal_sets(
    alternatives: list[list[dict[str, str]]], index: int, edits: list[dict[str, Any]],
) -> list[list[dict[str, str]]]:
    # A strict superset cannot be a second minimum when its exact subset was already approved.
    sets = [{(pair["source_id"], pair["supporting_text"]) for pair in group} for group in alternatives]
    retained = []
    for position, group in enumerate(alternatives):
        contained = next((other for other, proof in enumerate(sets)
                          if proof < sets[position] or (other < position and proof == sets[position])), None)
        if contained is None or not sets[contained] or len(sets[position]) != len(group):
            retained.append(group)
        else:
            edits.append({"path": f"/sufficient_evidence/{index}/alternatives/{position}",
                          "before": group, "covered_by_existing_alternative": contained})
    return retained


def localize_key_presentation(review: Adjudication) -> tuple[Adjudication, list[dict[str, Any]]]:
    """Apply exact local-ID presentation repairs without adding facts or evidence."""
    localized, edits = localize_source_approval(review)
    key = localized.key
    names = {entity.id: entity.name for entity in key.truth.entities}
    displayed = set(names.values())
    relationships = []
    for index, row in enumerate(key.ideal.relationships):
        endpoints = {
            field: names.get(value, value) if value not in displayed else value
            for field, value in (("source_name", row.source_name), ("target_name", row.target_name))
        }
        changed = {field: value for field, value in endpoints.items() if value != getattr(row, field)}
        if changed:
            edge = _edge(endpoints["source_name"], row.relationship_type, endpoints["target_name"])
            if (any(list(names.values()).count(name) != 1 for name in changed.values())
                    or not _already_approved_exact_pair(localized, edge, row.source_id, row.supporting_text, names)):
                raise ValueError("An ideal endpoint can be relabelled only against its uniquely approved exact evidence.")
            edits.extend({
                "path": f"/key/ideal/relationships/{index}/{field}", "before": getattr(row, field), "after": value,
            } for field, value in changed.items())
            row = row.model_copy(update=changed)
        relationships.append(row)
    if relationships == key.ideal.relationships:
        return localized, edits
    corrected = key.model_copy(update={"ideal": key.ideal.model_copy(update={"relationships": relationships})})
    return localized.model_copy(update={"key": corrected}), edits


def _already_approved_exact_pair(
    review: Adjudication, edge: SemanticEdge, source_id: str, quote: str, names: dict[str, str],
) -> bool:
    from benchmark_v3.replay_manifest import truth_edges

    if edge not in truth_edges(review.key.truth):
        return False
    ordinary = (
        reference for row in review.key.source_approval.relationships
        if _edge(names[row.source], row.type, names[row.target]) == edge
        for reference in row.approved_evidence
    )
    sufficient = (
        reference for row in review.key.sufficient_evidence if _edge(*row.edge) == edge
        for alternative in row.alternatives for reference in alternative
    )
    return any((reference.source_id, reference.supporting_text) == (source_id, quote)
               for reference in (*ordinary, *sufficient))
