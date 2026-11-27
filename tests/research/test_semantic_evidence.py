"""The live boundary is exercised with local HTTP responses only."""
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import checksum
from private_client_graph.research.evidence_quality import EvidenceQuality
from private_client_graph.research.provider import ModelResponse
from private_client_graph.research.semantic_evidence.assessment import execute, freeze as freeze_plan, open_plan
from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.research.semantic_evidence.inputs import (
    AssessmentInputs, Baseline, ExactOutcome, Item, _verify_quotations,
)
from private_client_graph.research.semantic_evidence.judging import Quotation, make_packet, parse_judgment
from private_client_graph.research.semantic_evidence.reporting import report
from private_client_graph.research.semantic_evidence.comparison import compare

RATES = (Decimal('1.32'), Decimal('3.96'))


@pytest.fixture
def inputs():
    quality = EvidenceQuality.model_validate({
        'state': 'complete', 'scope_sha256': 'fixture', 'qualified_reference_sha256': 'fixture',
        'scoring_sha256': 'fixture', 'combined_graph': None, 'qualified_graph': None,
        'observation_origin': 'live', 'planned_inputs': 35, 'observed_inputs': 35,
        'qualified_inputs': 34, 'observed_qualified_inputs': 34, 'expected_relationships': 113,
        'observed_proof_targets': 71, 'observed_joint_targets': 30,
        'complete_proof': {'complete': 11, 'targets': 71, 'rate': 11 / 71},
        'joint_only_complete_proof': {'complete': 0, 'targets': 30, 'rate': 0.0},
        'joint_only_coverage': {'targets': 30, 'mean': 1 / 60},
    })
    targets = [item for start, count, outcome in (
        (0, 11, 'complete'), (11, 56, 'incomplete'), (67, 2, 'missing_relationship'), (69, 2, 'unavailable_graph')
    ) for item in (_target(i, outcome) for i in range(start, start + count))]
    return AssessmentInputs(extractor_run='b' * 32, extractor_manifest_sha256='retained fixture',
                            evidence_quality=quality, targets=tuple(targets))


def freeze(directory, inputs, *, donors=(), task_root=None, task_call_ceiling=69):
    if task_root is None:
        task_root = directory.parent / f'{directory.name}-task'
        task_root.mkdir(exist_ok=True)
        if not (task_root / 'live-task.json').exists():
            initialize_task(task_root, 'Test semantic accounting')
    return freeze_plan(directory, inputs, donors=donors, task_root=task_root, task_call_ceiling=task_call_ceiling)


def _target(index: int, outcome: ExactOutcome) -> Item:
    edge = (f'Parent {index}', 'parent_of', f'Child {index}')
    members = (Quotation(id='M1', source='S1', text=f'Parent {index} is a parent of Child {index}.'),)
    multi_source = 11 <= index < 40 or index == 67
    if multi_source:
        members += (Quotation(id='M2', source='S2', text=f'The register identifies Child {index}.'),)
    routes = (tuple(member.id for member in members),)
    if index == 13:
        members += (Quotation(id='M3', source='S1', text='Names in original register.'),
                    Quotation(id='M4', source='S3', text='Original entry records the relationship.'),
                    Quotation(id='M5', source='S3', text='Entry takes effect after approval.'))
        routes += (('M3', 'M4', 'M5'),)
    exact = outcome == 'complete' or (outcome == 'incomplete' and index == 11)
    actual = ()
    if outcome in ('complete', 'incomplete'):
        actual = (Quotation(id='Q1', source='S1', text=members[0].text if exact else f'Child {index} has Parent {index} as a parent.'),)
        if index == 11:
            actual += (Quotation(id='Q2', source='S2', text=f'Child {index} is identified in the register.'),)
        if index == 13:
            actual += (Quotation(id='Q2', source='S3', text='The relationship appears in the original entry.'),)
    return Item(id=f'{index:064x}', edge=edge, family='fixture', condition='fixture',
        source_ids={q.source: f'private source ID {q.source}' for q in members},
        members=members, quotations=actual, alternatives=routes,
        baseline=Baseline(exact_outcome=outcome, best_exact_pair_coverage=0.5 if exact and multi_source else float(exact),
                          joint_only=multi_source))


def _judgment(packet: dict, verdict: str = 'Equivalent') -> dict:
    return {'decisions': [{**pair, 'verdict': verdict, 'reason': 'Fixture review of the attached words.',
                           'material_differences': ['A material detail is missing.'] if verdict == 'Partially Equivalent' else []}
                          for pair in packet['pairs']]}


def _response(packet: dict, *, tokens: int = 100, verdict: str = 'Equivalent') -> httpx.Response:
    return httpx.Response(200, json={
        'id': 'mock', 'object': 'chat.completion', 'created': 1, 'model': 'deepseek-v4-pro',
        'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {
            'role': 'assistant', 'content': json.dumps(_judgment(packet, verdict))}}],
        'usage': {'prompt_tokens': tokens, 'completion_tokens': 20, 'total_tokens': tokens + 20},
    })


def _run(directory, digest, client, rates=RATES, reference='offline test'):
    execute(directory, approved_digest=digest, approval_reference=reference, verified_rates=rates,
            api_key='fixture-key', http_client=client)


def test_fixed_targets_and_source_matched_request_boundary(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    offline = report(directory)
    assert offline['target_summary']['semantic_outcomes'] == {
        'unattempted': 56, 'no_eligible_comparison': 11, 'deterministic_delivery_failure': 4,
    }
    assert offline['target_summary']['multi_source_evidence_coverage'] == {
        'targets': 30, 'matched_target_equivalents': 0.5, 'mean': pytest.approx(1 / 60),
    }
    assert offline['target_summary']['evidence_support'] == {'count': 12, 'targets': 71, 'rate': pytest.approx(12 / 71)}
    assert offline['target_summary']['proof_completion']['count'] == 11
    assert offline['operations']['reserved_attempts'] == 0
    requests = []

    def transport(http_request):
        request = json.loads(http_request.content)
        requests.append(request)
        assert str(http_request.url) == 'https://api.deepseek.com/chat/completions'
        assert request['model'] == 'deepseek-v4-pro'
        assert request['max_tokens'] == 4000
        assert request['thinking'] == {'type': 'disabled'}
        assert request['response_format'] == {'type': 'json_object'}
        assert [message['role'] for message in request['messages']] == ['system', 'user']
        assertion = json.loads(request['messages'][1]['content'])
        assert set(assertion) == {'relationship', 'members', 'quotations', 'pairs'}
        assert all(set(quote) == {'id', 'source', 'text'} for quote in assertion['quotations'])
        assert 'private source ID' not in request['messages'][1]['content']
        if len(requests) == 1:
            return httpx.Response(429, json={'error': {'message': 'mock rate limit'}})
        if len(requests) == 2:
            return _response(assertion, verdict='Uncertain')
        return _response(assertion)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with ThreadPoolExecutor(max_workers=2) as workers:
            executions = [workers.submit(_run, directory, digest, client) for _ in range(2)]
            for execution in executions:
                execution.result(timeout=20)

    result = report(directory)
    assert len(requests) == 56
    summary = result['target_summary']
    assert summary['semantic_outcomes'] == {
        'no_eligible_comparison': 11, 'provider_failed': 1, 'judged': 55, 'deterministic_delivery_failure': 4,
    }
    assert summary['pair_verdicts']['Uncertain'] == 1
    assert result['operations']['reserved_attempts'] == 56
    assert result['operations']['reserved_attempts_without_usage'] == 1
    assert Decimal(result['operations']['maximum_estimated_peak_usd']) == Decimal('1.77408')
    assert result['deterministic_baseline'] == offline['deterministic_baseline']


def test_semantic_metrics_keep_exact_credit_and_score_each_alternative(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)

    def transport(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        subject = packet['relationship'][0]
        if subject == 'Parent 11':
            return _response(packet, verdict='old independent verdict')
        if subject == 'Parent 12':
            return _response(packet, verdict='Partially Equivalent')
        if subject == 'Parent 14':
            return _response(packet, verdict='Uncertain')
        if subject != 'Parent 13':
            return _response(packet)
        body = _response(packet).json()
        judgment = _judgment(packet)
        for decision in judgment['decisions']:
            if decision['member_id'] in {'M3', 'M5'}:
                decision.update(verdict='Not Equivalent', material_differences=['Different entry.'])
        body['choices'][0]['message']['content'] = json.dumps(judgment)
        return httpx.Response(200, json=body)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        _run(directory, digest, client)

    result = report(directory)
    summary = result['target_summary']
    assert summary['evidence_support'] == {'count': 65, 'targets': 71, 'rate': pytest.approx(65 / 71)}
    assert summary['proof_completion'] == {'count': 38, 'targets': 71, 'rate': pytest.approx(38 / 71)}
    assert summary['multi_source_evidence_coverage'] == {
        'targets': 30, 'matched_target_equivalents': 13.5, 'mean': pytest.approx(13.5 / 30),
    }
    assert summary['pair_verdicts']['Partially Equivalent'] == 1
    exact_row, partial_row, alternative_row = result['targets'][11:14]
    assert exact_row['status'] == 'invalid_judgment'
    assert exact_row['routes'][0]['matched_members'] == ['M1']
    assert partial_row['routes'][0]['matched_members'] == []
    assert [route['matched_members'] for route in alternative_row['routes']] == [['M1'], ['M4']]
    assert [len(route['members']) for route in alternative_row['routes']] == [2, 3]
    assert not any(route['complete'] for route in alternative_row['routes'])


def test_interruption_spends_its_single_slot_on_continuation(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    seen = []
    active_states = []

    def transport(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        seen.append(packet)
        if len(seen) == 1:
            raise KeyboardInterrupt
        if len(seen) == 2:
            active_states.append(report(directory)['target_summary']['semantic_outcomes'])
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(KeyboardInterrupt):
            _run(directory, digest, client)
        assert report(directory)['target_summary']['semantic_outcomes']['interrupted'] == 1
        with pytest.raises(ValueError, match='recorded approval reference'):
            _run(directory, digest, client, reference='different')
        _run(directory, digest, client)
    active, = active_states
    assert active['interrupted'] == active['awaiting_receipt'] == 1
    assert len(seen) == 56
    assert seen.count(seen[0]) == 1
    assert report(directory)['operations']['reserved_attempts'] == 56
    assert report(directory)['target_summary']['semantic_outcomes']['interrupted'] == 1


def test_price_digest_and_token_limits_block_dispatch(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    calls = []

    def transport(request):
        calls.append(request)
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        return _response(packet, tokens=12_001)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ValueError, match='exact approved digest'):
            _run(directory, 'wrong', client)
        with pytest.raises(ValueError, match='Provider pricing'):
            _run(directory, digest, client, rates=(Decimal('99'), RATES[1]))
        assert not calls
        for _ in range(2):
            with pytest.raises(ValueError, match='token usage exceeded'):
                _run(directory, digest, client)
    assert len(calls) == 1


def test_oversized_request_cannot_be_frozen(tmp_path, inputs):
    item = inputs.targets[12]
    large = Quotation(id='Q1', source='S1', text='é' * 6_500)
    targets = (*inputs.targets[:12], item.model_copy(update={'quotations': (large,)}), *inputs.targets[13:])
    with pytest.raises(ValueError, match='input-token envelope'):
        freeze(tmp_path / 'oversized', inputs.model_copy(update={'targets': targets}))


def test_mismatched_source_and_unsubmitted_pair_are_rejected():
    sources = [Source(id='original', title='hidden', text='Exact words'),
               Source(id='wrong', title='hidden', text='Another passage')]
    with pytest.raises(ValueError, match='attributed Source'):
        _verify_quotations({('wrong', 'Exact words')}, sources)

    packet = make_packet(('Person', 'trustee_of', 'Trust'),
                         (Quotation(id='M1', source='S1', text='Effective on 1 June.'),),
                         (Quotation(id='Q1', source='S1', text='Effective in June.'),))
    judgment = _judgment(packet.model_dump(mode='json'))
    judgment['decisions'][0]['quotation_id'] = 'unsubmitted'
    with pytest.raises(ValueError, match='exactly once'):
        parse_judgment(packet, _model_response(judgment))


def _model_response(judgment: dict) -> ModelResponse:
    return ModelResponse(raw_response={'content': json.dumps(judgment),
                                       'response_metadata': {'finish_reason': 'stop'}})


@pytest.mark.parametrize('invalid', ['omitted', 'duplicate', 'equivalent with difference', 'partial without difference', 'old verdict'])
def test_pair_responses_are_bound_and_consistent(invalid):
    packet = make_packet(('Person', 'trustee_of', 'Trust'),
                         (Quotation(id='M1', source='S1', text='Effective on 1 June.'),),
                         (Quotation(id='Q1', source='S1', text='Effective in June.'),))
    judgment = _judgment(packet.model_dump(mode='json'))
    decision, = judgment['decisions']
    if invalid == 'omitted':
        judgment['decisions'] = []
    elif invalid == 'duplicate':
        judgment['decisions'].append(decision)
    elif invalid == 'equivalent with difference':
        decision['material_differences'] = ['Missing appointment date.']
    elif invalid == 'partial without difference':
        decision['verdict'] = 'Partially Equivalent'
    else:
        decision['verdict'] = 'Supported'
    with pytest.raises(ValueError):
        parse_judgment(packet, _model_response(judgment))


@pytest.mark.parametrize('reference, actual, verdict, difference', [
    ('Nora is appointed effective 1 June 2040.', 'Nora is appointed effective 1 July 2040.',
     'Not Equivalent', 'The effective date is a month later.'),
    ('Nora serves only up to the 30 June 2040 cutoff.', 'Nora serves through July 2040.',
     'Not Equivalent', 'The actual quotation extends service past the stated cutoff.'),
    ('The signed deed appoints Nora.', 'The unsigned draft proposes appointing Nora.',
     'Not Equivalent', 'The attached text describes draft rather than operative authority.'),
    ('Jo is the parent of Lee.', 'Lee is the parent of Jo.',
     'Not Equivalent', 'The direction of the relationship is reversed.'),
    ('Nora is appointed effective 1 June 2040.', 'Nora is appointed.',
     'Partially Equivalent', 'The actual quotation omits the effective date.'),
    ('The signed deed appoints Nora.', 'It names Nora.',
     'Uncertain', 'The role and authority are unclear.'),
])
def test_material_differences_are_preserved_for_inspection(reference, actual, verdict, difference):
    edge = ('Jo', 'parent_of', 'Lee') if reference.startswith('Jo') else ('Nora', 'trustee_of', 'Trust')
    packet = make_packet(edge,
                         (Quotation(id='M1', source='S1', text=reference),),
                         (Quotation(id='Q1', source='S1', text=actual),))
    judgment = _judgment(packet.model_dump(mode='json'), verdict)
    judgment['decisions'][0]['material_differences'] = [difference]
    decision, = parse_judgment(packet, _model_response(judgment)).decisions
    assert decision.verdict == verdict
    assert decision.material_differences == (difference,)


def test_plan_tampering_cannot_use_original_digest(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    freeze(directory, inputs)
    path = directory / 'plan.json'
    path.write_bytes(path.read_bytes().replace(b'0.0', b'1.0', 1))
    with pytest.raises(ValueError, match='checksum mismatch'):
        open_plan(directory)


def test_old_independent_assessment_cannot_be_used_as_a_reuse_donor(tmp_path, inputs):
    donor = tmp_path / 'old'
    freeze(donor, inputs)
    path = donor / 'plan.json'
    payload = json.loads(path.read_text())
    payload['version'] = 'pcg-semantic-evidence-v1'
    raw = json.dumps(payload).encode()
    path.write_bytes(raw)
    (donor / 'plan-sha256.json').write_text(json.dumps(checksum(raw)))
    recipient = tmp_path / 'recipient'
    with pytest.raises(ValueError, match='pcg-semantic-evidence-equivalence'):
        freeze(recipient, inputs.model_copy(update={'extractor_run': 'a' * 32}), donors=(donor,))
    assert not recipient.exists()


def test_provider_access_failure_preserves_remaining_slots(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    seen = []

    def transport(request):
        seen.append(request)
        return httpx.Response(401, json={'error': {'message': 'fixture access denied'}})

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ValueError, match='access failed'):
            _run(directory, digest, client)
    assert len(seen) == 1
    assert report(directory)['target_summary']['semantic_outcomes']['provider_failed'] == 1
    assert report(directory)['operations']['reserved_attempts'] == 1


def test_reuse_binds_packet_source_target_and_keeps_invalid_in_comparison(tmp_path, inputs):
    donor, recipient = tmp_path / 'donor', tmp_path / 'recipient'
    donor_digest = freeze(donor, inputs)

    def original(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        if packet['relationship'][0] == 'Parent 15':
            return _response(packet, verdict='unsupported')
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(original)) as client:
        _run(donor, donor_digest, client)
    original_summary = report(donor)['deterministic_baseline']

    source_item = inputs.targets[12]
    same_words_new_source = source_item.model_copy(update={'quotations': (
        source_item.quotations[0].model_copy(update={'source': 'S2'}),
    )})
    new_source_item = inputs.targets[17]
    changed_item = new_source_item.model_copy(update={'quotations': (
        Quotation(id='Q1', source='S1', text='A different attached excerpt.'),
    )})
    right_targets = list(inputs.targets)
    right_targets[12], right_targets[17] = same_words_new_source, changed_item
    right_targets[13] = _target(13, 'missing_relationship')
    right_targets[69] = _target(69, 'incomplete')
    other = inputs.model_copy(update={'extractor_run': 'a' * 32, 'targets': tuple(right_targets)})
    digest = freeze(recipient, other, donors=(donor,))
    plan, _, _ = open_plan(recipient)
    assert plan.max_calls == 4
    assert len(plan.reused) == 52
    assert not {inputs.targets[index].id for index in (12, 13, 15, 17, 69)} & plan.reused.keys()
    assert all(reuse.origin_run == inputs.extractor_run and reuse.origin_plan_sha256 == donor_digest
               for reuse in plan.reused.values())

    pending = compare(donor, recipient)
    assert pending['formal_targets'] == 71
    assert pending['paired_valid_targets'] == 52
    assert len(pending['transitions']) == 71

    packets = []

    def changed(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        packets.append(packet)
        if packet['relationship'][0] == 'Parent 12':
            return _response(packet, verdict='Partially Equivalent')
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(changed)) as client:
        _run(recipient, digest, client)
    assert len(packets) == 4
    after = compare(donor, recipient)
    assert after['scope_note'] == report(donor)['scope_note']
    assert after['formal_targets'] == 71
    assert after['paired_valid_targets'] == 54
    for side in ('left', 'right'):
        summary = after[side]['target_summary']
        assert summary['evidence_support']['targets'] == summary['proof_completion']['targets'] == 71
        assert summary['multi_source_evidence_coverage']['targets'] == 30
    assert after['right']['operations']['reused_judgments'] == 52
    assert after['right']['operations']['reserved_attempts'] == 4
    rows = {row['id']: row for row in after['transitions']}
    assert rows[inputs.targets[15].id]['left']['status'] == 'invalid_judgment'
    assert rows[inputs.targets[12].id]['changed_members'] == [{
        'member_id': 'M1', 'source_id': 'private source ID S1',
        'quotation': 'Parent 12 is a parent of Child 12.', 'left': 'semantic', 'right': 'unmatched',
    }]
    assert rows[inputs.targets[13].id]['right']['status'] == 'deterministic_delivery_failure'
    assert report(recipient)['deterministic_baseline'] == original_summary


def test_fully_reused_plan_can_report_without_paid_authority(tmp_path, inputs):
    donor, recipient = tmp_path / 'donor', tmp_path / 'recipient'
    digest = freeze(donor, inputs)

    def transport(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        _run(donor, digest, client)
    freeze(recipient, inputs.model_copy(update={'extractor_run': 'a' * 32}), donors=(donor,))
    view = report(recipient)
    assert view['operations']['planned_attempts'] == view['operations']['reserved_attempts'] == 0
    assert view['operations']['reused_judgments'] == 56
    assert view['target_summary']['semantic_outcomes']['judged'] == 56


def test_private_workbench_reads_allow_owner_only(tmp_path, inputs, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from private_client_graph.workbench import semantic_evidence_api
    from private_client_graph.workbench.benchmark_v4_api import mount_benchmark_v4

    assessment = tmp_path / 'assessment'
    freeze(assessment, inputs)
    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(tmp_path))
    token = 'semantic-evidence-private-test-token'
    monkeypatch.setenv('PCG_BENCHMARK_V4_OWNER_TOKEN', token)
    monkeypatch.setattr(semantic_evidence_api, 'find',
        lambda root, identity: assessment if identity == inputs.extractor_run else None)
    app = FastAPI()
    assert mount_benchmark_v4(app, tmp_path, '/api/research/v2')
    path = f'/api/research/v2/semantic-evidence/runs/{inputs.extractor_run}'
    with TestClient(app, client=('127.0.0.1', 1234)) as client:
        assert client.get(path).status_code == 401
        response = client.get(path, auth=('owner', token))
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        assert len(response.json()['targets']) == 71
        assert 'cutoff absent' in response.json()['scope_note']
        assert client.post(path, auth=('owner', token)).status_code == 405
    with TestClient(app, client=('192.0.2.1', 1234)) as client:
        assert client.get(path, auth=('owner', token)).status_code == 403


def test_two_assessments_share_the_task_ceiling(tmp_path, inputs):
    from private_client_graph.research.artifacts import BudgetExceeded
    from private_client_graph.research.live_accounting import task_state

    task_root = tmp_path / 'semantic-task'
    task_root.mkdir()
    task = initialize_task(task_root, 'Shared semantic budget')
    first, second = tmp_path / 'first', tmp_path / 'second'
    cap = 57
    first_digest = freeze(first, inputs, task_root=task_root, task_call_ceiling=cap)
    other = inputs.model_copy(update={'extractor_run': 'a' * 32})
    second_digest = freeze(second, other, task_root=task_root, task_call_ceiling=cap)
    requests = []

    def transport(request):
        requests.append(request)
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        _run(first, first_digest, client)
        for _ in range(2):
            with pytest.raises(BudgetExceeded, match='Shared task allowance'):
                _run(second, second_digest, client)
    assert task_state(Path(task['ledger']))['used'] == len(requests) == cap
    assert report(first)['operations']['reserved_attempts'] == 56
    assert report(second)['operations']['reserved_attempts'] == 1


def test_in_flight_and_wrong_model_are_distinct(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    calls = []

    def transport(request):
        if not calls:
            assert report(directory)['target_summary']['semantic_outcomes']['awaiting_receipt'] == 1
        calls.append(request)
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        result = _response(packet).json()
        return httpx.Response(200, json={**result, 'model': 'different-model'})

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        _run(directory, digest, client)

    result = report(directory)
    assert result['target_summary']['semantic_outcomes'] == {
        'invalid_judgment': 56, 'no_eligible_comparison': 11, 'deterministic_delivery_failure': 4,
    }
    assert result['operations']['known_estimated_peak_usd'] > 0
    first = result['targets'][11]
    assert first['error'] == 'Provider did not return the frozen judge model'
    assert first['invalid_response']


def test_mismatched_scorer_and_frozen_reference_are_rejected(tmp_path, inputs):
    left, right = tmp_path / 'left', tmp_path / 'right'
    freeze(left, inputs)
    quality = inputs.evidence_quality.model_copy(update={'scoring_sha256': 'alternative'})
    other = inputs.model_copy(update={'extractor_run': 'a' * 32, 'evidence_quality': quality})
    freeze(right, other)
    with pytest.raises(ValueError, match='same frozen target scope'):
        compare(left, right)

    item = inputs.targets[12]
    altered = item.members[0].model_copy(update={'text': 'A different required quotation.'})
    targets = (*inputs.targets[:12], item.model_copy(update={'members': (altered, *item.members[1:])}), *inputs.targets[13:])
    other = inputs.model_copy(update={'extractor_run': 'c' * 32, 'targets': targets})
    freeze(tmp_path / 'other-reference', other)
    with pytest.raises(ValueError, match='same frozen target scope'):
        compare(left, tmp_path / 'other-reference')


def test_plan_is_retryable_on_interrupted_publication(tmp_path, inputs, monkeypatch):
    from private_client_graph.research.semantic_evidence import assessment

    directory = tmp_path / 'assessment'
    write = assessment.write_json_once

    def interrupt(path, value):
        if path.name == 'plan-sha256.json':
            raise KeyboardInterrupt
        write(path, value)

    with monkeypatch.context() as changes:
        changes.setattr(assessment, 'write_json_once', interrupt)
        with pytest.raises(KeyboardInterrupt):
            freeze(directory, inputs)
    assert not directory.exists()
    freeze(directory, inputs)


def test_sealed_receipts_detect_substitution(tmp_path, inputs):
    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)

    def interrupt_after_one(request):
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        if packet['relationship'][0] != 'Parent 11':
            raise KeyboardInterrupt
        return _response(packet)

    with httpx.Client(transport=httpx.MockTransport(interrupt_after_one)) as client:
        with pytest.raises(KeyboardInterrupt):
            _run(directory, digest, client)
    original = directory / 'receipts' / f'{inputs.targets[11].id}.json'
    original.write_bytes(original.read_bytes().replace(b'deepseek-v4-pro', b'changed-model'))
    with pytest.raises(ValueError, match='sealed completion'):
        report(directory)


def test_unsealed_response_and_missing_authority_block_resumption(tmp_path, inputs, monkeypatch):
    from private_client_graph.research.semantic_evidence import assessment

    directory = tmp_path / 'assessment'
    digest = freeze(directory, inputs)
    calls = []

    def transport(request):
        calls.append(request)
        packet = json.loads(json.loads(request.content)['messages'][1]['content'])
        return _response(packet, tokens=12_001)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with monkeypatch.context() as changes:
            changes.setattr(assessment, 'finish_external_attempt', interrupt)
            with pytest.raises(KeyboardInterrupt):
                _run(directory, digest, client)
        with pytest.raises(ValueError, match='lacks its completion seal'):
            _run(directory, digest, client)
    assert len(calls) == 1
    assert report(directory)['target_summary']['semantic_outcomes']['interrupted'] == 1
    _, _, task = open_plan(directory)
    authorization, = (Path(task['ledger']) / 'authorizations').glob('*.json')
    authorization.unlink()
    with pytest.raises(ValueError, match='missing their retained authorization'):
        report(directory)
    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ValueError, match='missing their retained authorization'):
            _run(directory, digest, client)
    assert len(calls) == 1


def test_task_registry_recovers_single_unpublished_identity(tmp_path, monkeypatch):
    from private_client_graph.research import live_accounting
    from private_client_graph.research.semantic_evidence import store

    write = live_accounting.write_json_once

    def interrupt(path, value):
        if path.name == 'live-task.json':
            raise KeyboardInterrupt
        write(path, value)

    with monkeypatch.context() as changes:
        changes.setattr(live_accounting, 'write_json_once', interrupt)
        with pytest.raises(KeyboardInterrupt):
            store.initialize(tmp_path)
    saved, = store.task_root(tmp_path).glob('task-ledgers/*/task.json')
    assert store.initialize(tmp_path) == json.loads(saved.read_text())
    assert store.initialize(tmp_path) == json.loads(saved.read_text())


def test_equivalence_packet_excludes_exact_matches_and_wrong_sources():
    actual = (
        Quotation(id='Q1', source='S1', text='Approved appointment.'),
        Quotation(id='Q2', source='S2', text='The appointment took effect on 1 June.'),
        Quotation(id='Q3', source='S3', text='The appointment took effect on 1 June.'),
    )
    required = (
        Quotation(id='M1', source='S1', text='Approved appointment.'),
        Quotation(id='M2', source='S2', text='Effective from the first of June.'),
    )
    packet = make_packet(('Nora Vale', 'trustee_of', 'Hearth Trust'), required, actual)
    assert [(pair.member_id, pair.quotation_id) for pair in packet.pairs] == [('M2', 'Q2')]
    assert [quote.id for quote in packet.quotations] == ['Q2']
    assert [member.id for member in packet.members] == ['M2']
