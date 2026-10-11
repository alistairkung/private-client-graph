"""Research timing boundaries, using a deterministic clock and real stage work."""
import pytest

from private_client_graph import resolution
from private_client_graph.research import runner
from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.plan import ExperimentPlan
from private_client_graph.research.provider import ModelRequest, ModelResponse
from private_client_graph.research.summary import summarize
from private_client_graph.research.results import ResearchResult


@pytest.fixture
def clock(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(runner.time, 'perf_counter', lambda: elapsed[0])
    # Keep the real operations; only their elapsed time is controlled. Artifact
    # I/O, response serialization and diagnostics must not inflate stage time.
    for owner, name, seconds in [
        (resolution, 'apply_edits', 3),
        (runner, 'build_graph', 100),
        (runner, 'evaluate_graph', 200),
        (runner, 'identity_diagnostics', 17),
        (ModelResponse, 'model_dump', 7),
        (Bundle, 'attempt', 11),
        (Bundle, 'reserve', 13),
        (Bundle, 'complete', 19),
    ]:
        original = getattr(owner, name)
        def timed(*args, _original=original, _seconds=seconds, **kwargs):
            elapsed[0] += _seconds
            return _original(*args, **kwargs)
        monkeypatch.setattr(owner, name, timed)
    assign = ResearchResult.__setattr__
    def classify(result, name, value):
        if name in ('status', 'stage', 'error_type'):
            elapsed[0] += 31
        assign(result, name, value)
    monkeypatch.setattr(ResearchResult, '__setattr__', classify)
    return elapsed


@pytest.mark.parametrize('outcome', [
    'completed', 'provider_error', 'parse_error', 'edit_error', 'graph_error', 'evaluation_error',
])
def test_stage_timings_include_failed_attempts_and_exclude_observation_overhead(tmp_path, clock, outcome):
    sample = load_inputs()[-2]
    if outcome == 'evaluation_error':
        sample.truth.relationships[0].source = 'missing-entity'
    bundle = Bundle.create(tmp_path / outcome, ExperimentPlan(inputs=[sample], repetitions=1))

    def provider(request):
        clock[0] += 5
        if outcome == 'provider_error':
            raise TimeoutError()
        if outcome == 'parse_error':
            return ModelResponse(error_type='ValidationError')
        edits = []
        if outcome in ('edit_error', 'graph_error'):
            edits = [{'candidate_index': 99 if outcome == 'edit_error' else 1,
                      'endpoint': 'source_name', 'name': 'Harbour Trust'}]
        return ModelResponse(payload={'edits': edits})

    runner.execute(bundle, provider=provider)
    result = next(row for row in bundle.results() if row['configuration'] != 'noop')
    assert result['status'] == outcome
    assert result['provider_seconds'] == 5
    reached_edits = outcome not in ('provider_error', 'parse_error')
    reached_graph = outcome in ('completed', 'graph_error', 'evaluation_error')
    reached_evaluation = outcome in ('completed', 'evaluation_error')
    assert result['resolution_seconds'] == (8 if reached_edits else 5)
    assert result['edit_seconds'] == (3 if reached_edits else None)
    assert result['graph_seconds'] == (100 if reached_graph else None)
    assert result['evaluation_seconds'] == (200 if reached_evaluation else None)
    expected_downstream = 300 if reached_evaluation else 100
    assert result['downstream_seconds'] == (expected_downstream if reached_graph else None)
    report = summarize(bundle)['samples'][0]
    assert report['resolver_latency']['mean'] == result['resolution_seconds']
    assert report['single_pipeline_latency']['mean'] is None  # No measured frozen extraction.


@pytest.mark.parametrize('outcome', ['completed', 'provider_error', 'parse_error', 'graph_error'])
def test_fresh_extraction_latency_is_the_provider_boundary_even_on_failure(tmp_path, clock, outcome):
    sample = load_inputs()[2]
    bundle = Bundle.create(tmp_path / outcome, ExperimentPlan(
        inputs=[sample], repetitions=1, fresh_extractions=1,
    ))

    def provider(request):
        if request.stage == 'resolution':
            clock[0] += 5
            edits = []
            first_candidate = request.extraction.relationships[0]
            if first_candidate.source_name == first_candidate.target_name:
                edits = [{'candidate_index': 0, 'endpoint': 'source_name',
                          'name': sample.extraction.relationships[0].source_name}]
            return ModelResponse(payload={'edits': edits})
        clock[0] += 23
        if outcome == 'provider_error':
            raise TimeoutError()
        if outcome == 'parse_error':
            return ModelResponse(error_type='ValidationError')
        extracted = sample.extraction.model_copy(deep=True)
        if outcome == 'graph_error':
            extracted.relationships[0].source_name = extracted.relationships[0].target_name
        return ModelResponse(payload=extracted.model_dump())

    runner.execute(bundle, provider=provider)
    fresh = next(row for row in summarize(bundle)['samples'] if row['cohort'] == 'fresh')
    assert fresh['extraction_seconds'] == 23
    if outcome == 'completed':
        assert fresh['baseline']['resolution_seconds'] == 0
        assert fresh['baseline_single_pipeline_latency'] == 323
        assert fresh['single_pipeline_latency']['mean'] == 331
    elif outcome == 'graph_error':
        assert fresh['baseline']['status'] == 'graph_error'
        assert fresh['baseline']['graph_seconds'] == fresh['baseline']['downstream_seconds'] == 100
        assert fresh['baseline']['evaluation_seconds'] is None
        assert fresh['baseline_single_pipeline_latency'] is None
        assert fresh['single_pipeline_latency']['mean'] == 331
    else:
        assert fresh['baseline']['status'] == 'unavailable'
        assert fresh['baseline']['resolution_seconds'] is None
        assert fresh['baseline_single_pipeline_latency'] is None
        assert fresh['single_pipeline_latency']['mean'] is None


@pytest.mark.parametrize('outcome', ['completed', 'provider_error', 'parse_error', 'uncertain'])
def test_resumed_timings_use_recorded_provider_duration_not_observation_read_time(tmp_path, clock, outcome):
    sample = load_inputs()[-2]
    bundle = Bundle.create(tmp_path / outcome, ExperimentPlan(inputs=[sample], repetitions=1))
    attempt_id = f'{sample.sample_id}-resolve-1'
    request = ModelRequest(stage='resolution', source=sample.source,
                           extraction=sample.extraction, settings=bundle.plan.settings)
    bundle.reserve(attempt_id, request.model_dump())
    if outcome != 'uncertain':
        response = ModelResponse(payload={'edits': []} if outcome == 'completed' else None,
                                 error_type='ValidationError' if outcome == 'parse_error' else None)
        observation = {'status': 'provider_error' if outcome == 'provider_error' else 'completed',
                       'provider_seconds': 29, 'response': response.model_dump()}
        bundle.complete(attempt_id, observation)

    runner.execute(bundle, provider=lambda request: pytest.fail('Never redispatch a recorded attempt'))
    result = next(row for row in bundle.results() if row['configuration'] != 'noop')
    assert result['status'] == outcome
    assert result['provider_seconds'] == (None if outcome == 'uncertain' else 29)
    expected_resolution = {'completed': 32, 'provider_error': 29, 'parse_error': 29, 'uncertain': None}
    assert result['resolution_seconds'] == expected_resolution[outcome]
    assert result['edit_seconds'] == (3 if outcome == 'completed' else None)
