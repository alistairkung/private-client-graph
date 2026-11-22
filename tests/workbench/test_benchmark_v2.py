"""Offline checks for the frozen development comparisons."""
import hashlib
import json
import subprocess
import sys

import pytest

from private_client_graph.models import GroundTruth, SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.pipeline import Pipeline, PipelineConfig
from private_client_graph.research.benchmark_decisions import DecisionTargets, diagnose
from private_client_graph.research.fixtures import ROOT
from private_client_graph.research.source_attribution import SourceEvidenceApproval, validate_source_approval
from private_client_graph.workbench.case_catalog import repository_inputs


def test_temporal_orders_change_only_the_source_sequence():
    inputs = {sample.case_id: sample for sample in repository_inputs()}
    forward = inputs['benchmark_v1_temporal_dev_5']
    reverse = inputs['benchmark_v1_temporal_dev_7']
    assert [source.id for source in forward.sources] == ['note_01', 'note_02', 'note_03', 'note_04']
    assert reverse.sources == list(reversed(forward.sources))
    assert reverse.truth == forward.truth
    assert reverse.source_evidence == forward.source_evidence
    assert reverse.sourced_extraction == forward.sourced_extraction


def test_evidence_sufficiency_requires_one_complete_set_attached_to_the_target():
    sample = next(s for s in repository_inputs() if s.case_id == 'benchmark_v1_cross_source_dev_2')
    result = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, sample.sourced_extraction)
    target = ('Anna Dale', 'trustee_of', 'Seaforth Trust')
    witness = dict(source_id='notice', supporting_text=sample.sourced_extraction.relationships[0].supporting_text)
    bridge = dict(source_id='index', supporting_text='Instrument L-29 belongs to Seaforth Trust.')
    labels = DecisionTargets.model_validate({'required': [target], 'sufficiency': [
        {'edge': target, 'alternatives': [[witness, bridge]]}]})
    partial = diagnose(result.state, sample.truth, labels)
    assert partial['sufficiency']['incomplete'] == [target]
    assert partial['sufficiency']['accuracy'] == 0
    labels.sufficiency[0].alternatives.append([labels.sufficiency[0].alternatives[0][0]])
    assert diagnose(result.state, sample.truth, labels)['sufficiency']['complete'] == [target]


def test_preflight_replays_all_fourteen_conditions_through_the_workbench(tmp_path):
    report = subprocess.run([sys.executable, '-m', 'benchmark_v2.preflight', '--artifacts', str(tmp_path)],
                            cwd=ROOT, check=True, capture_output=True, text=True)
    data = json.loads(report.stdout)
    assert data['evidence_policy_version'] == 'benchmark_v2_evidence_v1'
    assert len(data['conditions']) == 14
    assert data['pending_live_admission'] == []
    assert not (tmp_path / 'candidate-D13').exists()
    assert len(data['baseline_schedule']) == 18
    assert data['baseline_schedule'][7:13] == ['D8', 'D9'] * 3
    assert data['paid_attempts'] == 0
    proposals = data['proposed_run_configurations']
    assert [r['invocation_cap'] for r in proposals] == [7, 2, 2, 2, 5]
    assert all(r['task_call_cap'] == 18 and r['resolver'] == 'none' for r in proposals)
    rows = {row['condition']: row for row in data['conditions']}
    assert rows['D13']['legacy_source_attribution'] is None
    assert rows['D13']['graph']['tp'] == 3
    assert rows['D13']['graph']['provenance_passed'] == 2
    assert rows['D13']['decisions']['sufficiency']['accuracy'] == 1.0
    ordinary = rows['D13']['ordinary_evidence']
    assert ordinary['not_applicable'] == [['Anna Dale', 'trustee_of', 'Seaforth Trust']]
    for metric in ('quotation', 'source_attribution'):
        assert ordinary[metric]['assessed'] == ordinary[metric]['passed'] == 2
        assert sum(r['ordinary_evidence'][metric]['passed'] for r in rows.values()) == 67
    assert rows['D14']['graph']['tp'] == 11
    assert rows['D14']['source_count'] == 8


def test_wrong_source_or_wrong_edge_cannot_complete_a_sufficient_set():
    sample = next(s for s in repository_inputs() if s.case_id == 'benchmark_v1_cross_source_dev_2')
    notice, index, letter = sample.sources
    index_quote = 'Instrument L-29 belongs to Seaforth Trust.'
    notice_copy = notice.model_copy(update={'text': notice.text + '\n' + index_quote})
    trustee, settlor, other = sample.sourced_extraction.relationships
    target = ('Anna Dale', 'trustee_of', 'Seaforth Trust')
    labels = DecisionTargets.model_validate({'required': [target], 'forbidden': [
        ['Anna Dale', 'trustee_of', 'Hillstone Trust']], 'sufficiency': [
        {'edge': target, 'alternatives': [[dict(source_id=notice.id, supporting_text=trustee.supporting_text),
                                          dict(source_id=index.id, supporting_text=index_quote)]]}]})

    def score(candidates):
        extracted = SourcedExtractionResult(relationships=candidates)
        output = Pipeline(PipelineConfig()).run_from_sourced_extraction([notice_copy, index, letter], extracted)
        return diagnose(output.state, sample.truth, labels)

    correct_link = trustee.model_copy(update={'source_id': index.id, 'supporting_text': index_quote})
    misplaced = settlor.model_copy(update={'source_id': index.id, 'supporting_text': index_quote})
    wrong_source = correct_link.model_copy(update={'source_id': notice.id})
    assert score([trustee, settlor, other, correct_link])['sufficiency']['complete'] == [target]
    for wrong in [misplaced, wrong_source]:
        assert score([trustee, settlor, other, wrong])['sufficiency']['incomplete'] == [target]
    wrong_endpoint = trustee.model_copy(update={'target_name': 'Hillstone Trust'})
    missed = score([wrong_endpoint, settlor, other])
    assert missed['sufficiency'] == dict(version='attached_sufficient_set_v1', planned=1, assessed=0, complete=[], incomplete=[], missed=[target], accuracy=None)
    assert missed['required']['absent'] == [target]
    assert missed['forbidden']['present'] == [('Anna Dale', 'trustee_of', 'Hillstone Trust')]
    assert missed['unaffected']['fraction'] is None


def test_progressive_packages_match_original_reviewed_revision_byte_for_byte():
    # Independently calculated from the original PR's git blobs at d548322.
    expected = {
        'case_2': 'b97fe643b521ecbd668c61b44e8b74d7253358c2e6438dab2d0972ce1f671f60',
        'case_5': '6f9dab3700a3adaea6184fc6d9056bea1fd2776d9a35f676bd3663298c256cfc',
    }
    for name, digest in expected.items():
        directory = ROOT / 'benchmark_v1/temporal/dev' / name
        files = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in directory.rglob('*') if p.is_file()}
        assert hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() == digest


def test_linked_condition_hides_only_the_named_trust_and_preserves_both_endpoints():

    easy = next(s for s in repository_inputs() if s.case_id == 'benchmark_v1_cross_source_dev_2')
    directory = ROOT / 'benchmark_v2/candidates/D13'

    def read(file):
        return json.loads((directory / file).read_bytes())

    hard = [Source(id=s['id'], title=s['title'], text=(directory / s['path']).read_bytes().decode())
            for s in read('sources.json')]
    assert [(s.id, s.title) for s in easy.sources] == [(s.id, s.title) for s in hard]
    assert easy.sources[1:] == hard[1:]
    assert easy.sources[0].text.count(' of Seaforth Trust') == 1
    assert easy.sources[0].text.replace(' of Seaforth Trust', '') == hard[0].text
    truth = GroundTruth.model_validate(read('ground_truth.json'))
    assert truth.entities == easy.truth.entities
    assert [(e.source, e.type, e.target) for e in truth.relationships] == [
        (e.source, e.type, e.target) for e in easy.truth.relationships]
    approval = SourceEvidenceApproval.model_validate(read('source_evidence.json'))
    with pytest.raises(ValueError, match='Source approvals require'):
        validate_source_approval(approval, truth, hard)
    assert [e.approved_evidence for e in approval.relationships].count([]) == 1
    ideal = SourcedExtractionResult.model_validate(read('expected_source_extraction.json'))
    assert read('expected_extraction.json')['relationships'] == [
        e.model_dump(exclude={'source_id'}) for e in ideal.relationships]


def test_pending_v2_fixtures_can_replay_but_cannot_enter_a_paid_workbench_plan():
    from private_client_graph.research.run_plan import RunPlan
    sample = next(s for s in repository_inputs() if s.case_id == 'benchmark_v1_composite_dev_1')
    assert 'pending_semantic_review.md' in sample.origin_hashes
    assert 'human_review' in sample.origin_hashes
    # A historical snapshot lacking the signed disposition remains pending.
    sample.origin_hashes.pop('human_review')
    with pytest.raises(ValueError, match='semantic review'):
        RunPlan(inputs=[sample], input_mode='fresh', execution_mode='live', kind='live_experiment',
                fresh_extractions=1, task_call_cap=18, max_calls=1, invocation_cap=1)


def test_decision_diagnostic_rejects_duplicate_truth_ids_before_resolving_edges():
    sample = next(s for s in repository_inputs() if s.case_id == 'benchmark_v1_cross_source_dev_2')
    result = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, sample.sourced_extraction)
    truth = sample.truth.model_copy(update={'entities': [*sample.truth.entities, sample.truth.entities[0]]})
    with pytest.raises(ValueError, match='Duplicate ground-truth entity ID'):
        diagnose(result.state, truth, DecisionTargets())


def test_d13_is_selectable_for_live_planning_without_loading_other_diagnostic_packages(monkeypatch):
    from private_client_graph.research.run_plan import RunPlan
    from private_client_graph.workbench import case_catalog

    def unrelated_package(directory):
        pytest.fail(f'Accessed an unselected diagnostic package: {directory.name}')

    monkeypatch.setattr(case_catalog, '_diagnostic_package', unrelated_package)
    sample, = repository_inputs(input_ids=['benchmark_v1_cross_source_dev_3_fixture'])
    labels = case_catalog.frozen_case_metadata([sample])
    plan = RunPlan(inputs=[sample], case_metadata=labels, execution_mode='live', kind='live_experiment',
                   input_mode='fresh', fresh_extractions=1, resolver='none', max_calls=1, invocation_cap=1,
                   task_call_cap=18)
    assert len(plan.planned_slots) == 1
    assert labels[sample.sample_id].split == 'dev'
    assert sample.source_evidence is None
    assert 'human_review' in sample.origin_hashes


@pytest.mark.parametrize('changed', ['candidates/D13/source.txt', 'development.json', 'reviews/D13.md'])
def test_d13_admission_is_bound_to_reviewed_bytes(tmp_path, changed):
    import shutil
    from private_client_graph.research.benchmark_admission import D13_CASE, reviewed_snapshot

    study = ROOT / 'benchmark_v2'
    shutil.copytree(study / 'candidates/D13', tmp_path / 'candidates/D13')
    (tmp_path / 'reviews').mkdir()
    for name in ('development.json', 'reviews/D13.md'):
        shutil.copyfile(study / name, tmp_path / name)
    path = tmp_path / changed
    if changed == 'development.json':
        rows = json.loads(path.read_bytes())
        next(r for r in rows if r['condition'] == 'D13')['targets']['sufficiency'][0]['joint_only'] = False
        path.write_text(json.dumps(rows))
    else:
        path.write_bytes(path.read_bytes() + b' changed')
    with pytest.raises(ValueError, match='D13'):
        reviewed_snapshot(tmp_path, tmp_path / 'candidates/D13', D13_CASE)


def test_traced_environment_preserves_historical_sourced_request_bytes():
    import httpx
    from private_client_graph.research.provider import ModelRequest, ModelSettings, invoke_deepseek

    # Golden HTTP body from this same offline probe at benchmark revision 7d714ecd.
    bodies = []

    def respond(request):
        bodies.append(hashlib.sha256(request.content).hexdigest())
        assert request.extensions['timeout']['read'] == 90
        body = json.loads(request.content)
        tool = body['tools'][0]['function']['name']
        message = {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'mock', 'type': 'function', 'function': {'name': tool, 'arguments': '{"relationships":[]}'}}]}
        return httpx.Response(200, json={'id': 'mock', 'object': 'chat.completion', 'created': 0,
            'model': 'deepseek-flash', 'choices': [{'index': 0, 'message': message, 'finish_reason': 'tool_calls'}]})

    sources = [Source(id='source_b', title='Second', text='Synthetic probe B.'),
               Source(id='source_a', title='First', text='Synthetic probe A.')]
    request = ModelRequest(stage='extraction', source='', sources=sources, settings=ModelSettings(timeout_seconds=90))
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = invoke_deepseek(request, api_key='offline-test', http_client=client)
    assert bodies == ['20c4833ed423c7a8634872e3d0326f1722230866c34f9bae0f2aad5c31a3c6d7']
    assert result.payload == {'relationships': []}


def test_d13_model_facing_sources_come_from_the_verified_snapshot(monkeypatch):
    from pathlib import Path

    read_bytes = Path.read_bytes
    target = ROOT / 'benchmark_v2/candidates/D13/sources/letter.txt'
    reads = 0

    def read_once(path):
        nonlocal reads
        data = read_bytes(path)
        if path == target:
            reads += 1
            if reads > 1:
                return data + b' changed after review'
        return data

    monkeypatch.setattr(Path, 'read_bytes', read_once)
    sample, = repository_inputs(input_ids=['benchmark_v1_cross_source_dev_3_fixture'])
    letter, = [source for source in sample.sources if source.id == 'letter']
    assert reads == 1
    assert hashlib.sha256(letter.text.encode()).hexdigest() == sample.origin_hashes['sources/letter.txt']


def test_development_signature_does_not_transfer_to_revised_package_or_unrelated_case(tmp_path):
    import shutil
    from private_client_graph.research.benchmark_admission import pending_semantic_review, reviewed_snapshot

    case_id = 'benchmark_v1_composite_dev_1'
    selected, = repository_inputs(input_ids=[case_id + '_fixture'])
    assert 'pending_semantic_review.md' in selected.origin_hashes
    assert not pending_semantic_review(selected)
    assert pending_semantic_review(selected.model_copy(update={'case_id': 'unreviewed'}))
    package = tmp_path / 'package'
    shutil.copytree(ROOT / 'benchmark_v1/composite/dev/case_1', package)
    (package / 'source.txt').write_text('Different file after review')
    with pytest.raises(ValueError, match='D14 package differs'):
        reviewed_snapshot(ROOT / 'benchmark_v2', package, case_id)


def test_reviewed_lineage_is_bound_to_loaded_input_when_freezing_labels(monkeypatch):
    from pathlib import Path
    from private_client_graph.workbench.case_catalog import frozen_case_metadata

    sample, = repository_inputs(input_ids=['benchmark_v1_cross_source_dev_3_fixture'])
    metadata = ROOT / 'benchmark_v2/candidates/D13/metadata.json'
    read_bytes = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda path: b'{}' if path == metadata else read_bytes(path))
    with pytest.raises(ValueError, match='metadata differs'):
        frozen_case_metadata([sample])
