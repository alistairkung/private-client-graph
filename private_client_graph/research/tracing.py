"""Explicit, best-effort observations for the Workbench runner."""
import json
import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeVar

from langfuse import Langfuse, LangfuseEvaluator, LangfuseGeneration, LangfuseSpan
from opentelemetry.context import Context, attach, detach

from .artifacts import BudgetExceeded, Bundle, write_json_once
from .provider import ModelRequest, ModelResponse, request_messages
from .retained_inputs import value_digest
from .run_plan import RunPlan

_LOG = logging.getLogger(__name__)
_T = TypeVar('_T')


@dataclass(frozen=True)
class ResearchTracing:
    client: Langfuse
    synthetic_inputs: frozenset[str]
    detailed: bool


_active: ContextVar[LangfuseSpan | LangfuseGeneration | LangfuseEvaluator | None] = ContextVar('research_span', default=None)
_detailed: ContextVar[bool] = ContextVar('research_detailed', default=False)


def best_effort(operation: Callable[[], _T]) -> _T | None:
    try:
        return operation()
    except Exception:
        _LOG.warning('Workbench tracing operation failed')
        return None


@contextmanager
def observation(bundle: Bundle, tracing: ResearchTracing | None, key: str, *,
                sample_id: str, template_id: str, shared_extraction: bool = False) -> Iterator[None]:
    """Open a slot trace or a shared fresh-extraction trace."""
    plan = bundle.plan
    if tracing is None or not isinstance(plan, RunPlan) or template_id not in tracing.synthetic_inputs:
        yield
        return

    slots = [slot for slot in plan.planned_slots if slot.sample_id == sample_id and (
        slot.extraction_attempt_id == key if shared_extraction else slot.observation_id == key)]
    if not slots or trace_id(bundle, key):
        yield
        return

    first = slots[0]
    metadata = plan.case_metadata[template_id]
    prompt_hashes = bundle.manifest['provenance']['prompt_hashes']
    correlation = {
        'experiment_id': plan.experiment_id,
        'run_id': plan.run_id,
        'observation_ids': [slot.observation_id for slot in slots],
        'attempt_id': key if shared_extraction or first.repetition else first.extraction_attempt_id,
        'case_id': first.case_id,
        'input_id': template_id,
        'sample_id': sample_id,
        'matter_family': metadata.matter_family,
        'configuration': first.configuration,
        'pipeline_resolver': 'none' if shared_extraction else plan.resolver,
        'input_mode': plan.input_mode,
        'execution_mode': plan.execution_mode,
        'prompt_hashes': prompt_hashes,
        'model_settings_fingerprint': value_digest(plan.settings.model_dump(mode='json')),
        'detailed': tracing.detailed,
    }
    if not shared_extraction:
        correlation['observation_id'] = first.observation_id
    name = 'PCG Shared Semantic Extraction' if shared_extraction else 'PCG Research Observation'
    root = best_effort(lambda: _start_root(tracing.client, name, correlation))
    if root is None:
        yield
        return
    token = _detailed.set(tracing.detailed)
    try:
        with _scope(root):
            checkpoint = False
            try:
                yield
            except BudgetExceeded:
                checkpoint = True
                raise
            finally:
                if not checkpoint:
                    best_effort(lambda: write_json_once(
                        _trace_path(bundle, key), {'trace_id': root.trace_id}))
    finally:
        _detailed.reset(token)


def _start_root(client: Langfuse, name: str, metadata: dict[str, Any]) -> LangfuseSpan:
    # Start a true root even if the worker is launched inside unrelated OTel instrumentation.
    token = attach(Context())
    try:
        return client.start_observation(name=name, as_type='span', metadata=metadata)
    finally:
        detach(token)


def _trace_path(bundle: Bundle, key: str) -> Path:
    return bundle.path / 'langfuse' / f'{key}.json'


def trace_id(bundle: Bundle, key: str) -> str | None:
    """Read optional correlation independently of scientific artifact validation."""
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', key):
        return None
    try:
        record = json.loads(_trace_path(bundle, key).read_text())
        identity = record['trace_id']
        if isinstance(identity, str) and re.fullmatch(r'[0-9a-f]{32}', identity):
            return identity
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


@contextmanager
def _scope(span: LangfuseSpan | LangfuseGeneration | LangfuseEvaluator | None) -> Iterator[None]:
    token = _active.set(span)
    try:
        yield
    except BudgetExceeded:
        outcome(status='checkpoint')
        raise
    except Exception as error:
        mark_error(type(error).__name__)
        raise
    finally:
        _active.reset(token)
        if span is not None:
            best_effort(span.end)


@contextmanager
def span(name: str, *, as_type: Literal['span', 'evaluator'] = 'span') -> Iterator[None]:
    parent = _active.get()
    if parent is None:
        yield
        return
    with _scope(best_effort(lambda: parent.start_observation(name=name, as_type=as_type))):
        yield


def outcome(**metadata: Any) -> None:
    current = _active.get()
    if current is not None:
        best_effort(lambda: current.update(metadata=metadata))


def mark_error(error_type: str) -> None:
    current = _active.get()
    if current is not None:
        best_effort(lambda: current.update(level='ERROR', status_message=error_type))


@contextmanager
def generation(request: ModelRequest, attempt_id: str) -> Iterator[LangfuseGeneration | None]:
    parent = _active.get()
    if parent is None:
        yield None
        return
    current = best_effort(lambda: parent.start_observation(
        as_type='generation', name='DeepSeek LLM call', model=request.settings.model,
        model_parameters=request.settings.model_dump(exclude={'model'}),
        metadata={'attempt_id': attempt_id, 'requested_model': request.settings.model},
        input=([{'role': 'user' if role == 'human' else role, 'content': content}
                for role, content in request_messages(request)] if _detailed.get() else None)))
    with _scope(current):
        yield current


def generation_result(current: LangfuseGeneration | None, response: ModelResponse | None,
                      seconds: float, error_type: str | None) -> None:
    if current is None:
        return
    outcome(provider_seconds=seconds)
    if response is not None:
        usage = response.usage
        tokens = {'input': usage.input_tokens, 'output': usage.output_tokens,
                  'cache_read_input_tokens': usage.cached_tokens}
        best_effort(lambda: current.update(
            model=response.returned_model,
            usage_details={name: count for name, count in tokens.items() if count is not None},
            output=response.raw_response if _detailed.get() else None))
        error_type = response.error_type or ('MissingStructuredOutput' if response.payload is None else None)
    if error_type is not None:
        mark_error(error_type)
