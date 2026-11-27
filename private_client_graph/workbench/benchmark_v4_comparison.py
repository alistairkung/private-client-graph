"""Descriptive comparison across identical Benchmark v4 reference commitments."""
from private_client_graph.research.evidence_quality import EvidenceQuality
from .run_evaluation_contracts import BenchmarkV4Comparison, EvidenceQualityDelta, RunComparison, ObservationPair
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
        left_proofs=left.benchmark.cohort if left.benchmark else None,
        right_proofs=right.benchmark.cohort if right.benchmark else None,
        left_usage=left.pipeline_usage, right_usage=right.pipeline_usage,
        left_quality=left.quality, right_quality=right.quality,
        quality_delta=_quality_delta(left.quality, right.quality),
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


def _quality_delta(left: EvidenceQuality | None, right: EvidenceQuality | None) -> EvidenceQualityDelta | None:
    if (left is None or right is None or left.version != right.version
            or left.state != 'complete' or right.state != 'complete'):
        return None
    return EvidenceQualityDelta(
        combined_graph=_delta(left.combined_graph.f1 if left.combined_graph else None,
                              right.combined_graph.f1 if right.combined_graph else None),
        qualified_graph=_delta(left.qualified_graph.f1 if left.qualified_graph else None,
                               right.qualified_graph.f1 if right.qualified_graph else None),
        complete_proof=_delta(left.complete_proof.rate, right.complete_proof.rate),
        joint_only_coverage=_delta(left.joint_only_coverage.mean, right.joint_only_coverage.mean),
    )


def _delta(left: float | None, right: float | None) -> float | None:
    return right - left if left is not None and right is not None else None
