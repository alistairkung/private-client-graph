"""Explicit output keys for a condition-local adjudication."""

from typing import Any

from benchmark_v3.batch.contracts import Adjudication
from benchmark_v3.commissioning import json_text
from private_client_graph.evaluation import _edge
from private_client_graph.models.evaluation_result import SemanticEdge


RELEASE_JOBS = {
    "fresh_adjudication": "adjudicate-000-fresh",
    "complete_evidence_adjudication": "adjudicate-000-evidence",
}
SOURCE_APPROVAL_FAILURE = "Source approvals require each ground-truth relationship exactly once"
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
