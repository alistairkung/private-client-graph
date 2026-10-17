"""Paired execution over frozen inputs, with explicit live gates and no retries."""
import time
from collections.abc import Callable, Iterator
from typing import Any, Literal
from uuid import uuid4

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import CanonicalGraph, ExtractionResult, RelationshipCandidate
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.pipeline import Pipeline, PipelineConfig, PipelineInput, PipelineExecutionError
from private_client_graph.resolution import EndpointEdits, ResolutionRequest, ResolutionProvider
from .artifacts import Bundle, BudgetExceeded, code_snapshot, dependency_versions, utc_now, write_json_once
from .inputs import ResearchInput
from .plan import FiniteExperimentPlan
from .run_plan import RunPlan
from .metrics import IdentityDiagnostics, estimate_cost, identity_diagnostics
from .provider import ModelRequest, ModelResponse, TokenUsage
from .results import ResearchResult
from .source_attribution import diagnose_source_attribution

Provider = Callable[[ModelRequest], ModelResponse]


def execute(bundle: Bundle, *, provider: Provider, live: bool = False,
            max_new_attempts: int | None = None,
            should_stop: Callable[[], bool] = lambda: False) -> dict[str, Any]:
    """Resume recorded attempts without reissuing them, including uncertain calls."""
    validate_execution(bundle, live)
    initial_count = bundle.attempt_count
    stop_reason = 'matrix_complete'
    with bundle.execution_lock():
        # All writes, including task-wide budget reservations, precede dispatch.
        try:
            for sample in _ordered_inputs(bundle):
                _checkpoint(should_stop)
                _run_pair(bundle, sample, provider, initial_count, max_new_attempts, should_stop)
            for sample in _fresh_inputs(bundle, provider, initial_count, max_new_attempts, should_stop):
                _run_pair(bundle, sample, provider, initial_count, max_new_attempts, should_stop)
        except BudgetExceeded as error:
            stop_reason = str(error)
        session = {'finished_at': utc_now(), 'stop_reason': stop_reason,
                   'new_attempts': bundle.attempt_count - initial_count,
                   'attempts_total': bundle.attempt_count,
                   'task_attempts_total': bundle.task_attempt_count}
        write_json_once(bundle.path / 'sessions' / f'{uuid4().hex}.json', session)
    return session


def validate_execution(bundle: Bundle, live: bool) -> None:
    plan = bundle.plan
    if live != (plan.kind != 'demonstration'):
        raise ValueError('Live execution must be explicit and match the manifest kind')
    if plan.kind == 'live_experiment':
        from .live_accounting import validate_authorization
        validate_authorization(bundle)
    # These fields record workflow provenance; local validation cannot prove user authorization.
    if plan.kind == 'task_b_pilot' and not (plan.authorization_reference and plan.reviewed_commit):
        raise ValueError('Task B requires explicit user authorization and reviewed Task A commit')
    validate_environment(bundle)


def validate_environment(bundle: Bundle) -> None:
    if bundle.manifest['provenance']['code'] != code_snapshot():
        raise ValueError('Code changed since manifest creation; do not mix configurations on resume')
    if bundle.manifest['provenance']['dependencies'] != dependency_versions():
        raise ValueError('Dependencies changed since manifest creation; do not mix environments on resume')


def _ordered_inputs(bundle: Bundle) -> list[ResearchInput]:
    if isinstance(bundle.plan, FiniteExperimentPlan) and bundle.plan.input_mode == 'fresh':
        return []
    priorities = {'alias_merge': 0, 'alias_distinct': 1}
    return sorted(bundle.plan.inputs, key=lambda sample: priorities.get(sample.sample_id, 2))


def _observe(bundle: Bundle, attempt_id: str, request: ModelRequest,
             provider: Provider, initial_count: int, limit: int | None,
             should_stop: Callable[[], bool] = lambda: False) -> dict[str, Any]:
    existing = bundle.attempt(attempt_id)
    if existing is not None:
        return existing
    _checkpoint(should_stop)
    if limit is not None and bundle.attempt_count - initial_count >= limit:
        raise BudgetExceeded('Requested checkpoint reached; inspect artifacts before continuing')
    if not bundle.reserve(attempt_id, request.model_dump(mode='json')):
        recovered = bundle.attempt(attempt_id)
        assert recovered is not None
        return recovered
    started = time.perf_counter()
    try:
        response = provider(request)
    except Exception as error:
        provider_seconds = time.perf_counter() - started
        # Provider exception strings may contain request headers or credentials.
        observation: dict[str, Any] = {'status': 'provider_error', 'error_type': type(error).__name__}
    else:
        provider_seconds = time.perf_counter() - started
        observation = {'status': 'completed', 'response': response.model_dump(mode='json')}
    observation['provider_seconds'] = provider_seconds
    bundle.complete(attempt_id, observation)
    return {**observation, 'attempt_id': attempt_id}


def _run_pair(bundle: Bundle, sample: ResearchInput, provider: Provider,
              initial_count: int, limit: int | None,
              should_stop: Callable[[], bool]) -> None:
    assert sample.extraction is not None
    if not isinstance(bundle.plan, RunPlan) or bundle.plan.resolver == 'none':
        _save_baseline_if_needed(bundle, sample)
    repetitions = bundle.plan.resolution_repetitions
    for repetition in range(1, repetitions + 1):
        _checkpoint(should_stop)
        _run_resolution_repetition(
            bundle, sample, repetition, provider, initial_count, limit, should_stop
        )


def _save_baseline_if_needed(bundle: Bundle, sample: ResearchInput) -> None:
    baseline_id = f'{sample.sample_id}-noop'
    if bundle.has_result(baseline_id):
        return

    assert sample.extraction is not None
    baseline, _ = _pipeline_result(sample, PipelineConfig(), mode='replay')
    _save_baseline(bundle, sample, baseline)


def _save_baseline(bundle: Bundle, sample: ResearchInput, baseline: ResearchResult) -> None:
    baseline_id = f'{sample.sample_id}-noop'
    baseline.configuration = 'noop'
    baseline.repetition = 0
    baseline.provider_seconds = 0
    baseline.resolution_seconds = 0
    baseline.edit_seconds = 0
    baseline.incremental_cost = 0
    baseline.usage = TokenUsage(input_tokens=0, output_tokens=0, cached_tokens=0)
    bundle.save_result(baseline_id, baseline.model_dump(mode='json'))


def _run_resolution_repetition(
    bundle: Bundle,
    sample: ResearchInput,
    repetition: int,
    provider: Provider,
    initial_count: int,
    limit: int | None,
    should_stop: Callable[[], bool],
) -> None:
    attempt_id = f'{sample.sample_id}-resolve-{repetition}'
    if bundle.has_result(attempt_id):
        return

    observation: dict[str, Any] = {}
    observation_seconds = 0.0

    def resolve(request: ResolutionRequest) -> EndpointEdits:
        nonlocal observation, observation_seconds
        operational_request = ModelRequest(stage='resolution', source=request.source,
                                           extraction=request.extraction, settings=bundle.plan.settings)
        started = time.perf_counter()
        observation = _observe(bundle, attempt_id, operational_request, provider, initial_count, limit, should_stop)
        observation_seconds = time.perf_counter() - started
        return EndpointEdits.model_validate(_observed_payload(observation))

    result, _ = _pipeline_result(sample, PipelineConfig(resolver='generative'), mode='replay',
                                 resolution_provider=resolve)
    result.configuration = 'generative_full_source'
    result.repetition = repetition
    result.attempt_id = attempt_id
    result.provider_seconds = observation.get('provider_seconds')
    result.usage = TokenUsage.model_validate(observation.get('response', {}).get('usage', {}))
    result.incremental_cost = estimate_cost(result.usage, bundle.plan.pricing)
    if result.resolution_seconds is not None and result.provider_seconds is not None:
        # Replace observation I/O with the recorded call duration, also on resume.
        local_seconds = max(0, result.resolution_seconds - observation_seconds)
        result.resolution_seconds = local_seconds + result.provider_seconds
        if result.status not in ('provider_error', 'parse_error'):
            result.edit_seconds = local_seconds
        if result.extraction is not None:
            result.edits = observation['response']['payload']['edits']
    else:
        result.resolution_seconds = None
    bundle.save_result(attempt_id, result.model_dump(mode='json'))


class _ObservationFailure(Exception):
    def __init__(self, observation: dict[str, Any]):
        super().__init__('Provider observation unavailable')
        self.observation = observation


def _observed_payload(observation: dict[str, Any]) -> object:
    if observation['status'] != 'completed' or observation['response'].get('payload') is None:
        raise _ObservationFailure(observation)
    return observation['response']['payload']


def _base_result(sample: ResearchInput) -> ResearchResult:
    return ResearchResult(
        sample_id=sample.sample_id,
        case_id=sample.case_id,
        cohort=sample.cohort,
    )


def _replay_only(source: str) -> ExtractionResult:
    raise RuntimeError('Frozen research inputs must use explicit replay')


def _pipeline_result(
    sample: ResearchInput,
    config: PipelineConfig,
    *,
    mode: Literal['live', 'replay'],
    extractor: Callable[[str], ExtractionResult] = _replay_only,
    resolution_provider: ResolutionProvider | None = None,
    source_extractor: Callable[[list[Source]], SourcedExtractionResult] | None = None,
) -> tuple[ResearchResult, ExtractionResult | SourcedExtractionResult | None]:
    if sample.sources is not None and config.resolver == 'none':
        return _sourced_pipeline_result(sample, config, mode=mode, source_extractor=source_extractor)
    result = _base_result(sample)
    started = time.perf_counter()

    def timed_graph(candidates: list[RelationshipCandidate], *, document: str,
                    source_text: str) -> CanonicalGraph:
        result.resolution_seconds = time.perf_counter() - started
        graph_started = time.perf_counter()
        try:
            return build_graph(candidates, document=document, source_text=source_text)
        finally:
            result.graph_seconds = time.perf_counter() - graph_started
            result.downstream_seconds = result.graph_seconds

    pipeline = Pipeline(config, extractor=extractor,
                        resolution_provider=resolution_provider, graph_builder=timed_graph)
    input = PipelineInput(source_text=sample.source, document='source.txt')
    try:
        if mode == 'live':
            output = pipeline.run(input)
        else:
            assert sample.extraction is not None
            output = pipeline.run_from_extraction(input, sample.extraction)
    except PipelineExecutionError as error:
        if error.stage == 'resolution':
            result.resolution_seconds = time.perf_counter() - started
        if isinstance(error.__cause__, BudgetExceeded):
            raise error.__cause__
        _record_pipeline_failure(result, error)
        if error.resolved is not None:
            _record_prediction(result, sample, error.resolved)
        return result, error.extracted
    _record_prediction(result, sample, output.resolved)
    result.graph = output.graph
    _evaluate(result, sample)
    return result, output.extracted


def _record_pipeline_failure(result: ResearchResult, error: PipelineExecutionError) -> None:
    cause = error.__cause__
    if isinstance(cause, _ObservationFailure):
        observation = cause.observation
        if observation['status'] != 'completed':
            result.status = observation['status']
            result.stage = 'provider'
            result.error_type = observation.get('error_type')
        else:
            result.status = 'parse_error'
            result.stage = 'parse'
            result.error_type = observation['response'].get('error_type')
        return
    result.error_type = type(cause).__name__
    if error.stage == 'graph':
        result.status, result.stage = 'graph_error', 'graph'
    elif error.stage == 'resolution':
        result.status, result.stage = 'edit_error', 'edits'
    else:
        result.status, result.stage = 'unavailable', 'extraction'


def _record_prediction(result: ResearchResult, sample: ResearchInput,
                       extraction: ExtractionResult | SourcedExtractionResult) -> None:
    if isinstance(extraction, SourcedExtractionResult):
        result.sourced_extraction = extraction
        result.extraction = _legacy_projection(extraction)
        return
    result.extraction = extraction
    diagnostics = identity_diagnostics(sample, extraction)
    result.identity = IdentityDiagnostics.model_validate(diagnostics) if diagnostics is not None else None


def _evaluate(result: ResearchResult, sample: ResearchInput) -> None:
    assert result.graph is not None and result.graph_seconds is not None
    started = time.perf_counter()
    try:
        result.evaluation = evaluate_graph(result.graph, sample.truth)
        if result.state is not None and sample.source_evidence is not None:
            result.source_attribution = diagnose_source_attribution(result.state, sample.truth, sample.source_evidence)
    except ValueError as error:
        result.evaluation_seconds = time.perf_counter() - started
        result.status = 'evaluation_error'
        result.stage = 'evaluation'
        result.error_type = type(error).__name__
    else:
        result.evaluation_seconds = time.perf_counter() - started
    result.downstream_seconds = result.graph_seconds + result.evaluation_seconds


def _fresh_inputs(bundle: Bundle, provider: Provider, initial_count: int,
                  limit: int | None, should_stop: Callable[[], bool]) -> Iterator[ResearchInput]:
    if not bundle.plan.fresh_extractions:
        return
    for template, sample_id in _fresh_templates(bundle):
        _checkpoint(should_stop)
        sample = _fresh_sample(template, sample_id)

        def extract(source: str) -> ExtractionResult:
            request = ModelRequest(stage='extraction', source=source, settings=bundle.plan.settings)
            observation = _observe(bundle, f'{sample_id}-extraction', request, provider, initial_count, limit, should_stop)
            return ExtractionResult.model_validate(_observed_payload(observation))

        def extract_sources(sources: list[Source]) -> SourcedExtractionResult:
            request = ModelRequest(stage='extraction', source=sample.source, sources=sources,
                                   settings=bundle.plan.settings)
            observation = _observe(bundle, f'{sample_id}-extraction', request, provider, initial_count, limit, should_stop)
            return SourcedExtractionResult.model_validate(_observed_payload(observation))

        baseline, extracted = _pipeline_result(sample, PipelineConfig(), mode='live', extractor=extract,
                                               source_extractor=extract_sources)
        if extracted is None:
            _save_unavailable_fresh_results(bundle, sample)
            continue
        if isinstance(extracted, SourcedExtractionResult):
            sample.sourced_extraction = extracted
            sample.extraction = _legacy_projection(extracted)
        else:
            sample.extraction = extracted
        _save_fresh_input_snapshot(bundle, sample)
        include_baseline = not isinstance(bundle.plan, RunPlan) or bundle.plan.resolver == 'none'
        if include_baseline and not bundle.has_result(f'{sample_id}-noop'):
            _save_baseline(bundle, sample, baseline)
        yield sample


def _fresh_templates(bundle: Bundle) -> Iterator[tuple[ResearchInput, str]]:
    if isinstance(bundle.plan, RunPlan):
        for template in bundle.plan.inputs:
            for index in range(1, bundle.plan.fresh_extractions + 1):
                yield template, f'{template.sample_id}_fresh_{index:02d}'
        return
    template = next(sample for sample in bundle.plan.inputs if sample.case_id == 'case_03')
    for index in range(1, bundle.plan.fresh_extractions + 1):
        yield template, f'fresh_{index:02d}'


def _fresh_sample(template: ResearchInput, sample_id: str) -> ResearchInput:
    origin_hashes = {
        name: digest
        for name, digest in template.origin_hashes.items()
        if name not in ('extraction.json', 'expected_source_extraction.json', 'annotations.json')
    }
    return template.model_copy(update={
        'sample_id': sample_id,
        'cohort': 'fresh',
        'annotations': None,
        'historical': None,
        'extraction': None,
        'sourced_extraction': None,
        'origin_hashes': origin_hashes,
    })


def _save_unavailable_fresh_results(bundle: Bundle, sample: ResearchInput) -> None:
    result_variants: list[
        tuple[str, Literal['noop', 'generative_full_source'], int]
    ] = []
    if not isinstance(bundle.plan, RunPlan) or bundle.plan.resolver == 'none':
        result_variants.append(('noop', 'noop', 0))
    repetitions = bundle.plan.resolution_repetitions
    result_variants.extend(
        (f'resolve-{repetition}', 'generative_full_source', repetition)
        for repetition in range(1, repetitions + 1)
    )
    for suffix, configuration, repetition in result_variants:
        result_id = f'{sample.sample_id}-{suffix}'
        if bundle.has_result(result_id):
            continue
        unavailable = _base_result(sample)
        unavailable.status = 'unavailable'
        unavailable.stage = 'extraction'
        unavailable.configuration = configuration
        unavailable.repetition = repetition
        bundle.save_result(result_id, unavailable.model_dump(mode='json'))


def _save_fresh_input_snapshot(bundle: Bundle, sample: ResearchInput) -> None:
    snapshot = bundle.path / 'fresh_inputs' / f'{sample.sample_id}.json'
    if not snapshot.exists():
        write_json_once(snapshot, sample.model_dump(mode='json'))


def _checkpoint(should_stop: Callable[[], bool]) -> None:
    if should_stop():
        raise BudgetExceeded('Stopped after the current attempt; explicit continuation required')


def _legacy_projection(extraction: SourcedExtractionResult) -> ExtractionResult:
    """Expose legacy diagnostics without using the lossy projection for construction."""
    return ExtractionResult.model_validate(dict(relationships=[
        item.model_dump(exclude={'source_id'}) for item in extraction.relationships]))


def _sourced_pipeline_result(sample: ResearchInput, config: PipelineConfig, *,
                             mode: Literal['live', 'replay'],
                             source_extractor: Callable[[list[Source]], SourcedExtractionResult] | None
) -> tuple[ResearchResult, SourcedExtractionResult | None]:
    result = _base_result(sample)
    assert sample.sources is not None
    started = time.perf_counter()
    graph_started = started

    def timed_extract(sources: list[Source]) -> SourcedExtractionResult:
        nonlocal graph_started
        assert source_extractor is not None
        extracted = source_extractor(sources)
        graph_started = time.perf_counter()
        return extracted

    pipeline = Pipeline(config, source_extractor=timed_extract if source_extractor is not None else None)
    try:
        if mode == 'live':
            output = pipeline.run_sources(sample.sources)
        else:
            if sample.sourced_extraction is None:
                raise ValueError('Source-aware replay requires explicitly attributed extraction')
            output = pipeline.run_from_sourced_extraction(sample.sources, sample.sourced_extraction)
    except PipelineExecutionError as error:
        if isinstance(error.__cause__, BudgetExceeded):
            raise error.__cause__
        _record_pipeline_failure(result, error)
        if error.resolved is not None:
            _record_prediction(result, sample, error.resolved)
        extracted = error.extracted if isinstance(error.extracted, SourcedExtractionResult) else None
        return result, extracted
    result.resolution_seconds = 0
    result.graph_seconds = time.perf_counter() - graph_started
    result.downstream_seconds = result.graph_seconds
    _record_prediction(result, sample, output.resolved)
    result.state = output.state
    result.graph = output.graph
    _evaluate(result, sample)
    return result, output.extracted
