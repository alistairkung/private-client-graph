import json
from collections import Counter
from pathlib import Path

import pytest

from benchmark_v3.replay import preflight
from benchmark_v3.replay_evidence import EVIDENCE_POLICY_VERSION, SUFFICIENCY_VERSION
from benchmark_v3.replay_manifest import load_family
from private_client_graph.research.artifacts import checksum


ROOT = Path(__file__).resolve().parents[2] / 'benchmark_v3'
PROTOCOL_SHA256 = '7b8fa95a3ddb87a96b2dec1977f330f7822ac522342a2f381e55081175e59ead'
REVIEWED_COMMIT = '54699499f2727a4e30bfba77ce66e91d2235b214'
REVIEWED_ADMISSION_SHA256 = {
    'b': '5c5ccaa53a18bbee985dee5d4065dd96c8775e823b8abf3818e4551f91730ef7',
    'c': '86c7b9929204798fb61a58a85a0bbc29fc2787bb72d7f1d7901e9a54733cb16e',
}


def _json(path):
    return json.loads(path.read_bytes())


def _digest(path):
    return checksum(path.read_bytes())


@pytest.mark.parametrize('family, planned, positives', [('b', 2, 1), ('c', 3, 2)])
def test_admission_commitments_and_zero_call_replay(family, planned, positives, tmp_path):
    root = ROOT / f'family_{family}'
    manifest = root / 'manifest.json'
    admission = _json(root / 'admission.json')
    verified = load_family(manifest)

    assert admission['family'] == family.upper()
    assert admission['status'] == 'admitted' and admission['owner_decision'] == 'accept'
    signature = admission['signature']
    assert signature['verbatim_reply'] == 'I accept Family B and, separately, I accept Family C.'
    assert signature['reviewed_commit'] == REVIEWED_COMMIT
    reviewed_admission = dict(admission, status='pending_human_admission', owner_decision=None, signature=None)
    reviewed_bytes = (json.dumps(reviewed_admission, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    assert signature['reviewed_admission_sha256'] == REVIEWED_ADMISSION_SHA256[family] == checksum(reviewed_bytes)

    assert admission['dispatched'] is False
    assert admission['paid_pcg_extraction_attempts'] == 0
    assert admission['evidence_policy'] == EVIDENCE_POLICY_VERSION
    assert admission['proof_policy'] == SUFFICIENCY_VERSION
    assert admission['protocol_sha256'] == PROTOCOL_SHA256
    assert admission['manifest_sha256'] == verified.manifest_sha256
    assert admission['freeze_sha256'] == verified.freeze_sha256
    for name, expected in admission['review_files'].items():
        assert _digest(root / name) == expected
    for name, condition in verified.conditions.items():
        assert admission['ordered_sources'][name] == condition.sources_sha256
        assert admission['keys'][name] == condition.annotation_sha256
    for source in next(iter(verified.conditions.values())).sources:
        assert (root / 'originals' / f'{source.id}.txt').read_bytes() == source.text.encode()

    approved = [
        [part.model_dump(mode='json') for part in group]
        for case in verified.conditions.values()
        for proof in case.saved.sufficient_evidence
        for group in proof.alternatives
    ]
    masks = _json(root / 'review' / 'mask-results.json')
    assert masks
    for result in masks.values():
        if not result['passed']:
            assert result['kind'] == 'proof_subset'
            assert result['disposition'] == 'excluded_from_key'
            assert result['pairs'] not in approved
    deleted = _json(root / 'review' / 'proof-deletions.json')
    for proof in deleted:
        assert masks[proof['full_read']]['pairs'] == proof['alternative']
        assert masks[proof['full_read']]['passed']
        assert len(proof['deletions']) == len(proof['alternative'])
        assert all(row['passed'] for row in proof['deletions'])
    assert [proof['alternative'] for proof in deleted] == approved

    report = preflight(manifest, tmp_path / 'artifacts')
    assert report['paid_attempts'] == report['preview']['maximum_paid_slots'] == 0
    assert report['aggregate']['coverage']['scored'] == planned
    assert report['aggregate']['fp'] == report['aggregate']['fn'] == 0
    assert report['aggregate']['micro_f1'] == 1
    assert sum(row['ordinary_evidence']['sufficiency']['complete'] for row in report['conditions']) == positives


def test_dedicated_ledger_locks_fresh_condition_local_blind_reads_before_adjudication():
    ledger = ROOT / 'families_b_c_sessions.jsonl'
    rows = [json.loads(line) for line in ledger.read_bytes().splitlines()]
    assert sum(row['counted_session'] for row in rows) <= 70
    receipts = {row['slot']: row for row in rows if row['status'] == 'completed'}
    roles = Counter(row['role'] for row in receipts.values())
    assert roles['annotation'] == 10
    assert roles['adjudication'] == 5
    thread_ids = [row['verification']['isolation']['thread_id'] for row in receipts.values()]
    assert len(thread_ids) == len(set(thread_ids))
    for row in receipts.values():
        evidence = row['verification']
        isolation = evidence['isolation']
        assert isolation['ephemeral'] and isolation['empty_workspace']
        assert isolation['thread_environments'] == isolation['runtime_workspace_roots'] == []
        assert isolation['instruction_sources'] == evidence['observed_tool_actions'] == []
        assert isolation['sandbox'] == {'type': 'readOnly', 'networkAccess': False}

    for family in ('b', 'c'):
        root = ROOT / f'family_{family}'
        admission = _json(root / 'admission.json')
        freeze = _json(root / 'freeze.json')
        assert admission['ledger_sha256'] == _digest(ledger)
        locks = _json(root / 'review' / 'blind-lock.json')
        judgments = _json(root / 'review' / 'provisional-lock.json')
        assert locks.keys() == judgments.keys() == freeze['sources_sha256'].keys()
        for condition, readers in locks.items():
            assert len(readers) == 2
            assert readers[0]['packet_sha256'] == readers[1]['packet_sha256']
            assert readers[0]['session'] != readers[1]['session']
            for reader, suffix in zip(readers, ('a', 'b'), strict=True):
                row = receipts[reader['slot']]
                assert row['session'] == reader['session']
                assert set(row['inputs']) == {'sources', 'neutral_brief', 'ontology', 'annotation_rules'}
                assert row['inputs']['sources']['sha256'] == freeze['sources_sha256'][condition]
                assert _digest(root / 'review' / 'outputs' / f'{condition}-{suffix}.json') == reader['output_sha256']

    prompt_digests = {row['prompt']['sha256'] for row in receipts.values() if row['role'] == 'annotation'}
    assert len(prompt_digests) == 1

    last_blind = max(row['verification']['completed_at'] for row in receipts.values() if row['role'] == 'annotation')
    first_verdict = min(row['verification']['submitted_at'] for row in receipts.values() if row['role'] == 'adjudication')
    assert last_blind < first_verdict
