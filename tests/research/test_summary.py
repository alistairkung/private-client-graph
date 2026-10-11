import pytest

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.plan import ExperimentPlan, Pricing
from private_client_graph.research.provider import ModelResponse, TokenUsage
from private_client_graph.research.runner import execute
from private_client_graph.research.summary import summarize
from private_client_graph.research.metrics import estimate_cost


def test_aggregate_keeps_missing_scores_separate_and_uses_all_repetitions(tmp_path):
    sample = load_inputs()[-2]
    bundle = Bundle.create(tmp_path / 'summary', ExperimentPlan(inputs=[sample], max_calls=3))
    count = 0
    def provider(request):
        nonlocal count
        count += 1
        if count == 3:
            raise TimeoutError()
        return ModelResponse(payload={'edits': [{'candidate_index': 1, 'endpoint': 'source_name', 'name': 'Elizabeth Tan'}] if count == 1 else []})
    execute(bundle, provider=provider)
    report = summarize(bundle)
    row = report['samples'][0]
    assert row['resolver_metrics']['f1']['mean'] == .75
    assert row['resolver_metrics']['f1']['standard_deviation'] == pytest.approx(.35355339059)
    assert row['resolver_metrics']['f1']['minimum'] == .5
    assert row['paired_deltas']['mean'] == .25
    assert row['scored_repetitions'] == 2
    assert row['valid_repetitions'] == 2
    assert row['failed_repetitions'] == 1
    assert row['failure_rate_among_attempted'] == pytest.approx(1 / 3)
    assert row['paired_score_coverage'] == pytest.approx(2 / 3)
    assert report['operations']['attempted'] == 3
    assert report['operations']['valid_attempts'] == 2
    assert report['operations']['estimated_spend'] is None
    assert row['single_pipeline_cost']['mean'] is None  # authored extraction has no measured cost


def test_price_uses_cached_input_as_subset_and_does_not_invent_unknown_usage():
    rates = Pricing(model='test', input_per_million=2, cached_input_per_million=.5,
                    output_per_million=4, source_url='https://provider.test/prices', retrieved_at='2026-10-11')
    assert estimate_cost(TokenUsage(input_tokens=1_000_000, cached_tokens=200_000, output_tokens=10_000), rates) == pytest.approx(1.74)
    assert estimate_cost(TokenUsage(input_tokens=100, output_tokens=10), rates) is None
    assert estimate_cost(TokenUsage(), rates) is None


def test_identity_diagnostics_distinguish_harmful_merge_from_correct_abstention():
    from private_client_graph.research.metrics import identity_diagnostics
    from private_client_graph.resolution import apply_edits
    distinct = load_inputs()[-1]
    untouched = identity_diagnostics(distinct, distinct.extraction)
    assert untouched == {'incorrect_merges': 0, 'missed_merges': 0,
                         'different_truth_pairs': 1, 'same_truth_pairs': 1,
                         'eligible_pairs': 2, 'errors': []}
    merged = apply_edits(distinct.extraction, distinct.source,
                         {'edits': [{'candidate_index': 1, 'endpoint': 'source_name', 'name': 'Elizabeth Tan'}]})
    errors = identity_diagnostics(distinct, merged)
    assert errors['incorrect_merges'] == 1 and errors['missed_merges'] == 0
    assert errors['errors'][0]['left']['participant'] == 'elizabeth'
    assert errors['errors'][0]['right']['participant'] == 'beth'


def test_unattempted_repetitions_are_visible_and_single_score_has_no_sd(tmp_path):
    bundle = Bundle.create(tmp_path / 'partial', ExperimentPlan(inputs=load_inputs()[-2:], max_calls=1))
    execute(bundle, provider=lambda request: ModelResponse(payload={'edits': []}))
    summary = summarize(bundle)
    row = summary['samples'][0]
    assert row['resolver_metrics']['f1']['standard_deviation'] is None
    assert row['not_attempted_repetitions'] == 2
    assert summary['samples'][1]['not_attempted_repetitions'] == 3
    assert summary['samples'][1]['failure_rate_among_attempted'] is None


def test_historical_elapsed_time_is_not_treated_as_extraction_stage_time(tmp_path):
    sample = load_inputs()[3]
    bundle = Bundle.create(tmp_path / 'history', ExperimentPlan(inputs=[sample], repetitions=1))
    execute(bundle, provider=lambda request: ModelResponse(payload={'edits': []}))
    row = summarize(bundle)['samples'][0]
    assert row['historical_pipeline_seconds'] == sample.historical['metadata']['duration_seconds']
    assert row['extraction_seconds'] is None
    assert row['baseline_single_pipeline_latency'] is None
    assert row['single_pipeline_latency']['mean'] is None
