"""Additive source-attribution diagnostics, separate from approved-quote metrics."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from private_client_graph.evaluation import _edge
from private_client_graph.models import GroundTruth, RelationshipType
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source


class ApprovedSourceEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str
    supporting_text: str


class SourceEvidenceRelationship(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: str
    type: RelationshipType
    target: str
    approved_evidence: list[ApprovedSourceEvidence]


class SourceEvidenceApproval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    relationships: list[SourceEvidenceRelationship]


class AttributionFailure(BaseModel):
    edge: SemanticEdge
    evidence_id: str
    source_id: str
    supporting_text: str


class SourceAttributionDiagnostic(BaseModel):
    version: Literal['source_attribution_v1'] = 'source_attribution_v1'
    assessed: int = 0
    passed: int = 0
    failed: int = 0
    accuracy: float | None = None
    failures: list[AttributionFailure] = Field(default_factory=list)


def validate_source_approval(approval: SourceEvidenceApproval, truth: GroundTruth, sources: list[Source]) -> None:
    """Check a complete annotation mechanically; semantic approval stays with reviewers."""
    source_text = {source.id: source.text for source in sources}
    expected = {_edge(edge.source, edge.type, edge.target): set(edge.approved_evidence) for edge in truth.relationships}
    actual = {}
    for relationship in approval.relationships:
        key = _edge(relationship.source, relationship.type, relationship.target)
        if key in actual or key not in expected or not relationship.approved_evidence:
            raise ValueError('Source approvals require each ground-truth relationship exactly once')
        pairs = [(item.source_id, item.supporting_text) for item in relationship.approved_evidence]
        if len(set(pairs)) != len(pairs):
            raise ValueError('Duplicate approved Source/quote pair')
        for source_id, quote in pairs:
            if source_id not in source_text or not quote.strip() or quote not in source_text[source_id]:
                raise ValueError('Approved evidence must occur verbatim in its explicit Source')
            if quote not in expected[key]:
                raise ValueError('Source-aware approval must retain existing approved-quote semantics')
        if {quote for _, quote in pairs} != expected[key]:
            raise ValueError('Source approvals must cover every approved quote alternative')
        actual[key] = pairs
    if set(actual) != set(expected):
        raise ValueError('Source approvals must cover the complete ground truth')


def diagnose_source_attribution(state: CanonicalState, truth: GroundTruth,
                                approval: SourceEvidenceApproval) -> SourceAttributionDiagnostic:
    """Assess each attached Evidence association on TP edges; FP/FN stay separate."""
    from private_client_graph.canonical_state import validate_canonical_state
    validate_canonical_state(state)
    validate_source_approval(approval, truth, state.sources)
    names = {entity.id: entity.name for entity in truth.entities}
    approved = {
        _edge(names[edge.source], edge.type, names[edge.target]):
            {(item.source_id, item.supporting_text) for item in edge.approved_evidence}
        for edge in approval.relationships
    }
    names = {entity.id: entity.name for entity in state.entities}
    evidence = {item.id: item for item in state.evidence}
    diagnostic = SourceAttributionDiagnostic()
    for relationship in state.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        if edge not in approved:
            continue
        for identity in relationship.evidence_ids:
            item = evidence[identity]
            diagnostic.assessed += 1
            if (item.source_id, item.supporting_text) in approved[edge]:
                diagnostic.passed += 1
            else:
                diagnostic.failures.append(AttributionFailure(edge=edge, evidence_id=identity,
                    source_id=item.source_id, supporting_text=item.supporting_text))
    diagnostic.failed = diagnostic.assessed - diagnostic.passed
    diagnostic.accuracy = diagnostic.passed / diagnostic.assessed if diagnostic.assessed else None
    return diagnostic


def aggregate_source_attribution(diagnostics: list[SourceAttributionDiagnostic]) -> SourceAttributionDiagnostic:
    result = SourceAttributionDiagnostic(
        assessed=sum(item.assessed for item in diagnostics),
        passed=sum(item.passed for item in diagnostics),
        failed=sum(item.failed for item in diagnostics),
        failures=[failure for item in diagnostics for failure in item.failures])
    result.accuracy = result.passed / result.assessed if result.assessed else None
    return result
