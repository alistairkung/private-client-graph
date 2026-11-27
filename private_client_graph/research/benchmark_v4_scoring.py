"""Graph delivery across mixed references, with separate evidence contracts."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from benchmark_v3.evaluation_protocol import (
    ConditionResult, GraphCounts, Outcome, ProtocolResult, UnavailablePrediction, evaluate_protocol,
)
from private_client_graph.evaluation import _edge, evaluate_graph
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.pipeline import Pipeline, PipelineConfig, PipelineExecutionError
from .benchmark_v4 import BenchmarkWorkload

Prediction = SourcedExtractionResult | UnavailablePrediction
ObservationOrigin = Literal['live', 'offline_fixture']


class DeliveredGraphMetrics(BaseModel):
    inputs: int
    valid_graphs: int
    without_graph: int
    exact_graphs: int
    counts: GraphCounts
    precision: float
    recall: float
    f1: float
    outcomes: dict[Outcome, int]


class ConsensusEvidenceDiagnostics(BaseModel):
    adjudicated_relationships: int
    reference_citations: int
    matched_citations: int | None
    assessed: bool


class BenchmarkV4Summary(BaseModel):
    scope_sha256: str
    scoring_sha256: str | None = None
    observation_origin: ObservationOrigin
    state: Literal['unmeasured', 'provisional', 'complete']
    combined: DeliveredGraphMetrics | None
    qualified: DeliveredGraphMetrics | None
    consensus: DeliveredGraphMetrics | None
    by_matter: dict[str, DeliveredGraphMetrics]
    consensus_evidence: ConsensusEvidenceDiagnostics


@dataclass(frozen=True)
class MixedEvaluation:
    qualified: ProtocolResult
    consensus: ConditionResult
    summary: BenchmarkV4Summary


def evaluate_benchmark_v4(
    workload: BenchmarkWorkload,
    predictions: Mapping[str, Prediction],
    *,
    observation_origin: ObservationOrigin,
    complete: bool = False,
) -> MixedEvaluation:
    """Compare one observation per input, pooling edge counts across the full roster."""
    roster = workload.roster
    u8 = roster.definition.consensus
    if set(predictions) - {item.id for item in roster.inputs}:
        raise ValueError('Predictions contain inputs outside the Benchmark v4 roster')
    protocol = evaluate_protocol(workload.qualified,
        {identity: prediction for identity, prediction in predictions.items() if identity != u8.input},
        benchmark_sha256=roster.definition.qualified.private_register_sha256,
        observation_origin=observation_origin)
    consensus, evidence = _score_consensus(workload, predictions.get(u8.input, UnavailablePrediction('not_attempted')))
    qualified = list(protocol.conditions.values())
    measured = any(not isinstance(value, UnavailablePrediction) or value.outcome != 'not_attempted'
                   for value in predictions.values())
    complete = complete and all(row.outcome != 'not_attempted' for row in [*qualified, consensus])
    summary = BenchmarkV4Summary(scope_sha256=roster.sha256,
        observation_origin=observation_origin,
        state=('complete' if complete else 'provisional') if measured else 'unmeasured',
        combined=_delivered([*qualified, consensus]) if measured else None,
        qualified=_delivered(qualified) if measured else None,
        consensus=_delivered([consensus]) if consensus.outcome != 'not_attempted' else None,
        by_matter={
            matter: _delivered([row for row in [*qualified, consensus] if row.family == matter])
            for matter in dict.fromkeys(item.matter for item in roster.inputs)
        } if measured else {},
        consensus_evidence=evidence)
    return MixedEvaluation(protocol, consensus, summary)


def _score_consensus(
    workload: BenchmarkWorkload, prediction: Prediction,
) -> tuple[ConditionResult, ConsensusEvidenceDiagnostics]:
    sample = workload.inputs[-1]
    u8 = workload.roster.definition.consensus
    expected = _edge_citations(workload.consensus_state)
    diagnostic = ConsensusEvidenceDiagnostics(adjudicated_relationships=len(sample.truth.relationships),
        reference_citations=len(expected), matched_citations=None, assessed=False)
    dimensions = (u8.matter, u8.input)
    size = len(sample.truth.relationships)
    if isinstance(prediction, UnavailablePrediction):
        return ConditionResult(*dimensions, prediction.outcome, size, 0, 0,
                               failure_detail=prediction.error_type), diagnostic
    assert sample.sources is not None
    try:
        result = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, prediction)
    except PipelineExecutionError as error:
        if error.stage != 'graph' or not isinstance(error.__cause__, ValueError):
            raise
        return ConditionResult(*dimensions, 'validation_failure', size, 0, 0,
                               failure_detail=str(error.__cause__)), diagnostic

    graph = evaluate_graph(result.graph, sample.truth)
    diagnostic.assessed = True
    diagnostic.matched_citations = len(expected & _edge_citations(result.state))
    return ConditionResult(*dimensions, 'scored', size, 0, 0, graph=graph), diagnostic


def _edge_citations(state: CanonicalState) -> set[tuple[tuple[str, str, str], str, str]]:
    names = {entity.id: entity.name for entity in state.entities}
    quotes = {item.id: item for item in state.evidence}
    return {
        (_edge(names[row.source], row.type, names[row.target]),
         quotes[quote_id].source_id, quotes[quote_id].supporting_text)
        for row in state.relationships for quote_id in row.evidence_ids
    }


def _delivered(rows: Sequence[ConditionResult]) -> DeliveredGraphMetrics:
    graphs = [row.graph for row in rows if row.graph is not None]
    counts = GraphCounts(tp=sum(row.tp for row in graphs), fp=sum(row.fp for row in graphs),
        fn=sum(row.fn for row in graphs) + sum(row.expected_edges for row in rows if row.graph is None))
    predicted = counts.tp + counts.fp
    expected = counts.tp + counts.fn
    outcomes: dict[Outcome, int] = {}
    for row in rows:
        outcomes[row.outcome] = outcomes.get(row.outcome, 0) + 1
    return DeliveredGraphMetrics(inputs=len(rows), valid_graphs=len(graphs),
        without_graph=len(rows) - len(graphs), exact_graphs=sum(row.fp == row.fn == 0 for row in graphs),
        counts=counts, precision=counts.tp / predicted if predicted else 0.0,
        recall=counts.tp / expected if expected else 0.0, f1=counts.f1, outcomes=outcomes)
