import json
import subprocess
import sys
from pathlib import Path

import pytest

from private_client_graph.workbench.artifacts import artifact_digest, read_artifact
from private_client_graph.workbench.comparison import compare_experiments
from private_client_graph.workbench.evidence import relationship_outcomes
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.results import ResearchResult
from private_client_graph.workbench.restore import restore_archive
from private_client_graph.workbench.typescript import render


def test_issue_92_exact_missing_relationship_and_unchanged_artifacts(history_root):
    path = history_root / 'issue-92-pilot'
    before = artifact_digest(path)
    detail = read_artifact(path, path.name)
    assert detail.history.integrity == 'verified'
    assert detail.history.lifecycle == 'complete'
    assert detail.history.scored == detail.history.planned == 44
    sample = next(s for s in detail.samples if s.id == 'case_03_fixture')
    baseline = sample.observations[0]
    missing = next(r for r in baseline.relationships if r.outcome == 'missing')
    assert not missing.predicted
    assert missing.expected
    for quote in missing.expected:
        for start, end in quote.occurrences:
            assert sample.source[start:end] == quote.text
    assert sample.observations[1].evaluation.f1 == 1.0
    assert detail.operations['paid_attempts'] == 38
    assert artifact_digest(path) == before
    assert json.loads((path / 'manifest.json').read_text())['task_ledger'].startswith('/')


def test_comparison_matches_frozen_inputs_and_exposes_changed_configuration(history_root):
    left, right = [read_artifact(history_root / name, name)
                   for name in ('issue-91-demonstration', 'issue-92-pilot')]
    result = compare_experiments(left, right)
    assert result.matched_inputs >= 6
    assert result.scored_pairs >= 24
    assert result.differences
    assert any('Execution mode' in difference for difference in result.differences)
    right.samples[0].truth_digest = 'different'
    changed = compare_experiments(left, right)
    assert changed.matched_inputs < result.matched_inputs
    assert changed.exclusions
    for row in result.observations:
        assert row.delta_f1 == row.right_f1 - row.left_f1


@pytest.mark.parametrize('damage,integrity', [('version', 'unsupported'), ('manifest', 'corrupt'), ('result', 'corrupt'), ('missing', 'missing')])
def test_explicit_integrity_outcomes(history_root, damage, integrity):
    path = history_root / 'issue-92-pilot'
    (path / 'CHECKSUMS.json').unlink()
    if damage == 'version':
        manifest = json.loads((path / 'manifest.json').read_text())
        manifest['schema_version'] = 999
        (path / 'manifest.json').write_text(json.dumps(manifest))
    elif damage == 'manifest':
        (path / 'manifest.json').write_text('{invalid')
    elif damage == 'result':
        next((path / 'results').glob('*.json')).write_text('{invalid')
    else:
        (path / 'manifest.json').unlink()
    detail = read_artifact(path, path.name)
    assert detail.history.integrity == integrity
    assert detail.history.integrity_reason
    assert not detail.samples


def test_legacy_partial_and_uncertain_artifacts_remain_inspectable(history_root):
    path = history_root / 'issue-92-pilot'
    (path / 'CHECKSUMS.json').unlink()
    (path / 'results/case_03_fixture-resolve-3.json').unlink()
    (path / 'attempts/case_03_fixture-resolve-3.finished.json').unlink()
    detail = read_artifact(path, path.name)
    assert detail.history.integrity == 'verified'
    assert detail.history.lifecycle == 'incomplete'
    assert detail.operations['uncertain_attempts'] == 1
    sample = next(s for s in detail.samples if s.id == 'case_03_fixture')
    assert sample.observations[-1].status == 'uncertain'
    assert sample.observations[-1].evaluation is None
    assert sample.observations[-1].identity is None


def test_export_checksum_detects_changed_frozen_results(history_root):
    path = history_root / 'issue-92-pilot'
    next((path / 'results').glob('*.json')).write_text('{}')
    detail = read_artifact(path, path.name)
    assert detail.history.integrity == 'corrupt'
    assert 'checksum mismatch' in detail.history.integrity_reason


def test_repeated_evidence_unicode_and_provenance_failure(history_root):
    path = history_root / 'issue-92-pilot'
    manifest = json.loads((path / 'manifest.json').read_text())
    sample = ResearchInput.model_validate(manifest['plan']['inputs'][0])
    row = json.loads((path / 'results' / f'{sample.sample_id}-noop.json').read_text())
    result = ResearchResult.model_validate(row)
    edge = result.evaluation.true_positive_edges[0]
    result.evaluation.provenance_passes = []
    result.evaluation.provenance_failures = [edge]
    sample.source = '😀 ' + sample.source + '\n' + sample.source
    outcomes = relationship_outcomes(sample, result)
    failure = next(item for item in outcomes if item.outcome == 'provenance_failure')
    assert failure.expected and failure.predicted
    for quote in failure.predicted:
        assert len(quote.occurrences) >= 2
        assert all(sample.source[start:end] == quote.text for start, end in quote.occurrences)


def test_restore_never_overwrites_retained_artifacts(history_root):
    with pytest.raises(FileExistsError):
        restore_archive(Path('research/history/issue-92-pilot.zip'), history_root / 'issue-92-pilot')


def test_read_only_composition_has_no_runner_or_mutation_routes():
    script = '''
import sys
from private_client_graph.workbench.api import create_app
app = create_app()
assert 'private_client_graph.research.runner' not in sys.modules
assert not any(set(getattr(route, 'methods', [])) & {'POST', 'PUT', 'DELETE', 'PATCH'} for route in app.routes)
'''
    subprocess.run([sys.executable, '-c', script], check=True)


def test_typescript_contracts_match_backend():
    assert Path('web/research/shared/contracts.ts').read_text() == render()


@pytest.mark.parametrize('manifest', [[], None, 5, 'not an object'])
def test_malformed_manifest_keeps_discoverable_error(tmp_path, manifest):
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    detail = read_artifact(tmp_path, 'malformed')
    assert detail.history.integrity == 'corrupt'
    assert detail.history.scored is None
    assert detail.history.planned is None


def test_duplicate_inputs_do_not_create_arbitrary_pairs(history_root):
    left, right = [read_artifact(history_root / name, name)
                   for name in ('issue-91-demonstration', 'issue-92-pilot')]
    duplicate = left.samples[0].model_copy(deep=True)
    duplicate.id = 'duplicate_sample'
    left.samples.append(duplicate)
    comparison = compare_experiments(left, right)
    assert not any(row.left_sample in {duplicate.id, left.samples[0].id} for row in comparison.observations)
    assert any(item.sample_id == duplicate.id for item in comparison.exclusions)


def test_out_of_plan_repetition_is_not_silently_hidden(history_root):
    path = history_root / 'issue-92-pilot'
    (path / 'CHECKSUMS.json').unlink()
    result_path = path / 'results/case_03_fixture-resolve-3.json'
    row = json.loads(result_path.read_text())
    row['repetition'] = 99
    result_path.write_text(json.dumps(row))
    detail = read_artifact(path, path.name)
    assert detail.history.integrity == 'corrupt'
    assert 'outside the frozen plan' in detail.history.integrity_reason
