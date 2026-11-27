"""Provider-free regressions for the operational mixed-reference benchmark."""
import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from benchmark_v3.commissioning import trusted_bytes
from benchmark_v3.evaluation_protocol import GraphCounts, PlannedCondition, UnavailablePrediction
from benchmark_v3.replay_manifest import SavedIdeal, VerifiedCondition, VerifiedFamily
from benchmark_v3.retained_evaluation import verify_first_live_baseline
from private_client_graph.graph import build_canonical_state
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.models.sourced_extraction import SourcedRelationshipCandidate
from private_client_graph.research import benchmark_v4
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.benchmark_v4 import BenchmarkWorkload, load_roster, load_workload
from private_client_graph.research.benchmark_v4_scoring import evaluate_benchmark_v4
from private_client_graph.research.exploratory_reference import ConsensusReference
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.provider import ModelRequest, ModelResponse, request_messages
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.runner import execute
from private_client_graph.workbench import benchmark_v4 as workbench
from private_client_graph.workbench.api import create_app
from private_client_graph.workbench.benchmark_v4_comparison import compare_benchmark_v4_runs
from private_client_graph.workbench.execution_contracts import TaskBudget
from private_client_graph.workbench.run_inspection import read_run
from private_client_graph.workbench.run_planning import freeze_run, preview_run
from private_client_graph.workbench.supervisor import event
from private_client_graph.workbench.workspace_contracts import CreateExperiment, FreezeRun
from private_client_graph.workbench.workspaces import create_experiment

OWNER_CREDS = ('owner', 'private-test-token-not-a-secret-00')
DIGEST = 'a' * 64
FIRST = {'source_id': 'terms', 'supporting_text': 'The office is defined here.'}
SECOND = {'source_id': 'register', 'supporting_text': 'The steward is assigned here.'}


@pytest.fixture
def workload():
    roster = load_roster()
    records = defaultdict(dict)
    planned = []
    inputs = []
    for item in roster.inputs[:-1]:
        saved = SavedIdeal.model_validate({
            'condition': item.id,
            'truth': {
                'entities': [{'id': 'person', 'name': 'Tess', 'type': 'person'},
                             {'id': 'trust', 'name': 'Dale Trust', 'type': 'trust'}],
                'relationships': [{'source': 'person', 'type': 'trustee_of', 'target': 'trust',
                                   'approved_evidence': []}],
            },
            'source_approval': {'relationships': []},
            'ideal': {'relationships': []},
            'sufficient_evidence': [
                {'edge': ['Tess', 'trustee_of', 'Dale Trust'], 'joint_only': True,
                 'alternatives': [[FIRST, SECOND]]},
            ],
        })
        sources = [Source(id=part['source_id'], title=part['source_id'], text=part['supporting_text'])
                   for part in (FIRST, SECOND)]
        frozen = VerifiedCondition(saved, sources, DIGEST, DIGEST, {})
        planned.append(PlannedCondition(item.matter, frozen))
        records[item.matter][item.id] = frozen
        inputs.append(_template(item, sources, saved.truth.model_dump()))
    families = {matter: VerifiedFamily(matter, DIGEST, DIGEST, dict(conditions), {}, {}, set(), set())
                for matter, conditions in records.items()}

    u8_sources = [Source(id=f'doc_{index}', title=f'Test document {index}', text=f'Body {index}.')
                  for index in range(65)]
    accepted = [_candidate(f'Reference marker {index}', f'Person {index}', 'spouse_of',
                           source_id=f'doc_{index}', supporting_text=f'Body {index}.')
                for index in range(6)]
    state = build_canonical_state(accepted, sources=u8_sources)
    truth = {'entities': [item.model_dump() for item in state.entities], 'relationships': [
        {'source': item.source, 'type': item.type, 'target': item.target, 'approved_evidence': []}
        for item in state.relationships
    ]}
    inputs.append(_template(roster.inputs[-1], u8_sources, truth))
    reference = ConsensusReference(schema_version=1, kind='exploratory_ai_consensus', workload_id='test',
        source_file_sha256=DIGEST, cutoff='fixture', reviewer_count=10, majority=6,
        official_benchmark_eligible=False, limitations=[], reviewer_open_questions=[], relationships=[])
    return BenchmarkWorkload(roster, families, tuple(planned), reference, state, tuple(inputs))


def _template(item, sources, truth):
    return ResearchInput.model_validate({
        'sample_id': item.sample_id, 'case_id': item.matter, 'cohort': 'authored',
        'source': sources[0].text, 'sources': sources, 'truth': truth,
        'extraction': {'relationships': []}, 'sourced_extraction': {'relationships': []},
        'origin_hashes': {'sources': DIGEST, 'reference': DIGEST},
    })


def _candidate(source, target, predicate, *, source_id, supporting_text):
    return SourcedRelationshipCandidate.model_validate(dict(source_name=source, target_name=target,
        relationship_type=predicate, source_id=source_id, supporting_text=supporting_text))


def _qualified(*members):
    return SourcedExtractionResult(relationships=[
        _candidate('Tess', 'Dale Trust', 'trustee_of', **part) for part in members
    ])


def _consensus():
    return SourcedExtractionResult(relationships=[
        _candidate('Person 0', 'Reference marker 0', 'spouse_of', source_id='doc_0', supporting_text='Body 0.'),
        _candidate('Wrong', 'Pair', 'sibling_of', source_id='doc_0', supporting_text='Body 0.'),
    ])


def test_manifest_references_all_original_conditions_and_single_u8_input():
    roster = load_roster()
    public = json.loads(trusted_bytes('admissions/2026-11-24.json'))
    assert len(roster.inputs) == 35
    assert len({item.matter for item in roster.inputs}) == 20
    original = [(row['family'], condition) for row in public['families'] for condition in row['conditions']]
    assert [(item.matter, item.id) for item in roster.inputs[:-1]] == original
    assert {item.reference_methodology for item in roster.inputs[:-1]} == {'original_qualification'}
    u8 = roster.inputs[-1]
    assert (u8.matter, u8.id, u8.source_count, u8.reference_methodology) == (
        'U', 'u8', 65, 'consensus_adjudication',
    )
    assert roster.definition.consensus.source_file_sha256 == '6897368841e4ac84484783e109e3dd54ea587286322c382c15030465b977f6e1'
    assert roster.definition.consensus.reference_sha256 == 'eb5320f5627128472a5cae90337f22d3f8c88dc408164f0cf0ac03f0f46befca'


def test_graph_pool_uses_expected_edges_for_every_unavailable_input(workload):
    predictions = {'A0': _qualified(FIRST, SECOND),
                   'A1': _qualified(FIRST | {'source_id': 'unknown'}),
                   'A2': UnavailablePrediction('provider_failure'),
                   'B0': UnavailablePrediction('parse_failure'),
                   'B1': UnavailablePrediction('uncertain'),
                   'u8': _consensus()}
    result = evaluate_benchmark_v4(workload, predictions, observation_origin='offline_fixture', complete=True)
    assert result.summary.state == 'provisional'
    assert result.summary.combined.counts == GraphCounts(2, 1, 38)
    assert result.summary.combined.f1 == 4 / 43
    assert result.summary.combined.precision == 2 / 3
    assert result.summary.combined.recall == 2 / 40
    assert result.summary.combined.valid_graphs == 2
    assert result.summary.combined.without_graph == 33
    assert result.summary.combined.exact_graphs == 1
    assert result.summary.combined.outcomes == {'scored': 2, 'validation_failure': 1, 'provider_failure': 1,
        'parse_failure': 1, 'uncertain': 1, 'not_attempted': 29}
    assert result.summary.by_matter['U'].counts == GraphCounts(1, 1, 5)
    assert result.summary.qualified.counts == result.qualified.cohort.all_conditions == GraphCounts(1, 0, 33)
    assert result.qualified.cohort.complete_proofs == result.qualified.cohort.complete_joint_proofs == 1
    assert result.qualified.cohort.planned_proofs == result.qualified.cohort.planned_joint_proofs == 34
    assert result.consensus.planned_proofs == result.consensus.planned_joint_proofs == 0
    assert result.summary.consensus_evidence.matched_citations == 1
    assert result.summary.consensus_evidence.reference_citations == 6
    assert evaluate_benchmark_v4(workload, dict(reversed(list(predictions.items()))),
                                 observation_origin='offline_fixture').summary == result.summary


def test_missing_invalid_and_empty_u8_have_distinct_construction_outcomes(workload):
    result = evaluate_benchmark_v4(workload, {}, observation_origin='offline_fixture')
    assert result.summary.state == 'unmeasured' and result.summary.combined is None
    bad = _consensus().model_copy(deep=True)
    bad.relationships[0].supporting_text = 'Absent.'
    for prediction, expected in [
        (bad, 'validation_failure'), (UnavailablePrediction('provider_failure'), 'provider_failure'),
        (SourcedExtractionResult(relationships=[]), 'scored'),
    ]:
        result = evaluate_benchmark_v4(workload, {'u8': prediction}, observation_origin='offline_fixture')
        assert result.consensus.outcome == expected
        assert result.summary.consensus.counts == GraphCounts(0, 0, 6)
        assert result.summary.consensus_evidence.assessed is (expected == 'scored')
        assert result.summary.consensus.valid_graphs == int(expected == 'scored')


def test_v4_owner_catalog_and_default_frozen_workbench_plan(tmp_path, monkeypatch, workload):
    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(tmp_path))
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    monkeypatch.setenv('PCG_BENCHMARK_V4_OWNER_TOKEN', OWNER_CREDS[1])
    monkeypatch.setattr(workbench, 'load_workload', lambda _: workload)
    monkeypatch.setattr('private_client_graph.workbench.run_planning.require_live',
        lambda _: TaskBudget(task_id='fake-task', label='Fixture', used=0, cap=35, remaining=35))
    app = create_app()
    client = TestClient(app, client=('127.0.0.1', 54321))
    url = '/api/research/v2/benchmark-v4'
    assert client.get(url).status_code == 401
    remote = TestClient(app, client=('192.0.2.2', 54321))
    assert remote.get(url, auth=OWNER_CREDS).status_code == 403
    assert client.get(url, auth=OWNER_CREDS).headers['cache-control'] == 'no-store'
    for identity, quantity in [('A0', 1), ('u8', 6)]:
        response = client.get(f'{url}/inputs/{identity}', auth=OWNER_CREDS)
        assert response.status_code == 200
        inspection = response.json()
        assert inspection['result'] is None
        assert len(inspection['benchmark']['expected']['relationships']) == quantity
    assert client.get(f'{url}/inputs/unknown', auth=OWNER_CREDS).status_code == 404

    draft = workbench.default_benchmark_draft(tmp_path)
    preview = preview_run(draft.configuration, tmp_path)
    assert preview.extraction_call_maximum == preview.planned_observations == 35
    assert preview.resolution_call_maximum == 0
    with pytest.raises(ValueError, match='all 35'):
        preview_run(draft.configuration.model_copy(update={'input_ids': draft.configuration.input_ids[:-1]}), tmp_path)
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='create', name='Test'), initial_draft=draft)
    cmd = FreezeRun(request_id='freeze', expected_revision=0)
    frozen = freeze_run(tmp_path, workspace.id, cmd)
    assert freeze_run(tmp_path, workspace.id, cmd) == frozen
    retained = read_run(tmp_path, workspace.id, frozen.id)
    assert retained.benchmark_v4.combined is None
    assert retained.benchmark_v4.state == 'unmeasured'
    assert retained.benchmark.cohort.planned_conditions == 34
    assert len(retained.observations[-1].sources) == 65
    assert retained.attempts == []


def test_shared_runner_substitution_keeps_reference_out_of_requests(tmp_path, monkeypatch, workload):
    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(tmp_path))
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.setattr(benchmark_v4, 'load_workload', lambda _: workload)
    plan = RunPlan(benchmark_v4_sha256=workload.roster.sha256, inputs=list(workload.inputs),
        execution_mode='recorded', input_mode='fresh', fresh_extractions=1, max_calls=35, invocation_cap=35)
    bundle = Bundle.create(tmp_path / 'recorded', plan, task_ledger=tmp_path / 'ledger')
    requests: list[ModelRequest] = []

    def substitute(request: ModelRequest) -> ModelResponse:
        requests.append(request)
        extraction = _consensus() if len(request.sources or []) == 65 else _qualified(FIRST, SECOND)
        return ModelResponse(payload=extraction.model_dump())

    execute(bundle, provider=substitute)
    assert len(requests) == bundle.attempt_count == len(bundle.results()) == 35
    for request, sample in zip(requests, workload.inputs, strict=True):
        assert request == ModelRequest(stage='extraction', source=sample.source, sources=sample.sources,
                                       settings=plan.settings)
    u8_wire_messages = json.dumps(request_messages(requests[-1]))
    assert 'Reference marker' not in u8_wire_messages
    assert 'reference_sha256' not in u8_wire_messages
    assert len(requests[-1].sources) == 65
    execute(bundle, provider=lambda _: pytest.fail('Completed attempts must be replayed without a provider'))
    assert len(bundle.results()) == 35


def test_frozen_private_inputs_reference_and_baseline_reproduction():
    location = os.getenv('PCG_V3_PRIVATE_BASELINE_CUSTODY')
    if not location:
        pytest.skip('Set PCG_V3_PRIVATE_BASELINE_CUSTODY for exact custody replay')
    custody = Path(location).resolve()
    loaded = load_workload(custody)
    u8 = loaded.roster.definition.consensus
    assert len(loaded.inputs[-1].sources) == 65
    assert len(loaded.consensus_state.relationships) == 6
    old = verify_first_live_baseline(custody / 'live-baseline-2026-11-24',
                                     custody / 'admissions-2026-11-24' / 'ADMISSIONS.json')
    assert loaded.qualified == old.planned
    for template in loaded.inputs:
        assert ResearchInput.model_validate_json(template.model_dump_json()) == template
    replay = evaluate_benchmark_v4(loaded, old.predictions, observation_origin='live')
    assert replay.qualified.cohort == old.protocol.cohort
    assert replay.qualified.cohort.all_condition_micro_f1 == 182 / 214
    assert replay.qualified.cohort.exact_graphs == 20
    assert replay.qualified.cohort.complete_proofs == 18
    assert replay.qualified.cohort.complete_joint_proofs == 0
    assert replay.summary.state == 'provisional' and replay.summary.consensus is None
    assert loaded.inputs[-1].origin_hashes == {'sources': u8.source_file_sha256, 'reference': u8.reference_sha256}
    assert checksum((custody / u8.release_id / 'sources.json').read_bytes()) == u8.source_file_sha256


def test_private_custody_files_are_absent_from_git():
    tracked = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    private_names = {'REFERENCE-FREEZE.json', 'WORKBENCH-REFERENCE.json', 'AGREEMENT-MATRIX.json',
        'BLIND-COMMITMENTS.json', 'EVIDENCE-ADJUDICATED.json', 'MAJORITY-GRAPH.json'}
    assert not any(Path(path).name in private_names or 'exploratory-scale-65-7d5d252d15fd' in path
                   or '2026-11-27-u8-consensus' in path for path in tracked)


def test_substituted_live_v4_run_replays_the_same_workbench_and_cli_summary(tmp_path, monkeypatch, workload):
    from private_client_graph.research.live_accounting import initialize_task
    from private_client_graph.research.summary import summarize
    from private_client_graph.workbench.execution_contracts import LiveApproval
    from private_client_graph.workbench.planning import live_budget, open_executable
    from private_client_graph.workbench.retained_inputs import load_retained_inputs
    from private_client_graph.workbench.workspace_execution import prepare_authorization

    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(tmp_path))
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.setattr(benchmark_v4, 'load_workload', lambda _: workload)
    monkeypatch.setattr(workbench, 'load_workload', lambda _: workload)
    initialize_task(tmp_path, 'Substituted boundary test')
    draft = workbench.default_benchmark_draft(tmp_path)
    experiment = create_experiment(tmp_path, CreateExperiment(request_id='new', name='Tests'), initial_draft=draft)
    identity = experiment.id
    first = freeze_run(tmp_path, identity, FreezeRun(request_id='freeze', expected_revision=0))
    second = freeze_run(tmp_path, identity, FreezeRun(request_id='another', expected_revision=0))
    bundle, _ = open_executable(tmp_path, first.id)
    calls = []
    with pytest.raises(ValueError, match='approval'):
        execute(bundle, live=True, provider=lambda request: calls.append(request))
    assert calls == []

    prepare_authorization(tmp_path, first.id, LiveApproval(request_id='approve', plan_digest=first.digest,
        approved=True, task_id=first.task_id, expected_task_usage=0, expected_task_cap=0, task_cap=35),
        'http://localhost')
    bundle.authorization_id = 'approve'

    def stub(request):
        calls.append(request)
        index = len(calls)
        if index == 2:
            return ModelResponse(error_type='TestParseError')
        if index == 3:
            raise RuntimeError('Test provider failure')
        extraction = (_consensus() if len(request.sources) == 65 else _qualified(FIRST, SECOND))
        if index == 4:
            extraction.relationships[0].supporting_text = 'Absent.'
        return ModelResponse(payload=extraction.model_dump())

    execute(bundle, live=True, provider=stub)
    event(bundle, 'complete', 'Test outcome', 'approve')
    assert len(calls) == live_budget(tmp_path).used == 35
    retained = read_run(tmp_path, identity, first.id)
    assert retained.benchmark_v4.state == 'complete'
    assert retained.benchmark_v4.combined.counts == GraphCounts(32, 1, 8)
    assert retained.benchmark_v4.combined.without_graph == 3
    assert retained.benchmark.cohort.complete_proofs == 31
    assert retained.benchmark_v4.consensus_evidence.matched_citations == 1
    assert all(row['evaluation'] is None for row in bundle.results())
    assert [row.status for row in retained.observations[1:4]] == [
        'parse_failure', 'provider_failure', 'validation_failure',
    ]
    assert [len(row.sources) for row in retained.observations[1:4]] == [2, 2, 2]
    assert retained.benchmark_v4.model_dump(mode='json') == summarize(bundle)['benchmark_v4']
    assert 'attempts' not in summarize(bundle)['operations']
    assert read_run(tmp_path, identity, first.id).benchmark_v4 == retained.benchmark_v4

    comparison = compare_benchmark_v4_runs(retained, read_run(tmp_path, identity, second.id))
    assert comparison.comparable_scope and comparison.matched_inputs == 35
    assert not comparison.unqualified_improvement_allowed
    with pytest.raises(ValueError, match='stay in the private'):
        load_retained_inputs(tmp_path, identity, first.id)

    reservation = next((bundle.task_ledger / 'reservations').glob('*.json'))
    original = reservation.read_bytes()
    reservation.unlink()
    with pytest.raises(OSError):
        read_run(tmp_path, identity, first.id)
    reservation.write_bytes(original)
    assert read_run(tmp_path, identity, first.id).benchmark_v4 == retained.benchmark_v4

    with monkeypatch.context() as changed:
        changed.setattr('private_client_graph.research.benchmark_v4_run.benchmark_v4_scoring_digest',
                        lambda: 'b' * 64)
        with pytest.raises(ValueError, match='scorer differs'):
            read_run(tmp_path, identity, first.id)
    monkeypatch.delenv('PCG_BENCHMARK_V4_CUSTODY')
    with pytest.raises(ValueError, match='private custody'):
        read_run(tmp_path, identity, first.id)


def test_paired_resolver_retains_input_lineage_and_resumes_without_repeating_attempts(tmp_path, monkeypatch, workload):
    from private_client_graph.research.live_accounting import initialize_task
    from private_client_graph.research.summary import summarize
    from private_client_graph.workbench.execution_contracts import LiveApproval
    from private_client_graph.workbench.planning import live_budget, open_executable
    from private_client_graph.workbench.workspace_contracts import CopyRunDraft, DraftUpdate, RunConfiguration
    from private_client_graph.workbench.run_planning import copy_run_draft
    from private_client_graph.workbench.workspaces import update_draft
    from private_client_graph.workbench.workspace_execution import prepare_authorization

    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(tmp_path))
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    monkeypatch.setattr(benchmark_v4, 'load_workload', lambda _: workload)
    monkeypatch.setattr(workbench, 'load_workload', lambda _: workload)
    initialize_task(tmp_path, 'Substituted pair')
    draft = workbench.default_benchmark_draft(tmp_path)
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='new', name='Pair'), initial_draft=draft)
    identity = workspace.id
    first = freeze_run(tmp_path, identity, FreezeRun(request_id='first', expected_revision=0))
    second_config = dict(draft.configuration.model_dump(), input_mode='saved', resolver='generative',
                         retained_run_id=first.id, retained_experiment_id=identity, task_call_cap=70)
    paired = RunConfiguration.model_validate(second_config)
    with pytest.raises(ValueError, match='completed Run'):
        preview_run(paired, tmp_path)

    def open_authorized(frozen, invocation, continuation=False):
        budget = live_budget(tmp_path)
        prepare_authorization(tmp_path, frozen.id, LiveApproval(request_id=invocation, plan_digest=frozen.digest,
            approved=True, task_id=frozen.task_id, expected_task_usage=budget.used, expected_task_cap=budget.cap,
            task_cap=frozen.preview.proposal.task_call_cap, continuation=continuation), 'http://localhost')
        bundle, _ = open_executable(tmp_path, frozen.id)
        bundle.authorization_id = invocation
        return bundle

    first_bundle = open_authorized(first, 'extract')
    expected_requests, resolution_calls = [], []
    alias_input = _qualified(FIRST, SECOND)
    alias_input.relationships[0].source_name = 'T.'

    def extract(request):
        assert request.stage == 'extraction'
        expected_requests.append(request)
        index = len(expected_requests)
        if index == 2:
            return ModelResponse(error_type='SubstituteParseError')
        if index == 3:
            raise RuntimeError('Substitute provider error')
        if index == 4:
            prediction = SourcedExtractionResult(relationships=[])
        elif index == 1:
            prediction = alias_input
        else:
            prediction = _consensus() if len(request.sources) == 65 else _qualified(FIRST, SECOND)
        if index in (5, 6):
            prediction.relationships[0].source_id = 'unavailable-source'
        return ModelResponse(payload=prediction.model_dump())

    execute(first_bundle, live=True, provider=extract)
    event(first_bundle, 'complete', 'Substituted extraction finished', 'extract')
    assert len(expected_requests) == 35
    copied = copy_run_draft(tmp_path, identity, CopyRunDraft(request_id='copy', expected_revision=0, run_id=first.id))
    assert copied.configuration.resolver == 'none'
    with pytest.raises(ValueError, match='matching live Extractor-only'):
        preview_run(RunConfiguration.model_validate(dict(second_config, temperature=0.4)), tmp_path)
    other = create_experiment(tmp_path, CreateExperiment(request_id='other', name='Other'), initial_draft=draft)
    with pytest.raises(ValueError, match='belong to this Experiment'):
        preview_run(RunConfiguration.model_validate(dict(second_config, retained_experiment_id=other.id)), tmp_path)
    with pytest.raises(ValueError, match='all 35'):
        preview_run(RunConfiguration.model_validate(dict(second_config, input_ids=list(reversed(paired.input_ids)))), tmp_path)

    updated = update_draft(tmp_path, identity, DraftUpdate(request_id='pair', expected_revision=1, configuration=paired))
    second = freeze_run(tmp_path, identity, FreezeRun(request_id='second', expected_revision=updated.revision))
    assert (second.preview.planned_observations, second.preview.extraction_call_maximum,
            second.preview.resolution_call_maximum) == (35, 0, 35)
    assert second.preview.eligible_resolution_inputs == 33
    assert read_run(tmp_path, identity, second.id).benchmark_v4.state == 'unmeasured'
    second_bundle = open_authorized(second, 'resolve')
    assert second_bundle.plan.inputs == first_bundle.plan.inputs
    lineage = second_bundle.plan.retained_input_lineage
    assert len(lineage.samples) == 33 and lineage.run_id == first.id
    assert lineage.samples[first_bundle.plan.planned_slots[0].sample_id].extraction_attempt_id.endswith('-extraction')

    first_snapshot = first_bundle.path / 'fresh_inputs' / f'{first_bundle.plan.planned_slots[0].sample_id}.json'
    original = first_snapshot.read_bytes()
    first_snapshot.write_bytes(original + b' ')
    with pytest.raises(ValueError, match='frozen lineage'):
        execute(second_bundle, live=True, provider=lambda _: pytest.fail('Candidate origin changed before dispatch'))
    first_snapshot.write_bytes(original)

    def resolve(request):
        assert request.stage == 'resolution'
        wire = request_messages(request)[1][1]
        assert 'Reference marker 5' not in wire and 'truth' not in json.loads(wire)
        resolution_calls.append(request)
        if len(resolution_calls) == 2:
            assert request.extraction.relationships == []
            raise KeyboardInterrupt
        if len(resolution_calls) == 1:
            edits = [{'candidate_index': 0, 'endpoint': 'source_name', 'name': 'Tess'}]
        elif len(resolution_calls) == 3:
            edits = [{'candidate_index': 99, 'endpoint': 'source_name', 'name': 'Tess'}]
        else:
            edits = []
        return ModelResponse(payload={'edits': edits})

    event(second_bundle, 'running', 'Substituted first invocation', 'resolve')
    with pytest.raises(KeyboardInterrupt):
        execute(second_bundle, live=True, provider=resolve)
    event(second_bundle, 'interrupted', 'Substituted worker interrupted', 'resolve')
    partial = read_run(tmp_path, identity, second.id)
    assert partial.benchmark_v4.state == 'provisional'
    assert partial.observations[3].status == 'uncertain'

    second_bundle = open_authorized(second, 'continue', continuation=True)
    execute(second_bundle, live=True, provider=resolve)
    event(second_bundle, 'complete', 'Substituted resolution finished', 'continue')
    assert len(resolution_calls) == second_bundle.attempt_count == 33
    assert live_budget(tmp_path).used == 68
    assert len({attempt['attempt_id'] for attempt in second_bundle.attempts()}) == 33
    treatment = read_run(tmp_path, identity, second.id)
    control = read_run(tmp_path, identity, first.id)
    assert treatment.benchmark_v4.state == 'complete'
    assert [row.status for row in treatment.observations[:4]] == ['scored', 'parse_failure', 'provider_failure', 'uncertain']
    assert treatment.observations[0].result.sourced_extraction == _qualified(FIRST, SECOND)
    assert treatment.observations[4].status == 'parse_failure'
    assert treatment.observations[4].reason == 'Invalid resolver endpoint edits'
    assert treatment.observations[5].status == 'validation_failure'
    assert control.observations[3].status == 'scored' and control.observations[3].result.sourced_extraction.relationships == []
    assert treatment.benchmark.cohort.complete_proofs == control.benchmark.cohort.complete_proofs + 1
    assert treatment.benchmark_v4.consensus_evidence == control.benchmark_v4.consensus_evidence
    assert treatment.benchmark_v4.scoring_sha256 == control.benchmark_v4.scoring_sha256
    assert treatment.pipeline_usage.incremental.attempts == 33
    assert treatment.pipeline_usage.inherited_extraction.attempts == 35
    assert treatment.pipeline_usage.full_pipeline.attempts == 68
    assert treatment.pipeline_usage.full_pipeline.provider_seconds is None
    comparison = compare_benchmark_v4_runs(control, treatment)
    assert comparison.matched_inputs == 35 and comparison.benchmark_v4.shared_extraction_run_id == first.id
    assert summarize(second_bundle)['pipeline_usage'] == treatment.pipeline_usage.model_dump(mode='json')
    assert summarize(second_bundle)['benchmark_v4'] == treatment.benchmark_v4.model_dump(mode='json')
    assert all(result['evaluation'] is None for result in second_bundle.results())
    with pytest.raises(ValueError, match='matching live Extractor-only'):
        preview_run(RunConfiguration.model_validate(dict(second_config, retained_run_id=second.id)), tmp_path)
