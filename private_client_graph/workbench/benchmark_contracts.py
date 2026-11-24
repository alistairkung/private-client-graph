"""Read-only, typed projection of Benchmark v3 protocol results."""

from dataclasses import asdict
from typing import Literal
from hashlib import sha256
import hashlib

from pydantic import BaseModel, ConfigDict, Field, computed_field

from benchmark_v3.evaluation_protocol import (
    ConditionResult, EvaluationScope, Metrics, Outcome, ProtocolResult,
)
from private_client_graph.models import EvaluationResult, GroundTruth, SourcedExtractionResult
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.relationship import Relationship
from private_client_graph.models.sourced_evidence import SourcedEvidence
from private_client_graph.models.source import Source
from private_client_graph.research.retained_inputs import value_digest
from .contracts import EvidenceQuote
from .contracts import RelationshipOutcome
from private_client_graph.evaluation import _edge
from benchmark_v3.replay_evidence import assess_evidence
from benchmark_v3.retained_evaluation import VerifiedBaseline


class ProofMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    text: str
    attached: bool
    occurrences: list[tuple[int, int]] = Field(default_factory=list)


class ProofAlternative(BaseModel):
    model_config = ConfigDict(frozen=True)

    members: list[ProofMember]


class ProofTarget(BaseModel):
    model_config = ConfigDict(frozen=True)

    edge: SemanticEdge
    joint_only: bool
    status: Literal['complete', 'incomplete', 'missed', 'without_graph']
    alternatives: list[ProofAlternative]


class ExpectedRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    edge: SemanticEdge
    quotes: list[EvidenceQuote] = Field(default_factory=list)


class ConditionMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    tp: int
    fp: int
    fn: int
    planned_proofs: int
    complete_proofs: int
    planned_joint_proofs: int
    complete_joint_proofs: int
    incomplete_proofs: int
    missed_proofs: int
    quote_passed: int
    quote_assessed: int
    attribution_passed: int
    attribution_assessed: int


class BenchmarkCondition(BaseModel):
    model_config = ConfigDict(frozen=True)

    family: str
    condition: str
    contrast: str | None = None
    role: str | None = None
    outcome: Outcome
    expected: CanonicalState
    expected_edges: int
    parsed_prediction: SourcedExtractionResult | None = None
    expected_relationships: list[ExpectedRelationship] = Field(default_factory=list)
    graph: EvaluationResult | None = None
    proof_targets: list[ProofTarget] = Field(default_factory=list)
    metrics: ConditionMetrics
    failure_detail: str | None = None


class BenchmarkRun(BaseModel):
    """Protocol result attached to a Workbench Run; never grants execution authority."""

    model_config = ConfigDict(frozen=True)

    scope: EvaluationScope
    cohort: Metrics
    families: dict[str, Metrics]
    family_macro_f1: float
    valid_graph_only_family_macro_f1: float | None
    valid_graph_only_macro_family_count: int
    run_artifact_digest: str | None = None
    observations: list[BenchmarkCondition]

    @computed_field
    @property
    def scope_identity(self) -> str:
        return value_digest(asdict(self.scope))

    @classmethod
    def from_verified(cls, verified: VerifiedBaseline) -> 'BenchmarkRun':
        return cls(
            scope=verified.protocol.scope,
            cohort=verified.protocol.cohort,
            families=verified.protocol.families,
            family_macro_f1=verified.protocol.family_macro_f1,
            valid_graph_only_family_macro_f1=verified.protocol.valid_graph_only_family_macro_f1,
            valid_graph_only_macro_family_count=verified.protocol.valid_graph_only_macro_family_count,
            run_artifact_digest=verified.protocol.run_artifact_sha256,
            observations=[_condition_projection(item, verified) for item in verified.planned],
        )

    def as_protocol_result(self) -> ProtocolResult:
        """Adapt the projection to the protected compatibility guard's value type."""
        conditions = {
            row.condition: ConditionResult(
                family=row.family,
                condition=row.condition,
                outcome=row.outcome,
                expected_edges=row.expected_edges,
                planned_proofs=row.metrics.planned_proofs,
                planned_joint_proofs=row.metrics.planned_joint_proofs,
                graph=row.graph,
                complete_proofs=row.metrics.complete_proofs,
                complete_joint_proofs=row.metrics.complete_joint_proofs,
                incomplete_proofs=row.metrics.incomplete_proofs,
                missed_proofs=row.metrics.missed_proofs,
                quote_passed=row.metrics.quote_passed,
                quote_assessed=row.metrics.quote_assessed,
                attribution_passed=row.metrics.attribution_passed,
                attribution_assessed=row.metrics.attribution_assessed,
                failure_detail=row.failure_detail,
            )
            for row in self.observations
        }
        return ProtocolResult(
            scope=self.scope,
            conditions=conditions,
            cohort=self.cohort,
            families=self.families,
            family_macro_f1=self.family_macro_f1,
            valid_graph_only_family_macro_f1=self.valid_graph_only_family_macro_f1,
            valid_graph_only_macro_family_count=self.valid_graph_only_macro_family_count,
            run_artifact_sha256=self.run_artifact_digest,
        )


def condition_metrics(result: ConditionResult) -> ConditionMetrics:
    graph = result.graph
    return ConditionMetrics(
        tp=graph.tp if graph else 0,
        fp=graph.fp if graph else 0,
        fn=graph.fn if graph else result.expected_edges,
        planned_proofs=result.planned_proofs,
        complete_proofs=result.complete_proofs,
        planned_joint_proofs=result.planned_joint_proofs,
        complete_joint_proofs=result.complete_joint_proofs,
        incomplete_proofs=result.incomplete_proofs,
        missed_proofs=result.missed_proofs,
        quote_passed=result.quote_passed,
        quote_assessed=result.quote_assessed,
        attribution_passed=result.attribution_passed,
        attribution_assessed=result.attribution_assessed,
    )


def condition_relationship_outcomes(condition: BenchmarkCondition,
                                    result: EvaluationResult | None,
                                    state: CanonicalState | None) -> list[RelationshipOutcome]:
    if result is None:
        return [RelationshipOutcome(
            id=hashlib.sha256(repr(row.edge).encode()).hexdigest(), edge=row.edge,
            outcome='missing', expected=row.quotes, predicted=[],
        ) for row in condition.expected_relationships]
    expected = {row.edge: row.quotes for row in condition.expected_relationships}
    predicted = _predicted_quotes(state) if state else {}
    failures = set(result.provenance_failures)
    matched = set(result.true_positive_edges)
    outcomes: list[tuple[Literal['missing', 'extra', 'matched', 'provenance_failure'], SemanticEdge]] = [
        ('missing', edge) for edge in result.false_negative_edges
    ] + [
        ('extra', edge) for edge in result.false_positive_edges
    ] + [
        ('provenance_failure' if edge in failures else 'matched', edge)
        for edge in sorted(matched)
    ]
    return [RelationshipOutcome(
        id=hashlib.sha256(repr(edge).encode()).hexdigest(), edge=edge, outcome=outcome,
        expected=expected.get(edge, []), predicted=predicted.get(edge, []),
    ) for outcome, edge in outcomes]


def _condition_projection(item, verified: VerifiedBaseline) -> BenchmarkCondition:
    saved = item.frozen.saved
    result = verified.protocol.conditions[saved.condition]
    original = verified.original_results[saved.condition]
    expected = _expected_state(item.frozen.sources, saved.truth, saved.source_approval)
    predicted = original.state
    attachments = _attachments(predicted) if predicted else {}
    proof_by_edge = {_edge(*row.edge): row for row in saved.sufficient_evidence}
    proof_status = {}
    if predicted:
        scored = assess_evidence(predicted, saved)['sufficiency']['targets']
        proof_status = {_edge(*row['edge']): row['status'] for row in scored}
    targets = []
    for edge, annotation in sorted(proof_by_edge.items()):
        edge_attachments = attachments.get(edge, set())
        alternatives = [
            ProofAlternative(members=[
                _proof_member(source_id, text, edge_attachments, item.frozen.sources)
                for source_id, text in sorted({(quote.source_id, quote.supporting_text) for quote in group})
            ])
            for group in annotation.alternatives
        ]
        targets.append(ProofTarget(edge=edge, joint_only=annotation.joint_only,
            status=proof_status.get(edge, 'without_graph'), alternatives=alternatives))
    family = verified.family_details[item.family]
    natural_condition = next(iter(family.conditions))
    contrast = _contrast_label(item.family, saved.condition, family, natural_condition)
    return BenchmarkCondition(
        family=item.family, condition=saved.condition,
        contrast=contrast,
        role='natural' if saved.condition == natural_condition else 'matched',
        outcome=result.outcome, expected=expected, expected_edges=result.expected_edges,
        parsed_prediction=original.sourced_extraction,
        expected_relationships=_expected_relationships(item.frozen.sources, saved.truth,
                                                       saved.source_approval),
        graph=result.graph,
        proof_targets=targets, metrics=condition_metrics(result),
        failure_detail=result.failure_detail,
    )


def _contrast_label(family_id: str, condition: str, family, natural_condition: str) -> str:
    if condition == natural_condition:
        return f'{family_id} natural condition'
    if condition in family.edits:
        edit = family.edits[condition]
        return f'Precommitted literal change in Source {edit.source_id}'
    natural_sources = family.conditions[natural_condition].sources
    current_sources = family.conditions[condition].sources
    if ({source.id: source for source in natural_sources}
            == {source.id: source for source in current_sources}
            and natural_sources != current_sources):
        return f'Precommitted Source order permutation from {natural_condition}'
    natural_required = set(family.required.get(natural_condition, []))
    current_required = set(family.required.get(condition, []))
    changed = sorted(natural_required ^ current_required)
    if changed:
        rendered = ', '.join(f'{source} — {relationship} → {target}'
                             for source, relationship, target in changed)
        return f'Precommitted relationship contrast from {natural_condition}: {rendered}'
    return f'Precommitted matched variant from {natural_condition}'


def _expected_state(sources: list[Source], truth: GroundTruth, approval) -> CanonicalState:
    evidence_ids: dict[tuple[str, str], str] = {}
    evidence = []
    relationships = []
    approvals = {
        _edge(row.source, row.type, row.target): row.approved_evidence
        for row in approval.relationships
    }
    for row in truth.relationships:
        edge = _edge(row.source, row.type, row.target)
        ids = []
        for quote in approvals.get(edge, []):
            pair = (quote.source_id, quote.supporting_text)
            identity = evidence_ids.get(pair)
            if identity is None:
                identity = 'benchmark_expected_' + sha256(repr(pair).encode()).hexdigest()[:16]
                evidence_ids[pair] = identity
                source = next(source for source in sources if source.id == quote.source_id)
                evidence.append(SourcedEvidence(id=identity, document=source.title,
                    source_id=quote.source_id, supporting_text=quote.supporting_text))
            ids.append(identity)
        relationships.append(Relationship(source=row.source, type=row.type,
            target=row.target, evidence_ids=ids))
    return CanonicalState(sources=sources, entities=truth.entities,
        relationships=relationships, evidence=evidence)


def _attachments(state: CanonicalState) -> dict[tuple[str, str, str], set[tuple[str, str]]]:
    names = {entity.id: entity.name for entity in state.entities}
    evidence = {row.id: (row.source_id, row.supporting_text) for row in state.evidence}
    return {
        _edge(names[row.source], row.type, names[row.target]): {evidence[key] for key in row.evidence_ids}
        for row in state.relationships
    }


def _predicted_quotes(state: CanonicalState) -> dict[tuple[str, str, str], list[EvidenceQuote]]:
    sources = {source.id: source.text for source in state.sources}
    evidence = {row.id: row for row in state.evidence}
    names = {entity.id: entity.name for entity in state.entities}
    quotes: dict[tuple[str, str, str], list[EvidenceQuote]] = {}
    for relationship in state.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        for identity in relationship.evidence_ids:
            row = evidence[identity]
            text = row.supporting_text
            source_text = sources[row.source_id]
            occurrences = []
            position = source_text.find(text)
            while position >= 0:
                occurrences.append((position, position + len(text)))
                position = source_text.find(text, position + 1)
            quote = EvidenceQuote(id=identity, source_id=row.source_id, text=text,
                                  occurrences=occurrences)
            if quote not in quotes.setdefault(edge, []):
                quotes[edge].append(quote)
    return quotes


def _proof_member(source_id: str, text: str, attached: set[tuple[str, str]], sources: list[Source]) -> ProofMember:
    source = next((row for row in sources if row.id == source_id), None)
    occurrences = []
    if source is not None:
        position = source.text.find(text)
        while position >= 0:
            occurrences.append((position, position + len(text)))
            position = source.text.find(text, position + 1)
    return ProofMember(source_id=source_id, text=text, attached=(source_id, text) in attached,
                       occurrences=occurrences)


def _expected_relationships(sources: list[Source], truth: GroundTruth, approval) -> list[ExpectedRelationship]:
    names = {entity.id: entity.name for entity in truth.entities}
    approvals = {
        _edge(names[row.source], row.type, names[row.target]): row.approved_evidence
        for row in approval.relationships
    }
    expected = []
    for relationship in truth.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        quotes = []
        for item in approvals.get(edge, []):
            source = next(source for source in sources if source.id == item.source_id)
            occurrences = []
            position = source.text.find(item.supporting_text)
            while position >= 0:
                occurrences.append((position, position + len(item.supporting_text)))
                position = source.text.find(item.supporting_text, position + 1)
            identity = hashlib.sha256(repr((item.source_id, item.supporting_text)).encode()).hexdigest()
            quotes.append(EvidenceQuote(id=identity, source_id=item.source_id,
                text=item.supporting_text, occurrences=occurrences))
        expected.append(ExpectedRelationship(edge=edge, quotes=quotes))
    return expected
