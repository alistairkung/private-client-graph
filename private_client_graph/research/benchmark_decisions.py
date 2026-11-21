"""Evaluation-only diagnostics for predeclared decisions on a complete sourced graph."""
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.evaluation import _edge, evaluate_graph
from private_client_graph.models import GroundTruth
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge

from .source_attribution import ApprovedSourceEvidence


class SufficientEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    edge: SemanticEdge
    alternatives: list[list[ApprovedSourceEvidence]] = Field(min_length=1)


class DecisionTargets(BaseModel):
    model_config = ConfigDict(extra='forbid')
    required: list[SemanticEdge] = Field(default_factory=list)
    forbidden: list[SemanticEdge] = Field(default_factory=list)
    unaffected: list[SemanticEdge] = Field(default_factory=list)
    sufficiency: list[SufficientEvidence] = Field(default_factory=list)


def _edges(items: Iterable[SemanticEdge]) -> set[SemanticEdge]:
    canonical = [_edge(*edge) for edge in items]
    result = set(canonical)
    if len(result) != len(canonical):
        raise ValueError('Duplicate annotated decision')
    return result


def _hits(targets: set[SemanticEdge], predicted: set[SemanticEdge]) -> dict[str, Any]:
    found = targets & predicted
    return dict(present=sorted(found), absent=sorted(targets - found), total=len(targets),
                fraction=len(found) / len(targets) if targets else None)


def diagnose(state: CanonicalState, truth: GroundTruth, labels: DecisionTargets) -> dict[str, Any]:
    """Evaluate only the Evidence attached to each named target; missed targets stay explicit."""
    score = evaluate_graph(reconstruct_graph(state), truth)
    expected = set(score.true_positive_edges) | set(score.false_negative_edges)
    required, forbidden, unaffected = (_edges(group) for group in (labels.required, labels.forbidden, labels.unaffected))
    annotated = _edges(item.edge for item in labels.sufficiency)
    if (required | unaffected | annotated) - expected or forbidden & expected:
        raise ValueError('Annotated decision disagrees with complete ground truth')

    attachments = _attached_evidence(state)
    predicted = set(attachments)
    source_text = {source.id: source.text for source in state.sources}
    complete = set()
    for item in labels.sufficiency:
        edge = _edge(*item.edge)
        alternatives = _validate_alternatives(item, source_text)
        if any(parts <= attached for attached in attachments.get(edge, []) for parts in alternatives):
            complete.add(edge)
    assessed = annotated & predicted
    return dict(required=_hits(required, predicted), forbidden=_hits(forbidden, predicted),
                unaffected=_hits(unaffected, predicted), sufficiency=dict(
                    planned=len(annotated), assessed=len(assessed), complete=sorted(complete),
                    incomplete=sorted(assessed - complete), missed=sorted(annotated - predicted),
                    accuracy=len(complete) / len(assessed) if assessed else None))


def _attached_evidence(state: CanonicalState) -> dict[SemanticEdge, list[set[tuple[str, str]]]]:
    names = {entity.id: entity.name for entity in state.entities}
    witnesses = {item.id: (item.source_id, item.supporting_text) for item in state.evidence}
    attachments: dict[SemanticEdge, list[set[tuple[str, str]]]] = {}
    for rel in state.relationships:
        key = _edge(names[rel.source], rel.type, names[rel.target])
        attachments.setdefault(key, []).append({witnesses[i] for i in rel.evidence_ids})
    return attachments


def _validate_alternatives(item: SufficientEvidence, source_text: dict[str, str]) -> list[set[tuple[str, str]]]:
    alternatives = []
    for group in item.alternatives:
        parts = {(quote.source_id, quote.supporting_text) for quote in group}
        if not parts or len(parts) != len(group):
            raise ValueError('Sufficient sets require distinct, nonempty evidence')
        for source_id, text in parts:
            if not text.strip() or source_id not in source_text or text not in source_text[source_id]:
                raise ValueError('Sufficient evidence must occur verbatim in the identified Source')
        alternatives.append(parts)
    return alternatives
