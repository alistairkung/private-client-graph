"""Paired execution over frozen inputs, with explicit live gates and no retries."""
import time
from collections.abc import Callable, Iterator
from typing import Any, Literal
from uuid import uuid4

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult
from .artifacts import Bundle, BudgetExceeded, code_snapshot, dependency_versions, utc_now, write_json_once
from .inputs import ResearchInput
from .metrics import IdentityDiagnostics, estimate_cost, identity_diagnostics
from .provider import ModelRequest, ModelResponse, TokenUsage
from .resolution import apply_edits, no_resolution
from .results import ResearchResult

Provider = Callable[[ModelRequest], ModelResponse]


def execute(bundle: Bundle, *, provider: Provider, live: bool = False,
            max_new_attempts: int | None = None) -> dict[str, Any]:
    """Resume recorded attempts without reissuing them, including uncertain calls."""
    _validate_execution(bundle, live)
    initial_count = bundle.attempt_count
    stop_reason = 'matrix_complete'
    with bundle.execution_lock():
        # All writes, including task-wide budget reservations, precede dispatch.
        try:
            for sample in _ordered_inputs(bundle):
                _run_pair(bundle, sample, provider, initial_count, max_new_attempts)
            for sample in _fresh_inputs(bundle, provider, initial_count, max_new_attempts):
                _run_pair(bundle, sample, provider, initial_count, max_new_attempts)
        except BudgetExceeded as error:
            stop_reason = str(error)
        session = {'finished_at': utc_now(), 'stop_reason': stop_reason,
                   'new_attempts': bundle.attempt_count - initial_count,
                   'attempts_total': bundle.attempt_count,
                   'task_attempts_total': bundle.task_attempt_count}
        write_json_once(bundle.path / 'sessions' / f'{uuid4().hex}.json', session)
    return session


def _validate_execution(bundle: Bundle, live: bool) -> None:
    plan = bundle.plan
    if live != (plan.kind != 'demonstration'):
        raise ValueError('Live execution must be explicit and match the manifest kind')
    if plan.kind == 'task_b_pilot' and not (plan.authorization_reference and plan.reviewed_commit):
        raise ValueError('Task B requires explicit user authorization and reviewed Task A commit')
    if bundle.manifest['provenance']['code'] != code_snapshot():
        raise ValueError('Code changed since manifest creation; do not mix configurations on resume')
    if bundle.manifest['provenance']['dependencies'] != dependency_versions():
        raise ValueError('Dependencies changed since manifest creation; do not mix environments on resume')


def _ordered_inputs(bundle: Bundle) -> list[ResearchInput]:
    priorities = {'alias_merge': 0, 'alias_distinct': 1}
    return sorted(bundle.plan.inputs, key=lambda sample: priorities.get(sample.sample_id, 2))


def _observe(bundle: Bundle, attempt_id: str, request: ModelRequest,
             provider: Provider, initial_count: int, limit: int | None) -> dict[str, Any]:
    existing = next((a for a in bundle.attempts() if a['attempt_id'] == attempt_id), None)
    if existing is not None:
        return existing
    if limit is not None and bundle.attempt_count - initial_count >= limit:
        raise BudgetExceeded('Requested checkpoint reached; inspect artifacts before continuing')
    bundle.reserve(attempt_id, request.model_dump(mode='json'))
    started = time.perf_counter()
    try:
        response = provider(request)
        observation: dict[str, Any] = {'status': 'completed', 'response': response.model_dump(mode='json')}
    except Exception as error:
        # Provider exception strings may contain request headers or credentials.
        observation = {'status': 'provider_error', 'error_type': type(error).__name__}
    observation['provider_seconds'] = time.perf_counter() - started
    bundle.complete(attempt_id, observation)
    return {**observation, 'attempt_id': attempt_id}


def _run_pair(bundle: Bundle, sample: ResearchInput, provider: Provider,
              initial_count: int, limit: int | None) -> None:
    assert sample.extraction is not None
    baseline_id = f'{sample.sample_id}-noop'
    if not (bundle.path / 'results' / f'{baseline_id}.json').exists():
        baseline = _evaluate(sample, no_resolution(sample.extraction))
        baseline.configuration = 'noop'
        baseline.repetition = 0
        baseline.provider_seconds = 0
        baseline.resolution_seconds = 0
        baseline.edit_seconds = 0
        baseline.incremental_cost = 0
        baseline.usage = TokenUsage(input_tokens=0, output_tokens=0, cached_tokens=0)
        bundle.save_result(baseline_id, baseline.model_dump(mode='json'))
    request = ModelRequest(stage='resolution', source=sample.source,
                           extraction=sample.extraction, settings=bundle.plan.settings)
    for repetition in range(1, bundle.plan.repetitions + 1):
        attempt_id = f'{sample.sample_id}-resolve-{repetition}'
        if (bundle.path / 'results' / f'{attempt_id}.json').exists():
            continue
        observation = _observe(bundle, attempt_id, request, provider, initial_count, limit)
        result = _resolved_result(sample, observation)
        result.configuration = 'generative_full_source'
        result.repetition = repetition
        result.attempt_id = attempt_id
        result.provider_seconds = observation.get('provider_seconds')
        usage = TokenUsage.model_validate(observation.get('response', {}).get('usage', {}))
        result.usage = usage
        result.incremental_cost = estimate_cost(usage, bundle.plan.pricing)
        bundle.save_result(attempt_id, result.model_dump(mode='json'))


def _base_result(sample: ResearchInput) -> ResearchResult:
    return ResearchResult(
        sample_id=sample.sample_id,
        case_id=sample.case_id,
        cohort=sample.cohort,
    )


def _resolved_result(sample: ResearchInput, observation: dict[str, Any]) -> ResearchResult:
    result = _base_result(sample)
    if observation['status'] != 'completed':
        result.status = observation['status']
        result.stage = 'provider'
        result.error_type = observation.get('error_type')
        return result
    payload = observation['response'].get('payload')
    if payload is None:
        result.status = 'parse_error'
        result.stage = 'parse'
        result.error_type = observation['response'].get('error_type')
        return result
    assert sample.extraction is not None
    started = time.perf_counter()
    try:
        resolved = apply_edits(sample.extraction, sample.source, payload)
    except ValueError as error:
        result.status = 'edit_error'
        result.stage = 'edits'
        result.error_type = type(error).__name__
        result.edit_seconds = time.perf_counter() - started
        result.resolution_seconds = result.edit_seconds + observation['provider_seconds']
        return result
    edit_seconds = time.perf_counter() - started
    result = _evaluate(sample, resolved)
    result.edits = payload['edits']
    result.edit_seconds = edit_seconds
    result.resolution_seconds = edit_seconds + observation['provider_seconds']
    return result


def _evaluate(sample: ResearchInput, extraction: ExtractionResult) -> ResearchResult:
    result = _base_result(sample)
    result.extraction = extraction
    diagnostics = identity_diagnostics(sample, extraction)
    result.identity = IdentityDiagnostics.model_validate(diagnostics) if diagnostics is not None else None
    started = time.perf_counter()
    try:
        graph = build_graph(extraction.relationships, document='source.txt', source_text=sample.source)
    except ValueError as error:
        result.status = 'graph_error'
        result.stage = 'graph'
        result.error_type = type(error).__name__
        result.graph_seconds = time.perf_counter() - started
        return result
    result.graph = graph
    result.graph_seconds = time.perf_counter() - started
    started = time.perf_counter()
    try:
        result.evaluation = evaluate_graph(graph, sample.truth)
    except ValueError as error:
        result.status = 'evaluation_error'
        result.stage = 'evaluation'
        result.error_type = type(error).__name__
    result.evaluation_seconds = time.perf_counter() - started
    result.downstream_seconds = result.graph_seconds + result.evaluation_seconds
    return result


def _fresh_inputs(bundle: Bundle, provider: Provider, initial_count: int,
                  limit: int | None) -> Iterator[ResearchInput]:
    if not bundle.plan.fresh_extractions:
        return
    template = next(sample for sample in bundle.plan.inputs if sample.case_id == 'case_03')
    request = ModelRequest(stage='extraction', source=template.source, settings=bundle.plan.settings)
    for index in range(1, bundle.plan.fresh_extractions + 1):
        sample_id = f'fresh_{index:02d}'
        observation = _observe(bundle, f'{sample_id}-extraction', request, provider, initial_count, limit)
        sample = template.model_copy(update={'sample_id': sample_id, 'cohort': 'fresh',
                                            'annotations': None, 'historical': None, 'extraction': None,
                                            'origin_hashes': {k: v for k, v in template.origin_hashes.items()
                                                              if k in ('source.txt', 'ground_truth.json')}})
        try:
            if observation['status'] != 'completed':
                raise ValueError('No parsed extraction')
            sample.extraction = ExtractionResult.model_validate(observation['response']['payload'])
        except ValueError:
            unavailable_results: list[
                tuple[str, Literal['noop', 'generative_full_source'], int]
            ] = [('noop', 'noop', 0)]
            unavailable_results.extend(
                (f'resolve-{repetition}', 'generative_full_source', repetition)
                for repetition in range(1, bundle.plan.repetitions + 1)
            )
            for suffix, configuration, repetition in unavailable_results:
                result_id = f'{sample_id}-{suffix}'
                if not (bundle.path / 'results' / f'{result_id}.json').exists():
                    unavailable = _base_result(sample)
                    unavailable.status = 'unavailable'
                    unavailable.stage = 'extraction'
                    unavailable.configuration = configuration
                    unavailable.repetition = repetition
                    bundle.save_result(result_id, unavailable.model_dump(mode='json'))
            continue
        snapshot = bundle.path / 'fresh_inputs' / f'{sample_id}.json'
        if not snapshot.exists():
            write_json_once(snapshot, sample.model_dump(mode='json'))
        yield sample
