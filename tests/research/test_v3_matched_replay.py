import json

import pytest

from benchmark_v3.replay import preflight
from benchmark_v3.replay_manifest import source_commitments
from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import checksum
from private_client_graph.research.retained_inputs import value_digest


UNAFFECTED = ('Anya', 'sibling_of', 'Mona')


def _pair(source_id, text):
    return {'source_id': source_id, 'supporting_text': text}


def _candidate(edge, pair):
    left, predicate, right = edge
    return dict(source_name=left, relationship_type=predicate, target_name=right, **pair)


def _save(path, value):
    data = json.dumps(value, ensure_ascii=False).encode()
    path.write_bytes(data)
    return checksum(data)


def _package(root, family, mutation=None):
    if family == 'B':
        first = ('Alec', 'parent_of', 'Lara')
        second = ('Alec', 'parent_of', 'Sara')
        initial = 'Attendee: unknown'
        target_by_field = [(initial, []), ('Attendee: Lara', [first])]
        first_quote = 'Alec is my father.'
    else:
        first = ('Alec', 'beneficiary_of', 'Oak Trust')
        second = ('Alec', 'beneficiary_of', 'Ash Trust')
        initial = 'Parent deed: Oak Trust'
        target_by_field = [(initial, [first]), ('Parent deed: Ash Trust', [second]), ('Parent deed: unknown', [])]
        first_quote = 'Alec is appointed an object of the parent deed.'

    root.mkdir()
    (root / 'sources').mkdir()
    candidate_edges = [first, second]
    arrays, required, edits, cases = {}, {}, {}, {}
    names = set().union(*({a, b} for a, _, b in (UNAFFECTED, *candidate_edges)))
    entities = [dict(id=name, name=name, type='trust' if name.endswith('Trust') else 'person')
                for name in sorted(names)]
    ordinary = _pair('lineage', 'Anya and Mona are sisters.')
    relationship = dict(source='Anya', type='sibling_of', target='Mona')
    for i, (field, targets) in enumerate(target_by_field):
        identity = f'{family}{i}'
        required[identity] = targets
        arrays[identity] = [Source(id='record', title='Reference', text=field),
                            Source(id='statement', title='Instrument', text=first_quote),
                            Source(id='lineage', title='Letter', text=ordinary['supporting_text'])]
        if i:
            edits[identity] = dict(source_id='record', before=initial, after=field)
        truth = [dict(**relationship, approved_evidence=[ordinary['supporting_text']])]
        approvals = [dict(**relationship, approved_evidence=[ordinary])]
        candidates = [_candidate(UNAFFECTED, ordinary)]
        proof = []
        for edge in targets:
            left, predicate, right = edge
            truth.append(dict(source=left, type=predicate, target=right, approved_evidence=[]))
            parts = [_pair('statement', first_quote), _pair('record', field)]
            candidates.extend(_candidate(edge, part) for part in parts)
            proof.append(dict(edge=edge, joint_only=True, alternatives=[parts]))
        cases[identity] = dict(condition=identity, truth=dict(entities=entities, relationships=truth),
            source_approval=dict(schema_version=1, relationships=approvals), ideal=dict(relationships=candidates),
            sufficient_evidence=proof)

    identity = f'{family}1'
    if mutation == 'changed_title':
        arrays[identity][0] = arrays[identity][0].model_copy(update={'title': 'Extra change'})
    elif mutation == 'partial_proof':
        cases[identity]['ideal']['relationships'].pop()
    elif mutation == 'unsafe_assertion':
        unresolved = f'{family}{0 if family == "B" else 2}'
        cases[unresolved]['ideal']['relationships'].append(_candidate(second, _pair('statement', first_quote)))
    elif mutation == 'entity_drift':
        unused = second[2] if family == 'B' else first[2]
        cases[identity]['truth']['entities'] = [entity for entity in entities if entity['name'] != unused]
    elif mutation == 'wrong_target':
        required[identity] = [] if family == 'B' else [first]

    serialized = {i: [s.model_dump(mode='json') for s in array] for i, array in arrays.items()}
    for i, array in serialized.items():
        _save(root / 'sources' / f'{i}.json', array)
    freeze = _save(root / 'freeze.json', dict(order={i: [s.id for s in array] for i, array in arrays.items()},
        sources_sha256={i: value_digest(array) for i, array in serialized.items()},
        source_commitments={i: source_commitments(array) for i, array in arrays.items()},
        interventions=edits, candidates=candidate_edges, required=required))
    manifest = root / 'manifest.json'
    _save(manifest, dict(schema_version=2, family=family, freeze_sha256=freeze,
        conditions={i: _save(root / f'{i}.json', case) for i, case in cases.items()}))
    return manifest


@pytest.mark.parametrize('family, unresolved, planned', [('B', 'B0', 2), ('C', 'C2', 3)])
def test_exact_contrasts_and_unresolved_withholding(tmp_path, family, unresolved, planned):
    report = preflight(_package(tmp_path / 'case', family), tmp_path / 'run')
    assert report['preview']['maximum_paid_slots'] == report['paid_attempts'] == 0
    assert report['aggregate']['coverage']['scored'] == planned
    assert report['family'] == family
    assert len(report['matches']) == planned - 1
    for row in report['conditions']:
        assert row['exact_graph']
        assert row['decisions']['unaffected_present'] == [UNAFFECTED]
        assert row['decisions']['forbidden_present'] == []
        proof = row['ordinary_evidence']['sufficiency']
        if row['condition'] == unresolved:
            assert len(row['decisions']['forbidden']) == 2
            assert proof['planned'] == 0 and proof['complete_over_planned'] is None
        else:
            assert len(row['decisions']['required_present']) == 1
            assert proof['complete'] == proof['planned'] == 1


@pytest.mark.parametrize('family', ['B', 'C'])
@pytest.mark.parametrize('mutation, message', [
    ('changed_title', 'only by the precommitted literal Source body edit'),
    ('partial_proof', 'incomplete same-edge sufficient evidence'),
    ('unsafe_assertion', 'retained a forbidden edge'),
    ('wrong_target', 'critical decisions differ from the protocol'),
    ('entity_drift', 'changed the matched entity roster'),
])
def test_matched_controls_reject_mutations_with_recomputed_digests(tmp_path, family, mutation, message):
    with pytest.raises(ValueError, match=message):
        preflight(_package(tmp_path / 'case', family, mutation), tmp_path / 'run')
