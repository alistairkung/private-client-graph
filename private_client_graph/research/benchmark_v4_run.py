"""Verify one frozen matrix and replay its retained outcomes without a provider."""
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from benchmark_v3.evaluation_protocol import UnavailablePrediction
from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.graph import build_canonical_state
from private_client_graph.models import SourcedExtractionResult
from .artifacts import Bundle, benchmark_v4_scoring_digest
from .benchmark_v4 import BenchmarkWorkload
from .benchmark_v4_scoring import MixedEvaluation, Prediction, evaluate_benchmark_v4
from .live_accounting import read_run_authorization
from .provider import ModelRequest
from .results import ResearchResult
from .run_plan import RunPlan


@dataclass(frozen=True)
class VerifiedV4Run:
    evaluation: MixedEvaluation
    results: dict[str, ResearchResult]


def require_frozen_plan(bundle: Bundle, workload: BenchmarkWorkload) -> RunPlan:
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or not plan.benchmark_v4_sha256:
        raise ValueError('Expected a frozen Benchmark v4 Run')
    workload.require_plan_inputs(plan.benchmark_v4_sha256, plan.inputs)
    if bundle.manifest['provenance'].get('benchmark_v4_scoring_sha256') != benchmark_v4_scoring_digest():
        raise ValueError('Benchmark v4 scorer differs from the frozen Run')
    return plan


def evaluate_retained_run(bundle: Bundle, workload: BenchmarkWorkload, *,
                          attempts: Sequence[dict]) -> VerifiedV4Run:
    plan = require_frozen_plan(bundle, workload)
    lifecycle = [json.loads(path.read_text()) for path in (bundle.path / 'lifecycle').glob('*.json')]
    current = max(lifecycle, key=lambda row: row['at']) if lifecycle else {'state': 'frozen'}
    active = f"{bundle.path.name}-{current['invocation']}" if current['state'] in ('running', 'stopping') else None
    retained = _indexed(attempts, 'attempt_id')
    indexed_results = _indexed(bundle.results(), 'sample_id')
    predictions: dict[str, Prediction] = {}
    results: dict[str, ResearchResult] = {}
    verified_invocations: set[str] = set()

    for item, template, slot in zip(workload.roster.inputs, plan.inputs, plan.planned_slots, strict=True):
        assert slot.extraction_attempt_id is not None
        attempt = retained.pop(slot.extraction_attempt_id, None)
        request = ModelRequest(stage='extraction', source=template.source, sources=template.sources,
                               settings=plan.settings)
        if attempt is not None:
            if attempt.get('request') != request.model_dump(mode='json'):
                raise ValueError('Retained Benchmark v4 request differs from the frozen full-context input')
            if plan.kind == 'live_experiment':
                _verify_live_attempt(bundle, slot.extraction_attempt_id, attempt, verified_invocations)
        data = indexed_results.pop(slot.sample_id, None)
        result = ResearchResult.model_validate(data) if data is not None else None
        if result is not None:
            if (result.case_id, result.configuration, result.repetition) != (
                    slot.case_id, slot.configuration, slot.repetition):
                raise ValueError('Retained Benchmark v4 result differs from its frozen observation slot')
            results[item.id] = result
        prediction = _retained_prediction(result, attempt, active)
        if prediction is not None:
            predictions[item.id] = prediction
    if retained or indexed_results:
        raise ValueError('Retained Run contains records outside the Benchmark v4 matrix')

    mixed = evaluate_benchmark_v4(workload, predictions,
        observation_origin='live' if plan.execution_mode == 'live' else 'offline_fixture',
        complete=current['state'] == 'complete')
    mixed.summary.scoring_sha256 = bundle.manifest['provenance']['benchmark_v4_scoring_sha256']
    for item, template in zip(workload.roster.inputs, plan.inputs, strict=True):
        outcome = mixed.qualified.conditions.get(item.id, mixed.consensus)
        result = results.get(item.id)
        if result is not None and result.evaluation is not None:
            raise ValueError('Benchmark v4 must use its verified scope-specific scoring contract')
        if outcome.outcome == 'scored':
            assert result is not None and result.sourced_extraction is not None and template.sources is not None
            expected = build_canonical_state(result.sourced_extraction.relationships, sources=template.sources)
            if result.state != expected or result.graph != reconstruct_graph(expected):
                raise ValueError('Retained Benchmark v4 graph differs from deterministic construction')
        elif result is not None and (result.state is not None or result.graph is not None):
            raise ValueError('An unavailable Benchmark v4 graph has a stored constructed state')
    return VerifiedV4Run(mixed, results)


def _verify_live_attempt(bundle: Bundle, attempt_id: str, attempt: Mapping[str, Any],
                         verified_invocations: set[str]) -> None:
    prefix = f'{bundle.path.name}-'
    authority = attempt.get('authorization', '')
    if not authority.startswith(prefix):
        raise ValueError('Retained Benchmark v4 attempt has no matching live authorization')
    invocation = authority.removeprefix(prefix)
    if invocation not in verified_invocations:
        read_run_authorization(bundle, invocation)
        verified_invocations.add(invocation)
    identity = bundle.manifest['experiment_id']
    ledger = bundle.task_ledger / 'reservations' / f'{identity}-{attempt_id}.json'
    started = bundle.path / 'attempts' / f'{attempt_id}.started.json'
    reservation = json.loads(ledger.read_text())
    if (reservation.get('attempt_id') != attempt_id or reservation.get('authorization') != authority
            or reservation.get('request') != attempt['request']
            or (started.exists() and json.loads(started.read_text()) != reservation)):
        raise ValueError('Retained Benchmark v4 attempt differs from the shared reservation')


def _indexed(records: Sequence[dict], field: str) -> dict[str, dict]:
    indexed = {record[field]: record for record in records}
    if len(indexed) != len(records):
        raise ValueError('Duplicate Benchmark v4 retained record identity')
    return indexed


def _retained_prediction(result: ResearchResult | None, attempt: Mapping[str, Any] | None,
                         active: str | None) -> Prediction | None:
    if attempt is None:
        if result is not None:
            raise ValueError('Benchmark v4 result has no retained extraction attempt')
        return None
    if attempt['status'] == 'uncertain':
        if active is not None and attempt.get('authorization') == active:
            return None
        return UnavailablePrediction('uncertain')
    if attempt['status'] == 'provider_error':
        return UnavailablePrediction('provider_failure', attempt.get('error_type'))
    if attempt['status'] == 'completed':
        response = attempt.get('response', {})
        try:
            # A worker can stop after retaining the attempt and before saving
            # the result. A valid payload remains pending for inspection.
            parsed = SourcedExtractionResult.model_validate(response.get('payload'))
        except ValidationError:
            return UnavailablePrediction('parse_failure', response.get('error_type') or 'ValidationError')
        if result is None:
            return None
        if result.sourced_extraction != parsed:
            raise ValueError('Retained Benchmark v4 prediction differs from the extraction receipt')
        return parsed
    raise ValueError('Unknown Benchmark v4 extraction attempt status')
