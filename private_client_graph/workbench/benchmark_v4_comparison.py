"""Descriptive comparison across identical Benchmark v4 reference commitments."""
from .run_evaluation_contracts import BenchmarkV4Comparison, RunComparison, ObservationPair, QualityDelta
from .run_inspection import RunDetail


def compare_benchmark_v4_runs(left: RunDetail, right: RunDetail) -> RunComparison:
    output = RunComparison(left_run_id=left.id, right_run_id=right.id)
    first, second = left.benchmark_v4, right.benchmark_v4
    if (first is None or second is None or first.scope_sha256 != second.scope_sha256
            or first.scoring_sha256 != second.scoring_sha256
            or first.observation_origin != second.observation_origin):
        output.scope_differences = ['Benchmark v4 scope, scoring version or observation origin differ.']
        return output

    output.comparable_scope = True
    right_inputs = {row.sample_id: row for row in right.observations}
    output.pairs = [
        ObservationPair(left_observation=row.id, right_observation=right_inputs[row.sample_id].id,
                        left_sample=row.sample_id, right_sample=row.sample_id)
        for row in left.observations if row.sample_id in right_inputs
    ]
    output.matched_inputs = len(output.pairs)
    left_origin = left.pipeline_usage.origin_run_id if left.pipeline_usage else None
    right_origin = right.pipeline_usage.origin_run_id if right.pipeline_usage else None
    paired = (left_origin or left.id) == (right_origin or right.id)
    output.benchmark_v4 = BenchmarkV4Comparison(left=first, right=second,
        left_quality=left.quality, right_quality=right.quality,
        quality_delta=_quality_delta(left, right) if first.state == second.state == 'complete' else None,
        left_proofs=left.benchmark.cohort if left.benchmark else None,
        right_proofs=right.benchmark.cohort if right.benchmark else None,
        left_usage=left.pipeline_usage, right_usage=right.pipeline_usage,
        shared_extraction_run_id=(left_origin or right_origin) if paired else None)
    output.reasons = ['Differences are descriptive. A controlled comparison requires matched model, '
                      'prompt and execution settings apart from the intended configuration change.']
    a, b = left.plan.preview.proposal, right.plan.preview.proposal
    if (a.model, a.temperature, a.timeout_seconds) != (b.model, b.temperature, b.timeout_seconds):
        output.provenance_differences.append('Model, temperature or timeout differed.')
    for key in ('prompt_hashes', 'dependencies'):
        if left.provenance.get(key) != right.provenance.get(key):
            output.provenance_differences.append(f'Frozen {key.replace("_", " ")} differed.')
    if first.state != 'complete' or second.state != 'complete':
        output.reasons.append('A comparison includes a Run with incomplete coverage.')
    return output


def _quality_delta(left: RunDetail, right: RunDetail) -> QualityDelta | None:
    a, b = left.quality, right.quality
    if a is None or b is None or a.version != b.version:
        return None
    assert a.graph and b.graph and a.qualified_graph and b.qualified_graph and a.grounded and b.grounded
    return QualityDelta(graph=b.graph.f1 - a.graph.f1, qualified_graph=b.qualified_graph.f1 - a.qualified_graph.f1,
                        grounded=b.grounded.f1 - a.grounded.f1)
