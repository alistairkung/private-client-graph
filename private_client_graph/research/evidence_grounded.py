"""Versioned quality projection over verified semantic-edge and proof counts."""
from collections import Counter
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel

from benchmark_v3.evaluation_protocol import ConditionResult, GraphCounts


class RelationshipScore(BaseModel):
    counts: GraphCounts
    precision: float
    recall: float
    f1: float


class ProofRate(BaseModel):
    complete: int
    targets: int
    rate: float | None


class QualityProjection(BaseModel):
    version: Literal['evidence_grounded_f1_v1'] = 'evidence_grounded_f1_v1'
    planned_inputs: int
    observed_inputs: int
    qualified_inputs: int
    observed_qualified_inputs: int
    outcomes: dict[str, int]
    input_outcomes: dict[str, str]
    graph: RelationshipScore | None
    qualified_graph: RelationshipScore | None
    grounded: RelationshipScore | None
    complete_proof: ProofRate
    joint_only_proof: ProofRate


def project_quality(qualified: Iterable[ConditionResult], *,
                    other: Iterable[ConditionResult] = (),
                    processing: Iterable[str] = ()) -> QualityProjection:
    """Measure terminal observations and preserve coverage separately."""
    qualified, other = list(qualified), list(other)
    processing = set(processing)
    rows = [*qualified, *other]
    input_outcomes = {
        row.condition: 'processing' if row.outcome == 'not_attempted' and row.condition in processing else row.outcome
        for row in rows
    }
    measured = [row for row in rows if row.outcome != 'not_attempted']
    observed = [row for row in qualified if row.outcome != 'not_attempted']
    graph = _graph_counts(observed)
    complete = sum(row.complete_proofs for row in observed)
    if any(row.complete_proofs > (row.graph.tp if row.graph else 0) for row in observed):
        raise ValueError('Complete proofs must belong to distinct correct semantic edges')
    insufficient = graph.tp - complete
    grounded = GraphCounts(complete, graph.fp + insufficient, graph.fn + insufficient)
    return QualityProjection(
        planned_inputs=len(rows), observed_inputs=len(measured),
        qualified_inputs=len(qualified), observed_qualified_inputs=len(observed),
        outcomes=dict(Counter(input_outcomes.values())), input_outcomes=input_outcomes,
        graph=_score(_graph_counts(measured)) if measured else None,
        qualified_graph=_score(graph) if observed else None,
        grounded=_score(grounded) if observed else None,
        complete_proof=_proof_rate(complete, sum(row.planned_proofs for row in observed)),
        joint_only_proof=_proof_rate(sum(row.complete_joint_proofs for row in observed),
                                    sum(row.planned_joint_proofs for row in observed)),
    )


def _graph_counts(rows: list[ConditionResult]) -> GraphCounts:
    return GraphCounts(
        sum(row.graph.tp for row in rows if row.graph is not None),
        sum(row.graph.fp for row in rows if row.graph is not None),
        sum(row.graph.fn if row.graph is not None else row.expected_edges for row in rows),
    )


def _score(counts: GraphCounts) -> RelationshipScore:
    predicted, expected = counts.tp + counts.fp, counts.tp + counts.fn
    return RelationshipScore(counts=counts, precision=counts.tp / predicted if predicted else 0.0,
        recall=counts.tp / expected if expected else 0.0, f1=counts.f1)


def _proof_rate(complete: int, targets: int) -> ProofRate:
    return ProofRate(complete=complete, targets=targets, rate=complete / targets if targets else None)
