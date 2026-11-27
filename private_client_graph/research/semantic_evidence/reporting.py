"""Regenerate unverified comparisons from the fixed plan and retained observations."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from private_client_graph.research.artifacts import checksum
from private_client_graph.research.benchmark_v4 import configured_custody, load_workload

from .assessment import (
    SETTINGS, SYSTEM_PROMPT, Plan, Receipt, ReservationSnapshot, exceeded_envelope, execution_active, frozen_rates,
    open_plan, read_receipt, reservation_snapshot, upper_cost, validate_judge_response,
)
from .inputs import VERSION, AssessmentInputs, Item, extract_inputs
from .judging import Quotation
from .store import find

METHODOLOGY = 'Ground-Truth-Aligned Evidence Evaluation'
EvaluationState = Literal['exact_only', 'pending', 'complete', 'complete_with_failures']
SCOPE_NOTE = ('Approved Source quotations define the comparison. Stated dates, timing and authority '
              'are material. Model-assessed equivalence has no independent verification.')


def report_run(root: Path, run_id: str) -> dict[str, Any]:
    directory = find(root, run_id)
    if directory is not None:
        return report(directory)
    custody = configured_custody()
    if custody is None:
        raise ValueError('Evaluation requires the verified private Benchmark v4 custody')
    return exact_report(extract_inputs((root / run_id).resolve(), load_workload(custody)))


def exact_report(inputs: AssessmentInputs) -> dict[str, Any]:
    """Read a completed Run's exact baseline without freezing a plan or spending."""
    targets = [_row(item, {'status': _initial_status(item)}) for item in inputs.targets]
    return _report(inputs, targets, state='exact_only')


def report(directory: Path) -> dict[str, Any]:
    plan, digest, task = open_plan(directory)
    reservations = reservation_snapshot(plan, digest, task)
    targets = [_row(item, _assessment_outcome(directory, plan, item, reservations))
               for item in plan.inputs.targets]
    return _report(plan.inputs, targets, state=_assessment_state(targets), digest=digest,
                   operations=_operations(plan, targets, reservations.ids))


def _assessment_state(targets: list[dict[str, Any]]) -> EvaluationState:
    statuses = {row['status'] for row in targets}
    if statuses.intersection({'unattempted', 'awaiting_receipt', 'interrupted'}):
        return 'pending'
    if statuses.intersection({'invalid_judgment', 'provider_failed'}):
        return 'complete_with_failures'
    return 'complete'


def _report(inputs: AssessmentInputs, targets: list[dict[str, Any]], *, state: EvaluationState,
            digest: str | None = None, operations: dict[str, Any] | None = None) -> dict[str, Any]:
    quality = inputs.evidence_quality
    qualified = quality.qualified_graph
    return {
        'assessment': VERSION,
        'methodology': METHODOLOGY,
        'state': state,
        'scope_note': SCOPE_NOTE,
        'plan_sha256': digest,
        'extractor_run': inputs.extractor_run,
        'run_id': inputs.extractor_run,
        'evaluator': {
            'version': VERSION,
            'prompt_sha256': checksum(SYSTEM_PROMPT.encode()),
            'model': SETTINGS.model,
            'settings': SETTINGS.model_dump(mode='json'),
            'observation_origin': quality.observation_origin,
        },
        'extractor_manifest_sha256': inputs.extractor_manifest_sha256,
        'graph_f1': qualified.model_dump(mode='json') if qualified else None,
        'deterministic_baseline': {
            'report_version': quality.version,
            'benchmark_sha256': quality.scope_sha256,
            'qualified_reference_sha256': quality.qualified_reference_sha256,
            'scorer_sha256': quality.scoring_sha256,
            'proof_completion': quality.complete_proof.model_dump(mode='json'),
            'multi_source_evidence_coverage': quality.joint_only_coverage.model_dump(mode='json'),
        },
        'target_summary': _target_summary(targets, exact_only=state in ('exact_only', 'pending')),
        'operations': operations,
        'targets': targets,
    }


def _target_summary(targets: list[dict[str, Any]], *, exact_only: bool) -> dict[str, Any]:
    coverage = [_best_coverage(row, exact_only=exact_only) for row in targets]
    multi_source = [value for row, value in zip(targets, coverage, strict=True) if row['deterministic']['joint_only']]
    total_coverage = sum(multi_source, Fraction())
    return {
        'formal_targets': len(targets),
        'semantic_outcomes': dict(Counter(row['status'] for row in targets)),
        'pair_verdicts': dict(Counter(decision['verdict'] for row in targets for decision in row['decisions'])),
        'candidate_pairs': sum(len(row['candidate_pairs']) for row in targets),
        'evidence_support': _target_rate(sum(value > 0 for value in coverage), len(targets)),
        'proof_completion': _target_rate(sum(value == 1 for value in coverage), len(targets)),
        'multi_source_evidence_coverage': {
            'targets': len(multi_source),
            'matched_target_equivalents': float(total_coverage),
            'mean': float(total_coverage / len(multi_source)) if multi_source else None,
        },
        'exact_matched_members': sum(len(row['exact_matches']) for row in targets),
        'unmatched_required_members': sum(len(row['members']) - len(row['exact_matches']) - len(row['semantic_members'])
                                          for row in targets),
        'targets_with_added_matches': sum(bool(row['semantic_members']) for row in targets),
        'additional_matched_members': sum(len(row['semantic_members']) for row in targets),
        'newly_completed_proofs': sum(row['deterministic']['exact_outcome'] != 'complete'
                                      and any(route['complete'] for route in row['routes']) for row in targets),
    }


def _best_coverage(row: dict[str, Any], *, exact_only: bool) -> Fraction:
    exact = row['exact_matches']
    return max(Fraction(sum(not exact_only or member in exact for member in route['matched_members']),
                        len(route['members'])) for route in row['routes'])


def _target_rate(count: int, targets: int) -> dict[str, int | float | None]:
    return {'count': count, 'targets': targets, 'rate': count / targets if targets else None}


def _row(item: Item, outcome: dict[str, Any]) -> dict[str, Any]:
    packet = item.packet
    row: dict[str, Any] = {
        'id': item.id,
        'condition': item.condition,
        'family': item.family,
        'edge': item.edge,
        'deterministic': item.baseline.model_dump(mode='json'),
        'members': [_attributed(quote, item) for quote in item.members],
        'quotations': [_attributed(quote, item) for quote in item.quotations],
        'exact_matches': item.exact,
        'candidate_pairs': [pair.model_dump(mode='json') for pair in packet.pairs] if packet else [],
        'decisions': [],
    }
    row.update(outcome)
    semantic = {decision['member_id'] for decision in row['decisions'] if decision['verdict'] == 'Equivalent'}
    matched = set(row['exact_matches']) | semantic
    row['semantic_members'] = sorted(semantic)
    row['routes'] = [{
        'members': list(route),
        'matched_members': [member for member in route if member in matched],
        'complete': matched.issuperset(route),
    } for route in item.alternatives]
    return row


def _attributed(quote: Quotation, item: Item) -> dict[str, Any]:
    return {**quote.model_dump(mode='json'), 'source_id': item.source_ids[quote.source]}


def _initial_status(item: Item) -> str:
    if item.baseline.exact_outcome in ('missing_relationship', 'unavailable_graph'):
        return 'deterministic_delivery_failure'
    return 'unattempted' if item.packet is not None else 'no_eligible_comparison'


def _assessment_outcome(directory: Path, plan: Plan, item: Item, reservations: ReservationSnapshot) -> dict[str, Any]:
    initial = _initial_status(item)
    if initial != 'unattempted':
        return {'status': initial}
    outcome: dict[str, Any] = {'request_sha256': plan.request_sha256[item.id]}
    reused = plan.reused.get(item.id)
    receipt = reused.receipt if reused else read_receipt(directory, plan, item, reservations)
    if receipt is None:
        if item.id not in reservations.ids:
            return {**outcome, 'status': 'unattempted'}
        return {**outcome, 'status': 'awaiting_receipt' if execution_active(directory, item) else 'interrupted'}
    if reused:
        outcome['reuse'] = {'origin_run': reused.origin_run, 'origin_plan_sha256': reused.origin_plan_sha256,
                            'origin_request_sha256': receipt.request_sha256,
                            'origin_receipt_sha256': reused.origin_receipt_sha256}
    else:
        outcome['provider'] = _provider_details(plan, receipt)
    if receipt.response is None:
        return {**outcome, 'status': 'provider_failed', 'error': receipt.provider_error}
    try:
        judgment = validate_judge_response(plan, item, receipt.response)
    except ValueError as error:
        content = receipt.response.raw_response.get('content')
        return {**outcome, 'status': 'invalid_judgment', 'error': str(error),
                'invalid_response': content if isinstance(content, str) else None}
    return {**outcome, 'status': 'judged',
            'decisions': [decision.model_dump(mode='json') for decision in judgment.decisions]}


def _provider_details(plan: Plan, receipt: Receipt) -> dict[str, Any]:
    details: dict[str, Any] = {'latency_seconds': receipt.latency_seconds, 'estimated_peak_usd': None}
    response = receipt.response
    if response is None:
        return {**details, 'status_code': receipt.provider_status_code}
    usage = response.usage
    estimate = None
    if usage.input_tokens is not None and usage.output_tokens is not None:
        estimate = (usage.input_tokens * plan.pricing.input_per_million
                    + usage.output_tokens * plan.pricing.output_per_million) / 1_000_000
    return {**details, 'usage': usage.model_dump(mode='json'), 'estimated_peak_usd': estimate,
            'returned_model': response.returned_model, 'exceeded_envelope': exceeded_envelope(plan, response),
            'finish_reason': response.raw_response.get('response_metadata', {}).get('finish_reason')}


def _operations(plan: Plan, rows: list[dict[str, Any]], reservations: frozenset[str]) -> dict[str, Any]:
    providers = [row['provider'] for row in rows if 'provider' in row]
    costs = [provider['estimated_peak_usd'] for provider in providers if provider['estimated_peak_usd'] is not None]
    latencies = [provider['latency_seconds'] for provider in providers]
    return {
        'requested_model': plan.settings.model,
        'planned_attempts': plan.max_calls,
        'task_call_ceiling': plan.task_limit,
        'reserved_attempts': len(reservations),
        'reused_judgments': len(plan.reused),
        'usd_ceiling': str(plan.max_usd),
        'maximum_estimated_peak_usd': str(upper_cost(plan, frozen_rates(plan))),
        'known_estimated_peak_usd': sum(costs) if costs else None,
        'reserved_attempts_without_usage': len(reservations) - len(costs),
        'mean_latency_seconds': sum(latencies) / len(latencies) if latencies else None,
        'returned_models': sorted({provider['returned_model'] for provider in providers if provider.get('returned_model')}),
    }
