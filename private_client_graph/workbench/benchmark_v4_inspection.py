"""Project retained Benchmark v4 outcomes into the existing graph and Evidence inspector."""
from typing import TYPE_CHECKING

from benchmark_v3.evaluation_protocol import ConditionResult
from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.benchmark_v4 import BenchmarkWorkload, EvaluationInput
from private_client_graph.research.benchmark_v4_run import evaluate_retained_run
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.run_plan import RunPlan
from .benchmark_contracts import (
    BenchmarkCondition, BenchmarkRun, ExpectedRelationship, condition_metrics,
    condition_relationship_outcomes, project_qualified_condition, attributed_quotes,
)
from .benchmark_v4 import load_private_workload, workload_metadata

if TYPE_CHECKING:
    from .run_inspection import RunDetail, RunObservation


def attach_benchmark_v4(detail: 'RunDetail', bundle: Bundle) -> None:
    assert isinstance(bundle.plan, RunPlan) and bundle.plan.benchmark_v4_sha256
    workload = load_private_workload()
    retained = evaluate_retained_run(bundle, workload, attempts=detail.attempts)
    mixed, results = retained.evaluation, retained.results
    detail.benchmark_v4 = mixed.summary
    detail.benchmark = BenchmarkRun.from_protocol(mixed.qualified, workload.qualified,
                                                  workload.family_details, results)
    projections = [*detail.benchmark.observations,
                   _consensus_condition(workload, mixed.consensus, results.get(mixed.consensus.condition))]
    for observation, condition, template in zip(detail.observations, projections, bundle.plan.inputs, strict=True):
        consensus = condition.role == 'consensus'
        outcome = mixed.consensus if consensus else mixed.qualified.conditions[condition.condition]
        observation.sources = template.sources
        observation.benchmark = condition
        observation.status = condition.outcome
        observation.reason = condition.failure_detail
        observation.relationships = condition_relationship_outcomes(condition, outcome.graph,
            observation.result.state if observation.result else None, score_provenance=not consensus)


def inspect_frozen_input(workload: BenchmarkWorkload, identity: str) -> 'RunObservation | None':
    from .run_inspection import RunObservation
    for index, (item, sample) in enumerate(zip(workload.roster.inputs, workload.inputs, strict=True)):
        if item.id == identity:
            break
    else:
        return None
    expected_count = len(sample.truth.relationships)
    row = ConditionResult(item.matter, identity, 'not_attempted', expected_count, 0, 0)
    condition = _unmeasured_condition(workload, item, index, row)
    return RunObservation(id=identity, sample_id=sample.sample_id, case_id=item.matter,
        configuration='full_context', repetition=0, status='not_attempted', sources=sample.sources,
        metadata=workload_metadata(workload.roster)[item.sample_id], benchmark=condition)


def _unmeasured_condition(workload: BenchmarkWorkload, item: EvaluationInput, index: int,
                          row: ConditionResult) -> BenchmarkCondition:
    if item.reference_methodology == 'consensus_adjudication':
        return _consensus_condition(workload, row, None)
    condition = workload.qualified[index]
    saved = condition.frozen.saved
    planned = ConditionResult(item.matter, item.id, 'not_attempted', row.expected_edges,
        len(saved.sufficient_evidence), sum(proof.joint_only for proof in saved.sufficient_evidence))
    return project_qualified_condition(condition, planned, workload.family_details[item.matter], None)


def _consensus_condition(workload: BenchmarkWorkload, row: ConditionResult,
                         result: ResearchResult | None) -> BenchmarkCondition:
    expected = workload.consensus_state
    evidence = attributed_quotes(expected)
    return BenchmarkCondition(family=row.family, condition=row.condition, role='consensus',
        outcome=row.outcome, expected=expected, expected_edges=row.expected_edges,
        parsed_prediction=result.sourced_extraction if result else None,
        expected_relationships=[ExpectedRelationship(edge=edge, quotes=quotes)
                                for edge, quotes in sorted(evidence.items())],
        metrics=condition_metrics(row), failure_detail=row.failure_detail)
