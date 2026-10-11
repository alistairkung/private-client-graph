"""Deterministic projections of frozen Run observations; no execution access."""
from decimal import Decimal
import hashlib
import json
from typing import Literal

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.metrics import estimate_cost
from private_client_graph.research.provider import TokenUsage
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.run_plan import RunPlan

from .run_evaluation_contracts import (
    AttemptCost, BenchmarkScope, CaseAggregate, ChartEligibility,
    ObservationCoverage, ObservationPair, PairingExclusion, PlannedObservation,
    RunAggregate, RunComparison, RunCost, RunEvaluation, ScopeInput,
)


def evaluate_run(bundle: Bundle) -> RunEvaluation:
    if not isinstance(bundle.plan, RunPlan):
        reason = 'Legacy bundle lacks a verified single-configuration Run mapping and planned slots.'
        return RunEvaluation(run_id=bundle.manifest['experiment_id'], aggregate=RunAggregate(reasons=[reason]),
            cost=RunCost(known_subtotal=None, reasons=[reason]), reasons=[reason],
            eligibility=ChartEligibility(f1_reasons=[reason], cost_reasons=[reason]))
    slots = [PlannedObservation.model_validate(row.model_dump()) for row in bundle.plan.planned_slots]
    results = [ResearchResult.model_validate(row) for row in bundle.results()]
    attempts, authority_reasons = retained_attempts(bundle)
    lifecycle: list[dict] = [json.loads(path.read_text()) for path in (bundle.path / 'lifecycle').glob('*.json')]
    lifecycle.sort(key=lambda row: row['at'])
    current = lifecycle[-1] if lifecycle else {'state': 'frozen'}
    aggregate = aggregate_observations(slots, results, _slot_statuses(slots, attempts, current, bundle.path.name))
    cost = _bundle_cost(bundle, attempts, authority_reasons)
    f1_reasons = [] if aggregate.f1 is not None else ['No scored planned observations.']
    return RunEvaluation(run_id=bundle.plan.run_id or bundle.manifest['experiment_id'], aggregate=aggregate,
        cost=cost, scope=_benchmark_scope(bundle.plan),
        artifact_digest=_digest({'manifest': bundle.manifest,
            'results': [row.model_dump(mode='json') for row in results], 'attempts': attempts,
            'authority_reasons': authority_reasons, 'lifecycle': lifecycle}),
        eligibility=ChartEligibility(f1_by_run=aggregate.f1 is not None,
            f1_vs_cost=aggregate.f1 is not None and cost.total is not None,
            f1_reasons=f1_reasons, cost_reasons=[*f1_reasons, *cost.reasons]))


def compare_runs(left: Bundle, right: Bundle) -> RunComparison:
    first, second = evaluate_run(left), evaluate_run(right)
    comparison = RunComparison(left_run_id=first.run_id, right_run_id=second.run_id)
    if first.scope is None or second.scope is None:
        comparison.reasons = ['One or both bundles lack a verified Run scope.']
        return comparison
    for field in ('input_mode', 'evaluator_version', 'aggregate_version'):
        if getattr(first.scope, field) != getattr(second.scope, field):
            comparison.scope_differences.append(f'{field} differs.')
    comparison.scope_differences.extend(_input_scope_differences(first.scope, second.scope))
    comparison.comparable_scope = not comparison.scope_differences
    assert isinstance(left.plan, RunPlan) and isinstance(right.plan, RunPlan)
    for label, a, b in (
        ('Configuration', left.plan.resolver, right.plan.resolver),
        ('Model/settings', left.plan.settings, right.plan.settings),
        ('Effective model', left.plan.effective_model, right.plan.effective_model),
        ('Code/dependency/prompt provenance', left.manifest.get('provenance'), right.manifest.get('provenance')),
    ):
        if a != b:
            comparison.provenance_differences.append(f'{label} differs.')
    _pair_exact_inputs(left, right, comparison)
    comparison.unqualified_improvement_allowed = (comparison.comparable_scope
        and first.aggregate.state == second.aggregate.state == 'complete'
        and first.aggregate.coverage == second.aggregate.coverage and not comparison.exclusions)
    if not comparison.unqualified_improvement_allowed:
        comparison.reasons.append('Scope, complete scored coverage and verified exact pairing are required for an unqualified comparison.')
    return comparison


def aggregate_observations(slots: list[PlannedObservation], results: list[ResearchResult],
                           execution_statuses: dict[str, str] | None = None) -> RunAggregate:
    if len({slot.observation_id for slot in slots}) != len(slots):
        raise ValueError('Duplicate planned observation identity')
    keys = [(slot.sample_id, slot.configuration, slot.repetition) for slot in slots]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate planned observation mapping')
    if len({slot.configuration for slot in slots}) > 1:
        raise ValueError('A Run contains one selected configuration')
    aggregate = RunAggregate()
    indexed = {(row.sample_id, row.configuration, row.repetition or 0): row for row in results}
    if len(indexed) != len(results):
        raise ValueError('Duplicate result identity')
    cases = {slot.case_id: CaseAggregate(case_id=slot.case_id) for slot in slots}
    for slot in slots:
        row = indexed.get((slot.sample_id, slot.configuration, slot.repetition))
        if row and row.case_id != slot.case_id:
            raise ValueError('Result Case identity differs from its frozen observation slot')
        status = row.status if row else (execution_statuses or {}).get(slot.observation_id, 'not_attempted')
        observation = _observation_coverage(slot, row, status)
        aggregate.observations.append(observation)
        state = observation.state
        case = cases[slot.case_id]
        for coverage in (case.coverage, aggregate.coverage):
            coverage.planned += 1
            setattr(coverage, state, getattr(coverage, state) + 1)
        if state == 'scored' and row and row.evaluation:
            for counts in (case, aggregate):
                counts.tp += row.evaluation.tp
                counts.fp += row.evaluation.fp
                counts.fn += row.evaluation.fn
    aggregate.cases = [cases[key] for key in sorted(cases)]
    aggregate.f1 = _f1(aggregate.tp, aggregate.fp, aggregate.fn, aggregate.coverage.scored)
    for case in aggregate.cases:
        case.f1 = _f1(case.tp, case.fp, case.fn, case.coverage.scored)
    if aggregate.coverage.scored:
        aggregate.state = ('complete' if aggregate.coverage.scored == aggregate.coverage.planned else 'provisional')
    if aggregate.state == 'provisional':
        aggregate.reasons.append('Only scored survivors contribute; incomplete coverage can introduce selection bias.')
    return aggregate


def incurred_cost(attempts: list[AttemptCost]) -> RunCost:
    """Sum authoritative incurred attempts, excluding inherited or simulated work."""
    unique: dict[str, AttemptCost] = {}
    for attempt in attempts:
        if not attempt.incurred:
            continue
        if attempt.attempt_id in unique and unique[attempt.attempt_id] != attempt:
            raise ValueError('Conflicting records for one incurred attempt')
        unique[attempt.attempt_id] = attempt
    unpriced = [row for row in unique.values() if row.cost is None or not row.currency]
    currencies = {row.currency for row in unique.values() if row.cost is not None and row.currency}
    reasons = [f'{row.attempt_id}: {row.reason or "Usage or pricing unavailable."}' for row in unpriced]
    if len(currencies) > 1:
        return RunCost(known_subtotal=None, currency=None, attempts=len(unique),
            unpriced_attempts=len(unpriced), reasons=['Incompatible currencies; no combined total.', *reasons])
    subtotal = sum((Decimal(str(row.cost)) for row in unique.values()
        if row.cost is not None and row.currency), Decimal(0))
    return RunCost(total=None if unpriced else float(subtotal), known_subtotal=float(subtotal),
        currency=next(iter(currencies), 'USD'), attempts=len(unique),
        unpriced_attempts=len(unpriced), reasons=reasons)


def _f1(tp: int, fp: int, fn: int, scored: int) -> float | None:
    denominator = 2 * tp + fp + fn
    return (2 * tp / denominator if denominator else 0.0) if scored else None


def _benchmark_scope(plan: RunPlan) -> BenchmarkScope:
    inputs = [ScopeInput(input_id=row.sample_id, case_id=row.case_id,
        cohort='fresh' if plan.input_mode == 'fresh' else row.cohort,
        source_digest=hashlib.sha256(row.source.encode()).hexdigest(),
        truth_digest=_digest(row.truth.model_dump(mode='json')),
        samples=plan.fresh_extractions if plan.input_mode == 'fresh' else 1,
        repetitions=plan.repetitions) for row in plan.inputs]
    inputs.sort(key=lambda row: row.input_id)
    identity = dict(inputs=[row.model_dump() for row in inputs], input_mode=plan.input_mode,
        evaluator_version=plan.evaluator_version, aggregate_version=plan.aggregate_version)
    allocations = {case_id: sum(row.samples * row.repetitions for row in inputs if row.case_id == case_id)
                   for case_id in {row.case_id for row in inputs}}
    return BenchmarkScope(identity=_digest(identity), inputs=inputs, input_mode=plan.input_mode,
        evaluator_version=plan.evaluator_version, aggregate_version=plan.aggregate_version,
        unequal_allocation=len(set(allocations.values())) > 1)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def retained_attempts(bundle: Bundle) -> tuple[list[dict], list[str]]:
    """Read shared-only reservations without invoking mutating crash recovery."""
    local = bundle.attempts()
    if bundle.plan.kind != 'live_experiment':
        return local, []
    if not bundle.task_ledger.is_dir():
        return local, ['Authoritative task ledger is unavailable; incurred attempts cannot be verified.']
    prefix = bundle.manifest['experiment_id']
    shared = [json.loads(path.read_text()) for path in
              sorted((bundle.task_ledger / 'reservations').glob(f'{prefix}-*.json'))]
    shared_ids = {row['attempt_id'] for row in shared}
    missing = any(row['attempt_id'] not in shared_ids for row in local)
    local_ids = {row['attempt_id'] for row in local}
    return [*local, *(row for row in shared if row['attempt_id'] not in local_ids)], (
        ['Authoritative task ledger is incomplete.'] if missing else [])


def _bundle_cost(bundle: Bundle, attempts: list[dict], reasons: list[str]) -> RunCost:
    if bundle.plan.kind != 'live_experiment':
        return incurred_cost([])
    pricing = bundle.plan.pricing
    costs = [AttemptCost(attempt_id=row['attempt_id'],
        cost=estimate_cost(TokenUsage.model_validate(row.get('response', {}).get('usage', {})), pricing),
        currency=pricing.currency if pricing else None,
        reason='Retained usage or pricing unavailable.') for row in attempts]
    value = incurred_cost(costs)
    if reasons:
        value.total = None
        value.reasons.extend(reasons)
    return value


def _slot_statuses(slots: list[PlannedObservation], attempts: list[dict],
                   current: dict, bundle_name: str) -> dict[str, str]:
    indexed = {row['attempt_id']: row for row in attempts}
    states = {}
    for slot in slots:
        attempt = indexed.get(slot.observation_id)
        upstream = indexed.get(slot.extraction_attempt_id) if slot.extraction_attempt_id else None
        relevant = attempt or (upstream if upstream and upstream['status'] != 'completed' else None)
        if relevant:
            state = relevant['status']
            current_authority = f"{bundle_name}-{current.get('invocation', '')}"
            if (state == 'uncertain' and current['state'] in ('running', 'stopping')
                    and relevant.get('authorization') == current_authority):
                state = 'running'
            states[slot.observation_id] = state
    return states


def _pair_exact_inputs(left: Bundle, right: Bundle, comparison: RunComparison) -> None:
    if not isinstance(left.plan, RunPlan) or not isinstance(right.plan, RunPlan):
        return
    first, second = _pairable_inputs(left), _pairable_inputs(right)
    matched_left: set[str] = set()
    matched_right: set[str] = set()
    for key in sorted(first.keys() & second.keys()):
        if len(first[key]) != 1 or len(second[key]) != 1:
            continue
        a, b = first[key][0], second[key][0]
        left_slots = sorted((row for row in left.plan.planned_slots if row.sample_id == a), key=lambda row: row.repetition)
        right_slots = sorted((row for row in right.plan.planned_slots if row.sample_id == b), key=lambda row: row.repetition)
        if len(left_slots) != len(right_slots):
            continue
        comparison.matched_inputs += 1
        for x, y in zip(left_slots, right_slots):
            comparison.pairs.append(ObservationPair(left_observation=x.observation_id,
                right_observation=y.observation_id, left_sample=a, right_sample=b))
            matched_left.add(x.observation_id)
            matched_right.add(y.observation_id)
    sides: list[tuple[Literal['left', 'right'], RunPlan, set[str]]] = [('left', left.plan, matched_left), ('right', right.plan, matched_right)]
    for side, plan, matched in sides:
        comparison.exclusions.extend(PairingExclusion(side=side, observation_id=row.observation_id,
            reason='No independently verified unique Source/truth/cohort/extraction match with equal observation allocation.')
            for row in plan.planned_slots if row.observation_id not in matched)


def _pairable_inputs(bundle: Bundle) -> dict[str, list[str]]:
    plan = bundle.plan
    if not isinstance(plan, RunPlan):
        return {}
    # Fresh observations remain unpaired without an independent exact-match record.
    # Equal model output bytes alone do not prove shared extraction execution.
    if plan.input_mode == 'fresh':
        return {}
    grouped: dict[str, list[str]] = {}
    for sample in plan.inputs:
        if sample.extraction is None:
            continue
        key = _digest(dict(case_id=sample.case_id, cohort=sample.cohort,
            source=sample.source, truth=sample.truth.model_dump(mode='json'),
            extraction=sample.extraction.model_dump(mode='json')))
        grouped.setdefault(key, []).append(sample.sample_id)
    return grouped


def _input_scope_differences(left: BenchmarkScope, right: BenchmarkScope) -> list[str]:
    first = {row.input_id: row for row in left.inputs}
    second = {row.input_id: row for row in right.inputs}
    differences = []
    if first.keys() != second.keys():
        differences.append(f'Case/fixture selection differs: left-only {sorted(first.keys() - second.keys())}; right-only {sorted(second.keys() - first.keys())}.')
    for identity in sorted(first.keys() & second.keys()):
        for field in ('case_id', 'source_digest', 'truth_digest', 'cohort', 'samples', 'repetitions'):
            if getattr(first[identity], field) != getattr(second[identity], field):
                differences.append(f'{identity}: {field} differs.')
    return differences


def _observation_coverage(slot: PlannedObservation, row: ResearchResult | None,
                          status: str) -> ObservationCoverage:
    state: Literal['scored', 'pending', 'failed', 'uncertain', 'unavailable']
    invalid = bool(row and row.evaluation and
                   min(row.evaluation.tp, row.evaluation.fp, row.evaluation.fn) < 0)
    if invalid:
        state = 'unavailable'
    elif status in ('not_attempted', 'running'):
        state = 'pending'
    elif status == 'completed' and row and row.evaluation:
        state = 'scored'
    elif status in ('completed', 'unavailable', 'result_missing'):
        state = 'unavailable'
    elif status == 'uncertain':
        state = 'uncertain'
    else:
        state = 'failed'
    reason = None if state == 'scored' else f'{status}: no scored evaluation.'
    if invalid:
        reason = 'Invalid evaluator counts.'
    return ObservationCoverage(observation_id=slot.observation_id, case_id=slot.case_id,
        state=state, status=status, reason=reason)
