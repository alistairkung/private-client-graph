"""Attribution diagnostics supplement, never reinterpret, legacy quote scoring."""
import json

import pytest

from private_client_graph.graph import build_canonical_state
from private_client_graph.models import SourcedExtractionResult, GroundTruth
from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.export import export_bundle, verify_export
from private_client_graph.research.provider import ModelResponse, request_messages, ModelRequest, ModelSettings
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.runner import execute
from private_client_graph.research.source_attribution import (
    SourceEvidenceApproval, diagnose_source_attribution, aggregate_source_attribution,
)
from private_client_graph.research.summary import summarize
from private_client_graph.workbench.case_catalog import repository_inputs, default_input_ids, load_case_catalog
from private_client_graph.workbench.evidence import relationship_outcomes
from private_client_graph.workbench.run_evaluation import aggregate_observations


def test_all_development_and_heldout_ideals_replay_actual_sourced_pipeline_without_providers(tmp_path):
    inputs = [sample for sample in repository_inputs() if sample.sample_id in default_input_ids()
              or sample.case_id.startswith('heldout_')]
    assert len(inputs) == 15
    assert len(default_input_ids()) == 5
    plan = RunPlan(inputs=inputs, max_calls=0, invocation_cap=0)
    bundle = Bundle.create(tmp_path / 'ideals', plan)
    execute(bundle, provider=lambda _: pytest.fail('Replay cannot invoke a provider'))
    rows = bundle.results()
    assert len(rows) == 15
    assert all(row['evaluation']['f1'] == 1 for row in rows if row['case_id'] != 'case_03')
    alias_baseline = next(row for row in rows if row['case_id'] == 'case_03')
    assert alias_baseline['evaluation']['f1'] == pytest.approx(6 / 7)
    # Case 03 deliberately preserves surface aliases in its raw authored fixture.
    assert all(row['source_attribution']['failed'] == 0 for row in rows)
    assert all(row['source_attribution']['assessed'] > 0 for row in rows)
    assert all(row['sourced_extraction'] and row['state'] for row in rows)
    results = [ResearchResult.model_validate(row) for row in rows]
    aggregate = aggregate_observations(plan.planned_slots, results)
    assert aggregate.coverage.scored == 15
    assert aggregate.source_attribution.assessed == sum(row.source_attribution.assessed for row in results)
    assert aggregate.source_attribution.accuracy == 1
    assert {item.kind for item in load_case_catalog() if item.case_id.startswith('heldout_')} == {'heldout'}
    write_json_once(bundle.path / 'summary.json', summarize(bundle))
    archive = export_bundle(bundle, tmp_path / 'ideals.zip')
    assert verify_export(archive)
    reopened = Bundle.open(bundle.path)
    assert reopened.plan.inputs == inputs
    assert reopened.plan.inputs[-1].sources == inputs[-1].sources


def test_fresh_source_request_freezes_order_identity_and_failed_or_completed_provider_outputs(tmp_path):
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_05')
    plan = RunPlan(inputs=[sample], input_mode='fresh', fresh_extractions=1,
                   execution_mode='recorded', max_calls=1, invocation_cap=1)
    bundle = Bundle.create(tmp_path / 'fresh', plan)
    requests = []
    def provider(request):
        requests.append(request)
        assert request.sources == sample.sources
        assert json.loads(request_messages(request)[1][1]) == [source.model_dump() for source in sample.sources]
        assert 'latest explicitly effective' in request_messages(request)[0][1]
        return ModelResponse(payload=sample.sourced_extraction.model_dump())
    execute(bundle, provider=provider)
    assert len(requests) == 1
    row = ResearchResult.model_validate(bundle.results()[0])
    assert row.state.sources == sample.sources
    assert row.evaluation.f1 == 1
    assert row.source_attribution.accuracy == 1
    assert bundle.attempts()[0]['request']['sources'] == [source.model_dump() for source in sample.sources]
    execute(bundle, provider=lambda _: pytest.fail('Retained attempts cannot be reissued'))
    from private_client_graph.research.inputs import ResearchInput
    frozen = ResearchInput.model_validate_json(next((bundle.path / 'fresh_inputs').glob('*.json')).read_text())
    assert frozen.sourced_extraction == sample.sourced_extraction
    assert frozen.source_evidence == sample.source_evidence
    assert frozen.origin_hashes['sources/note_01.txt'] == sample.origin_hashes['sources/note_01.txt']


def test_invalid_source_output_remains_unscored_and_retains_raw_attributed_candidates(tmp_path):
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_04')
    payload = sample.sourced_extraction.model_dump()
    payload['relationships'][0]['source_id'] = 'absent'
    plan = RunPlan(inputs=[sample], input_mode='fresh', fresh_extractions=1,
                   execution_mode='recorded', max_calls=1, invocation_cap=1)
    bundle = Bundle.create(tmp_path / 'invalid', plan)
    execute(bundle, provider=lambda _: ModelResponse(payload=payload))
    row = bundle.results()[0]
    assert row['status'] == 'graph_error'
    assert row['evaluation'] is None
    assert row['sourced_extraction']['relationships'][0]['source_id'] == 'absent'
    assert bundle.attempt_count == 1


def test_wrong_source_with_identical_quote_fails_attribution_while_quote_metric_passes():
    from private_client_graph.evaluation import evaluate_graph
    from private_client_graph.canonical_state import reconstruct_graph
    quote = 'Alice is trustee of Harbour Trust.'
    sources = [Source(id=identity, title='Same title', text=quote) for identity in ('first', 'second')]
    truth = GroundTruth(entities=[dict(id='p', type='person', name='Alice'), dict(id='t', type='trust', name='Harbour Trust')],
        relationships=[dict(source='p', type='trustee_of', target='t', approved_evidence=[quote])])
    approval = SourceEvidenceApproval(relationships=[dict(source='p', type='trustee_of', target='t',
        approved_evidence=[dict(source_id='first', supporting_text=quote)])])
    claims = SourcedExtractionResult(relationships=[dict(source_id='second', source_name='Alice',
        relationship_type='trustee_of', target_name='Harbour Trust', supporting_text=quote)])
    state = build_canonical_state(claims.relationships, sources=sources)
    assert evaluate_graph(reconstruct_graph(state), truth).provenance_accuracy == 1
    diagnostic = diagnose_source_attribution(state, truth, approval)
    assert (diagnostic.assessed, diagnostic.passed, diagnostic.failed, diagnostic.accuracy) == (1, 0, 1, 0)
    assert diagnostic.failures[0].source_id == 'second'
    empty = build_canonical_state([], sources=sources)
    missing = diagnose_source_attribution(empty, truth, approval)
    assert missing.assessed == 0 and missing.accuracy is None
    assert aggregate_source_attribution([missing, diagnostic]).accuracy == 0


def test_workbench_quote_occurrences_use_actual_source_and_preserve_expected_source_pairs():
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_04')
    state = build_canonical_state(sample.sourced_extraction.relationships, sources=sample.sources)
    from private_client_graph.canonical_state import reconstruct_graph
    from private_client_graph.evaluation import evaluate_graph
    graph = reconstruct_graph(state)
    result = ResearchResult(sample_id=sample.sample_id, case_id=sample.case_id, cohort=sample.cohort,
                            state=state, graph=graph, evaluation=evaluate_graph(graph, sample.truth))
    outcomes = relationship_outcomes(sample, result)
    sources = {source.id: source.text for source in sample.sources}
    for relationship in outcomes:
        for quote in relationship.expected + relationship.predicted:
            assert quote.source_id in sources
            assert quote.occurrences
            assert all(sources[quote.source_id][start:end] == quote.text for start, end in quote.occurrences)
    assert len({quote.source_id for relationship in outcomes for quote in relationship.predicted}) == 2


def test_source_bundle_comparison_identity_changes_with_order_and_identity():
    from private_client_graph.workbench.run_evaluation import _benchmark_scope
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_04')
    plan = RunPlan(inputs=[sample], max_calls=0, invocation_cap=0)
    reversed_sample = sample.model_copy(deep=True)
    reversed_sample.sources.reverse()
    other = RunPlan(inputs=[reversed_sample], max_calls=0, invocation_cap=0)
    assert _benchmark_scope(plan).identity != _benchmark_scope(other).identity


def test_external_application_reservations_share_task_ceiling_and_never_reset_it(tmp_path):
    from private_client_graph.research.live_accounting import (
        initialize_task, authorize_external_invocation, reserve_external_attempt, task_state,
    )
    from private_client_graph.research.artifacts import BudgetExceeded
    from pathlib import Path
    root = tmp_path / 'task'
    task = initialize_task(root, 'Test shared synthetic task')
    research = authorize_external_invocation(root, purpose='substituted research caller', task_cap=3,
                                             invocation_cap=2, approval_reference='deterministic test')
    application = authorize_external_invocation(root, purpose='application smoke', task_cap=3,
                                                invocation_cap=2, approval_reference='deterministic test')
    assert reserve_external_attempt(root, authorization=research['authorization'], attempt_id='dev1')
    assert reserve_external_attempt(root, authorization=research['authorization'], attempt_id='dev1') is False
    assert reserve_external_attempt(root, authorization=application['authorization'], attempt_id='app1')
    assert reserve_external_attempt(root, authorization=research['authorization'], attempt_id='dev2')
    assert task_state(Path(task['ledger']))['used'] == 3
    with pytest.raises(BudgetExceeded, match='Shared task'):
        reserve_external_attempt(root, authorization=application['authorization'], attempt_id='app2')
    assert task_state(Path(task['ledger']))['used'] == 3
    shared = next((Path(task['ledger']) / 'reservations').glob('*-app1.json'))
    shared.unlink()
    with pytest.raises(ValueError, match='incomplete'):
        task_state(Path(task['ledger']))


@pytest.mark.parametrize('defect', ['missing_edge', 'duplicate_edge', 'empty_support', 'duplicate_pair',
                                    'unknown_source', 'wrong_quote', 'missing_alternative'])
def test_malformed_source_approvals_fail_before_any_experiment(defect):
    from private_client_graph.research.inputs import ResearchInput
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_04')
    raw = sample.model_dump()
    approval = raw['source_evidence']['relationships']
    if defect == 'missing_edge':
        approval.pop()
    elif defect == 'duplicate_edge':
        approval.append(approval[0])
    elif defect == 'empty_support':
        approval[0]['approved_evidence'] = []
    elif defect == 'duplicate_pair':
        approval[0]['approved_evidence'].append(approval[0]['approved_evidence'][0])
    elif defect == 'unknown_source':
        approval[0]['approved_evidence'][0]['source_id'] = 'absent'
    elif defect == 'wrong_quote':
        approval[0]['approved_evidence'][0]['supporting_text'] = 'Invented quote'
    elif defect == 'missing_alternative':
        edge = next(edge for edge in approval if len({item['supporting_text'] for item in edge['approved_evidence']}) > 1)
        edge['approved_evidence'] = edge['approved_evidence'][:1]
    with pytest.raises(ValueError):
        ResearchInput.model_validate(raw)


def test_source_aware_recorded_response_keeps_schema_and_has_distinct_identity(tmp_path):
    from private_client_graph.research.demo import recording_key, recorded_response
    sample = next(sample for sample in repository_inputs() if sample.case_id == 'case_05')
    request = ModelRequest(stage='extraction', source=sample.source, sources=sample.sources, settings=ModelSettings())
    legacy = ModelRequest(stage='extraction', source=sample.source, settings=ModelSettings())
    assert recording_key(request) != recording_key(legacy)
    records = {'extraction': {recording_key(request): sample.sourced_extraction.model_dump()}}
    assert recorded_response(request, records=records).payload == sample.sourced_extraction.model_dump()
    with pytest.raises(ValueError, match='exact input'):
        recorded_response(legacy, records=records)


def test_external_failure_outcome_retains_shared_attempt_without_refunding_or_reissuing(tmp_path):
    from pathlib import Path
    from private_client_graph.research.live_accounting import (
        initialize_task, authorize_external_invocation, reserve_external_attempt,
        finish_external_attempt, task_state,
    )
    from private_client_graph.research.artifacts import BudgetExceeded
    task = initialize_task(tmp_path, 'Shared caller failure')
    authority = authorize_external_invocation(tmp_path, purpose='Application smoke', task_cap=1,
        invocation_cap=1, approval_reference='Deterministic explicit approval')
    authorization = authority['authorization']
    assert reserve_external_attempt(tmp_path, authorization=authorization, attempt_id='failed-call')
    finish_external_attempt(tmp_path, authorization=authorization, attempt_id='failed-call',
                            outcome='failed', error_type='TimeoutError')
    retained = json.loads((tmp_path / 'external-invocations' / authorization /
                          'attempts/failed-call.finished.json').read_text())
    assert retained['outcome'] == 'failed'
    assert retained['error_type'] == 'TimeoutError'
    assert retained['usage'] is None
    assert task_state(Path(task['ledger']))['used'] == 1
    assert not reserve_external_attempt(tmp_path, authorization=authorization, attempt_id='failed-call')
    with pytest.raises(BudgetExceeded):
        reserve_external_attempt(tmp_path, authorization=authorization, attempt_id='retry')
    with pytest.raises(FileExistsError):
        finish_external_attempt(tmp_path, authorization=authorization, attempt_id='failed-call',
                                outcome='completed')


@pytest.mark.parametrize('authorization,attempt_id', [('external-invalid', 'call'),
                                                       ('external-' + 'a' * 32, '../escape')])
def test_external_completion_rejects_unsafe_identity_before_reading_task(tmp_path, authorization, attempt_id):
    from private_client_graph.research.live_accounting import finish_external_attempt
    with pytest.raises(ValueError, match='identity'):
        finish_external_attempt(tmp_path, authorization=authorization, attempt_id=attempt_id,
                                outcome='completed')
