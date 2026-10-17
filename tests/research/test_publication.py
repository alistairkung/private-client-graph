"""Offline publication seam with a safe retained-package fixture, never live calls.

The committed curated specimen supplies synthetic Sources and recorded outcomes;
this fixture rebuilds only the retained file contracts needed by the publisher.
Raw communications are test sentinels, not copied provider records.
"""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from private_client_graph.research.publication import RUN_IDS, build_public_snapshot

SPECIMEN = Path(__file__).resolve().parents[2] / 'private_client_graph/published/research-results.v1.json'
SECRET = 'PRIVATE-TEST-SENTINEL-DO-NOT-PUBLISH'


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _zip(files, manifest_name):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr(manifest_name, _json({name: _sha(data) for name, data in files.items()}))
    return stream.getvalue()


@pytest.fixture
def retained_package(tmp_path):
    snapshot = json.loads(SPECIMEN.read_bytes())
    raw = {'private-ledger.json': _json({'credential': SECRET})}
    report = {'experiment_id': snapshot['experiment_id'], 'identity': {}, 'metrics': {}, 'edits': []}
    views = {}
    for run in snapshot['runs']:
        label, run_id = run['label'], run['run_id']
        prefix = run_id + '/'
        report['identity'][label] = {'run_id': run_id, 'git_commit': run['git_commit'],
                                    'frozen_plan_digest': run['plan_digest'], 'artifact_digest': run['artifact_digest']}
        report['metrics'][label] = {**run['metrics'], 'coverage': run['coverage']}
        inputs, slots, observations = [], [], []
        for case in snapshot['cases']:
            observation = next(item for item in case['observations'] if item['run_label'] == label)
            sample = {'sample_id': observation['sample_id'], 'case_id': case['case_id'],
                      'sources': case['sources'], 'truth': case['truth'], 'source_evidence': case['source_evidence'],
                      'extraction': {'relationships': []}, 'sourced_extraction': {'relationships': []},
                      'annotations': {'private': SECRET}}
            inputs.append(sample)
            slots.append({'observation_id': observation['observation_id'], 'sample_id': observation['sample_id'],
                          'case_id': case['case_id']})
            result = {key: observation[key] for key in ('sample_id', 'status', 'state', 'evaluation', 'source_attribution')}
            result['case_id'] = case['case_id']
            result['private_path'] = SECRET
            raw[prefix + 'results/' + observation['observation_id'] + '.json'] = _json(result)
            if label == 'A':
                raw[prefix + 'fresh_inputs/' + sample['sample_id'] + '.json'] = _json(sample)
            observations.append({'case_id': case['case_id'], 'metadata': {'name': case['name'],
                                'description': case['description'], 'internal_annotations': SECRET},
                                 'result': result, 'relationships': observation['relationships']})
            if label == 'B':
                report['edits'].extend({**edit, 'case_id': case['case_id']} for edit in observation['edits'])
        plan = {'run_id': run_id, 'experiment_id': snapshot['experiment_id'], 'planned_slots': slots,
                'inputs': inputs, 'evaluator_version': 'semantic_edges_v1',
                'aggregate_version': 'observation_micro_f1_v1', 'settings': {'model': 'deepseek-flash'}}
        manifest = _json({'plan': plan, 'provenance': {'git_sha': run['git_commit'], 'prompts': SECRET}})
        raw[prefix + 'manifest.json'] = manifest
        raw[prefix + 'manifest-checksum.json'] = _json(_sha(manifest))
        raw[prefix + 'execution.json'] = _json({'digest': run['plan_digest'], 'authorization': SECRET})
        for call in run['calls']:
            stem = prefix + 'attempts/' + call['attempt_id']
            raw[stem + '.started.json'] = _json({'attempt_id': call['attempt_id'], 'request': SECRET})
            raw[stem + '.finished.json'] = _json({'status': call['status'], 'provider_seconds': call['provider_seconds'],
                'incremental_cost': call['cost'], 'response': {'returned_model': call['model'], 'raw_response': SECRET,
                'usage': {key: call[key] for key in ('input_tokens', 'output_tokens', 'cached_tokens')}}})
        views[label] = {'observations': observations, 'evaluation': {'scope': {
            'identity': '3180ee9ad5d4f8e84376ca51158094b00a59a2f308d511e7e73326d4de32ab89',
            'evaluator_version': 'semantic_edges_v1', 'aggregate_version': 'observation_micro_f1_v1'}}}
    reports = {'results.json': _json(report), 'control-workbench-run.json': _json(views['A_prime']),
               'B-workbench-run.json': _json(views['B']),
               'control-equivalence.json': _json({'verified': True, 'paired_samples': 10, 'provider_attempts': 0,
                   'compared_fields': ['case_id', 'status', 'state', 'evaluation', 'source_attribution']}),
               'paired-comparison.json': _json({'left_run_id': RUN_IDS['A_prime'], 'right_run_id': RUN_IDS['B'],
                   'matched_inputs': 10, 'exclusions': []})}

    def package(*, mutate_raw=None, mutate_report=None):
        records = dict(raw)
        documents = dict(reports)
        if mutate_raw:
            mutate_raw(records)
        if mutate_report:
            mutate_report(documents)
        raw_bytes = _zip(records, 'SNAPSHOT_SHA256.json')
        documents['raw-artifacts.zip'] = raw_bytes
        documents['RAW_SNAPSHOT_SHA256.json'] = _json({'archive_sha256': _sha(raw_bytes),
                                                       'files': {name: _sha(data) for name, data in records.items()}})
        content = _zip(documents, 'RESULTS_SHA256.json')
        path = tmp_path / 'retained.zip'
        path.write_bytes(content)
        return path, _sha(content)
    return package


def test_export_preserves_exact_evidence_excludes_private_fields_and_is_reproducible(retained_package):
    path, trusted_digest = retained_package()
    before = path.read_bytes()
    output = build_public_snapshot(path, expected_archive_digest=trusted_digest)
    snapshot = json.loads(output)
    assert snapshot['runs'][0]['metrics']['micro_f1'] == 37 / 39
    assert snapshot['runs'][2]['metrics']['source_pair_assessed'] == 41
    assert snapshot['runs'][1]['calls'] == []
    assert snapshot['runs'][1]['usage']['total_tokens'] == 0
    assert snapshot['runs'][2]['usage']['total_tokens'] == 9821
    assert snapshot['runs'][2]['usage']['cost'] is None
    assert snapshot['runs'][2]['calls'][0]['stage'] == 'resolution'
    case = snapshot['cases'][2]
    assert 'In this note, Bea means Beatrice Ng; no second person is being introduced.' in case['sources'][0]['text']
    assert case['observations'][2]['edits'][0]['supporting_text'] == 'Bea is the settlor of the Larch Family Trust.'
    assert case['observations'][2]['edits'][0]['resolved_name'] == 'Beatrice Ng'
    assert SECRET not in output.decode()
    assert output == build_public_snapshot(path, expected_archive_digest=trusted_digest)
    assert path.read_bytes() == before


def test_export_rejects_untrusted_archive_before_reading_contents(retained_package):
    path, _ = retained_package()
    with pytest.raises(ValueError, match='Untrusted'):
        build_public_snapshot(path)


def test_export_rejects_missing_observation_even_with_valid_package_checksums(retained_package):
    def missing(raw):
        del raw[RUN_IDS['B'] + '/results/heldout_03_fixture_fresh_01-resolve-1.json']
    path, digest = retained_package(mutate_raw=missing)
    with pytest.raises(ValueError, match='Incomplete Observations'):
        build_public_snapshot(path, expected_archive_digest=digest)


def test_export_rejects_unscored_observation(retained_package):
    def unscored(raw):
        key = RUN_IDS['B'] + '/results/heldout_03_fixture_fresh_01-resolve-1.json'
        record = json.loads(raw[key])
        record['evaluation'] = None
        raw[key] = _json(record)
    path, digest = retained_package(mutate_raw=unscored)
    with pytest.raises(ValueError, match='Unscored'):
        build_public_snapshot(path, expected_archive_digest=digest)


def test_export_rejects_frozen_input_mismatch(retained_package):
    def changed(raw):
        prefix = RUN_IDS['B'] + '/'
        manifest = json.loads(raw[prefix + 'manifest.json'])
        manifest['plan']['inputs'][0]['sources'][0]['text'] += ' changed'
        raw[prefix + 'manifest.json'] = _json(manifest)
        raw[prefix + 'manifest-checksum.json'] = _json(_sha(raw[prefix + 'manifest.json']))
    path, digest = retained_package(mutate_raw=changed)
    with pytest.raises(ValueError, match='Frozen input mismatch'):
        build_public_snapshot(path, expected_archive_digest=digest)


def test_export_rejects_inconsistent_retained_aggregate(retained_package):
    def changed(reports):
        report = json.loads(reports['results.json'])
        report['metrics']['B']['tp'] = 38
        reports['results.json'] = _json(report)
    path, digest = retained_package(mutate_report=changed)
    with pytest.raises(ValueError, match='Unexpected recorded aggregate'):
        build_public_snapshot(path, expected_archive_digest=digest)


def test_export_rejects_metric_values_inconsistent_with_retained_counts(retained_package):
    def changed(reports):
        report = json.loads(reports['results.json'])
        report['metrics']['B']['micro_f1'] = 0.5
        reports['results.json'] = _json(report)
    path, digest = retained_package(mutate_report=changed)
    with pytest.raises(ValueError, match='Recorded metric'):
        build_public_snapshot(path, expected_archive_digest=digest)
