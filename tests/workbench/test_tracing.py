"""Workbench tracing uses the real SDK with a network-free OpenTelemetry exporter."""
import json
from uuid import uuid4

import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from private_client_graph.research.provider import ModelResponse, TokenUsage, request_messages
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.runner import execute
from private_client_graph.research.tracing import trace_id
from private_client_graph.workbench import tracing
from private_client_graph.workbench.planning import open_executable
from private_client_graph.workbench.run_inspection import read_run
from private_client_graph.workbench.run_planning import freeze_run
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate, FreezeRun, RunConfiguration
from private_client_graph.workbench.workspaces import create_experiment, save_draft


@pytest.fixture
def exporter(monkeypatch):
    exporter = InMemorySpanExporter()
    monkeypatch.setenv('PCG_RESEARCH_LANGFUSE_ENABLED', '1')
    monkeypatch.setenv('PCG_RESEARCH_LANGFUSE_DETAILS', '0')
    monkeypatch.setenv('LANGFUSE_TRACING_ENABLED', 'true')
    monkeypatch.setenv('LANGFUSE_PUBLIC_KEY', f'pk-offline-{uuid4().hex}')
    monkeypatch.setenv('LANGFUSE_SECRET_KEY', 'offline-exporter-key')
    monkeypatch.setenv('LANGFUSE_BASE_URL', 'https://langfuse.invalid')
    monkeypatch.setattr(tracing, 'Langfuse', lambda **kwargs: Langfuse(span_exporter=exporter, **kwargs))
    return exporter


def freeze(root, **configuration):
    experiment = create_experiment(root, CreateExperiment(request_id='create', name='Synthetic tracing'))
    draft = save_draft(root, experiment.id, DraftUpdate(request_id='draft', expected_revision=0,
        configuration=RunConfiguration(input_ids=['case_01_fixture'], **configuration)))
    frozen = freeze_run(root, experiment.id, FreezeRun(request_id='freeze', expected_revision=draft.revision))
    return open_executable(root, frozen.id)[0]


def run(bundle, provider, **options):
    with tracing.workbench_tracing(bundle) as recorder:
        return execute(bundle, provider=provider, tracing=recorder, **options)


def forbidden_provider(request):
    pytest.fail('Replay must never dispatch a provider')


def test_disabled_replay_keeps_artifacts_and_evaluation(tmp_path, monkeypatch, exporter):
    monkeypatch.setenv('PCG_RESEARCH_LANGFUSE_ENABLED', '0')
    bundle = freeze(tmp_path)
    run(bundle, forbidden_provider)
    detail = read_run(tmp_path, bundle.plan.experiment_id, bundle.plan.run_id)
    assert detail.evaluation.aggregate.f1 == 1.0
    assert detail.observations[0].langfuse_trace_ids == []
    assert bundle.attempt_count == 0
    assert exporter.get_finished_spans() == ()


def test_replay_exports_actual_stages_and_inspection_correlates(tmp_path, exporter):
    bundle = freeze(tmp_path)
    run(bundle, forbidden_provider)
    detail = read_run(tmp_path, bundle.plan.experiment_id, bundle.plan.run_id)
    observation = detail.observations[0]
    spans = {span.name: span for span in exporter.get_finished_spans()}
    root = spans['PCG Research Observation']
    graph = spans['Deterministic Graph Construction']
    evaluation = spans['Evaluation']
    assert set(spans) == {root.name, graph.name, evaluation.name,
                          'Graph correctness and approved provenance', 'Source attribution'}
    assert root.parent is None
    assert graph.parent == evaluation.parent == root.context
    assert spans['Source attribution'].parent == evaluation.context
    assert spans['Graph correctness and approved provenance'].parent == evaluation.context
    assert observation.langfuse_trace_ids == [f'{root.context.trace_id:032x}']
    metadata = root.attributes
    assert json.loads(metadata['langfuse.observation.metadata.observation_id']) == observation.id
    assert json.loads(metadata['langfuse.observation.metadata.experiment_id']) == detail.experiment_id
    assert json.loads(metadata['langfuse.observation.metadata.run_id']) == detail.id
    assert json.loads(metadata['langfuse.observation.metadata.model_settings_fingerprint']) == value_digest(
        bundle.plan.settings.model_dump(mode='json'))
    assert observation.result.evaluation.f1 == 1.0
    assert bundle.attempt_count == 0


@pytest.mark.parametrize('detailed', [False, True])
def test_generation_policy_usage_and_resume(tmp_path, monkeypatch, exporter, detailed):
    monkeypatch.setenv('PCG_RESEARCH_LANGFUSE_DETAILS', '1' if detailed else '0')
    bundle = freeze(tmp_path, input_mode='fresh', execution_mode='recorded', invocation_cap=1)
    requests = []
    raw = {'content': 'Synthetic model response'}

    def provider(request):
        requests.append(request)
        return ModelResponse(payload=bundle.plan.inputs[0].sourced_extraction.model_dump(),
            raw_response=raw, returned_model='deepseek-test',
            usage=TokenUsage(input_tokens=12, output_tokens=4, cached_tokens=3))

    first = run(bundle, provider)
    second = run(bundle, provider)
    assert len(requests) == first['new_attempts'] == bundle.attempt_count == 1
    assert second['new_attempts'] == 0
    spans = exporter.get_finished_spans()
    generation, = [span for span in spans if span.name == 'DeepSeek LLM call']
    extraction, = [span for span in spans if span.name == 'Semantic Extraction']
    assert generation.parent == extraction.context
    assert trace_id(bundle, bundle.plan.planned_slots[0].observation_id) == f'{generation.context.trace_id:032x}'
    attributes = generation.attributes
    assert attributes['langfuse.observation.model.name'] == 'deepseek-test'
    assert json.loads(attributes['langfuse.observation.usage_details']) == {
        'input': 12, 'output': 4, 'cache_read_input_tokens': 3}
    assert float(attributes['langfuse.observation.metadata.provider_seconds']) >= 0
    assert json.loads(attributes['langfuse.observation.metadata.attempt_id']) == bundle.plan.planned_slots[0].extraction_attempt_id
    if detailed:
        expected = [{'role': 'user' if role == 'human' else role, 'content': content}
                    for role, content in request_messages(requests[0])]
        assert json.loads(attributes['langfuse.observation.input']) == expected
        assert json.loads(attributes['langfuse.observation.output']) == raw
    else:
        assert 'langfuse.observation.input' not in attributes
        assert 'langfuse.observation.output' not in attributes
    assert bundle.results()[0]['evaluation']['f1'] == 1.0


def test_shared_failed_extraction_correlates_with_each_affected_slot(tmp_path, exporter):
    bundle = freeze(tmp_path, input_mode='fresh', execution_mode='recorded',
                    resolver='generative', resolver_repetitions=2, invocation_cap=3)

    def provider(request):
        assert request.stage == 'extraction'
        raise RuntimeError('private request failure details')

    run(bundle, provider)
    detail = read_run(tmp_path, bundle.plan.experiment_id, bundle.plan.run_id)
    root, = [span for span in exporter.get_finished_spans() if span.parent is None]
    generation, = [span for span in exporter.get_finished_spans() if span.name == 'DeepSeek LLM call']
    assert root.name == 'PCG Shared Semantic Extraction'
    assert json.loads(root.attributes['langfuse.observation.metadata.observation_ids']) == [
        item.id for item in detail.observations]
    assert all(item.langfuse_trace_ids == [f'{root.context.trace_id:032x}'] for item in detail.observations)
    assert generation.attributes['langfuse.observation.status_message'] == 'RuntimeError'
    assert 'private request failure details' not in str(generation.attributes)
    assert not generation.events
    assert bundle.attempt_count == 1


def test_shared_extraction_resume_links_new_resolution_without_reissuing_extraction(tmp_path, exporter):
    bundle = freeze(tmp_path, input_mode='fresh', execution_mode='recorded',
                    resolver='generative', invocation_cap=2)
    calls = []

    def provider(request):
        calls.append(request.stage)
        if request.stage == 'extraction':
            return ModelResponse(payload=bundle.plan.inputs[0].sourced_extraction.model_dump())
        return ModelResponse(payload={'edits': []})

    first = run(bundle, provider, max_new_attempts=1)
    slot, = bundle.plan.planned_slots
    assert first['new_attempts'] == 1
    assert trace_id(bundle, slot.observation_id) is None
    assert trace_id(bundle, slot.extraction_attempt_id) is not None
    exporter.clear()

    resumed = run(bundle, provider)
    detail = read_run(tmp_path, bundle.plan.experiment_id, bundle.plan.run_id)
    spans = {span.name: span for span in exporter.get_finished_spans()}
    root = spans['PCG Research Observation']
    assert spans['DeepSeek LLM call'].parent == spans['Resolution'].context
    assert spans['Resolution'].parent == root.context
    assert 'Semantic Extraction' not in spans
    assert detail.observations[0].langfuse_trace_ids == [
        f'{root.context.trace_id:032x}', trace_id(bundle, slot.extraction_attempt_id)]
    assert detail.evaluation.aggregate.f1 == 1.0
    assert resumed['new_attempts'] == 1
    assert calls == ['extraction', 'resolution']


def test_tracing_failure_preserves_result_and_provider_count(tmp_path, monkeypatch, exporter):
    bundle = freeze(tmp_path, execution_mode='recorded', resolver='generative', invocation_cap=1)
    calls = []

    def provider(request):
        calls.append(request)
        return ModelResponse(payload={'edits': []})

    def bad_export(*args, **kwargs):
        raise RuntimeError('simulated tracing failure')

    monkeypatch.setattr(Langfuse, 'flush', bad_export)
    monkeypatch.setattr(Langfuse, 'start_observation', bad_export)
    run(bundle, provider)
    assert len(calls) == bundle.attempt_count == 1
    assert bundle.results()[0]['evaluation']['f1'] == 1.0
    assert bundle.results()[0]['attempt_id'] == bundle.plan.planned_slots[0].observation_id


def test_modified_fixture_cannot_enable_any_tracing(tmp_path, monkeypatch, exporter):
    bundle = freeze(tmp_path)
    bundle.plan.inputs[0].source = 'Unverified source content'
    monkeypatch.setenv('PCG_RESEARCH_LANGFUSE_DETAILS', '1')
    run(bundle, forbidden_provider)
    assert exporter.get_finished_spans() == ()
    assert bundle.attempt_count == 0
