import json
from pathlib import Path

import pytest

from benchmark_v3 import replay
from benchmark_v3.replay_manifest import load_family
from private_client_graph.research.artifacts import checksum


DEVELOPMENT = Path(__file__).resolve().parents[2] / 'benchmark_v3'


@pytest.mark.parametrize(('family', 'removed', 'added'), [('D', 1, 1), ('E', 1, 0), ('F', 0, 0)])
def test_commissioned_family_saved_ideals_replay_without_dispatch(family, removed, added, tmp_path):
    manifest = DEVELOPMENT / f'family_{family.lower()}' / 'manifest.json'
    report = replay.preflight(manifest, tmp_path / 'artifacts')

    assert report['paid_attempts'] == report['preview']['maximum_paid_slots'] == 0
    assert report['aggregate']['coverage']['scored'] == 2
    assert report['aggregate']['micro_f1'] == 1
    assert all(row['exact_graph'] for row in report['conditions'])
    assert all(not row['decisions']['forbidden_present'] for row in report['conditions'])
    match = report['matches'][f'{family}1']
    assert len(match['removed']) == removed
    assert len(match['added']) == added
    for row in report['conditions']:
        ordinary = row['ordinary_evidence']
        assert ordinary['quotation']['failed'] == ordinary['source_attribution']['failed'] == 0
        proof = ordinary['sufficiency']
        assert proof['complete'] == proof['planned']
    if family == 'F':
        assert all(row['ordinary_evidence']['sufficiency']['complete'] >= 2 for row in report['conditions'])


@pytest.mark.parametrize('family', ['D', 'E', 'F'])
def test_commissioned_freeze_rejects_changed_contrast_after_rehash(family, tmp_path):
    saved = DEVELOPMENT / f'family_{family.lower()}'
    (tmp_path / 'sources').mkdir()
    manifest = json.loads((saved / 'manifest.json').read_text())
    freeze = json.loads((saved / 'freeze.json').read_text())
    for identity in manifest['conditions']:
        for relative in (f'{identity}.json', f'sources/{identity}.json'):
            (tmp_path / relative).write_bytes((saved / relative).read_bytes())

    # Keep source/annotation bytes and all commitments valid while claiming a
    # scientifically different intervention result.
    freeze['required'][f'{family}1'] = (
        [] if family == 'F' else freeze['required'][f'{family}0']
    )
    freeze_bytes = json.dumps(freeze).encode()
    (tmp_path / 'freeze.json').write_bytes(freeze_bytes)
    manifest['freeze_sha256'] = checksum(freeze_bytes)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match='critical decisions differ'):
        load_family(path)


def test_label_collision_rejects_cross_person_evidence_with_exact_graph(tmp_path):
    source = DEVELOPMENT / 'family_f'
    (tmp_path / 'sources').mkdir()
    manifest = json.loads((source / 'manifest.json').read_text())
    for relative in ('freeze.json', 'F0.json', 'sources/F0.json', 'sources/F1.json'):
        (tmp_path / relative).write_bytes((source / relative).read_bytes())

    case = json.loads((source / 'F1.json').read_text())
    group = case['sufficient_evidence']
    critical = json.loads((source / 'freeze.json').read_text())['required']['F1']
    first, second = [next(row for row in group if row['edge'] == edge) for edge in critical]
    first_names, second_names = [set(row['edge'][::2]) for row in (first, second)]
    assert first_names.isdisjoint(second_names)
    first_parts, second_parts = [row['alternatives'][0] for row in (first, second)]
    shared_source = next(part['source_id'] for part in first_parts
                         if any(other['source_id'] == part['source_id'] for other in second_parts))
    wrong = next(part for part in second_parts if part['source_id'] == shared_source)
    altered = next(rel for rel in case['ideal']['relationships']
                   if [rel['source_name'], rel['relationship_type'], rel['target_name']] == first['edge']
                   and rel['source_id'] == shared_source)
    altered['supporting_text'] = wrong['supporting_text']

    changed = json.dumps(case).encode()
    (tmp_path / 'F1.json').write_bytes(changed)
    manifest['conditions']['F1'] = checksum(changed)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match='incomplete same-edge sufficient evidence'):
        replay.preflight(path, tmp_path / 'artifacts')


def test_invariant_beneficiary_proof_tracks_the_committed_locator(tmp_path):
    source = DEVELOPMENT / 'family_d'
    (tmp_path / 'sources').mkdir()
    manifest = json.loads((source / 'manifest.json').read_text())
    for relative in ('freeze.json', 'D0.json', 'sources/D0.json', 'sources/D1.json'):
        (tmp_path / relative).write_bytes((source / relative).read_bytes())

    freeze = json.loads((source / 'freeze.json').read_text())
    case = json.loads((source / 'D1.json').read_text())
    changed_part = next(
        pair for proof in case['sufficient_evidence'] if proof['edge'] not in freeze['candidates']
        for group in proof['alternatives'] for pair in group
        if pair['source_id'] == freeze['intervention']['source_id']
        and freeze['intervention']['after'] in pair['supporting_text']
    )
    edit = freeze['intervention']
    changed_part['supporting_text'] = changed_part['supporting_text'].replace(edit['after'], edit['before'])
    changed = json.dumps(case).encode()
    (tmp_path / 'D1.json').write_bytes(changed)
    manifest['conditions']['D1'] = checksum(changed)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match='changed unaffected sufficient evidence sets'):
        load_family(path)
