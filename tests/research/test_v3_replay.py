import json
from copy import deepcopy

import pytest

from benchmark_v3 import replay
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.retained_inputs import value_digest


SUCCESSOR = ('Rhea', 'trustee_of', 'Toy Trust')
INCUMBENT = ('Niko', 'trustee_of', 'Toy Trust')
UNAFFECTED = ('Jo', 'spouse_of', 'Niko')
SIGNED_QUOTE = 'The deed names Rhea as replacement on release.'
COPY_QUOTE = 'The counterpart names Rhea and takes effect on release.'
INITIAL_QUOTE = 'Niko holds office before the change.'
DISPOSITION = 'Status: released.'
HOLD = 'Status: held through the meeting.'
MARRIAGE_QUOTE = 'Jo and Niko are married.'


def _pair(source_id, quote):
    return {'source_id': source_id, 'supporting_text': quote}


def _candidate(edge, pair):
    source, kind, target = edge
    return {'source_name': source, 'relationship_type': kind, 'target_name': target, **pair}


@pytest.fixture
def package(tmp_path):
    sources = [
        {'id': 'deed', 'title': 'Instrument', 'text': SIGNED_QUOTE},
        {'id': 'copy', 'title': 'Counterpart', 'text': COPY_QUOTE},
        {'id': 'initial', 'title': 'Opening position', 'text': INITIAL_QUOTE},
        {'id': 'status', 'title': 'Register', 'text': DISPOSITION},
        {'id': 'message', 'title': 'Message', 'text': MARRIAGE_QUOTE},
        {'id': 'other', 'title': 'Copied wording elsewhere', 'text': f'{MARRIAGE_QUOTE} {DISPOSITION}'},
    ]
    ordered = {'A0': sources, 'A1': list(reversed(sources)), 'A2': deepcopy(sources)}
    ordered['A2'][3]['text'] = HOLD
    edit = {'source_id': 'status', 'before': DISPOSITION, 'after': HOLD}
    entities = [
        {'id': 'rhea', 'type': 'person', 'name': 'Rhea'},
        {'id': 'niko', 'type': 'person', 'name': 'Niko'},
        {'id': 'jo', 'type': 'person', 'name': 'Jo'},
        {'id': 'trust', 'type': 'trust', 'name': 'Toy Trust'},
    ]
    spouse_edge = {'source': 'jo', 'type': 'spouse_of', 'target': 'niko'}
    spouse_pair = _pair('message', MARRIAGE_QUOTE)
    rows = {}
    for identity in ordered:
        held = identity == 'A2'
        trustee, critical = ('niko', INCUMBENT) if held else ('rhea', SUCCESSOR)
        status_pair = _pair('status', HOLD if held else DISPOSITION)
        primary = _pair('initial', INITIAL_QUOTE) if held else _pair('deed', SIGNED_QUOTE)
        alternatives = [[primary, status_pair]]
        if not held:
            alternatives.append([_pair('copy', COPY_QUOTE), status_pair])
        rows[identity] = dict(condition=identity,
            truth={'entities': deepcopy(entities), 'relationships': [
                {'source': trustee, 'type': 'trustee_of', 'target': 'trust', 'approved_evidence': []},
                {**spouse_edge, 'approved_evidence': [MARRIAGE_QUOTE]},
            ]},
            source_approval={'schema_version': 1, 'relationships': [
                {**spouse_edge, 'approved_evidence': [deepcopy(spouse_pair)]},
            ]},
            sufficient_evidence=[{'edge': critical, 'joint_only': True, 'alternatives': alternatives}],
            ideal={'relationships': [
                _candidate(critical, primary), _candidate(critical, status_pair), _candidate(UNAFFECTED, spouse_pair),
            ]})

    root = tmp_path / 'fixtures'
    return root, ordered, rows, edit


def _write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return checksum(path.read_bytes())


def _freeze(package):
    root, sources, rows, edit = package
    (root / 'sources').mkdir(parents=True, exist_ok=True)
    for identity, array in sources.items():
        _write(root / 'sources' / f'{identity}.json', array)
    freeze = _write(root / 'freeze.json', dict(
        sources_sha256={identity: value_digest(array) for identity, array in sources.items()},
        order={identity: [source['id'] for source in array] for identity, array in sources.items()},
        source_commitments={identity: {
            s['id']: {'id_sha256': checksum(s['id'].encode()), 'title_sha256': checksum(s['title'].encode()),
                      'body_sha256': checksum(s['text'].encode()), 'serialized_source_sha256': value_digest(s)}
            for s in array} for identity, array in sources.items()},
        declared_removed=[SUCCESSOR], declared_added=[INCUMBENT], intervention=edit))
    conditions = {identity: _write(root / f'{identity}.json', row) for identity, row in rows.items()}
    manifest = root / 'manifest.json'
    _write(manifest, dict(schema_version=1, family='A', freeze_sha256=freeze, conditions=conditions,
        contrast={**edit, 'removed': [SUCCESSOR], 'added': [INCUMBENT]}))
    return manifest


def test_reopens_scored_ideals_and_reports_matching_and_zero_paid_slots(package, tmp_path):
    artifacts = tmp_path / 'artifacts'
    report = replay.preflight(_freeze(package), artifacts)
    assert report['preview']['maximum_paid_slots'] == report['paid_attempts'] == 0
    assert report['preview']['planned_observations'] == report['aggregate']['coverage']['scored'] == 3
    assert report['aggregate']['tp'] == 6
    assert report['aggregate']['micro_f1'] == 1
    assert report['matches']['invariance']['edges'] == [UNAFFECTED, SUCCESSOR]
    assert report['matches']['sensitivity']['removed'] == [SUCCESSOR]
    assert report['matches']['sensitivity']['added'] == [INCUMBENT]
    assert report['matches']['sensitivity']['unaffected'] == [UNAFFECTED]

    natural, permuted, held = report['conditions']
    assert natural['ordered_sources_sha256'] != permuted['ordered_sources_sha256']
    assert natural['graph']['provenance_failed'] == 1
    assert natural['ordinary_evidence']['not_applicable'] == [SUCCESSOR]
    assert natural['ordinary_evidence']['quotation']['assessed'] == 1
    assert natural['ordinary_evidence']['source_attribution']['passed'] == 1
    assert natural['ordinary_evidence']['sufficiency']['complete_over_planned'] == 1
    assert held['decisions']['required_present'] == [INCUMBENT]
    assert held['decisions']['forbidden_present'] == []

    bundle = Bundle.open(artifacts / 'run')
    assert bundle.attempt_count == 0
    assert len(bundle.results()) == 3
    assert json.loads((artifacts / 'preflight.json').read_text())['paid_attempts'] == 0


def test_second_approved_proof_is_sufficient_on_its_own(package, tmp_path):
    _, _, rows, _ = package
    rows['A1']['ideal']['relationships'][0] = _candidate(SUCCESSOR, _pair('copy', COPY_QUOTE))
    report = replay.preflight(_freeze(package), tmp_path / 'artifacts')
    proof = report['conditions'][1]['ordinary_evidence']['sufficiency']
    assert proof['complete'] == 1
    assert proof['targets'] == [{'edge': SUCCESSOR, 'status': 'complete', 'missing_by_alternative': []}]


@pytest.mark.parametrize('mutation, error', [
    ('partial', 'incomplete same-edge sufficient evidence'),
    ('wrong_edge', 'incomplete same-edge sufficient evidence'),
    ('wrong_proof_source', 'incomplete same-edge sufficient evidence'),
    ('wrong_source', 'failed ordinary Source attribution'),
    ('critical_omission', 'missed a critical edge'),
    ('forbidden', 'retained a forbidden edge'),
    ('unscored', 'unscored slots: benchmark_v3_a1'),
])
def test_replay_rejects_mutated_retained_graphs(package, tmp_path, mutation, error):
    _, _, rows, _ = package
    candidates = rows['A1']['ideal']['relationships']
    if mutation == 'partial':
        candidates.pop(1)
    elif mutation == 'wrong_edge':
        candidates[1] = _candidate(UNAFFECTED, _pair('status', DISPOSITION))
    elif mutation == 'wrong_proof_source':
        candidates[1]['source_id'] = 'other'
    elif mutation == 'wrong_source':
        candidates[2]['source_id'] = 'other'
    elif mutation == 'critical_omission':
        del candidates[:2]
    elif mutation == 'forbidden':
        candidates.append(_candidate(INCUMBENT, _pair('initial', INITIAL_QUOTE)))
    else:
        candidates[1]['supporting_text'] = 'The Source never says this.'

    artifacts = tmp_path / 'artifacts'
    with pytest.raises(ValueError, match=error):
        replay.preflight(_freeze(package), artifacts)
    bundle = Bundle.open(artifacts / 'run')
    assert bundle.attempt_count == 0
    assert not (artifacts / 'preflight.json').exists()
    if mutation == 'wrong_source':
        row = next(row for row in bundle.results() if row['sample_id'] == 'benchmark_v3_a1')
        assert row['evaluation']['provenance_passed'] == 1


@pytest.mark.parametrize('mutation, error', [
    ('a1_title', 'A1 must change only the order'),
    ('a1_same_order', 'A1 must change only the order'),
    ('a2_second_body', 'A2 must differ from A0 only'),
    ('a2_title', 'A2 must differ from A0 only'),
    ('a2_order', 'A2 must differ from A0 only'),
    ('a2_repeated_field', 'must occur exactly once'),
    ('unmodeled_source_field', 'outside the extraction contract'),
    ('a1_approval', 'A1 changed frozen A0 source_approval'),
    ('a1_sufficient_set', 'A1 changed frozen A0 sufficient_evidence'),
    ('a2_approval', 'A2 changed unaffected Source approvals'),
    ('a2_extra_edge', 'A2 truth differs by more'),
])
def test_match_checks_survive_recomputed_hashes(package, tmp_path, mutation, error):
    _, sources, rows, _ = package
    if mutation == 'a1_title':
        sources['A1'][0] = {**sources['A1'][0], 'title': 'Different metadata'}
    elif mutation == 'a1_same_order':
        sources['A1'] = sources['A0']
    elif mutation == 'a2_second_body':
        sources['A2'][0]['text'] += ' An unrelated editorial change.'
    elif mutation == 'a2_title':
        sources['A2'][3]['title'] = 'Different register title'
    elif mutation == 'a2_order':
        sources['A2'].reverse()
    elif mutation == 'a2_repeated_field':
        sources['A0'][3]['text'] += DISPOSITION
    elif mutation == 'unmodeled_source_field':
        sources['A2'][3]['date'] = '2026-10-06'
    elif mutation == 'a1_approval':
        rows['A1']['source_approval']['relationships'][0]['approved_evidence'][0]['source_id'] = 'other'
    elif mutation == 'a1_sufficient_set':
        rows['A1']['sufficient_evidence'][0]['alternatives'].reverse()
    elif mutation == 'a2_approval':
        rows['A2']['source_approval']['relationships'][0]['approved_evidence'][0]['source_id'] = 'other'
    else:
        rows['A2']['truth']['relationships'].append(
            {'source': 'rhea', 'type': 'beneficiary_of', 'target': 'trust', 'approved_evidence': [SIGNED_QUOTE]})

    with pytest.raises(ValueError, match=error):
        replay.preflight(_freeze(package), tmp_path / 'artifacts')


def test_requires_every_condition_even_when_manifest_and_freeze_agree(package, tmp_path):
    _, sources, rows, _ = package
    del sources['A2']
    del rows['A2']
    with pytest.raises(ValueError, match='cover exactly A0, A1 and A2'):
        replay.preflight(_freeze(package), tmp_path / 'artifacts')


@pytest.mark.parametrize('relative', ['A0.json', 'sources/A1.json', 'freeze.json'])
def test_rejects_drift_from_committed_digests(package, tmp_path, relative):
    manifest = _freeze(package)
    path = manifest.parent / relative
    if relative.startswith('sources/'):
        document = json.loads(path.read_text())
        document[0]['text'] += ' Uncommitted text.'
        _write(path, document)
    else:
        path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='Digest mismatch'):
        replay.preflight(manifest, tmp_path / 'artifacts')


def test_rejects_annotation_leak_into_extraction_preview(package, tmp_path, monkeypatch):
    request_messages = replay.request_messages
    monkeypatch.setattr(replay, 'request_messages', lambda request: [
        *request_messages(request), ('human', 'Leaked reference answer'),
    ])
    with pytest.raises(ValueError, match='Unexpected extraction request contents'):
        replay.preflight(_freeze(package), tmp_path / 'artifacts')


def test_cli_identifies_missing_fixture(package, tmp_path, monkeypatch, capsys):
    manifest = _freeze(package)
    (manifest.parent / 'A1.json').unlink()
    monkeypatch.setattr('sys.argv', ['replay', '--manifest', str(manifest), '--artifacts', str(tmp_path / 'artifacts')])
    with pytest.raises(SystemExit) as exited:
        replay.main()
    assert exited.value.code == 1
    assert 'Family A offline replay failed:' in capsys.readouterr().err


@pytest.mark.parametrize('field', ['source_commitments', 'declared_added'])
def test_audits_individual_source_and_semantic_declarations(package, tmp_path, field):
    manifest_path = _freeze(package)
    manifest = json.loads(manifest_path.read_bytes())
    freeze_path = manifest_path.parent / 'freeze.json'
    freeze = json.loads(freeze_path.read_bytes())
    if field == 'source_commitments':
        freeze[field]['A1']['deed']['title_sha256'] = '0' * 64
    else:
        freeze[field] = [SUCCESSOR]
    manifest['freeze_sha256'] = _write(freeze_path, freeze)
    _write(manifest_path, manifest)
    with pytest.raises(ValueError, match='Source commitment mismatch|switch differs'):
        replay.preflight(manifest_path, tmp_path / 'artifacts')


def test_excludes_changed_sourced_prompt_before_run_creation(package, tmp_path, monkeypatch):
    monkeypatch.setattr(replay, 'SOURCED_EXTRACTION_PROMPT', 'A changed prompt')
    artifacts = tmp_path / 'artifacts'
    with pytest.raises(ValueError, match='differs from the frozen baseline'):
        replay.preflight(_freeze(package), artifacts)
    assert not artifacts.exists()
