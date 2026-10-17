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
    expected = _expected_quotes(sample, result)
    predicted = _predicted_quotes(sample, result)

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


def _expected_quotes(sample: ResearchInput, result: ResearchResult) -> dict[tuple, list[EvidenceQuote]]:
    names = {entity.id: entity.name for entity in sample.truth.entities}
    sourced = result.state is not None and sample.source_evidence is not None
    relationships = sample.source_evidence.relationships if sourced else sample.truth.relationships
    sources = {source.id: source.text for source in sample.sources or []}
    legacy_source_id = digest_text(sample.source)
    expected: dict[tuple, list[EvidenceQuote]] = {}
    for relationship in relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        pairs = ([(item.source_id, item.supporting_text) for item in relationship.approved_evidence]
                 if sourced else [(legacy_source_id, text) for text in relationship.approved_evidence])
        for source_id, text in pairs:
            source = sources[source_id] if sourced else sample.source
            identity = digest_text(repr((source_id, text))) if sourced else digest_text(source_id + text)
            quote = _quote(identity, source_id, text, source)
            if quote not in expected.setdefault(edge, []):
                expected[edge].append(quote)
    return expected


def _predicted_quotes(sample: ResearchInput, result: ResearchResult) -> dict[tuple, list[EvidenceQuote]]:
    graph = result.state if result.state is not None else result.graph
    if graph is None:
        return {}
    names = {entity.id: entity.name for entity in graph.entities}
    evidence = {item.id: item for item in graph.evidence}
    sources = {source.id: source.text for source in result.state.sources} if result.state else {}
    legacy_source_id = digest_text(sample.source)
    predicted: dict[tuple, list[EvidenceQuote]] = {}
    for relationship in graph.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        for identity in relationship.evidence_ids:
            item = evidence[identity]
            source_id = item.source_id if result.state is not None else legacy_source_id
            source = sources[source_id] if result.state is not None else sample.source
            quote = _quote(item.id, source_id, item.supporting_text, source)
            if quote not in predicted.setdefault(edge, []):
                predicted[edge].append(quote)
    return predicted
