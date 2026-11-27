"""Regenerate unverified comparisons from the fixed plan and retained observations."""
from collections import Counter
from pathlib import Path
from typing import Any

from private_client_graph.research.artifacts import checksum

from .assessment import (
    Plan, Receipt, ReservationSnapshot, exceeded_envelope, execution_active, frozen_rates,
    open_plan, read_receipt, reservation_snapshot, upper_cost, validate_judge_response,
)
from .inputs import Item
from .judging import Judgment

TEMPORAL_LIMITATION = (
    'Benchmark v4 targets have no explicit assessment cutoff. Timing findings, including satisfied, '
    'describe the submitted quotations. When a claim depends on a cutoff, temporal correctness at that '
    'cutoff remains unverified.'
)


def report(directory: Path) -> dict[str, Any]:
    plan, digest, task = open_plan(directory)
    reservations = reservation_snapshot(plan, digest, task)
    targets = [_row(directory, plan, item, reservations) for item in plan.inputs.targets]
    controls = [_row(directory, plan, item, reservations) for item in plan.inputs.controls]
    incomplete = [row for row in targets if row['deterministic']['exact_outcome'] == 'incomplete']
    count = sum('potentially_sufficient_overlooked_by_exact_matching' in row['flags'] for row in incomplete)
    judged_incomplete = sum(row['status'] == 'judged' for row in incomplete)
    joint_only = [row for row in targets if row['deterministic']['joint_only']]
    quality = plan.inputs.evidence_quality
    return {
        'assessment': plan.version,
        'status': 'Exploratory and unverified',
        'temporal_limitation': TEMPORAL_LIMITATION,
        'plan_sha256': digest,
        'extractor_run': plan.inputs.extractor_run,
        'run_id': plan.inputs.extractor_run,
        'evaluator': {
            'version': plan.version,
            'prompt_sha256': checksum(plan.system_prompt.encode()),
            'model': plan.settings.model,
            'settings': plan.settings.model_dump(mode='json'),
            'observation_origin': plan.inputs.evidence_quality.observation_origin,
        },
        'extractor_manifest_sha256': plan.inputs.extractor_manifest_sha256,
        'deterministic_baseline': {
            'report_version': quality.version,
            'benchmark_sha256': quality.scope_sha256,
            'qualified_reference_sha256': quality.qualified_reference_sha256,
            'scorer_sha256': quality.scoring_sha256,
            'proof_completion': quality.complete_proof.model_dump(mode='json'),
            'multi_source_proof_completion': quality.joint_only_complete_proof.model_dump(mode='json'),
            'multi_source_evidence_coverage': quality.joint_only_coverage.model_dump(mode='json'),
        },
        'target_summary': {
            'formal_targets': len(targets),
            'recovered_targets': sum(item.packet is not None for item in plan.inputs.targets),
            'deterministic_outcomes': dict(Counter(row['deterministic']['exact_outcome'] for row in targets)),
            'semantic_outcomes': dict(Counter(row['status'] for row in targets)),
            'verdicts': _verdicts(targets),
            'flags': dict(Counter(flag for row in targets for flag in row['flags'])),
            'verdicts_by_exact_outcome': {
                outcome: _verdicts([row for row in targets if row['deterministic']['exact_outcome'] == outcome])
                for outcome in ('complete', 'incomplete')
            },
            'joint_only': {
                'formal_targets': len(joint_only),
                'semantic_outcomes': dict(Counter(row['status'] for row in joint_only)),
                'verdicts': _verdicts(joint_only),
            },
            'multi_source_evidence': _multi_source_evidence(joint_only),
            'potentially_sufficient_overlooked_by_exact_matching': {
                'count': count if judged_incomplete else None,
                'formal_target_denominator': len(targets),
                'recovered_exact_incomplete_denominator': len(incomplete),
                'recovered_exact_incomplete_judged': judged_incomplete,
            },
        },
        'control_summary': {
            'count': len(controls),
            'semantic_outcomes': dict(Counter(row['status'] for row in controls)),
            'verdicts': _verdicts(controls),
            'supported_warnings': sum('supported_control' in row['flags'] for row in controls),
        },
        'operations': _operations(plan, [*targets, *controls], reservations.ids),
        'targets': targets,
        'controls': controls,
    }


def _row(directory: Path, plan: Plan, item: Item, reservations: ReservationSnapshot) -> dict[str, Any]:
    row: dict[str, Any] = {
        'id': item.id,
        'condition': item.condition,
        'family': item.family,
        'edge': item.edge,
        'control': item.control,
        'deterministic': item.baseline.model_dump(mode='json') if item.baseline else None,
        'flags': [],
    }
    packet = item.packet
    if packet is None:
        return {**row, 'status': 'deterministic_delivery_failure'}
    row['quotations'] = [{**quote.model_dump(mode='json'), 'source_id': item.source_ids[quote.source]}
                         for quote in packet.quotations]
    row['request_sha256'] = plan.request_sha256[item.id]
    reused = plan.reused.get(item.id)
    receipt = reused.receipt if reused else read_receipt(directory, plan, item, reservations)
    if receipt is None:
        if item.id not in reservations.ids:
            return {**row, 'status': 'unattempted'}
        return {**row, 'status': 'awaiting_receipt' if execution_active(directory, item) else 'interrupted'}
    if reused:
        row['reuse'] = {'origin_run': reused.origin_run, 'origin_plan_sha256': reused.origin_plan_sha256,
                        'origin_request_sha256': receipt.request_sha256,
                        'origin_receipt_sha256': reused.origin_receipt_sha256}
    else:
        row['provider'] = _provider_details(plan, receipt)
    if receipt.response is None:
        return {**row, 'status': 'provider_failed', 'error': receipt.provider_error}
    try:
        judgment = validate_judge_response(plan, item, receipt.response)
    except ValueError as error:
        content = receipt.response.raw_response.get('content')
        return {**row, 'status': 'invalid_judgment', 'error': str(error),
                'invalid_response': content if isinstance(content, str) else None}
    return {**row, 'status': 'judged', 'judgment': judgment.model_dump(mode='json'),
            'flags': _flags(item, judgment)}


def _flags(item: Item, judgment: Judgment) -> list[str]:
    flags = []
    supported = judgment.verdict == 'Supported'
    if item.control is not None:
        return ['supported_control'] if supported else []
    assert item.baseline is not None and item.packet is not None
    baseline = item.baseline
    cited = {identity for fact in judgment.facts if fact.status == 'satisfied' for identity in fact.quotation_ids}
    if baseline.exact_outcome == 'incomplete':
        if supported:
            flags.append('potentially_sufficient_overlooked_by_exact_matching')
        elif judgment.verdict == 'Partially Supported' and cited.difference(baseline.matches_any_approved_pair):
            flags.append('potential_new_partial_support')
    if baseline.exact_outcome == 'complete' and not supported:
        flags.append('exact_complete_not_called_supported')
    if supported and baseline.joint_only and len({quote.source for quote in item.packet.quotations
                                                 if quote.id in cited}) == 1:
        flags.append('joint_only_supported_with_one_cited_source')
    return flags


def _multi_source_evidence(targets: list[dict[str, Any]]) -> dict[str, Any]:
    judged = [row for row in targets if row['status'] == 'judged']
    return {
        'targets': len(targets),
        'judged': len(judged),
        'supported_with_multiple_sources': sum(
            row['judgment']['verdict'] == 'Supported' and _cites_multiple_supporting_sources(row)
            for row in judged
        ),
        'fact_coverage': sum(_satisfied_fact_fraction(row) for row in judged) / len(targets) if judged else None,
    }


def _cites_multiple_supporting_sources(row: dict[str, Any]) -> bool:
    cited = {identity for fact in row['judgment']['facts'] if fact['status'] == 'satisfied'
             for identity in fact['quotation_ids']}
    return len({quote['source_id'] for quote in row['quotations'] if quote['id'] in cited}) >= 2


def _satisfied_fact_fraction(row: dict[str, Any]) -> float:
    applicable = [fact for fact in row['judgment']['facts'] if fact['status'] != 'inapplicable']
    return sum(fact['status'] == 'satisfied' for fact in applicable) / len(applicable)


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


def _verdicts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(row['judgment']['verdict'] for row in rows if row['status'] == 'judged'))


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
