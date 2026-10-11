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
    selected = [r for r in rows if r['sample_id'] == sample['sample_id']]
    baseline = next((r for r in selected if r['configuration'] == 'noop'), {'status': 'not_attempted'})
    repetitions: list[dict[str, Any]] = [next((r for r in selected if r['configuration'] == 'generative_full_source'
                        and r['repetition'] == i), {'status': 'not_attempted', 'repetition': i})
                   for i in range(1, bundle.plan.repetitions + 1)]
    metrics = {metric: distribution([_score(r, metric) for r in repetitions]) for metric in QUALITY}
    baseline_f1 = _score(baseline, 'f1')
    costs = [r.get('incremental_cost') for r in repetitions]
    extraction_cost, extraction_seconds, extraction_usage = _extraction_observation(bundle, sample, attempts)
    pipeline_costs = [c + extraction_cost if c is not None and extraction_cost is not None else None for c in costs]
    resolver_seconds = [r.get('resolution_seconds') for r in repetitions]
    failed = sum(r['status'] in FAILURES for r in repetitions)
    attempted = sum('attempt_id' in r for r in repetitions)
    attempted_failures = sum('attempt_id' in r and r['status'] in FAILURES for r in repetitions)
    paired = sum(_score(r, 'f1') is not None and baseline_f1 is not None for r in repetitions)
    historical = next((s.historical for s in bundle.plan.inputs if s.sample_id == sample['sample_id']), None)
    return {**sample, 'baseline': baseline, 'repetitions': repetitions,
            'resolver_metrics': metrics, 'scored_repetitions': metrics['f1']['n'],
            'valid_repetitions': sum(r['status'] == 'completed' for r in repetitions),
            'failed_repetitions': failed,
            'attempted_repetitions': attempted,
            'failure_rate_among_attempted': attempted_failures / attempted if attempted else None,
            'paired_score_coverage': paired / len(repetitions),
            'not_attempted_repetitions': sum(r['status'] == 'not_attempted' for r in repetitions),
            'paired_deltas': distribution([_score(r, 'f1') - baseline_f1
                if _score(r, 'f1') is not None and baseline_f1 is not None else None for r in repetitions]),
            'incremental_cost': distribution(costs), 'extraction_cost': extraction_cost,
            'extraction_seconds': extraction_seconds, 'extraction_usage': extraction_usage,
            'historical_pipeline_seconds': historical['metadata'].get('duration_seconds') if historical else None,
            'single_pipeline_cost': distribution(pipeline_costs),
            'provider_latency': distribution([r.get('provider_seconds') for r in repetitions]),
            'resolver_latency': distribution(resolver_seconds),
            'baseline_single_pipeline_latency': _pipeline_seconds(baseline, extraction_seconds),
            'single_pipeline_latency': distribution([_pipeline_seconds(r, extraction_seconds) for r in repetitions]),
            'no_edit_repetitions': sum(r.get('edits') == [] for r in repetitions)}


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
    known_costs = [c for c in costs if c is not None]
    usage_totals = {}
    for field in ('input_tokens', 'output_tokens', 'cached_tokens'):
        observed = [getattr(u, field) for u in usages if getattr(u, field) is not None]
        usage_totals[field] = {'known_sum': sum(observed), 'known_attempts': len(observed),
                               'unknown_attempts': len(usages) - len(observed)}
    return {'attempted': len(attempts), 'paid_attempts': len(attempts) if bundle.plan.kind != 'demonstration' else 0,
            'valid_attempts': sum(a['status'] == 'completed'
                                  and a.get('response', {}).get('payload') is not None for a in attempts),
            'uncertain_attempts': sum(a['status'] == 'uncertain' for a in attempts),
            'provider_failed_attempts': sum(a['status'] == 'provider_error' for a in attempts),
            'estimated_spend': sum(known_costs) if len(known_costs) == len(costs) else None,
            'known_cost_sum': sum(known_costs), 'unpriced_attempts': len(costs) - len(known_costs),
            'tokens': usage_totals, 'provider_latency': distribution([a.get('provider_seconds') for a in attempts]),
            'returned_models': sorted({a['response']['returned_model'] for a in attempts
                                      if a.get('response', {}).get('returned_model')}),
            'attempts': attempts}


def _sessions(bundle: Bundle) -> list[dict[str, Any]]:
    import json
    return sorted([json.loads(p.read_text()) for p in (bundle.path / 'sessions').glob('*.json')],
                  key=lambda item: item['finished_at'])
