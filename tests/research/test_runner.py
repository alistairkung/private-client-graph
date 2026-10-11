from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.plan import ExperimentPlan, Pricing
from private_client_graph.research.provider import ModelResponse, TokenUsage
from private_client_graph.research.runner import execute


def test_paired_runner_keeps_each_response_and_resumes_without_reissuing(tmp_path):
    samples = load_inputs()[-2:]
    bundle = Bundle.create(tmp_path / 'paired', ExperimentPlan(inputs=samples, max_calls=6))
    requests = []
    def provider(request):
        requests.append(request.model_dump())
        edit = {'candidate_index': 1, 'endpoint': 'source_name', 'name': 'Elizabeth Tan'}
        return ModelResponse(payload={'edits': [edit] if 'nickname' in request.source else []},
                             usage=TokenUsage(input_tokens=100, output_tokens=10, cached_tokens=0))
    execute(bundle, provider=provider)
    assert len(requests) == 6
    assert requests[0] == requests[1] == requests[2]
    rows = bundle.results()
    assert len(rows) == 8
    baseline = next(r for r in rows if r['sample_id'] == 'alias_merge' and r['configuration'] == 'noop')
    assert baseline['evaluation']['f1'] == .5
    treatment = [r for r in rows if r['configuration'] == 'generative_full_source']
    assert all(r['evaluation']['f1'] == 1 for r in treatment)
    assert all(r['identity']['incorrect_merges'] == 0 and r['identity']['missed_merges'] == 0 for r in treatment)
    execute(Bundle.open(bundle.path), provider=provider)
    assert len(requests) == 6


def test_failures_are_retained_without_baseline_fallback_or_replacement_calls(tmp_path):
    sample = load_inputs()[-2]
    bundle = Bundle.create(tmp_path / 'failures', ExperimentPlan(inputs=[sample], max_calls=3))
    calls = []
    def provider(request):
        calls.append(request)
        if len(calls) == 1:
            raise TimeoutError('Authorization: SECRET must never be persisted')
        if len(calls) == 2:
            return ModelResponse(raw_response={'bad': 'original response'}, error_type='ValidationError')
        return ModelResponse(payload={'edits': [{'candidate_index': 99, 'endpoint': 'source_name', 'name': 'Beth'}]})
    execute(bundle, provider=provider)
    treatments = [r for r in bundle.results() if r['configuration'] != 'noop']
    assert [r['status'] for r in treatments] == ['provider_error', 'parse_error', 'edit_error']
    assert all(r['evaluation'] is None for r in treatments)
    assert len(bundle.attempts()) == 3
    assert bundle.attempts()[1]['response']['raw_response'] == {'bad': 'original response'}
    assert 'SECRET' not in ''.join(p.read_text() for p in (bundle.path / 'attempts').glob('*.json'))


def test_uncertain_attempt_is_not_reissued_and_explicit_live_gate_is_required(tmp_path):
    import pytest
    from private_client_graph.research.provider import ModelRequest
    sample = load_inputs()[-2]
    bundle = Bundle.create(tmp_path / 'interrupted', ExperimentPlan(inputs=[sample], repetitions=1))
    request = ModelRequest(stage='resolution', source=sample.source, extraction=sample.extraction, settings=bundle.plan.settings)
    bundle.reserve('alias_merge-resolve-1', request.model_dump())
    def forbidden(request):
        raise AssertionError('Must not reissue interrupted call')
    execute(bundle, provider=forbidden)
    assert next(r for r in bundle.results() if r['configuration'] != 'noop')['status'] == 'uncertain'
    pricing = Pricing(model='deepseek-flash', input_per_million=1, output_per_million=2,
                      source_url='https://provider.test/pricing', retrieved_at='2026-10-11')
    paid = Bundle.create(tmp_path / 'paid', ExperimentPlan(
        kind='task_b_pilot', task_id='92', inputs=[sample],
        effective_model='deepseek-flash', pricing=pricing,
    ), task_ledger=tmp_path / 'ledger')
    with pytest.raises(ValueError, match='explicit'):
        execute(paid, provider=forbidden)
    with pytest.raises(ValueError, match='authorization'):
        execute(paid, provider=forbidden, live=True)


def test_task_b_plan_requires_effective_model_and_pricing_before_dispatch():
    import pytest

    sample = load_inputs()[-2]
    with pytest.raises(ValueError, match='effective model'):
        ExperimentPlan(kind='task_b_pilot', task_id='92', inputs=[sample])

    with pytest.raises(ValueError, match='pricing metadata'):
        ExperimentPlan(
            kind='task_b_pilot', task_id='92', inputs=[sample],
            effective_model='deepseek-flash',
        )


def test_fresh_extractions_repeat_same_input_without_copying_annotations(tmp_path):
    frozen = load_inputs()[2]
    bundle = Bundle.create(tmp_path / 'fresh', ExperimentPlan(inputs=[frozen], repetitions=2,
                                                            fresh_extractions=2, max_calls=8))
    calls = []
    def provider(request):
        calls.append(request)
        if request.stage == 'extraction':
            if sum(r.stage == 'extraction' for r in calls) == 2:
                return ModelResponse(error_type='NoStructuredOutput')
            return ModelResponse(payload=frozen.extraction.model_dump())
        return ModelResponse(payload={'edits': []})
    execute(bundle, provider=provider)
    assert len(calls) == 6  # 2 frozen resolver + 2 extraction + 2 fresh resolver
    fresh = [r for r in bundle.results() if r['cohort'] == 'fresh']
    assert len(fresh) == 6
    assert all(r['identity'] is None for r in fresh)
    assert all(r['status'] == 'unavailable' for r in fresh if r['sample_id'] == 'fresh_02')
    execute(Bundle.open(bundle.path), provider=provider)
    assert len(calls) == 6


def test_graph_error_retains_prediction_and_cannot_masquerade_as_score_zero(tmp_path):
    sample = load_inputs()[-2]
    bundle = Bundle.create(tmp_path / 'invalid-graph', ExperimentPlan(inputs=[sample], repetitions=1))
    def provider(request):
        return ModelResponse(payload={'edits': [
            {'candidate_index': 1, 'endpoint': 'source_name', 'name': 'Harbour Trust'}]})
    execute(bundle, provider=provider)
    result = next(r for r in bundle.results() if r['configuration'] != 'noop')
    assert result['status'] == 'graph_error'
    assert result['evaluation'] is None
    assert result['extraction']['relationships'][1]['source_name'] == 'Harbour Trust'


def test_stage_timings_separate_resolution_from_graph_and_evaluation(tmp_path, monkeypatch):
    from private_client_graph.research import runner
    clock = [0.0]
    monkeypatch.setattr(runner.time, 'perf_counter', lambda: clock[0])
    for name, seconds in [('apply_edits', 3), ('build_graph', 100), ('evaluate_graph', 200)]:
        original = getattr(runner, name)
        def timed(*args, _original=original, _seconds=seconds, **kwargs):
            clock[0] += _seconds
            return _original(*args, **kwargs)
        monkeypatch.setattr(runner, name, timed)
    sample = load_inputs()[2]
    bundle = Bundle.create(tmp_path / 'timing', ExperimentPlan(inputs=[sample], repetitions=1,
                                                            fresh_extractions=1))
    def provider(request):
        clock[0] += 5
        if request.stage == 'extraction':
            return ModelResponse(payload=sample.extraction.model_dump())
        return ModelResponse(payload={'edits': []})
    execute(bundle, provider=provider)
    baseline = next(r for r in bundle.results() if r['configuration'] == 'noop')
    result = next(r for r in bundle.results() if r['configuration'] != 'noop')
    assert baseline['resolution_seconds'] == 0
    assert baseline['downstream_seconds'] == 300
    assert result['provider_seconds'] == 5
    assert result['edit_seconds'] == 3
    assert result['resolution_seconds'] == 8
    assert result['graph_seconds'] == 100
    assert result['evaluation_seconds'] == 200
    assert result['downstream_seconds'] == 300
    from private_client_graph.research.summary import summarize
    fresh = next(s for s in summarize(bundle)['samples'] if s['cohort'] == 'fresh')
    assert fresh['baseline_single_pipeline_latency'] == 305
    assert fresh['single_pipeline_latency']['mean'] == 313
