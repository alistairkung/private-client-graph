"""Benchmark v3 development evaluation over retained predictions only."""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean
from typing import Literal

from benchmark_v3.replay_evidence import EVIDENCE_POLICY_VERSION, SUFFICIENCY_VERSION, assess_evidence
from benchmark_v3.replay_manifest import VerifiedCondition, truth_edges
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.models import EvaluationResult, SourcedExtractionResult
from private_client_graph.pipeline import Pipeline, PipelineConfig, PipelineExecutionError


PROTOCOL_VERSION = 'benchmark_v3_evaluation_v1'
GRAPH_SCORER = 'semantic_edges_v1'
Unavailable = Literal['provider_failure', 'parse_failure', 'uncertain', 'not_attempted']
Outcome = Unavailable | Literal['scored', 'validation_failure']


@dataclass(frozen=True)
class PlannedCondition:
    family: str
    frozen: VerifiedCondition


@dataclass(frozen=True)
class UnavailablePrediction:
    outcome: Unavailable
    error_type: str | None = None


@dataclass(frozen=True)
class ConditionResult:
    family: str
    condition: str
    outcome: Outcome
    expected_edges: int
    planned_proofs: int
    planned_joint_proofs: int
    graph: EvaluationResult | None = None
    complete_proofs: int = 0
    complete_joint_proofs: int = 0
    incomplete_proofs: int = 0
    missed_proofs: int = 0
    quote_passed: int = 0
    quote_assessed: int = 0
    attribution_passed: int = 0
    attribution_assessed: int = 0
    failure_detail: str | None = None


@dataclass(frozen=True)
class GraphCounts:
    tp: int
    fp: int
    fn: int

    @property
    def f1(self) -> float:
        denominator = 2 * self.tp + self.fp + self.fn
        return 2 * self.tp / denominator if denominator else 0.0


@dataclass(frozen=True)
class Metrics:
    planned_conditions: int
    valid_graphs: int
    exact_graphs: int
    construction_success_rate: float
    exact_graph_accuracy: float
    valid_graph_only_exact_accuracy: float | None
    all_conditions: GraphCounts
    all_condition_micro_f1: float
    valid_graph_only: GraphCounts
    valid_graph_only_micro_f1: float | None
    expected_edges_without_graph: int
    planned_proofs: int
    complete_proofs: int
    proof_completion_rate: float | None
    planned_joint_proofs: int
    complete_joint_proofs: int
    joint_proof_completion_rate: float | None
    incomplete_proofs: int
    missed_proofs: int
    proofs_without_graph: int
    quote_passed: int
    quote_assessed: int
    attribution_passed: int
    attribution_assessed: int
    outcomes: dict[Outcome, int]


@dataclass(frozen=True)
class ConditionCommitment:
    family: str
    condition: str
    ordered_sources_sha256: str
    key_sha256: str


@dataclass(frozen=True)
class EvaluationScope:
    benchmark_sha256: str
    conditions: tuple[ConditionCommitment, ...]
    observation_origin: Literal['live', 'offline_fixture']
    protocol_version: str = PROTOCOL_VERSION
    split: Literal['development'] = 'development'
    graph_scorer: str = GRAPH_SCORER
    evidence_policy: str = EVIDENCE_POLICY_VERSION
    sufficiency_policy: str = SUFFICIENCY_VERSION
    attribution_policy: str = 'source_attribution_v1'


@dataclass(frozen=True)
class ProtocolResult:
    scope: EvaluationScope
    conditions: dict[str, ConditionResult]
    cohort: Metrics
    families: dict[str, Metrics]
    family_macro_f1: float
    valid_graph_only_family_macro_f1: float | None
    valid_graph_only_macro_family_count: int
    run_artifact_sha256: str | None = None


def evaluate_protocol(
    planned: Sequence[PlannedCondition],
    predictions: Mapping[str, SourcedExtractionResult | UnavailablePrediction],
    *,
    benchmark_sha256: str,
    observation_origin: Literal['live', 'offline_fixture'],
    run_artifact_sha256: str | None = None,
) -> ProtocolResult:
    """Use the protected scorers and apply protocol denominators to every planned condition."""
    scope = _scope(planned, benchmark_sha256, observation_origin)
    if set(predictions) - {item.condition for item in scope.conditions}:
        raise ValueError('Predictions contain conditions outside the frozen roster')

    conditions = {}
    grouped = defaultdict(list)
    for item in planned:
        condition = item.frozen.saved.condition
        prediction = predictions.get(condition, UnavailablePrediction('not_attempted'))
        result = _score_condition(item, prediction)
        conditions[condition] = result
        grouped[item.family].append(result)

    families = {name: _summarize(rows) for name, rows in grouped.items()}
    valid_family_scores = [
        item.valid_graph_only_micro_f1 for item in families.values()
        if item.valid_graph_only_micro_f1 is not None
    ]
    return ProtocolResult(
        scope=scope,
        conditions=conditions,
        cohort=_summarize(list(conditions.values())),
        families=families,
        family_macro_f1=mean(item.all_condition_micro_f1 for item in families.values()),
        valid_graph_only_family_macro_f1=mean(valid_family_scores) if valid_family_scores else None,
        valid_graph_only_macro_family_count=len(valid_family_scores),
        run_artifact_sha256=run_artifact_sha256,
    )


def require_compatible_scope(left: ProtocolResult, right: ProtocolResult) -> None:
    """Check scoring and cohort compatibility. Experimental control is a separate check."""
    if left.scope.protocol_version != PROTOCOL_VERSION or left.scope != right.scope:
        raise ValueError('Evaluation protocol, benchmark, planned conditions or observation origin differ')


def _scope(
    planned: Sequence[PlannedCondition], benchmark_sha256: str,
    observation_origin: Literal['live', 'offline_fixture'],
) -> EvaluationScope:
    if len(benchmark_sha256) != 64 or set(benchmark_sha256) - set('0123456789abcdef'):
        raise ValueError('Benchmark commitment must be a SHA-256 digest')
    commitments = tuple(
        ConditionCommitment(row.family, row.frozen.saved.condition, row.frozen.sources_sha256, row.frozen.case_sha256)
        for row in planned
    )
    if not commitments or len({row.condition for row in commitments}) != len(commitments):
        raise ValueError('Protocol requires distinct planned conditions')
    return EvaluationScope(benchmark_sha256, commitments, observation_origin)


def _score_condition(
    item: PlannedCondition, prediction: SourcedExtractionResult | UnavailablePrediction,
) -> ConditionResult:
    saved = item.frozen.saved
    expected = len(truth_edges(saved.truth))
    proofs = len(saved.sufficient_evidence)
    joint = sum(proof.joint_only for proof in saved.sufficient_evidence)
    dimensions = (item.family, saved.condition)
    if isinstance(prediction, UnavailablePrediction):
        return ConditionResult(*dimensions, prediction.outcome, expected, proofs, joint,
                               failure_detail=prediction.error_type)
    try:
        result = Pipeline(PipelineConfig()).run_from_sourced_extraction(item.frozen.sources, prediction)
    except PipelineExecutionError as error:
        if error.stage != 'graph' or not isinstance(error.__cause__, ValueError):
            raise
        return ConditionResult(*dimensions, 'validation_failure', expected, proofs, joint,
                               failure_detail=str(error.__cause__))

    graph = evaluate_graph(result.graph, saved.truth)
    evidence = assess_evidence(result.state, saved)
    sufficient = evidence['sufficiency']
    joint_edges = {tuple(edge) for edge in evidence['not_applicable']}
    return ConditionResult(
        *dimensions, 'scored', expected, proofs, joint, graph,
        complete_proofs=sufficient['complete'],
        complete_joint_proofs=sum(
            target['status'] == 'complete' and tuple(target['edge']) in joint_edges
            for target in sufficient['targets']
        ),
        incomplete_proofs=sufficient['incomplete'],
        missed_proofs=sufficient['missed'],
        quote_passed=evidence['quotation']['passed'],
        quote_assessed=evidence['quotation']['assessed'],
        attribution_passed=evidence['source_attribution']['passed'],
        attribution_assessed=evidence['source_attribution']['assessed'],
    )


def _summarize(rows: Sequence[ConditionResult]) -> Metrics:
    valid = [row.graph for row in rows if row.graph is not None]
    scored_counts = GraphCounts(sum(x.tp for x in valid), sum(x.fp for x in valid), sum(x.fn for x in valid))
    omitted = sum(row.expected_edges for row in rows if row.graph is None)
    delivered = GraphCounts(scored_counts.tp, scored_counts.fp, scored_counts.fn + omitted)
    exact = sum(x.fp == x.fn == 0 for x in valid)
    planned_proofs = sum(x.planned_proofs for x in rows)
    planned_joint = sum(x.planned_joint_proofs for x in rows)
    complete = sum(x.complete_proofs for x in rows)
    joint_complete = sum(x.complete_joint_proofs for x in rows)
    return Metrics(
        planned_conditions=len(rows), valid_graphs=len(valid), exact_graphs=exact,
        construction_success_rate=len(valid) / len(rows), exact_graph_accuracy=exact / len(rows),
        valid_graph_only_exact_accuracy=exact / len(valid) if valid else None,
        all_conditions=delivered, all_condition_micro_f1=delivered.f1, valid_graph_only=scored_counts,
        valid_graph_only_micro_f1=scored_counts.f1 if valid else None, expected_edges_without_graph=omitted,
        planned_proofs=planned_proofs, complete_proofs=complete,
        proof_completion_rate=complete / planned_proofs if planned_proofs else None,
        planned_joint_proofs=planned_joint, complete_joint_proofs=joint_complete,
        joint_proof_completion_rate=joint_complete / planned_joint if planned_joint else None,
        incomplete_proofs=sum(x.incomplete_proofs for x in rows), missed_proofs=sum(x.missed_proofs for x in rows),
        proofs_without_graph=sum(x.planned_proofs for x in rows if x.graph is None),
        quote_passed=sum(x.quote_passed for x in rows), quote_assessed=sum(x.quote_assessed for x in rows),
        attribution_passed=sum(x.attribution_passed for x in rows),
        attribution_assessed=sum(x.attribution_assessed for x in rows),
        outcomes=dict(Counter(x.outcome for x in rows)),
    )
