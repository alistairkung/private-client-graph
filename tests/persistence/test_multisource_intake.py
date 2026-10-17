"""Real multipart/PDF/pipeline/PostgreSQL multi-Source practitioner journeys."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE
from private_client_graph.application import matter_proposals
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.matter_proposals import find_reference
from private_client_graph.persistence.proposal_allowance import quota_reset

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'
PARENT = 'Alice Example is the parent of Ben Example.'
SOURCES = [{'id': 'first', 'title': 'Synthetic note'}, {'id': 'second', 'title': 'Synthetic note'}]


def _headers(client):
    return {'origin': 'https://testserver', 'x-csrftoken': client.cookies[CSRF_COOKIE]}


def _submit(client, *, sources=None, pdfs=None, reference='Multi/1', confirmation='true', headers=None):
    sources = SOURCES if sources is None else sources
    pdfs = [FIXTURES.joinpath('synthetic-proposal.pdf').read_bytes()] * 2 if pdfs is None else pdfs
    return client.post('/api/matter-proposals', data={
        'external_reference': reference, 'matter_title': 'Synthetic combined review',
        'sources': json.dumps(sources), 'synthetic_confirmation': confirmation,
    }, files=[('pdfs', (f'note-{i}.pdf', pdf, 'application/pdf')) for i, pdf in enumerate(pdfs)],
        headers=_headers(client) if headers is None else headers)


@pytest.fixture
def client(database, authenticated_client, monkeypatch):
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_LIMIT', '1')
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', '86400')
    return authenticated_client(create_app())


@pytest.fixture
def provider(monkeypatch):
    calls = []

    def extract(sources, *, llm):
        calls.append(sources)
        assert llm.max_retries == 0
        relationships = []
        for source in sources:
            if source.text == PARENT:
                relationships.append({'source_name': 'Alice Example', 'relationship_type': 'parent_of',
                    'target_name': 'Ben Example', 'supporting_text': PARENT, 'source_id': source.id})
            else:
                for role in ['settlor', 'beneficiary', 'trustee']:
                    relationships.append({'source_name': 'Morgan Example', 'relationship_type': f'{role}_of',
                        'target_name': 'Fictional Trust', 'supporting_text': f'Morgan Example is {role} of the Fictional Trust.',
                        'source_id': source.id})
        return SourcedExtractionResult.model_validate({'relationships': relationships})

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_sources', extract)
    return calls


@pytest.mark.parametrize('same_text', [True, False])
def test_multiple_real_pdfs_review_confirm_and_reopen_complete_state(client, provider, same_text, tracked_upload_files):
    pdfs = [FIXTURES.joinpath('synthetic-proposal.pdf').read_bytes(), FIXTURES.joinpath(
        'synthetic-proposal.pdf' if same_text else 'multiple-role-proposal.pdf').read_bytes()]
    response = _submit(client, pdfs=pdfs)
    assert response.status_code == 201, response.text
    proposal = response.json()
    state = proposal['state']
    assert proposal['authoritative_source'] is None
    assert [(s['id'], s['title']) for s in state['sources']] == [('first', 'Synthetic note'), ('second', 'Synthetic note')]
    assert len(provider) == 1 and [s.id for s in provider[0]] == ['first', 'second']
    assert [s.text for s in provider[0]] == [s['text'] for s in state['sources']]
    assert len(state['relationships']) == (1 if same_text else 4)
    assert len(state['evidence']) == (2 if same_text else 4)
    assert {item['source_id'] for item in state['evidence']} == {'first', 'second'}
    if same_text:
        assert state['sources'][0]['text'] == state['sources'][1]['text']
        assert len(state['relationships'][0]['evidence_ids']) == 2
    assert client.get(response.headers['location']).json() == proposal
    assert all(file.closed for file in tracked_upload_files)
    duplicate = _submit(client)
    assert duplicate.status_code == 409
    assert len(provider) == 1
    confirmation = client.post('/api/matters', json={'matter_proposal_id': proposal['id']}, headers=_headers(client))
    assert confirmation.status_code == 201, confirmation.text
    matter = confirmation.json()
    assert matter['authoritative_source'] is None
    assert matter['state'] == state
    assert matter['current_graph'] == proposal['proposed_graph']
    assert client.get(confirmation.headers['location']).json() == matter
    assert client.get(response.headers['location']).status_code == 404
    assert client.get('/api/matter-proposals').json() == []
    assert find_reference('multi/1').resource_kind == 'matter'
    assert len(provider) == 1  # Confirmation and reads never analyse again.


@pytest.mark.parametrize('change,code', [
    ('duplicate_ids', 'invalid_sources'), ('missing_pdf', 'invalid_sources'),
    ('invalid_second', 'invalid_pdf'), ('long_combined_text', 'source_too_long'),
    ('large_combined_bytes', 'pdf_too_large'), ('too_many', 'invalid_form'),
    ('invalid_metadata', 'invalid_metadata'), ('unconfirmed', 'synthetic_confirmation_required'),
])
def test_bundle_admission_fails_before_provider_quota_reference_or_persistence(client, provider, change, code, tracked_upload_files):
    sources = [dict(item) for item in SOURCES]
    pdfs = [FIXTURES.joinpath('synthetic-proposal.pdf').read_bytes()] * 2
    confirmation = 'true'
    if change == 'duplicate_ids':
        sources[1]['id'] = sources[0]['id']
    elif change == 'missing_pdf':
        pdfs.pop()
    elif change == 'invalid_second':
        pdfs[1] = b'not a PDF'
    elif change == 'long_combined_text':
        pdfs[0] = FIXTURES.joinpath('source-at-limit.pdf').read_bytes()
    elif change == 'large_combined_bytes':
        pdfs[0] = pdfs[0].ljust(10 * 1024 * 1024, b' ')
    elif change == 'too_many':
        sources = [{'id': f's{i}', 'title': 'Note'} for i in range(6)]
        pdfs = pdfs * 3
    elif change == 'invalid_metadata':
        sources[1]['title'] = 'bad\nline'
    elif change == 'unconfirmed':
        confirmation = 'false'
    response = _submit(client, sources=sources, pdfs=pdfs, confirmation=confirmation)
    assert response.status_code == 422, response.text
    assert response.json()['error']['code'] == code
    assert provider == []
    assert quota_reset(limit=1, window_seconds=86400) is None
    assert find_reference('Multi/1') is None
    assert client.get('/api/matter-proposals').json() == []
    assert tracked_upload_files and all(file.closed for file in tracked_upload_files)


def test_bundle_retains_authentication_origin_and_csrf_checks(client, provider):
    anonymous = TestClient(client.app, base_url='https://testserver')
    anonymous.get('/api/matter-proposals')
    assert _submit(anonymous).status_code == 401
    for headers in [{'origin': 'https://testserver'}, {**_headers(client), 'origin': 'https://other.example'}]:
        assert _submit(client, headers=headers).status_code == 403
    assert provider == []
    assert quota_reset(limit=1, window_seconds=86400) is None


def test_bad_source_attribution_spends_one_attempt_but_saves_nothing(client, monkeypatch):
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_sources', lambda sources, **kwargs:
        SourcedExtractionResult.model_validate({'relationships': [{
            'source_name': 'Alice Example', 'relationship_type': 'parent_of', 'target_name': 'Ben Example',
            'supporting_text': PARENT, 'source_id': 'missing',
        }]}))
    response = _submit(client)
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'invalid_graph'
    assert quota_reset(limit=1, window_seconds=86400) is not None
    assert find_reference('Multi/1') is None
    assert client.get('/api/matter-proposals').json() == []


def test_confirmation_failure_retains_every_source_and_reference_atomically(client, provider):
    response = _submit(client)
    assert response.status_code == 201
    state = response.json()['state']
    with database_engine().begin() as connection:
        connection.execute(text("""
            CREATE FUNCTION reject_second_source() RETURNS trigger AS $$
            BEGIN IF NEW.id = 'second' THEN RAISE check_violation USING MESSAGE = 'Synthetic rejection'; END IF;
            RETURN NEW; END; $$ LANGUAGE plpgsql
        """))
        connection.execute(text('CREATE TRIGGER reject_second_source BEFORE INSERT ON matter_sources FOR EACH ROW EXECUTE FUNCTION reject_second_source()'))
    failure = client.post('/api/matters', json={'matter_proposal_id': response.json()['id']}, headers=_headers(client))
    assert failure.status_code == 503
    assert failure.json()['error']['code'] == 'confirmation_failed'
    assert client.get(response.headers['location']).json()['state'] == state
    assert find_reference('Multi/1').resource_kind == 'matter_proposal'
    with database_engine().connect() as connection:
        for table in ['matters', 'matter_sources', 'matter_entities', 'matter_evidence', 'matter_relationships', 'matter_relationship_evidence']:
            assert connection.scalar(text(f'SELECT count(*) FROM {table}')) == 0
    assert len(provider) == 1
