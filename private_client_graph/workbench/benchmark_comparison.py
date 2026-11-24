"""Descriptive comparison of verified Benchmark v3 Runs."""
from dataclasses import fields
from typing import TYPE_CHECKING

from benchmark_v3.evaluation_protocol import (
    ConditionResult,
    EvaluationScope,
    GraphCounts,
    Metrics,
    require_compatible_scope,
)

from .run_evaluation_contracts import (
    BenchmarkComparison,
    BenchmarkConditionDelta,
    BenchmarkCountDelta,
    BenchmarkFamilyDelta,
    BenchmarkMetricDelta,
    RunComparison,
)

if TYPE_CHECKING:
    from .run_inspection import RunDetail


def compare_benchmark_runs(left: "RunDetail", right: "RunDetail") -> RunComparison:
    result = RunComparison(left_run_id=left.id, right_run_id=right.id, benchmark=BenchmarkComparison())
    if left.benchmark is None or right.benchmark is None:
        result.scope_differences = ['Both Runs must have verified Evaluation Protocol v1 results.']
        return result

    first, second = left.benchmark.as_protocol_result(), right.benchmark.as_protocol_result()
    result.provenance_differences = _provenance_differences(left, right)
    try:
        require_compatible_scope(first, second)
    except ValueError as error:
        result.scope_differences = _scope_differences(first.scope, second.scope) or [str(error)]
        return result

    result.comparable_scope = True
    result.matched_inputs = len(first.scope.conditions)
    result.reasons = ['Condition-aligned descriptive comparison. Experimental control is verified separately.']
    result.benchmark = BenchmarkComparison(
        cohort=_metrics_delta(first.cohort, second.cohort),
        families=[
            BenchmarkFamilyDelta(family=family, **_metrics_delta(metrics, second.families[family]).model_dump())
            for family, metrics in first.families.items()
        ],
        conditions=[
            _condition_delta(first.conditions[item.condition], second.conditions[item.condition])
            for item in first.scope.conditions
        ],
        family_macro_f1_delta=second.family_macro_f1 - first.family_macro_f1,
    )
    return result


def _metrics_delta(left: Metrics, right: Metrics) -> BenchmarkMetricDelta:
    counts = _count_delta(left, right, left.all_conditions, right.all_conditions)
    return BenchmarkMetricDelta(
        **counts.model_dump(),
        all_condition_micro_f1=right.all_condition_micro_f1 - left.all_condition_micro_f1,
        planned_conditions=right.planned_conditions - left.planned_conditions,
        valid_graphs=right.valid_graphs - left.valid_graphs,
        exact_graphs=right.exact_graphs - left.exact_graphs,
    )


def _condition_delta(left: ConditionResult, right: ConditionResult) -> BenchmarkConditionDelta:
    counts = _count_delta(left, right, _delivered_counts(left), _delivered_counts(right))
    return BenchmarkConditionDelta(
        **counts.model_dump(), family=left.family, condition=left.condition,
        left_outcome=left.outcome, right_outcome=right.outcome,
    )


def _delivered_counts(condition: ConditionResult) -> GraphCounts:
    graph = condition.graph
    return GraphCounts(graph.tp, graph.fp, graph.fn) if graph else GraphCounts(0, 0, condition.expected_edges)


def _count_delta(
    left: Metrics | ConditionResult,
    right: Metrics | ConditionResult,
    left_counts: GraphCounts,
    right_counts: GraphCounts,
) -> BenchmarkCountDelta:
    return BenchmarkCountDelta(
        tp=right_counts.tp - left_counts.tp,
        fp=right_counts.fp - left_counts.fp,
        fn=right_counts.fn - left_counts.fn,
        complete_proofs=right.complete_proofs - left.complete_proofs,
        planned_proofs=right.planned_proofs - left.planned_proofs,
        complete_joint_proofs=right.complete_joint_proofs - left.complete_joint_proofs,
        planned_joint_proofs=right.planned_joint_proofs - left.planned_joint_proofs,
    )


def _scope_differences(left: EvaluationScope, right: EvaluationScope) -> list[str]:
    reasons = [
        f'{field.name.replace("_", " ").capitalize()} differs.'
        for field in fields(EvaluationScope)
        if field.name != 'conditions' and getattr(left, field.name) != getattr(right, field.name)
    ]
    left_by_id = {(item.family, item.condition): item for item in left.conditions}
    right_by_id = {(item.family, item.condition): item for item in right.conditions}
    if left_by_id.keys() != right_by_id.keys():
        reasons.append('The planned family and Condition roster differs.')
    elif tuple(left_by_id) != tuple(right_by_id):
        reasons.append('The order of the planned Conditions differs.')
    for (family, condition), first in left_by_id.items():
        second = right_by_id.get((family, condition))
        if second is None:
            continue
        if first.ordered_sources_sha256 != second.ordered_sources_sha256:
            reasons.append(f'{condition}: ordered Source commitment differs.')
        if first.key_sha256 != second.key_sha256:
            reasons.append(f'{condition}: admitted key commitment differs.')
    return reasons


def _provenance_differences(left: "RunDetail", right: "RunDetail") -> list[str]:
    reasons = []
    if left.plan.preview.proposal != right.plan.preview.proposal:
        reasons.append('Retained pipeline configuration differs.')
    if left.provenance != right.provenance:
        reasons.append('Retained execution provenance differs.')
    return reasons
