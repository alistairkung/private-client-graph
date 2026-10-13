"""Join recorded evaluator outcomes to frozen Evidence; never rescore results."""
import hashlib
from typing import Literal
from private_client_graph.models.evaluation_result import SemanticEdge

from private_client_graph.evaluation import _edge
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.results import ResearchResult

from .contracts import EvidenceQuote, RelationshipOutcome


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _quote(identity: str, source_id: str, text: str, source: str) -> EvidenceQuote:
    occurrences = []
    start = source.find(text) if text else -1
    while start >= 0:
        occurrences.append((start, start + len(text)))
        start = source.find(text, start + 1)
    return EvidenceQuote(id=identity, source_id=source_id, text=text, occurrences=occurrences)


def relationship_outcomes(sample: ResearchInput, result: ResearchResult) -> list[RelationshipOutcome]:
    if result.evaluation is None:
        return []
    source_id = digest_text(sample.source)
    expected: dict[tuple, list[EvidenceQuote]] = {}
    names = {entity.id: entity.name for entity in sample.truth.entities}
    for relationship in sample.truth.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        for text in relationship.approved_evidence:
            quote = _quote(digest_text(source_id + text), source_id, text, sample.source)
            if quote not in expected.setdefault(edge, []):
                expected[edge].append(quote)

    predicted: dict[tuple, list[EvidenceQuote]] = {}
    if result.graph is not None:
        names = {entity.id: entity.name for entity in result.graph.entities}
        evidence = {item.id: item for item in result.graph.evidence}
        for predicted_relationship in result.graph.relationships:
            edge = _edge(names[predicted_relationship.source], predicted_relationship.type, names[predicted_relationship.target])
            for identity in predicted_relationship.evidence_ids:
                item = evidence[identity]
                quote = _quote(item.id, source_id, item.supporting_text, sample.source)
                if quote not in predicted.setdefault(edge, []):
                    predicted[edge].append(quote)

    evaluation = result.evaluation
    groups: list[tuple[Literal["missing", "extra", "provenance_failure", "matched"], list[SemanticEdge]]] = [
        ("missing", evaluation.false_negative_edges),
        ("extra", evaluation.false_positive_edges),
        ("provenance_failure", evaluation.provenance_failures),
        ("matched", evaluation.provenance_passes),
    ]
    return [RelationshipOutcome(
        id=digest_text(repr(edge)), edge=edge, outcome=outcome,
        expected=expected.get(edge, []), predicted=predicted.get(edge, []),
    ) for outcome, edges in groups for edge in edges]
