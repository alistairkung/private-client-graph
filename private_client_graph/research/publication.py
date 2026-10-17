"""Offline allowlisted publication of the approved retained A/A′/B experiment.

Only serialization, retained-count reductions and integrity checks occur here.
This module deliberately imports no pipeline, evaluator, Workbench or provider.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from private_client_graph.published import canonical_bytes, publication_digest

EXPERIMENT_ID = '83b5778e74ba5e6e882d334fd4f87f09'
RUN_IDS = {'A': '97d26d8e5f9d5964826b144c9ca45ad7',
           'A_prime': 'd67a391bc95a5ad39e1b5786a04795c0',
           'B': '841389cef51957ce8523ea41c03d2baa'}
APPROVED_ARCHIVE_SHA256 = '74167126e2b4af44ff9beedba0c4304520c47f89ea36d155d4c3ade12f980df8'
METRIC_FIELDS = ('tp', 'fp', 'fn', 'micro_f1', 'macro_f1', 'quote_passed',
                 'quote_assessed', 'quote_accuracy', 'source_pair_passed',
                 'source_pair_assessed', 'source_pair_accuracy')
EVALUATION_FIELDS = ('tp', 'fp', 'fn', 'precision', 'recall', 'f1', 'true_positive_edges',
                     'false_positive_edges', 'false_negative_edges', 'provenance_passed',
                     'provenance_failed', 'provenance_accuracy', 'provenance_passes',
                     'provenance_failures')


def build_public_snapshot(archive_path: Path, *,
                          expected_archive_digest: str = APPROVED_ARCHIVE_SHA256) -> bytes:
    """Verify a trusted retained package and return a reproducible public artifact.

    The default trust anchor identifies the owner-approved package. The explicit
    digest argument also supports deterministic synthetic package tests offline.
    No destination is written until every source and publication check passes.
    """
    package = archive_path.read_bytes()
    _require(_sha256(package) == expected_archive_digest, 'Untrusted report archive')
    report_files = _verified_archive(package, 'RESULTS_SHA256.json')
    raw_manifest = json.loads(report_files['RAW_SNAPSHOT_SHA256.json'])
    raw_bytes = report_files['raw-artifacts.zip']
    _require(_sha256(raw_bytes) == raw_manifest['archive_sha256'], 'Raw archive checksum mismatch')
    raw_files = _verified_archive(raw_bytes, 'SNAPSHOT_SHA256.json')
    _require({name: _sha256(data) for name, data in raw_files.items()} == raw_manifest['files'],
             'Raw archive inventory mismatch')
    report = json.loads(report_files['results.json'])
    _require(report['experiment_id'] == EXPERIMENT_ID, 'Wrong Experiment')
    runs, results, inputs = _verified_runs(raw_files, report)
    _verify_pairing(inputs, results, report_files)
    cases = _public_cases(inputs, results, report, report_files)
    snapshot = {'schema_version': 1, 'snapshot_id': 'final-heldout-a-aprime-b-v1',
                'experiment_id': EXPERIMENT_ID,
                'benchmark': {'case_count': len(cases),
                              'source_count': sum(len(case['sources']) for case in cases),
                              'expected_relationships': sum(len(case['truth']['relationships']) for case in cases)},
                'pairing': {'control_equivalent': True, 'frozen_inputs_verified': True},
                'runs': runs, 'cases': cases}
    _require(snapshot['benchmark'] == {'case_count': 10, 'source_count': 14, 'expected_relationships': 39},
             'Unexpected benchmark coverage')
    snapshot['integrity'] = {'algorithm': 'sha256', 'digest': publication_digest(snapshot),
                             'scope': 'canonical-json-excluding-integrity'}
    return canonical_bytes(snapshot) + b'\n'


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pick(value: dict, fields: tuple[str, ...]) -> dict:
    return {field: value[field] for field in fields}


def _verified_archive(data: bytes, checksum_name: str) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        _require(len(names) == len(set(names)), 'Duplicate archive members')
        _require(all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in names),
                 'Unsafe archive member')
        hashes = json.loads(archive.read(checksum_name))
        _require(set(names) == set(hashes) | {checksum_name}, 'Archive inventory mismatch')
        files = {name: archive.read(name) for name in hashes}
        _require(all(_sha256(content) == hashes[name] for name, content in files.items()),
                 'Archive checksum mismatch')
        return files


def _verified_runs(files: dict[str, bytes], report: dict) -> tuple[list[dict], dict, dict]:
    runs, results, inputs = [], {}, {}
    for label, run_id in RUN_IDS.items():
        prefix = f'{run_id}/'
        manifest_bytes = files[prefix + 'manifest.json']
        _require(_sha256(manifest_bytes) == json.loads(files[prefix + 'manifest-checksum.json']),
                 'Manifest checksum mismatch')
        manifest = json.loads(manifest_bytes)
        plan = manifest['plan']
        identity = report['identity'][label]
        _require(plan['run_id'] == identity['run_id'] == run_id and plan['experiment_id'] == EXPERIMENT_ID,
                 'Run identity mismatch')
        _require(identity['git_commit'] == manifest['provenance']['git_sha'], 'Run commit mismatch')
        execution = json.loads(files[prefix + 'execution.json'])
        _require(identity['frozen_plan_digest'] == execution['digest'], 'Frozen plan mismatch')
        _require(plan['evaluator_version'] == 'semantic_edges_v1' and
                 plan['aggregate_version'] == 'observation_micro_f1_v1', 'Unexpected metric definitions')
        retained = [json.loads(data) for name, data in sorted(files.items())
                    if name.startswith(prefix + 'results/') and name.endswith('.json')]
        slots = {slot['observation_id'] for slot in plan['planned_slots']}
        actual = {Path(name).stem for name in files if name.startswith(prefix + 'results/') and name.endswith('.json')}
        _require(len(retained) == len(slots) == 10 and actual == slots, 'Incomplete Observations')
        _require(all(result['status'] == 'completed' and result['evaluation'] is not None
                     and result['state'] is not None and result['source_attribution'] is not None
                     for result in retained), 'Unscored Observation')
        results[label] = {result['case_id']: result for result in retained}
        _require(len(results[label]) == 10, 'Duplicate Benchmark Case')
        if label == 'A':
            samples = [json.loads(data) for name, data in sorted(files.items())
                       if name.startswith(prefix + 'fresh_inputs/') and name.endswith('.json')]
        else:
            samples = plan['inputs']
        inputs[label] = {sample['case_id']: sample for sample in samples}
        _require(set(inputs[label]) == set(results[label]), 'Input and Observation mismatch')
        calls = _public_calls(files, prefix, run_id, plan)
        metrics = _pick(report['metrics'][label], METRIC_FIELDS)
        metrics['micro_precision'] = metrics['tp'] / (metrics['tp'] + metrics['fp'])
        metrics['micro_recall'] = metrics['tp'] / (metrics['tp'] + metrics['fn'])
        _verify_counts(label, retained, metrics)
        coverage = _pick(report['metrics'][label]['coverage'],
                         ('planned', 'scored', 'pending', 'failed', 'uncertain', 'unavailable'))
        _require(coverage == {'planned': 10, 'scored': 10, 'pending': 0, 'failed': 0,
                              'uncertain': 0, 'unavailable': 0}, 'Incomplete coverage')
        runs.append({'label': label, 'run_id': run_id, 'git_commit': identity['git_commit'],
                     'plan_digest': identity['frozen_plan_digest'], 'artifact_digest': identity['artifact_digest'],
                     'metrics': metrics, 'coverage': coverage, 'calls': calls,
                     'usage': _usage(calls)})
    _require([len(run['calls']) for run in runs] == [10, 0, 10], 'Unexpected provider attempts')
    _require(runs[2]['usage']['total_tokens'] == 9821, 'Unexpected treatment token usage')
    return runs, results, inputs


def _public_calls(files: dict[str, bytes], prefix: str, run_id: str, plan: dict) -> list[dict]:
    calls = []
    for name in sorted(files):
        if not name.startswith(prefix + 'attempts/') or not name.endswith('.started.json'):
            continue
        start = json.loads(files[name])
        finish_name = name.replace('.started.json', '.finished.json')
        finish = json.loads(files[finish_name]) if finish_name in files else {}
        attempt_id = start['attempt_id']
        response = finish.get('response') or {}
        usage = response.get('usage') or {}
        case_id = next((slot['case_id'] for slot in plan['planned_slots']
                        if attempt_id.startswith(slot['sample_id'])), None)
        _require(case_id is not None, 'Attempt has no Benchmark Case')
        stage = 'extraction' if attempt_id.endswith('-extraction') else 'resolution'
        calls.append({'attempt_id': attempt_id, 'run_id': run_id, 'case_id': case_id,
                      'stage': stage, 'model': response.get('returned_model') or plan['settings'].get('model'),
                      'status': finish.get('status', 'uncertain'),
                      'input_tokens': usage.get('input_tokens'), 'output_tokens': usage.get('output_tokens'),
                      'cached_tokens': usage.get('cached_tokens'),
                      'provider_seconds': finish.get('provider_seconds'),
                      'cost': finish.get('incremental_cost'), 'currency': 'USD'})
    return calls


def _usage(calls: list[dict]) -> dict:
    result = {'attempts': len(calls), 'currency': 'USD',
              'unpriced_attempts': sum(call['cost'] is None for call in calls)}
    for field in ('input_tokens', 'output_tokens', 'cached_tokens', 'provider_seconds', 'cost'):
        result[field] = None if any(call[field] is None for call in calls) else sum(call[field] for call in calls)
    result['total_tokens'] = (result['input_tokens'] + result['output_tokens']
                              if result['input_tokens'] is not None and result['output_tokens'] is not None else None)
    return result


def _verify_counts(label: str, results: list[dict], metrics: dict) -> None:
    expected = (37, 2, 2, 34, 37, 35, 39) if label != 'B' else (39, 0, 0, 36, 39, 37, 41)
    fields = ('tp', 'fp', 'fn', 'quote_passed', 'quote_assessed', 'source_pair_passed', 'source_pair_assessed')
    _require(tuple(metrics[field] for field in fields) == expected, 'Unexpected recorded aggregate')
    for field in ('tp', 'fp', 'fn'):
        _require(sum(result['evaluation'][field] for result in results) == metrics[field],
                 'Recorded aggregate differs from Observations')
    _require(sum(result['evaluation']['provenance_passed'] for result in results) == metrics['quote_passed'] and
             sum(result['source_attribution']['passed'] for result in results) == metrics['source_pair_passed'] and
             sum(result['source_attribution']['assessed'] for result in results) == metrics['source_pair_assessed'],
             'Recorded provenance aggregate differs from Observations')
    _require(sum(result['evaluation']['f1'] for result in results) / 10 == metrics['macro_f1'],
             'Recorded macro F1 differs from Observations')


def _verify_pairing(inputs: dict, results: dict, reports: dict[str, bytes]) -> None:
    control = json.loads(reports['control-equivalence.json'])
    paired = json.loads(reports['paired-comparison.json'])
    _require(control['verified'] and control['paired_samples'] == 10 and control['provider_attempts'] == 0,
             'Invalid replay control')
    _require(paired['left_run_id'] == RUN_IDS['A_prime'] and paired['right_run_id'] == RUN_IDS['B']
             and paired['matched_inputs'] == 10 and not paired['exclusions'], 'Invalid frozen pairing')
    fields = ('sources', 'truth', 'source_evidence', 'extraction', 'sourced_extraction')
    for case_id, sample in inputs['A'].items():
        _require(all(_pick(inputs[label][case_id], fields) == _pick(sample, fields)
                     for label in ('A_prime', 'B')), 'Frozen input mismatch')
        _require(all(results['A'][case_id].get(field) == results['A_prime'][case_id].get(field)
                     for field in control['compared_fields']), 'Replay outcome mismatch')


def _public_state(state: dict) -> dict:
    return {'sources': [_pick(source, ('id', 'title', 'text')) for source in state['sources']],
            'entities': [_pick(entity, ('id', 'type', 'name')) for entity in state['entities']],
            'relationships': [_pick(edge, ('source', 'type', 'target', 'evidence_ids')) for edge in state['relationships']],
            'evidence': [_pick(item, ('id', 'document', 'supporting_text', 'source_id')) for item in state['evidence']]}


def _public_cases(inputs: dict, results: dict, report: dict, reports: dict[str, bytes]) -> list[dict]:
    retained_views = {
        'A_prime': {observation['case_id']: observation for observation in
                    json.loads(reports['control-workbench-run.json'])['observations']},
        'B': {observation['case_id']: observation for observation in
              json.loads(reports['B-workbench-run.json'])['observations']},
    }
    retained_views['A'] = retained_views['A_prime']
    cases = []
    for case_id, sample in sorted(inputs['A'].items()):
        truth = {'entities': [_pick(entity, ('id', 'type', 'name')) for entity in sample['truth']['entities']],
                 'relationships': [_pick(edge, ('source', 'type', 'target', 'approved_evidence'))
                                   for edge in sample['truth']['relationships']]}
        approval = {'schema_version': 1, 'relationships': [
            {**_pick(edge, ('source', 'type', 'target')), 'approved_evidence': [
                _pick(item, ('source_id', 'supporting_text')) for item in edge['approved_evidence']]}
            for edge in sample['source_evidence']['relationships']]}
        observations = []
        for label in RUN_IDS:
            result = results[label][case_id]
            attribution = _pick(result['source_attribution'], ('version', 'assessed', 'passed', 'failed', 'accuracy'))
            attribution['failures'] = [_pick(failure, ('edge', 'evidence_id', 'source_id', 'supporting_text'))
                                       for failure in result['source_attribution']['failures']]
            view = retained_views[label][case_id]
            relationships = _public_relationships(view, result, sample)
            edits = [_pick(edit, ('candidate_index', 'endpoint', 'original_name', 'resolved_name',
                                 'relationship_type', 'other_endpoint', 'source_id', 'supporting_text'))
                     for edit in report['edits'] if edit['case_id'] == case_id] if label == 'B' else []
            for edit in edits:
                matches = [relationship for relationship in relationships
                           if relationship['edge'][1] == edit['relationship_type']
                           and edit['resolved_name'] in (relationship['edge'][0], relationship['edge'][2])
                           and edit['other_endpoint'] in (relationship['edge'][0], relationship['edge'][2])]
                _require(len(matches) == 1, 'Endpoint edit has no unique relationship')
                edit['outcome_id'] = matches[0]['id']
            observations.append({'run_label': label, 'observation_id': sample['sample_id'] +
                                 ('-resolve-1' if label == 'B' else '-noop'),
                                 'sample_id': result['sample_id'], 'status': result['status'],
                                 'state': _public_state(result['state']),
                                 'evaluation': _pick(result['evaluation'], EVALUATION_FIELDS),
                                 'source_attribution': attribution, 'edits': edits, 'relationships': relationships})
        # Human-facing names are retained metadata, never inferred from a Source.
        metadata = retained_views['B'][case_id]['metadata']
        cases.append({'case_id': case_id, 'name': metadata.get('name', case_id),
                      'description': metadata['description'],
                      'sources': [_pick(source, ('id', 'title', 'text')) for source in sample['sources']],
                      'truth': truth, 'source_evidence': approval, 'observations': observations})
    return cases



def _public_relationships(view: dict, result: dict, sample: dict) -> list[dict]:
    """Project already-retained joined outcomes; do not reconstruct scoring rules."""
    _require(view['result']['evaluation'] == result['evaluation'] and
             view['result']['state'] == result['state'], 'Retained inspection differs from Observation')
    sources = {source['id']: source['text'] for source in sample['sources']}
    relationships = []
    for relationship in view['relationships']:
        public = _pick(relationship, ('id', 'edge', 'outcome'))
        _require(public['outcome'] in ('matched', 'missing', 'extra', 'provenance_failure',
                                      'source_attribution_failure'), 'Unknown recorded outcome')
        for kind in ('expected', 'predicted'):
            public[kind] = [_pick(quote, ('id', 'source_id', 'text', 'occurrences'))
                            for quote in relationship[kind]]
            for quote in public[kind]:
                _require(quote['source_id'] in sources and quote['text'] in sources[quote['source_id']],
                         'Evidence does not occur in original Source')
                _require(all(sources[quote['source_id']][start:end] == quote['text']
                             for start, end in quote['occurrences']), 'Evidence occurrence mismatch')
        relationships.append(public)
    evaluation = result['evaluation']
    for outcome, key in (('missing', 'false_negative_edges'), ('extra', 'false_positive_edges')):
        _require(sorted(row['edge'] for row in relationships if row['outcome'] == outcome)
                 == sorted(evaluation[key]), 'Inspection outcomes differ from recorded evaluation')
    _require(sorted(row['edge'] for row in relationships if row['outcome'] not in ('missing', 'extra'))
             == sorted(evaluation['true_positive_edges']), 'Inspection true positives differ from recorded evaluation')
    return relationships

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    snapshot = build_public_snapshot(args.archive)
    with args.destination.open('xb') as stream:
        stream.write(snapshot)


if __name__ == '__main__':
    main()
