import pytest
from pydantic import ValidationError

from private_client_graph.models import ExtractionResult
from private_client_graph.pipeline import Pipeline, PipelineConfig, PipelineInput


SOURCE = 'Alice is a beneficiary of Harbour Trust.'


def extraction():
    return ExtractionResult(relationships=[dict(
        source_name='Alice', relationship_type='beneficiary_of',
        target_name='Harbour Trust', supporting_text=SOURCE,
    )])


def test_live_and_replay_return_independent_equivalent_snapshots():
    original = extraction()
    calls = []
    def extract(source):
        calls.append(source)
        return original
    def forbidden(request):
        pytest.fail('No resolution must never invoke a provider')
    pipeline = Pipeline(PipelineConfig(), extractor=extract, resolution_provider=forbidden)
    input = PipelineInput(source_text=SOURCE, document='Intake title')
    live = pipeline.run(input)
    replay = pipeline.run_from_extraction(input, original)
    assert calls == [SOURCE]
    assert live == replay
    assert live.extracted == live.resolved == original
    assert live.graph.evidence[0].document == 'Intake title'
    live.resolved.relationships[0].source_name = 'Changed'
    assert live.extracted == replay.resolved == original
    original.relationships.clear()
    assert len(live.extracted.relationships) == 1


@pytest.mark.parametrize('config', [{'resolver': 'unknown'}, {'extra': True}])
def test_configuration_is_finite_and_extra_forbidding(config):
    with pytest.raises(ValidationError):
        PipelineConfig(**config)


@pytest.mark.parametrize('live', [False, True])
def test_generative_resolution_preserves_protected_fields_and_exact_graph_input(live):
    from private_client_graph.resolution import EndpointEdits, resolution_messages
    original = extraction()
    source = SOURCE + ' Alice is Alice Tan.'
    requests = []
    def provider(request):
        requests.append(resolution_messages(request.source, request.extraction))
        # Even a provider mutating its request cannot change extracted snapshots.
        request.extraction.relationships.clear()
        return EndpointEdits(edits=[dict(candidate_index=0, endpoint='source_name', name='Alice Tan')])
    pipeline = Pipeline(PipelineConfig(resolver='generative'), extractor=lambda _: original,
                        resolution_provider=provider)
    input = PipelineInput(source, 'Supplied title')
    result = pipeline.run(input) if live else pipeline.run_from_extraction(input, original)
    assert len(requests) == 1
    assert source in requests[0][1][1]
    assert result.extracted == original
    assert result.resolved.relationships[0].model_dump() == {
        **original.relationships[0].model_dump(), 'source_name': 'Alice Tan',
    }
    assert result.graph.evidence[0].document == 'Supplied title'
    assert result.graph.evidence[0].supporting_text == SOURCE
    assert 'Alice Tan' in [entity.name for entity in result.graph.entities]


@pytest.mark.parametrize('stage', ['extraction', 'resolution', 'graph'])
def test_stage_failure_retains_only_completed_outputs_and_chains_cause(stage):
    from private_client_graph.pipeline import PipelineExecutionError
    from private_client_graph.resolution import EndpointEdits
    original = extraction()
    cause = ValueError('stage failure')
    calls = []
    def extract(source):
        calls.append('extraction')
        if stage == 'extraction':
            raise cause
        return original
    def resolve(request):
        calls.append('resolution')
        if stage == 'resolution':
            raise cause
        return EndpointEdits(edits=[])
    def graph(candidates, **kwargs):
        calls.append('graph')
        candidates.clear()
        raise cause
    pipeline = Pipeline(PipelineConfig(resolver='generative'), extractor=extract,
                        resolution_provider=resolve, graph_builder=graph)
    with pytest.raises(PipelineExecutionError) as raised:
        pipeline.run(PipelineInput(SOURCE, 'title'))
    error = raised.value
    assert error.stage == stage
    assert error.__cause__ is cause
    assert error.extracted == (None if stage == 'extraction' else original)
    assert error.resolved == (original if stage == 'graph' else None)
    assert calls == ['extraction', 'resolution', 'graph'][:len(calls)]
    assert len(calls) == ['extraction', 'resolution', 'graph'].index(stage) + 1
    original.relationships.clear()
    if error.extracted is not None:
        assert len(error.extracted.relationships) == 1
    if error.resolved is not None:
        assert len(error.resolved.relationships) == 1


def test_invalid_generative_edits_fail_without_graph_or_baseline_fallback():
    from private_client_graph.pipeline import PipelineExecutionError
    from private_client_graph.resolution import EndpointEdits
    def provider(request):
        return EndpointEdits(edits=[dict(candidate_index=50, endpoint='source_name', name='Alice')])
    pipeline = Pipeline(PipelineConfig(resolver='generative'), extractor=lambda _: extraction(),
                        resolution_provider=provider)
    with pytest.raises(PipelineExecutionError) as raised:
        pipeline.run(PipelineInput(SOURCE, 'title'))
    assert raised.value.stage == 'resolution'
    assert raised.value.resolved is None


def test_configuration_and_success_outer_contracts_are_immutable():
    from dataclasses import FrozenInstanceError
    config = PipelineConfig()
    with pytest.raises(ValidationError):
        config.resolver = 'generative'
    pipeline = Pipeline(config, extractor=lambda _: extraction())
    input = PipelineInput(SOURCE, 'title')
    result = pipeline.run(input)
    with pytest.raises(FrozenInstanceError):
        result.extracted = extraction()
    with pytest.raises(FrozenInstanceError):
        input.document = 'changed'
