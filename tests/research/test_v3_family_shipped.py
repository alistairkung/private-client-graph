"""Check the shipped research packet, including public evidence for blinding."""
import hashlib
import json
from pathlib import Path

from benchmark_v3.replay import preflight
from private_client_graph.research.retained_inputs import value_digest


FAMILY = Path(__file__).resolve().parents[2] / 'benchmark_v3' / 'family_a'


def _read(path):
    return json.loads(path.read_bytes())


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_packaged_family_replays_at_zero_calls(tmp_path):
    report = preflight(FAMILY / 'manifest.json', tmp_path / 'replay')
    assert report['paid_attempts'] == 0
    assert report['aggregate']['coverage']['scored'] == 3
    assert report['matches']['invariance']['passed']
    assert report['matches']['sensitivity']['passed']
    assert _read(FAMILY / 'freeze.json')['admission'] == 'pending'


def test_public_blind_readings_bind_the_frozen_source_bytes_and_peer_commits():
    review = FAMILY / 'review'
    freeze = _read(FAMILY / 'freeze.json')
    locks = _read(review / 'blind-lock.json')
    sessions = [json.loads(line) for line in (review / 'sessions.jsonl').read_bytes().splitlines()]
    by_phase = {entry['phase']: entry for entry in sessions}
    thread_ids = [entry['verification']['isolation']['thread_id'] for entry in sessions]
    assert len(set(thread_ids)) == len(sessions) <= 40
    for condition, locked in locks['annotations'].items():
        sources = _read(FAMILY / 'sources' / f'{condition}.json')
        for source in sources:
            if condition != 'A2' or source['id'] != freeze['intervention']['source_id']:
                assert (FAMILY / 'originals' / f"{source['id']}.txt").read_bytes() == source['text'].encode()
        instruction_dir = FAMILY.parent / 'instructions'
        inputs = {
            'sources': json.dumps(sources, ensure_ascii=False),
            'neutral_brief': freeze['neutral_brief'],
            'ontology': (instruction_dir / 'ontology.md').read_text(),
            'annotation_rules': (instruction_dir / 'annotation.md').read_text(),
        }
        digest = value_digest({'inputs': inputs, 'prompt': (review / 'annotation-prompt.txt').read_text()})
        for reader in ('p', 'q'):
            phase = f'{condition}-{reader}'
            receipt = by_phase[phase]['verification']
            assert by_phase[phase]['role'] == 'annotation'
            assert digest == receipt['packet_sha256']
            assert receipt['output']['sha256'] == locked[reader] == _sha(review / 'outputs' / f'{phase}.txt')
            assert receipt['completed_at'] <= locks['locked_at']
            assert receipt['status'] == 'completed' and receipt['observed_tool_actions'] == []
        assert locks['locked_at'] <= by_phase[f'{condition}-judgment']['verification']['submitted_at']
    assert set(locks['annotations']) == {'A0', 'A1', 'A2'}


def test_admission_commitments_cover_final_ruling_and_accepted_excerpts():
    marker = _read(FAMILY / 'admission.json')
    assert marker['manifest_sha256'] == _sha(FAMILY / 'manifest.json')
    assert marker['status'] == 'admitted' and marker['owner_decision'] == 'accept'
    assert marker['signature']['verbatim_reply'] == 'accepted'
    assert marker['signature']['reviewed_commit'] == '2fe04ef1eb1df86638868de10038decc8989086d'
    assert marker['manifest_sha256'] == 'b81002b2547ebb80c77bde6fd67191578eceeb558fcd2fb125746573db2538d4'
    assert marker['dispatched'] is False
    for name, digest in marker['review_files'].items():
        assert _sha(FAMILY / name) == digest
    readers = _read(FAMILY / 'review' / 'proof-subsets.json')['readers']
    for condition, reader in [('A0', 's-01'), ('A1', 's-01'), ('A2', 's-02')]:
        key = _read(FAMILY / f'{condition}.json')
        for field, digest in marker['keys'][condition].items():
            assert value_digest(key[field]) == digest
        critical, = key['sufficient_evidence']
        excerpts = next(trial['sources'] for trial in readers if trial['reader'] == reader)
        accepted = [{'source_id': source['id'], 'supporting_text': source['text']} for source in excerpts]
        assert critical['joint_only'] and critical['alternatives'] == [accepted]
