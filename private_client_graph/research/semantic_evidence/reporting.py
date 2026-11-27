"""Regenerate unverified comparisons from the fixed plan and retained observations."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from private_client_graph.research.artifacts import checksum

from .assessment import (
    Plan, Receipt, ReservationSnapshot, exceeded_envelope, execution_active, frozen_rates,
    open_plan, read_receipt, reservation_snapshot, upper_cost, validate_judge_response,
)
from .inputs import Item
from .judging import Quotation

SCOPE_NOTE = ('Approved members define the comparison. Preserve stated dates, timing and authority. '
              'A cutoff absent from the approved text is not inferred.')


def report(directory: Path) -> dict[str, Any]:
    plan, digest, task = open_plan(directory)
    reservations = reservation_snapshot(plan, digest, task)
    targets = [_row(directory, plan, item, reservations) for item in plan.inputs.targets]
    quality = plan.inputs.evidence_quality
    return {
        'assessment': plan.version,
        'status': 'AI-assisted, unverified',
        'scope_note': SCOPE_NOTE,
        'plan_sha256': digest,
        'extractor_run': plan.inputs.extractor_run,
        'run_id': plan.inputs.extractor_run,
        'evaluator': {
            'version': plan.version,
            'prompt_sha256': checksum(plan.system_prompt.encode()),
            'model': plan.settings.model,
            'settings': plan.settings.model_dump(mode='json'),
            'observation_origin': quality.observation_origin,
        },
        'extractor_manifest_sha256': plan.inputs.extractor_manifest_sha256,
        'deterministic_baseline': {
            'report_version': quality.version,
            'benchmark_sha256': quality.scope_sha256,
            'qualified_reference_sha256': quality.qualified_reference_sha256,
            'scorer_sha256': quality.scoring_sha256,
            'proof_completion': quality.complete_proof.model_dump(mode='json'),
            'multi_source_evidence_coverage': quality.joint_only_coverage.model_dump(mode='json'),
        },
        'target_summary': _target_summary(targets),
        'operations': _operations(plan, targets, reservations.ids),
        'targets': targets,
    }


def _target_summary(targets: list[dict[str, Any]]) -> dict[str, Any]:
    multi_source = [row for row in targets if row['deterministic']['joint_only']]
    total_coverage = sum((_best_coverage(row) for row in multi_source), Fraction())
    return {
        'formal_targets': len(targets),
        'semantic_outcomes': dict(Counter(row['status'] for row in targets)),
        'pair_verdicts': dict(Counter(decision['verdict'] for row in targets for decision in row['decisions'])),
        'candidate_pairs': sum(len(row['candidate_pairs']) for row in targets),
        'evidence_support': _target_rate(sum(any(route['matched_members'] for route in row['routes'])
                                             for row in targets), len(targets)),
        'proof_completion': _target_rate(sum(any(route['complete'] for route in row['routes'])
                                              for row in targets), len(targets)),
        'multi_source_evidence_coverage': {
            'targets': len(multi_source),
            'matched_target_equivalents': float(total_coverage),
            'mean': float(total_coverage / len(multi_source)) if multi_source else None,
        },
        'targets_with_added_matches': sum(bool(row['semantic_members']) for row in targets),
        'additional_matched_members': sum(len(row['semantic_members']) for row in targets),
        'newly_completed_proofs': sum(row['deterministic']['exact_outcome'] != 'complete'
                                      and any(route['complete'] for route in row['routes']) for row in targets),
    }


def _best_coverage(row: dict[str, Any]) -> Fraction:
    return max(Fraction(len(route['matched_members']), len(route['members'])) for route in row['routes'])


def _target_rate(count: int, targets: int) -> dict[str, int | float | None]:
    return {'count': count, 'targets': targets, 'rate': count / targets if targets else None}


def _row(directory: Path, plan: Plan, item: Item, reservations: ReservationSnapshot) -> dict[str, Any]:
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
    row.update(_assessment_outcome(directory, plan, item, reservations))
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


def _assessment_outcome(directory: Path, plan: Plan, item: Item, reservations: ReservationSnapshot) -> dict[str, Any]:
    if item.baseline.exact_outcome in ('missing_relationship', 'unavailable_graph'):
        return {'status': 'deterministic_delivery_failure'}
    if item.packet is None:
        return {'status': 'no_eligible_comparison'}
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
