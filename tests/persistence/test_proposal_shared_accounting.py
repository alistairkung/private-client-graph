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
