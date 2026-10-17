"""Authenticated dispatch shares the durable research task ceiling; providers are substituted."""
import json
from pathlib import Path

import pytest

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE
from private_client_graph.application import matter_proposals
from private_client_graph.models import ExtractionResult, SourcedExtractionResult
from private_client_graph.research.live_accounting import (
    authorize_external_invocation, initialize_task, read_task, task_state,
)


@pytest.fixture
def dispatch(database, authenticated_client, monkeypatch, tmp_path):
    root = tmp_path / 'substituted-provider-task'
    initialize_task(root, 'Deterministic authenticated dispatch test')
    authority = authorize_external_invocation(root, purpose='Substituted practitioner check',
        task_cap=2, invocation_cap=2, approval_reference='deterministic-test-only')
    monkeypatch.setenv('PCG_PROVIDER_TASK_ROOT', str(root))
    monkeypatch.setenv('PCG_PROVIDER_AUTHORIZATION', authority['authorization'])
    client = authenticated_client(create_app())
    calls = []
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text',
        lambda *args, **kwargs: calls.append('single') or ExtractionResult(relationships=[]))
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_sources',
        lambda *args, **kwargs: calls.append('multi') or SourcedExtractionResult(relationships=[]))
    return client, root, calls


def submit(client, multi=False, reference='Accounting/1'):
    fields = dict(external_reference=reference, matter_title='Synthetic accounting', synthetic_confirmation='true')
    pdf = (Path(__file__).parents[1] / 'fixtures/synthetic-proposal.pdf').read_bytes()
    if multi:
        fields['sources'] = json.dumps([{'id': 'first', 'title': 'Note'}, {'id': 'second', 'title': 'Note'}])
        files = [('pdfs', ('a.pdf', pdf, 'application/pdf')), ('pdfs', ('b.pdf', pdf, 'application/pdf'))]
    else:
        fields['source_title'] = 'Note'
        files = [('pdf', ('a.pdf', pdf, 'application/pdf'))]
    return client.post('/api/matter-proposals', data=fields, files=files,
        headers={'origin': 'https://testserver', 'x-csrftoken': client.cookies[CSRF_COOKIE]})


@pytest.mark.parametrize('multi', [False, True])
def test_missing_shared_authorization_blocks_actual_authenticated_dispatch(dispatch, monkeypatch, authenticated_client, multi):
    client, root, calls = dispatch
    monkeypatch.delenv('PCG_PROVIDER_AUTHORIZATION')
    client = authenticated_client(create_app())
    response = submit(client, multi)
    assert response.status_code == 503, response.text
    assert response.json()['error']['code'] == 'provider_authorization_unavailable'
    assert calls == []
    assert task_state(Path(read_task(root)['ledger']))['used'] == 0


def test_provider_failure_stays_charged_and_has_a_retained_outcome(dispatch, monkeypatch):
    client, root, calls = dispatch

    def failed(*args, **kwargs):
        calls.append('failed')
        raise RuntimeError('sensitive provider detail')

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', failed)
    response = submit(client)
    assert response.status_code == 422
    assert 'sensitive provider detail' not in response.text
    assert calls == ['failed']
    assert task_state(Path(read_task(root)['ledger']))['used'] == 1
    finished = list(root.glob('external-invocations/*/attempts/*.finished.json'))
    assert len(finished) == 1
    outcome = json.loads(finished[0].read_text())
    assert outcome['outcome'] == 'failed'
    assert 'sensitive provider detail' not in finished[0].read_text()


@pytest.mark.parametrize('multi', [False, True])
def test_successful_dispatch_is_reserved_before_provider_and_retained(dispatch, monkeypatch, multi):
    client, root, calls = dispatch

    def extract(*args, **kwargs):
        assert task_state(Path(read_task(root)['ledger']))['used'] == 1
        calls.append('dispatched')
        return SourcedExtractionResult(relationships=[]) if multi else ExtractionResult(relationships=[])

    monkeypatch.setattr(matter_proposals,
        'extract_relationships_from_sources' if multi else 'extract_relationships_from_text', extract)
    assert submit(client, multi).status_code == 201
    assert calls == ['dispatched']
    finished = list(root.glob('external-invocations/*/attempts/*.finished.json'))
    assert len(finished) == 1
    assert json.loads(finished[0].read_text())['outcome'] == 'completed'


def test_failed_dispatch_and_explicit_retry_use_distinct_slots_without_reset(dispatch, monkeypatch):
    client, root, calls = dispatch

    def fail(*args, **kwargs):
        calls.append('failure')
        raise RuntimeError('substituted failure')

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', fail)
    assert submit(client).status_code == 422
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text',
        lambda *args, **kwargs: calls.append('retry') or ExtractionResult(relationships=[]))
    assert submit(client).status_code == 201
    response = submit(client, reference='Accounting/2')
    assert response.status_code == 429
    assert response.json()['error']['code'] == 'provider_allowance_exhausted'
    assert calls == ['failure', 'retry']
    assert task_state(Path(read_task(root)['ledger']))['used'] == 2
    started = list(root.glob('external-invocations/*/attempts/*.started.json'))
    assert len({json.loads(path.read_text())['attempt_id'] for path in started}) == 2


@pytest.mark.parametrize('defect', ['missing_root', 'invalid_identity', 'mismatched_approval', 'incomplete_ledger'])
def test_unavailable_shared_authority_never_dispatches(dispatch, monkeypatch, authenticated_client, defect):
    client, root, calls = dispatch
    task = read_task(root)
    ledger = Path(task['ledger'])
    if defect == 'missing_root':
        monkeypatch.delenv('PCG_PROVIDER_TASK_ROOT')
    elif defect == 'invalid_identity':
        monkeypatch.setenv('PCG_PROVIDER_AUTHORIZATION', '../unsafe')
    elif defect == 'mismatched_approval':
        path = next((root / 'external-invocations').glob('*/authorization.json'))
        value = json.loads(path.read_text())
        value['purpose'] = 'not the approved publication'
        path.write_text(json.dumps(value))
    else:
        from private_client_graph.research.live_accounting import reserve_external_attempt
        authorization = next((root / 'external-invocations').iterdir()).name
        reserve_external_attempt(root, authorization=authorization, attempt_id='uncertain-prior')
        next((ledger / 'reservations').iterdir()).unlink()
    client = authenticated_client(create_app())
    response = submit(client)
    assert response.status_code == 503, response.text
    assert response.json()['error']['code'] == 'provider_authorization_unavailable'
    assert calls == []


def test_pre_dispatch_rejection_does_not_reserve_shared_allowance(dispatch):
    client, root, calls = dispatch
    from fastapi.testclient import TestClient
    anonymous = TestClient(client.app, base_url='https://testserver')
    anonymous.get('/api/matter-proposals')
    assert submit(anonymous).status_code == 401
    assert calls == []
    assert task_state(Path(read_task(root)['ledger']))['used'] == 0
