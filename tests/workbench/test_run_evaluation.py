"""Approved Run aggregation arithmetic, coverage and scientific matching seam."""
from private_client_graph.models import EvaluationResult
from private_client_graph.research.results import ResearchResult
from private_client_graph.workbench.run_evaluation import aggregate_observations
from private_client_graph.workbench.run_evaluation_contracts import PlannedObservation


def slot(identity, case='case_01', repetition=1):
    return PlannedObservation(observation_id=identity, sample_id=identity, case_id=case,
        configuration='generative_full_source', repetition=repetition)


def result(planned, counts):
    tp, fp, fn = counts
    return ResearchResult(sample_id=planned.sample_id, case_id=planned.case_id,
        cohort='authored', configuration=planned.configuration, repetition=planned.repetition,
        evaluation=EvaluationResult(tp=tp, fp=fp, fn=fn, precision=0, recall=0, f1=0,
            true_positive_edges=[], false_positive_edges=[], false_negative_edges=[],
            provenance_passed=0, provenance_failed=0, provenance_accuracy=0,
            provenance_passes=[], provenance_failures=[]))


def test_pool_integer_counts_across_observations_instead_of_averaging_f1():
    first, second = slot('a'), slot('b', 'case_02')
    aggregate = aggregate_observations([first, second],
        [result(first, (8, 2, 2)), result(second, (1, 0, 3))])
    assert (aggregate.tp, aggregate.fp, aggregate.fn, aggregate.f1) == (9, 2, 5, 0.72)
    assert aggregate.cases[0].f1 == 0.8
    assert aggregate.cases[1].f1 == 0.4


def test_failed_slot_keeps_planned_membership_and_survivor_score():
    first, second, third = slot('a'), slot('b', 'case_02'), slot('c', 'case_03')
    failed = ResearchResult(sample_id='c', case_id='case_03', cohort='authored',
        configuration='generative_full_source', repetition=1, status='provider_error')
    aggregate = aggregate_observations([first, second, third],
        [result(first, (8, 2, 2)), result(second, (1, 0, 3)), failed])
    assert aggregate.f1 == 0.72
    assert aggregate.state == 'provisional'
    assert aggregate.coverage.model_dump() == dict(planned=3, scored=2, pending=0, failed=1, uncertain=0, unavailable=0)
    assert aggregate.cases[2].coverage.failed == 1
    assert aggregate.cases[2].f1 is None


def test_repeated_observations_retain_weight_but_duplicate_slots_fail():
    import pytest
    first, second, third = slot('a'), slot('b', 'case_02'), slot('c', 'case_02', 2)
    rows = [result(first, (8, 2, 2)), result(second, (1, 0, 3)), result(third, (1, 0, 3))]
    aggregate = aggregate_observations([third, first, second], rows[::-1])
    assert (aggregate.tp, aggregate.fp, aggregate.fn) == (10, 2, 8)
    assert aggregate.f1 == pytest.approx(20 / 30)
    assert aggregate.state == 'complete'
    with pytest.raises(ValueError, match='Duplicate'):
        aggregate_observations([first, first], rows[:1])
    with pytest.raises(ValueError, match='Duplicate'):
        aggregate_observations([first], [rows[0], rows[0]])


def test_zero_differs_from_null_and_completed_without_evaluation_is_unavailable():
    first = slot('a')
    zero = result(first, (0, 0, 0))
    assert aggregate_observations([first], [zero]).f1 == 0
    missing = zero.model_copy(update={'evaluation': None})
    aggregate = aggregate_observations([first], [missing])
    assert aggregate.f1 is None
    assert aggregate.coverage.unavailable == 1
    assert aggregate.state == 'unavailable'
    assert aggregate_observations([first], []).coverage.pending == 1


def test_invalid_counts_do_not_produce_a_numeric_aggregate():
    first = slot('a')
    invalid = result(first, (-1, 0, 0))
    aggregate = aggregate_observations([first], [invalid])
    assert aggregate.f1 is None
    assert aggregate.coverage.unavailable == 1
    assert 'invalid' in aggregate.observations[0].reason.lower()


def test_incurred_cost_counts_unique_attempts_including_failure_and_not_saved_spend():
    from private_client_graph.workbench.run_evaluation import incurred_cost
    from private_client_graph.workbench.run_evaluation_contracts import AttemptCost
    attempts = [AttemptCost(attempt_id='extract', cost=.10),
        AttemptCost(attempt_id='resolve1', cost=.02), AttemptCost(attempt_id='resolve2', cost=.02),
        AttemptCost(attempt_id='failed', cost=.01), AttemptCost(attempt_id='extract', cost=.10),
        AttemptCost(attempt_id='old', cost=4, incurred=False)]
    cost = incurred_cost(attempts)
    assert cost.total == .15
    assert cost.known_subtotal == .15
    assert cost.unpriced_attempts == 0
    assert cost.attempts == 4
    assert incurred_cost([]).total == 0


def test_unpriced_or_incompatible_currency_cannot_be_reported_as_known_total():
    import pytest
    from private_client_graph.workbench.run_evaluation import incurred_cost
    from private_client_graph.workbench.run_evaluation_contracts import AttemptCost
    known = AttemptCost(attempt_id='known', cost=.15)
    cost = incurred_cost([known, AttemptCost(attempt_id='uncertain')])
    assert cost.total is None
    assert cost.known_subtotal == .15
    assert cost.unpriced_attempts == 1
    assert cost.reasons
    incompatible = incurred_cost([known, AttemptCost(attempt_id='eur', cost=.2, currency='EUR')])
    assert incompatible.total is None
    assert incompatible.known_subtotal is None
    assert 'currenc' in incompatible.reasons[0].lower()
    with pytest.raises(ValueError, match='Conflicting'):
        incurred_cost([known, known.model_copy(update={'cost': .20})])


def test_legacy_bundle_cannot_silently_gain_new_run_aggregate(tmp_path):
    from private_client_graph.research.artifacts import Bundle
    from private_client_graph.research.fixtures import load_inputs
    from private_client_graph.research.plan import ExperimentPlan
    from private_client_graph.workbench.run_evaluation import evaluate_run
    bundle = Bundle.create(tmp_path / 'legacy', ExperimentPlan(inputs=load_inputs()[:1]),
        task_ledger=tmp_path / 'ledger')
    projection = evaluate_run(bundle)
    assert projection.aggregate.f1 is None
    assert projection.cost.total is None
    assert projection.scope is None
    assert projection.reasons
    assert not projection.eligibility.f1_by_run


def run_bundle(path, *, mode='saved', execution='recorded', repetitions=1):
    from private_client_graph.research.artifacts import Bundle
    from private_client_graph.research.fixtures import load_inputs
    from private_client_graph.research.run_plan import RunPlan
    from private_client_graph.research.plan import Pricing
    inputs = [row for row in load_inputs() if row.sample_id in ('case_01_fixture', 'case_02_fixture')]
    count = len(inputs) * (repetitions + (mode == 'fresh'))
    plan = RunPlan(pricing=Pricing(input_per_million=.1, output_per_million=.2, model='deepseek-flash', source_url='retained', retrieved_at='2026-10-12'), inputs=inputs, input_mode=mode, execution_mode=execution,
        resolver='generative', repetitions=repetitions, fresh_extractions=int(mode == 'fresh'),
        max_calls=count, invocation_cap=count,
        task_call_cap=20 if execution == 'live' else 0,
        kind='live_experiment' if execution == 'live' else 'demonstration')
    return Bundle.create(path, plan, task_ledger=path.parent / 'ledger')


def test_bundle_projection_has_one_point_and_records_scope_and_artifact_identity(tmp_path):
    from private_client_graph.workbench.run_evaluation import evaluate_run
    bundle = run_bundle(tmp_path / 'run')
    slots = [PlannedObservation.model_validate(row.model_dump()) for row in bundle.plan.planned_slots]
    for planned, counts in zip(slots, [(8, 2, 2), (1, 0, 3)]):
        bundle.save_result(planned.observation_id, result(planned, counts).model_dump(mode='json'))
    value = evaluate_run(bundle)
    assert value.aggregate.f1 == .72
    assert value.eligibility.f1_by_run
    assert value.eligibility.f1_vs_cost
    assert value.cost.total == 0
    assert value.scope.identity
    assert value.artifact_digest
    assert value.run_id == bundle.manifest['experiment_id']


def test_live_cost_reads_shared_only_reservation_without_mutating_bundle(tmp_path):
    from private_client_graph.research.artifacts import write_json_once
    from private_client_graph.workbench.run_evaluation import evaluate_run
    bundle = run_bundle(tmp_path / 'live', execution='live')
    planned = PlannedObservation.model_validate(bundle.plan.planned_slots[0].model_dump())
    bundle.save_result('result', result(planned, (8, 2, 2)).model_dump(mode='json'))
    record = {'attempt_id': planned.observation_id, 'status': 'provider_error', 'response': {'usage': {'input_tokens': 1500000, 'output_tokens': 0, 'cached_tokens': 0}}}
    write_json_once(bundle.path / 'attempts' / 'first.started.json', record)
    shared = bundle.task_ledger / 'reservations'
    prefix = bundle.manifest['experiment_id']
    write_json_once(shared / f'{prefix}-first.json', record)
    known = evaluate_run(bundle)
    assert known.cost.total == .15
    write_json_once(shared / f'{prefix}-uncertain.json', {'attempt_id': 'uncertain', 'status': 'uncertain'})
    value = evaluate_run(bundle)
    assert value.cost.total is None
    assert value.cost.known_subtotal == .15
    assert value.cost.unpriced_attempts == 1
    assert value.eligibility.f1_by_run and not value.eligibility.f1_vs_cost
    assert len(bundle.attempts()) == 1


def test_upstream_failure_preserves_every_planned_repetition(tmp_path):
    from private_client_graph.research.artifacts import write_json_once
    from private_client_graph.workbench.run_evaluation import evaluate_run
    bundle = run_bundle(tmp_path / 'fresh', mode='fresh', repetitions=3)
    first = bundle.plan.planned_slots[0]
    write_json_once(bundle.path / 'attempts' / 'failed.started.json',
        {'attempt_id': first.extraction_attempt_id, 'status': 'provider_error'})
    value = evaluate_run(bundle)
    assert value.aggregate.coverage.planned == 6
    assert value.aggregate.coverage.failed == 3
    assert value.aggregate.coverage.pending == 3
    assert value.aggregate.cases[0].coverage.failed == 3
    assert value.aggregate.f1 is None


def test_scope_matching_ignores_labels_but_discloses_provenance_and_source_changes(tmp_path):
    from private_client_graph.workbench.run_evaluation import compare_runs
    left, right = run_bundle(tmp_path / 'left'), run_bundle(tmp_path / 'right')
    right.plan.case_metadata = {'case_01_fixture': {'name': 'Renamed'}}
    right.manifest['provenance']['git_sha'] = 'different'
    comparison = compare_runs(left, right)
    assert comparison.comparable_scope
    assert comparison.matched_inputs == 2
    assert len(comparison.pairs) == 2
    assert comparison.provenance_differences
    assert not comparison.unqualified_improvement_allowed
    right.plan.inputs[0].source += '\nChanged source'
    changed = compare_runs(left, right)
    assert not changed.comparable_scope
    assert changed.scope_differences
    assert changed.matched_inputs == 1
    assert len(changed.exclusions) == 2


def test_real_retained_usage_prices_extraction_resolvers_and_known_failure_once(tmp_path):
    from private_client_graph.research.artifacts import write_json_once
    from private_client_graph.workbench.run_evaluation import evaluate_run
    bundle = run_bundle(tmp_path / 'live', mode='fresh', execution='live', repetitions=2)
    for identity, tokens, status in [('extract', 1000000, 'completed'),
        ('resolve1', 200000, 'completed'), ('resolve2', 200000, 'completed'),
        ('failed', 100000, 'provider_error')]:
        record = {'attempt_id': identity, 'status': status,
            'response': {'usage': {'input_tokens': tokens, 'output_tokens': 0, 'cached_tokens': 0}}}
        write_json_once(bundle.path / 'attempts' / f'{identity}.started.json', record)
        write_json_once(bundle.task_ledger / 'reservations' / f"{bundle.manifest['experiment_id']}-{identity}.json", record)
    cost = evaluate_run(bundle).cost
    assert cost.total == .15
    assert cost.known_subtotal == .15
    assert cost.attempts == 4


def test_fresh_matching_scope_does_not_claim_exact_pairing(tmp_path):
    from private_client_graph.workbench.run_evaluation import compare_runs
    comparison = compare_runs(run_bundle(tmp_path / 'left', mode='fresh'),
        run_bundle(tmp_path / 'right', mode='fresh'))
    assert comparison.comparable_scope
    assert comparison.matched_inputs == 0
    assert len(comparison.exclusions) == 4
    assert not comparison.unqualified_improvement_allowed


def test_scope_differences_explain_truth_and_allocation_changes(tmp_path):
    from private_client_graph.workbench.run_evaluation import compare_runs
    left, right = run_bundle(tmp_path / 'left'), run_bundle(tmp_path / 'right', repetitions=2)
    right.plan.inputs[0].truth.relationships.clear()
    comparison = compare_runs(left, right)
    assert any('truth_digest' in difference for difference in comparison.scope_differences)
    assert any('repetitions' in difference for difference in comparison.scope_differences)
    assert not comparison.comparable_scope
