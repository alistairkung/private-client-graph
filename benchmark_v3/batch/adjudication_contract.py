"""Explicit output keys for a condition-local adjudication."""

from typing import Any

from benchmark_v3.batch.contracts import Adjudication
from benchmark_v3.commissioning import json_text
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
