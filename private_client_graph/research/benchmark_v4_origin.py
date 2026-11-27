"""Verify the retained Extractor-only origin of a Benchmark v4 resolver Run."""
from dataclasses import dataclass
from pathlib import Path
import re

from benchmark_v3.evaluation_protocol import UnavailablePrediction
from private_client_graph.models import ExtractionResult, SourcedExtractionResult

from .artifacts import Bundle, checksum
from .benchmark_v4 import BenchmarkWorkload
from .inputs import ResearchInput
from .live_accounting import plan_digest, retained_run_attempts
from .plan import Pricing
from .provider import ModelSettings
from .retained_inputs import RetainedInputLineage, RetainedSampleLineage, input_digests, value_digest
from .run_plan import RunPlan


@dataclass(frozen=True)
class ExtractionOrigin:
    lineage: RetainedInputLineage
    samples: dict[str, ResearchInput]
    unavailable: dict[str, UnavailablePrediction]
    attempts: list[dict]
    pricing: Pricing | None


def load_extraction_origin(root: Path, experiment_id: str, run_id: str, workload: BenchmarkWorkload,
                           settings: ModelSettings, task_id: str) -> ExtractionOrigin:
    from .benchmark_v4_run import evaluate_retained_run, require_frozen_plan

    if not re.fullmatch(r'[a-f0-9]{32}', run_id):
        raise ValueError('Invalid Benchmark v4 extraction origin identity')
    path = root / run_id
    if path.is_symlink() or any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Benchmark v4 extraction origin cannot contain symlinks')
    parent = Bundle.open(path)
    plan = require_frozen_plan(parent, workload)
    if (plan.run_id != run_id or plan.experiment_id != experiment_id or plan.task_id != task_id
            or plan.execution_mode != 'live' or plan.input_mode != 'fresh' or plan.resolver != 'none'
            or plan.settings != settings):
        raise ValueError('Benchmark v4 requires a matching live Extractor-only Run in this Experiment')

    attempts, reasons = retained_run_attempts(parent)
    if reasons:
        raise ValueError('Benchmark v4 extraction origin is missing authoritative receipts')
    verified = evaluate_retained_run(parent, workload, attempts=attempts)
    if verified.evaluation.summary.state != 'complete' or len(attempts) != len(workload.inputs):
        raise ValueError('Benchmark v4 extraction origin must be a completed Run')
    samples, lineage, unavailable = {}, {}, {}
    receipts = {attempt['attempt_id']: attempt for attempt in attempts}
    ordered_receipts = []
    for item, template, slot in zip(workload.roster.inputs, plan.inputs, plan.planned_slots, strict=True):
        assert slot.extraction_attempt_id is not None
        receipt = receipts[slot.extraction_attempt_id]
        ordered_receipts.append(receipt)
        snapshot = path / 'fresh_inputs' / f'{slot.sample_id}.json'
        prediction = verified.predictions[item.id]
        if isinstance(prediction, UnavailablePrediction):
            if snapshot.exists():
                raise ValueError('Unavailable extraction unexpectedly has a candidate snapshot')
            unavailable[slot.sample_id] = prediction
            continue
        raw = snapshot.read_bytes()
        sample = _verified_snapshot(raw, template, slot.sample_id, prediction)
        samples[slot.sample_id] = sample
        digests = input_digests(sample)
        lineage[slot.sample_id] = RetainedSampleLineage(original_sample_id=slot.sample_id,
            extraction_attempt_id=slot.extraction_attempt_id, snapshot_digest=checksum(raw),
            source_digest=digests['source_digest'], truth_digest=digests['truth_digest'],
            extraction_digest=digests['extraction_digest'])

    binding = RetainedInputLineage(experiment_id=experiment_id, run_id=run_id, plan_digest=plan_digest(parent),
        artifact_digest=value_digest(ordered_receipts), samples=lineage)
    return ExtractionOrigin(binding, samples, unavailable, ordered_receipts, plan.pricing)


def verify_extraction_origin(bundle: Bundle, workload: BenchmarkWorkload) -> ExtractionOrigin | None:
    assert isinstance(bundle.plan, RunPlan)
    origin = bundle.plan.retained_input_lineage
    if origin is None:
        return None
    if bundle.plan.experiment_id != origin.experiment_id:
        raise ValueError('Benchmark v4 extraction origin must belong to this Experiment')
    verified = load_extraction_origin(bundle.path.parent, origin.experiment_id, origin.run_id, workload,
                                     bundle.plan.settings, bundle.plan.task_id)
    if verified.lineage != origin:
        raise ValueError('Benchmark v4 extraction origin differs from its frozen lineage')
    return verified


def _verified_snapshot(raw: bytes, template: ResearchInput, identity: str,
                       candidates: SourcedExtractionResult) -> ResearchInput:
    sample = ResearchInput.model_validate_json(raw)
    legacy = ExtractionResult.model_validate({'relationships': [
        candidate.model_dump(exclude={'source_id'}) for candidate in candidates.relationships
    ]})
    expected = template.model_copy(update={'sample_id': identity, 'cohort': 'fresh',
                                           'extraction': legacy, 'sourced_extraction': candidates})
    if sample != expected:
        raise ValueError('Benchmark v4 candidate snapshot differs from its frozen template or extraction receipt')
    return sample
