"""Project frozen Benchmark v2 labels and Workbench Runs into a read-only JSON report."""
import argparse
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Literal

from private_client_graph.models.evaluation_result import EvaluationResult
from private_client_graph.research.benchmark_decisions import DecisionTargets, diagnose
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.metrics import estimate_cost
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.workbench.run_evaluation import incurred_cost
from private_client_graph.workbench.run_evaluation_contracts import AttemptCost, Coverage

from benchmark_v2.report_protocol import (
    ConditionCommitment,
    ConditionLabels as ConditionLabels,
    ReportManifest as ReportManifest,
    RetainedAttempt,
    RunRecord,
    compare_chronology,
    development_batches,
    inspect_protocol,
    open_run,
    shared_task_mismatch,
)


_HISTORICAL_FINGERPRINT = 'bc19ba97cbe016479903222bb1578db6'
_SCORERS = ('private_client_graph/evaluation.py', 'private_client_graph/research/source_attribution.py')


def development_report(manifest: ReportManifest, baseline: Sequence[Path]) -> dict[str, Any]:
    """Report all planned baseline Observations, including missing Runs and unscored slots."""
    batches = None
    if manifest.execution_mode == 'live':
        batches = development_batches(manifest, require_approval=bool(baseline))
    return {
        **_report_header(manifest),
        'baseline': _arm(manifest, [open_run(path) for path in baseline], 'baseline', batches=batches),
    }


def final_report(manifest: ReportManifest, baseline: Sequence[Path], final: Sequence[Path]) -> dict[str, Any]:
    """Compare independent fresh Observations on each committed Matter family."""
    if any(row.observations != 1 for row in manifest.conditions) or (
        len({row.matter_family for row in manifest.conditions}) != len(manifest.conditions)
    ):
        raise ValueError('Final reporting requires one condition and Observation per Matter family in each arm')
    if manifest.execution_mode == 'live' and not (manifest.baseline_plan_digests and manifest.final_plan_digests):
        raise ValueError('Live final reporting requires the predeclared plan digests for both arms')
    baseline_runs = [open_run(path) for path in baseline]
    final_runs = [open_run(path) for path in final]
    if {run.plan.run_id for run in baseline_runs} & {run.plan.run_id for run in final_runs}:
        raise ValueError('Final arms must use independent Runs')
    task_issue = None
    if manifest.execution_mode == 'live':
        approved = set(manifest.baseline_plan_digests or []) | set(manifest.final_plan_digests or [])
        approved_runs = [run for run in [*baseline_runs, *final_runs] if run.provenance['plan_digest'] in approved]
        task_issue = shared_task_mismatch(approved_runs)
        if task_issue is None and any(run.plan.task_call_cap != manifest.final_attempt_cap for run in approved_runs):
            task_issue = 'Run cap differs from the predeclared final attempt cap.'
    left = _arm(manifest, baseline_runs, 'baseline', task_issue=task_issue)
    right = _arm(manifest, final_runs, 'final', task_issue=task_issue)
    pairs = [
        _pair(a, b, first='baseline' if index % 2 == 0 else 'final')
        for index, (a, b) in enumerate(zip(left['conditions'], right['conditions'], strict=True))
    ]
    scored = [pair for pair in pairs if pair['delta'] is not None]
    return {
        **_report_header(manifest),
        'baseline': left,
        'final': right,
        'shared_task_mismatch': task_issue,
        'paired_coverage': {'planned': len(pairs), 'scored': len(scored)},
        'pairs': pairs,
        'paired_graph': {arm: _pool([pair[arm] for pair in scored])['graph'] for arm in ('baseline', 'final')},
    }


def _pair(baseline: dict[str, Any], final: dict[str, Any],
          *, first: Literal['baseline', 'final']) -> dict[str, Any]:
    left, right = baseline['observations'][0], final['observations'][0]
    order = [('baseline', left), ('final', right)]
    if first == 'final':
        order.reverse()
    chronology = compare_chronology([(arm, row.get('extraction_started_at')) for arm, row in order])
    reason = None
    if left['state'] != 'scored' or right['state'] != 'scored':
        reason = 'Both committed Observations must be scored.'
    elif not left['extraction_request_matches'] or not right['extraction_request_matches']:
        reason = 'Both fresh extraction requests must match the exact ordered Sources.'
    elif chronology['deviations']:
        reason = 'Retained extraction start times conflict with the committed arm order.'
    elif chronology['state'] != 'verified':
        reason = 'Retained extraction start times cannot verify the committed arm order.'
    elif left['scorer_digests'] != right['scorer_digests'] or None in left['scorer_digests'].values():
        reason = 'Frozen evaluator implementations could not be matched.'
    return {
        'condition': baseline['condition'],
        'matter_family': baseline['matter_family'],
        'baseline': left,
        'final': right,
        'exclusion_reason': reason,
        'chronology': chronology,
        'delta': _paired_delta(left, right) if reason is None else None,
    }


def _paired_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    before, after = left['graph'], right['graph']
    resources_before, resources_after = left['resources'], right['resources']
    cost_before, cost_after = resources_before['cost'], resources_after['cost']
    currency = cost_before['currency'] if cost_before['currency'] == cost_after['currency'] else None
    return {
        'graph': {key: after[key] - before[key] for key in ('tp', 'fp', 'fn', 'f1', 'exact_graph')},
        'fp_fixed': sorted(set(before['false_positive_edges']) - set(after['false_positive_edges'])),
        'fp_regressed': sorted(set(after['false_positive_edges']) - set(before['false_positive_edges'])),
        'fn_fixed': sorted(set(before['false_negative_edges']) - set(after['false_negative_edges'])),
        'fn_regressed': sorted(set(after['false_negative_edges']) - set(before['false_negative_edges'])),
        **_evidence_delta(left, right),
        'tokens': {key: _difference(resources_before['tokens'][key]['total'], metric['total'])
                   for key, metric in resources_after['tokens'].items()},
        'provider_seconds': _difference(resources_before['provider_seconds']['total'],
                                        resources_after['provider_seconds']['total']),
        'cost': {'currency': currency,
                 'total': _difference(cost_before['total'], cost_after['total']) if currency else None},
        'fingerprints_changed': _fingerprint_change(resources_before, resources_after),
    }


def _evidence_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    quote_before, quote_after = left['quote_provenance'], right['quote_provenance']
    source_before, source_after = left['source_attribution'], right['source_attribution']
    decisions_before, decisions_after = left['decisions'], right['decisions']
    sufficiency = None
    source_attribution = None
    if decisions_before is not None and decisions_after is not None:
        sufficiency = _evidence_change(decisions_before['sufficiency'], decisions_after['sufficiency'],
                                       'complete', 'accuracy')
    if source_before is not None and source_after is not None:
        source_attribution = {
            'passed': source_after['passed'] - source_before['passed'],
            'assessed': source_after['assessed'] - source_before['assessed'],
            'accuracy': _difference(source_before['accuracy'], source_after['accuracy']),
        }
    return {
        'quote_provenance': _evidence_change(quote_before, quote_after, 'passes', 'accuracy'),
        'source_attribution': source_attribution,
        'sufficiency': sufficiency,
    }


def _evidence_change(before: dict[str, Any], after: dict[str, Any], edges: str, accuracy: str) -> dict[str, Any]:
    return {
        f'{edges}_gained': sorted(set(after[edges]) - set(before[edges])),
        f'{edges}_lost': sorted(set(before[edges]) - set(after[edges])),
        'accuracy': _difference(before[accuracy], after[accuracy]),
        'assessed': after['assessed'] - before['assessed'],
    }


def _difference(before: int | float | None, after: int | float | None) -> int | float | None:
    if before is None or after is None:
        return None
    if isinstance(before, int) and isinstance(after, int):
        return after - before
    return float(Decimal(str(after)) - Decimal(str(before)))


def _fingerprint_change(before: dict[str, Any], after: dict[str, Any]) -> bool | None:
    left = {row['system_fingerprint'] for row in before['attempts']}
    right = {row['system_fingerprint'] for row in after['attempts']}
    return left != right if left and right and None not in left | right else None


def _report_header(manifest: ReportManifest) -> dict[str, Any]:
    return {
        'manifest_digest': value_digest(manifest.model_dump(mode='json')),
        'evaluator_version': manifest.evaluator_version,
        'execution_mode': manifest.execution_mode,
        'live_observations': manifest.execution_mode == 'live',
        'matter_families': len({row.matter_family for row in manifest.conditions}),
        'conditions': len(manifest.conditions),
    }


def _arm(manifest: ReportManifest, runs: list[RunRecord], arm: Literal['baseline', 'final'],
         *, batches: dict[str, list[str]] | None = None, task_issue: str | None = None) -> dict[str, Any]:
    if len({run.plan.run_id for run in runs}) != len(runs):
        raise ValueError('One arm cannot include a Run more than once')
    expected = {row.input_id for row in manifest.conditions}
    unexpected = [
        {'run_id': run.plan.run_id, 'input_id': sample.sample_id}
        for run in runs for sample in run.plan.inputs if sample.sample_id not in expected
    ]
    issues, chronology = inspect_protocol(manifest, runs, arm, batches, task_issue)
    out_of_order = {key for pair in chronology['deviations'] for key in pair} if chronology else set()
    conditions = [_condition(row, runs, issues, out_of_order) for row in manifest.conditions]
    observations = [row for condition in conditions for row in condition['observations']]
    resources = _resources([(run, list(run.attempts.values())) for run in runs])
    return {
        **_pool(observations),
        'conditions': conditions,
        'runs': [{**run.provenance, 'protocol_mismatch': issues[run.plan.run_id]} for run in runs],
        'unexpected_inputs': unexpected,
        'resources': resources,
        'chronology': chronology,
        'historical_fingerprint': _historical_fingerprint(runs, issues) if arm == 'baseline' else None,
    }


def _historical_fingerprint(runs: list[RunRecord], issues: dict[str | None, str | None]) -> dict[str, Any]:
    observed = [
        _fingerprint(run.attempts[identity])
        for run in runs if issues[run.plan.run_id] is None
        for identity in {slot.extraction_attempt_id for slot in run.plan.planned_slots}
        if identity is not None and identity in run.attempts
    ]
    known = sorted({value for value in observed if value is not None})
    unknown = observed.count(None)
    comparison = (
        'drift_observed' if any(value != _HISTORICAL_FINGERPRINT for value in known)
        else 'unknown' if unknown or not known else 'matched'
    )
    return {'original': _HISTORICAL_FINGERPRINT, 'observed': known,
            'unavailable_attempts': unknown, 'comparison': comparison}


def _condition(labels: ConditionCommitment, runs: list[RunRecord], protocol_issues: dict[str | None, str | None],
               out_of_order: set[str]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for run in runs:
        sample = next((sample for sample in run.plan.inputs if sample.sample_id == labels.input_id), None)
        if sample is None:
            continue
        mismatch = protocol_issues[run.plan.run_id]
        destination = exclusions if mismatch else observations
        for slot in run.plan.planned_slots:
            if _template_id(slot.sample_id, slot.extraction_attempt_id) != sample.sample_id:
                continue
            row = _observe(run, slot.observation_id, slot.extraction_attempt_id, sample, labels, mismatch)
            key = f'{run.plan.run_id}/{slot.observation_id}'
            if key in out_of_order:
                row['chronology_deviation'] = True
                if row['state'] == 'scored':
                    exclusions.append(row)
                    observations.append(_unavailable('Retained extraction start order differs from the commitment.'))
                    continue
            destination.append(row)

    if len(observations) > labels.observations:
        exclusions.extend(observations)
        observations = [_unavailable('The supplied Runs contain more slots than the study predeclared.')
                        for _ in range(labels.observations)]
    observations.extend(_unavailable('No admitted Run froze this planned study slot.')
                        for _ in range(labels.observations - len(observations)))
    return {
        'condition': labels.condition,
        'matter_family': labels.matter_family,
        'input_id': labels.input_id,
        'target_counts_per_observation': {name: len(getattr(labels.targets, name))
                                          for name in ('required', 'forbidden', 'unaffected', 'sufficiency')},
        **_pool(observations),
        'observations': observations,
        'excluded_observations': exclusions,
    }


def _template_id(sample_id: str, extraction_attempt_id: str | None) -> str:
    return sample_id.rsplit('_fresh_', 1)[0] if extraction_attempt_id else sample_id


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        'state': 'unavailable', 'status': 'unavailable', 'reason': reason,
        'run_id': None, 'observation_id': None,
        'graph': None, 'quote_provenance': None, 'source_attribution': None,
        'decisions': None, 'resources': None,
    }


def _observe(run: RunRecord, observation_id: str, extraction_id: str | None, sample: ResearchInput,
             labels: ConditionCommitment, mismatch: str | None) -> dict[str, Any]:
    state, status, reason = run.states[observation_id]
    result = run.results[observation_id]
    attempts = [run.attempts[key] for key in (extraction_id, observation_id) if key in run.attempts]
    row = _unavailable(mismatch or reason or '')
    row.update(run_id=run.plan.run_id, observation_id=observation_id, status=status,
               resources=_resources([(run, attempts)]))
    if mismatch:
        return row
    extraction = run.attempts.get(extraction_id) if extraction_id else None
    request = extraction.request if extraction else None
    row.update(state=state, reason=reason,
               scorer_digests={path: run.code_hashes.get(path) for path in _SCORERS},
               extraction_started_at=extraction.started_at.isoformat() if extraction and extraction.started_at else None,
               extraction_request_matches=(request is not None and request.stage == 'extraction'
                                           and request.sources == sample.sources))
    if state == 'scored' and extraction_id and not row['extraction_request_matches']:
        row.update(state='unavailable', reason='The retained extraction request does not match the ordered Sources.')
        return row
    if state == 'scored' and result is not None and result.evaluation is not None:
        row.update(_scored_observation(result, result.evaluation, sample, labels.targets))
    return row


def _scored_observation(result: ResearchResult, score: EvaluationResult,
                        sample: ResearchInput, labels: DecisionTargets) -> dict[str, Any]:
    decisions = None
    results_sources_match = result.state is not None and result.state.sources == sample.sources
    if result.state is not None and results_sources_match:
        decisions = diagnose(result.state, sample.truth, labels)
        critical = set(decisions['required']['absent'])
        forbidden = set(decisions['forbidden']['present'])
        decisions.update(
            critical_omissions=sorted(critical),
            other_false_negatives=sorted(set(score.false_negative_edges) - critical),
            other_false_positives=sorted(set(score.false_positive_edges) - forbidden),
        )
        for group in ('required', 'forbidden', 'unaffected'):
            decisions[group]['present_count'] = len(decisions[group]['present'])
        decisions['sufficiency']['complete_count'] = len(decisions['sufficiency']['complete'])
    return {
        'graph': {
            'tp': score.tp, 'fp': score.fp, 'fn': score.fn, 'f1': score.f1,
            'exact_graph': score.fp == score.fn == 0,
            'true_positive_edges': score.true_positive_edges,
            'false_positive_edges': score.false_positive_edges,
            'false_negative_edges': score.false_negative_edges,
        },
        'quote_provenance': {
            'passed': score.provenance_passed, 'assessed': score.tp,
            'accuracy': score.provenance_accuracy,
            'passes': score.provenance_passes, 'failures': score.provenance_failures,
        },
        'source_attribution': result.source_attribution.model_dump()
                              if result.source_attribution and results_sources_match else None,
        'decisions': decisions,
        'decision_diagnostic_reason': None if decisions else 'No attached Evidence from the committed Sources.',
    }


def _pool(observations: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = Coverage(planned=len(observations))
    for row in observations:
        state = row['state']
        setattr(coverage, state, getattr(coverage, state) + 1)
    scores = [row['graph'] for row in observations if row['state'] == 'scored']
    tp, fp, fn = (sum(score[key] for score in scores) for key in ('tp', 'fp', 'fn'))
    denominator = 2 * tp + fp + fn
    return {
        'coverage': coverage.model_dump(),
        'graph': {'tp': tp, 'fp': fp, 'fn': fn,
                  'f1': (2 * tp / denominator if denominator else 0.0) if scores else None,
                  'exact_graphs': sum(score['exact_graph'] for score in scores)},
    }


def _measurement(values: Sequence[int | float | None], authority_reasons: list[str]) -> dict[str, Any]:
    measured = [value for value in values if value is not None]
    subtotal = sum(measured)
    return {'known_subtotal': subtotal, 'measured_attempts': len(measured),
            'total': subtotal if len(measured) == len(values) and not authority_reasons else None}


def _fingerprint(attempt: RetainedAttempt) -> str | None:
    value = attempt.response.raw_response.get('response_metadata', {}).get('system_fingerprint')
    return value if isinstance(value, str) and value else None


def _resources(group: list[tuple[RunRecord, list[RetainedAttempt]]]) -> dict[str, Any]:
    attempts = [(run, attempt) for run, records in group for attempt in records]
    reasons = sorted({reason for run, _ in group for reason in run.authority_reasons})
    costs = []
    for run, attempt in attempts:
        if run.plan.execution_mode == 'live':
            pricing = run.plan.pricing
            costs.append(AttemptCost(attempt_id=f'{run.plan.run_id}/{attempt.attempt_id}',
                                    cost=estimate_cost(attempt.response.usage, pricing),
                                    currency=pricing.currency if pricing else None))
    cost = incurred_cost(costs)
    if reasons:
        cost.total = None
        cost.reasons.extend(reasons)
    return {
        'retained_attempts': len(attempts),
        'authority_reasons': reasons,
        'tokens': {name: _measurement([getattr(attempt.response.usage, name) for _, attempt in attempts], reasons)
                   for name in ('input_tokens', 'output_tokens', 'cached_tokens')},
        'provider_seconds': _measurement([attempt.provider_seconds for _, attempt in attempts], reasons),
        'cost': cost.model_dump(),
        'attempts': [{
            'run_id': run.plan.run_id, 'id': attempt.attempt_id, 'status': attempt.status,
            'returned_model': attempt.response.returned_model,
            'system_fingerprint': _fingerprint(attempt),
        } for run, attempt in attempts],
    }


def _development_manifest(labels_path: Path, commitments_path: Path,
                          plan_digests: list[str] | None) -> ReportManifest:
    commitments = json.loads(commitments_path.read_text())
    labels = json.loads(labels_path.read_text())
    expected = [f'D{index}' for index in range(1, 15)]
    batches = [expected[:7], ['D8', 'D9'], ['D8', 'D9'], ['D8', 'D9'], expected[9:]]
    schedule = [condition for batch in batches for condition in batch]
    if [row['condition'] for row in labels] != expected or commitments['baseline_schedule'] != schedule:
        raise ValueError('Development reporting requires the frozen D1–D14 roster and 18-slot schedule')
    counts = Counter(schedule)
    rows = {row['condition']: row for row in commitments['conditions']}
    fields = ('matter_family', 'case_id', 'source_digest', 'truth_digest', 'extraction_digest', 'annotation_digest')
    conditions = []
    for label in labels:
        key = label['condition']
        row = rows[key]
        if row['input_id'] != label['input_id']:
            raise ValueError(f'Committed input ID differs for {key}')
        conditions.append({**label, **{key: row[key] for key in fields}, 'observations': counts[key]})
    return ReportManifest.model_validate({
        'evaluator_version': 'semantic_edges_v1', 'conditions': conditions,
        'baseline_plan_digests': plan_digests, 'development_batches': batches,
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='phase', required=True)
    development = commands.add_parser('development', help='Report the 18-slot development baseline')
    development.add_argument('--commitments', required=True, type=Path, help='Retained preflight.json')
    development.add_argument('--baseline-plan-digest', action='append',
                             help='Approved Run plan digest. Repeat in committed batch order.')
    development.add_argument('--labels', default=Path(__file__).with_name('development.json'), type=Path)
    final = commands.add_parser('final', help='Report the four held-out pairs after unsealing')
    final.add_argument('--commitments', required=True, type=Path, help='Private frozen final report manifest')
    final.add_argument('--final-run', action='append', type=Path, default=[])
    for command in (development, final):
        command.add_argument('--baseline-run', action='append', type=Path, default=[],
                             help='Frozen Workbench Run directory. Repeat for multiple Runs.')
    options = parser.parse_args()
    if options.phase == 'development':
        manifest = _development_manifest(options.labels, options.commitments, options.baseline_plan_digest)
        report = development_report(manifest, options.baseline_run)
    else:
        manifest = ReportManifest.model_validate_json(options.commitments.read_bytes())
        if len(manifest.conditions) != 4 or manifest.execution_mode != 'live':
            parser.error('The final protocol requires four conditions and live execution mode')
        report = final_report(manifest, options.baseline_run, options.final_run)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
