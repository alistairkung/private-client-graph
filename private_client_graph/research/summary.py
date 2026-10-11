"""Explicitly labelled descriptive statistics; failures are never score zero."""
from statistics import mean, stdev
from typing import Any

from .artifacts import Bundle
from .metrics import estimate_cost
from .provider import TokenUsage

QUALITY = ('precision', 'recall', 'f1', 'provenance_accuracy')
FAILURES = {'provider_error', 'parse_error', 'edit_error', 'graph_error',
            'evaluation_error', 'uncertain', 'unavailable'}


def distribution(values: list[float | None]) -> dict[str, Any]:
    observed = [v for v in values if v is not None]
    return {'n': len(observed), 'missing': len(values) - len(observed),
            'mean': mean(observed) if observed else None,
            'standard_deviation': stdev(observed) if len(observed) > 1 else None,
            'minimum': min(observed) if observed else None,
            'maximum': max(observed) if observed else None}


def summarize(bundle: Bundle) -> dict[str, Any]:
    rows = bundle.results()
    attempts = bundle.attempts()
    samples = [{'sample_id': s.sample_id, 'case_id': s.case_id, 'cohort': s.cohort}
               for s in bundle.plan.inputs]
    samples += [{'sample_id': f'fresh_{i:02d}', 'case_id': 'case_03', 'cohort': 'fresh'}
                for i in range(1, bundle.plan.fresh_extractions + 1)]
    summaries = [_sample_summary(bundle, sample, rows, attempts) for sample in samples]
    return {'schema_version': 1, 'experiment_id': bundle.manifest['experiment_id'],
            'kind': bundle.plan.kind, 'task_id': bundle.plan.task_id,
            'model': bundle.plan.settings.model, 'effective_model': bundle.plan.effective_model,
            'configuration': bundle.plan.model_dump(mode='json', exclude={'inputs'}),
            'planned_provider_attempts': len(bundle.plan.inputs) * bundle.plan.repetitions
                + bundle.plan.fresh_extractions * (1 + bundle.plan.repetitions),
            'call_cap': bundle.plan.max_calls, 'samples': summaries,
            'cohorts': _cohorts(summaries), 'operations': _operations(bundle, attempts),
            'provenance': bundle.manifest['provenance'],
            'sessions': _sessions(bundle)}


def _sample_summary(bundle: Bundle, sample: dict[str, Any], rows: list[dict[str, Any]],
                    attempts: list[dict[str, Any]]) -> dict[str, Any]:
    baseline, repetitions = _sample_results(
        sample['sample_id'], rows, bundle.plan.repetitions
    )
    quality = _quality_summary(baseline, repetitions)
    execution = _repetition_summary(repetitions)
    cost_and_latency = _cost_and_latency_summary(
        bundle, sample, baseline, repetitions, attempts
    )
    return {
        **sample,
        'baseline': baseline,
        'repetitions': repetitions,
        **quality,
        **execution,
        **cost_and_latency,
    }


def _sample_results(
    sample_id: str,
    rows: list[dict[str, Any]],
    repetition_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected = [row for row in rows if row['sample_id'] == sample_id]
    baseline = next(
        (row for row in selected if row['configuration'] == 'noop'),
        {'status': 'not_attempted'},
    )
    repetitions = [
        next(
            (
                row for row in selected
                if row['configuration'] == 'generative_full_source'
                and row['repetition'] == repetition
            ),
            {'status': 'not_attempted', 'repetition': repetition},
        )
        for repetition in range(1, repetition_count + 1)
    ]
    return baseline, repetitions


def _quality_summary(
    baseline: dict[str, Any],
    repetitions: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = {
        metric: distribution([_score(result, metric) for result in repetitions])
        for metric in QUALITY
    }
    baseline_f1 = _score(baseline, 'f1')
    deltas = [
        _score(result, 'f1') - baseline_f1
        if _score(result, 'f1') is not None and baseline_f1 is not None else None
        for result in repetitions
    ]
    paired_count = sum(delta is not None for delta in deltas)
    return {
        'resolver_metrics': metrics,
        'scored_repetitions': metrics['f1']['n'],
        'paired_score_coverage': paired_count / len(repetitions),
        'paired_deltas': distribution(deltas),
    }


def _repetition_summary(repetitions: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = [result for result in repetitions if 'attempt_id' in result]
    attempted_failures = sum(result['status'] in FAILURES for result in attempted)
    return {
        'valid_repetitions': sum(result['status'] == 'completed' for result in repetitions),
        'failed_repetitions': sum(result['status'] in FAILURES for result in repetitions),
        'attempted_repetitions': len(attempted),
        'failure_rate_among_attempted': (
            attempted_failures / len(attempted) if attempted else None
        ),
        'not_attempted_repetitions': sum(
            result['status'] == 'not_attempted' for result in repetitions
        ),
        'no_edit_repetitions': sum(result.get('edits') == [] for result in repetitions),
    }


def _cost_and_latency_summary(
    bundle: Bundle,
    sample: dict[str, Any],
    baseline: dict[str, Any],
    repetitions: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    incremental_costs = [result.get('incremental_cost') for result in repetitions]
    extraction_cost, extraction_seconds, extraction_usage = _extraction_observation(
        bundle, sample, attempts
    )
    pipeline_costs = [
        cost + extraction_cost
        if cost is not None and extraction_cost is not None else None
        for cost in incremental_costs
    ]
    historical = next(
        (item.historical for item in bundle.plan.inputs
         if item.sample_id == sample['sample_id']),
        None,
    )
    return {
        'incremental_cost': distribution(incremental_costs),
        'extraction_cost': extraction_cost,
        'extraction_seconds': extraction_seconds,
        'extraction_usage': extraction_usage,
        'historical_pipeline_seconds': (
            historical['metadata'].get('duration_seconds') if historical else None
        ),
        'single_pipeline_cost': distribution(pipeline_costs),
        'provider_latency': distribution([
            result.get('provider_seconds') for result in repetitions
        ]),
        'resolver_latency': distribution([
            result.get('resolution_seconds') for result in repetitions
        ]),
        'baseline_single_pipeline_latency': _pipeline_seconds(baseline, extraction_seconds),
        'single_pipeline_latency': distribution([
            _pipeline_seconds(result, extraction_seconds) for result in repetitions
        ]),
    }


def _score(row: dict[str, Any], metric: str) -> Any:
    return (row.get('evaluation') or {}).get(metric)


def _pipeline_seconds(row: dict[str, Any], extraction_seconds: float | None) -> float | None:
    stages = [extraction_seconds, row.get('resolution_seconds'), row.get('downstream_seconds')]
    if row['status'] != 'completed' or any(value is None for value in stages):
        return None
    return sum(value for value in stages if value is not None)


def _cohorts(samples: list[dict[str, Any]]) -> dict[str, Any]:
    cohorts = {}
    for cohort in ('fresh', 'authored', 'historical'):
        group = [s for s in samples if s['cohort'] == cohort]
        if not group:
            continue
        cohorts[cohort] = {'samples': len(group), 'cases': sorted({s['case_id'] for s in group}),
            'baseline_metrics': {m: distribution([_score(s['baseline'], m) for s in group]) for m in QUALITY},
            'resolver_per_input_means': {m: distribution([s['resolver_metrics'][m]['mean'] for s in group]) for m in QUALITY},
            'within_input_f1_standard_deviations': {s['sample_id']: s['resolver_metrics']['f1']['standard_deviation'] for s in group},
            'valid_repetitions': sum(s['valid_repetitions'] for s in group),
            'scored_repetitions': sum(s['scored_repetitions'] for s in group),
            'failed_repetitions': sum(s['failed_repetitions'] for s in group),
            'not_attempted_repetitions': sum(s['not_attempted_repetitions'] for s in group),
            'paired_score_count': sum(s['paired_deltas']['n'] for s in group)}
    return cohorts


def _extraction_observation(bundle: Bundle, sample: dict[str, Any],
                            attempts: list[dict[str, Any]]) -> tuple[float | None, float | None, Any]:
    if sample['cohort'] == 'fresh':
        attempt = next((a for a in attempts if a['attempt_id'] == f"{sample['sample_id']}-extraction"), {})
        usage = TokenUsage.model_validate(attempt.get('response', {}).get('usage', {}))
        return estimate_cost(usage, bundle.plan.pricing), attempt.get('provider_seconds'), usage.model_dump()
    historical = next((s.historical for s in bundle.plan.inputs if s.sample_id == sample['sample_id']), None)
    if historical:
        metadata = historical['metadata']
        # Historical wall-clock measurement includes local processing; no historical price was recorded.
        return None, None, metadata.get('llm_output', {}).get('token_usage')
    return None, None, None


def _operations(bundle: Bundle, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    usages = [TokenUsage.model_validate(a.get('response', {}).get('usage', {})) for a in attempts]
    costs = [estimate_cost(u, bundle.plan.pricing) for u in usages]
    return {
        **_attempt_counts(bundle, attempts),
        **_cost_totals(costs),
        'tokens': _token_totals(usages),
        'provider_latency': distribution([a.get('provider_seconds') for a in attempts]),
        'returned_models': sorted({
            a['response']['returned_model']
            for a in attempts
            if a.get('response', {}).get('returned_model')
        }),
        'attempts': attempts,
    }


def _attempt_counts(bundle: Bundle, attempts: list[dict[str, Any]]) -> dict[str, int]:
    return {
        'attempted': len(attempts),
        'paid_attempts': len(attempts) if bundle.plan.kind != 'demonstration' else 0,
        'valid_attempts': sum(
            attempt['status'] == 'completed'
            and attempt.get('response', {}).get('payload') is not None
            for attempt in attempts
        ),
        'uncertain_attempts': sum(attempt['status'] == 'uncertain' for attempt in attempts),
        'provider_failed_attempts': sum(
            attempt['status'] == 'provider_error' for attempt in attempts
        ),
    }


def _cost_totals(costs: list[float | None]) -> dict[str, float | int | None]:
    known_costs = [cost for cost in costs if cost is not None]
    return {
        'estimated_spend': sum(known_costs) if len(known_costs) == len(costs) else None,
        'known_cost_sum': sum(known_costs),
        'unpriced_attempts': len(costs) - len(known_costs),
    }


def _token_totals(usages: list[TokenUsage]) -> dict[str, dict[str, int]]:
    totals = {}
    for field in ('input_tokens', 'output_tokens', 'cached_tokens'):
        observed = [
            value
            for usage in usages
            if (value := getattr(usage, field)) is not None
        ]
        totals[field] = {
            'known_sum': sum(observed),
            'known_attempts': len(observed),
            'unknown_attempts': len(usages) - len(observed),
        }
    return totals


def _sessions(bundle: Bundle) -> list[dict[str, Any]]:
    import json
    return sorted([json.loads(p.read_text()) for p in (bundle.path / 'sessions').glob('*.json')],
                  key=lambda item: item['finished_at'])
