"""Derive current report fields after Benchmark v4 retained Run verification."""
import json
from collections.abc import Sequence

from .artifacts import Bundle
from .benchmark_v4_run import VerifiedV4Run
from .evidence_grounded import QualityProjection, project_quality
from .run_plan import RunPlan


def report_quality(bundle: Bundle, retained: VerifiedV4Run, attempts: Sequence[dict]) -> QualityProjection:
    evaluation = retained.evaluation
    return project_quality(evaluation.qualified.conditions.values(), other=[evaluation.consensus],
                           processing=_processing_inputs(bundle, retained, attempts))


def _processing_inputs(bundle: Bundle, retained: VerifiedV4Run, attempts: Sequence[dict]) -> set[str]:
    assert isinstance(bundle.plan, RunPlan)
    lifecycle = [json.loads(path.read_text()) for path in (bundle.path / 'lifecycle').glob('*.json')]
    current = max(lifecycle, key=lambda row: row['at'], default={'state': 'frozen'})
    if current['state'] not in ('running', 'stopping'):
        return set()
    authority = f"{bundle.path.name}-{current['invocation']}"
    active = {row['attempt_id'] for row in attempts if row.get('authorization') == authority}
    inputs = [*retained.evaluation.qualified.conditions, retained.evaluation.consensus.condition]
    return {
        identity for identity, slot in zip(inputs, bundle.plan.planned_slots, strict=True)
        if (slot.observation_id if retained.origin else slot.extraction_attempt_id) in active
        and identity not in retained.predictions
    }
