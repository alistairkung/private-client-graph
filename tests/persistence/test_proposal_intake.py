from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE
from private_client_graph.models import ExtractionResult

PDF = Path(__file__).parents[1] / 'fixtures' / 'synthetic-proposal.pdf'
SOURCE = 'Alice Example is the parent of Ben Example.'
FIELDS = {'external_reference': '  Example/48  ', 'matter_title': '  Example family  ',
          'source_title': '  Fictional attendance note  ', 'synthetic_confirmation': 'true'}


@pytest.fixture
def proposal_client(database, monkeypatch, authenticated_client):
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_LIMIT', '1')
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', '86400')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only')
    return authenticated_client(create_app())


def headers(client):
    return {'origin': 'https://testserver', 'x-csrftoken': client.cookies[CSRF_COOKIE]}


def submit(client, *, fields=None, pdf=None):
    return client.post('/api/matter-proposals', data=fields or FIELDS,
        files={'pdf': ('advisory.txt', PDF.read_bytes() if pdf is None else pdf, 'text/plain')},
        headers=headers(client))


def test_confirmation_creates_the_matter_resource_and_accepts_only_a_proposal_id(proposal_client):
    from private_client_graph.application.proposal_contracts import ProposalMetadata
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import save_proposal

    proposal = save_proposal(
        ProposalMetadata(
            external_reference="Example/49",
            matter_title="Example family",
            source_title="Fictional attendance note",
        ),
        SOURCE,
        CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )

    response = proposal_client.post(
        "/api/matters",
        json={"matter_proposal_id": str(proposal.id)},
        headers=headers(proposal_client),
    )

    assert response.status_code == 201, response.text
    matter = response.json()
    assert response.headers["location"] == f"/api/matters/{matter['id']}"
    assert matter == {
        "id": matter["id"],
        "external_reference": proposal.external_reference,
        "title": proposal.matter_title,
        "authoritative_source": proposal.authoritative_source.model_dump(),
        "current_graph": proposal.proposed_graph.model_dump(mode="json"),
    }
    assert matter["id"] != str(proposal.id)
    assert proposal_client.get(response.headers["location"]).json() == matter
    assert proposal_client.get(f"/api/matter-proposals/{proposal.id}").status_code == 404

    rejected = proposal_client.post(
        "/api/matters",
        json={
            "matter_proposal_id": str(proposal.id),
            "title": "A client-supplied title must not be accepted",
        },
        headers=headers(proposal_client),
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "invalid_confirmation"

    replay = proposal_client.post(
        "/api/matters",
        json={"matter_proposal_id": str(proposal.id)},
        headers=headers(proposal_client),
    )
    assert replay.status_code == 404
    assert replay.json()["error"] == {
        "code": "confirmation_outcome_unknown",
        "message": "This Matter Proposal is no longer available. If confirmation may have completed, check the Matter Ledger to find the accepted Matter.",
        "retryable": False,
        "outcome_unknown": True,
        "resets_at": None,
        "existing_resource": None,
    }


def test_known_confirmation_rollback_is_safe_and_leaves_the_proposal_reviewable(proposal_client):
    from sqlalchemy import text
    from private_client_graph.application.proposal_contracts import ProposalMetadata
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import save_proposal

    proposal = save_proposal(
        ProposalMetadata(external_reference="Example/49", matter_title="Example family", source_title="Note"),
        SOURCE,
        CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )
    with database_engine().begin() as connection:
        connection.execute(text("""
            CREATE FUNCTION reject_matter_insert() RETURNS trigger AS $$
            BEGIN RAISE check_violation USING MESSAGE = 'Synthetic rejection'; END;
            $$ LANGUAGE plpgsql
        """))
        connection.execute(text("""
            CREATE TRIGGER reject_matter_insert BEFORE INSERT ON matters
            FOR EACH ROW EXECUTE FUNCTION reject_matter_insert()
        """))

    response = proposal_client.post(
        "/api/matters",
        json={"matter_proposal_id": str(proposal.id)},
        headers=headers(proposal_client),
    )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "confirmation_failed",
        "message": "The Matter could not be created. The Matter Proposal remains available. You may retry confirmation.",
        "retryable": True,
        "outcome_unknown": False,
        "resets_at": None,
        "existing_resource": None,
    }
    assert proposal_client.get(f"/api/matter-proposals/{proposal.id}").status_code == 200
    assert proposal_client.get("/api/matters").json() == []


def test_lost_confirmation_commit_response_reports_unknown_outcome_and_points_to_ledger(
    proposal_client, monkeypatch,
):
    from sqlalchemy.exc import OperationalError
    from private_client_graph.application.proposal_contracts import ProposalMetadata
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import save_proposal

    proposal = save_proposal(
        ProposalMetadata(external_reference="Example/49", matter_title="Example family", source_title="Note"),
        SOURCE,
        CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )
    dialect = database_engine().dialect
    real_commit = dialect.do_commit

    def lose_acknowledgement(connection):
        real_commit(connection)
        raise OperationalError(None, None, Exception("connection lost"))

    with monkeypatch.context() as fault:
        fault.setattr(dialect, "do_commit", lose_acknowledgement)
        response = proposal_client.post(
            "/api/matters",
            json={"matter_proposal_id": str(proposal.id)},
            headers=headers(proposal_client),
        )

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "confirmation_outcome_unknown"
    assert error["outcome_unknown"] is True
    assert error["retryable"] is False
    assert "Matter Ledger" in error["message"]
    assert proposal_client.get(f"/api/matter-proposals/{proposal.id}").status_code == 404
    assert proposal_client.get("/api/matters").json()[0]["external_reference"] == "Example/49"


def test_upload_review_duplicate_and_discard_with_exact_evidence(
    proposal_client, monkeypatch, tmp_path, tracked_upload_files,
):
    from private_client_graph.application import matter_proposals
    calls = []

    def extract(source, *, llm):
        calls.append(source)
        assert llm.max_retries == 0
        return ExtractionResult.model_validate({'relationships': [{
            'source_name': 'Alice Example', 'relationship_type': 'parent_of',
            'target_name': 'Ben Example', 'supporting_text': SOURCE,
        }]})

    monkeypatch.setenv('PCG_RUN_DIR', str(tmp_path))
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    response = submit(proposal_client)
    assert response.status_code == 201, response.text
    assert tracked_upload_files and all(file.closed for file in tracked_upload_files)
    proposal = response.json()
    location = response.headers['location']
    assert proposal['external_reference'] == 'Example/48'
    assert proposal['matter_title'] == 'Example family'
    assert proposal['authoritative_source'] == {'title': 'Fictional attendance note', 'text': SOURCE}
    assert proposal['proposed_graph']['evidence'][0]['supporting_text'] == SOURCE
    assert proposal_client.get(location).json() == proposal
    assert proposal_client.get('/api/matter-proposals').json() == [{
        'id': proposal['id'], 'external_reference': 'Example/48', 'matter_title': 'Example family',
    }]
    duplicate = submit(proposal_client, fields={**FIELDS, 'external_reference': 'example/48'})
    assert duplicate.status_code == 409
    assert duplicate.json()['error']['existing_resource'] == {
        'resource_kind': 'matter_proposal', 'resource_id': proposal['id'], 'location': location,
    }
    assert calls == [SOURCE]
    assert list(tmp_path.iterdir()) == []
    assert proposal_client.delete(location, headers=headers(proposal_client)).status_code == 204
    assert proposal_client.get(location).status_code == 404
    assert proposal_client.get('/api/matter-proposals').json() == []
    assert proposal_client.get('/api/matters').json() == []
    assert submit(proposal_client).status_code == 429


def test_security_and_validation_rejections_do_not_spend_an_attempt(proposal_client, monkeypatch):
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.proposal_allowance import quota_reset
    calls = []

    def extract(source, *, llm):
        calls.append(source)
        return ExtractionResult(relationships=[])

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    app = proposal_client.app
    anonymous = TestClient(app, base_url='https://testserver')
    anonymous.get('/api/matter-proposals')
    assert submit(anonymous).status_code == 401
    monkeypatch.setenv('PCG_GOOGLE_SUB_ALLOWLIST', 'someone-else')
    assert proposal_client.get('/api/matter-proposals').status_code == 403
    monkeypatch.setenv('PCG_GOOGLE_SUB_ALLOWLIST', 'test-subject')
    from google_boundary import sign_in
    assert sign_in(proposal_client).status_code == 303
    for invalid_headers in (
        {'origin': 'https://testserver'},
        {**headers(proposal_client), 'origin': 'https://untrusted.example'},
    ):
        assert proposal_client.post('/api/matter-proposals', data=FIELDS,
            files={'pdf': ('file.pdf', PDF.read_bytes())}, headers=invalid_headers).status_code == 403
    assert submit(proposal_client, fields={**FIELDS, 'synthetic_confirmation': 'false'}).status_code == 422
    assert submit(proposal_client, fields={**FIELDS, 'matter_title': '  '}).status_code == 422
    assert submit(proposal_client, pdf=b'invalid').status_code == 422
    assert calls == []
    assert quota_reset(limit=1, window_seconds=86400) is None
    response = submit(proposal_client)
    assert response.status_code == 201
    assert response.json()['proposed_graph'] == {'entities': [], 'relationships': [], 'evidence': []}
    assert calls == [SOURCE]
    assert quota_reset(limit=1, window_seconds=86400) is not None
    # Exhaustion never blocks review/discard, and reset timing is exposed.
    exhausted = submit(proposal_client, fields={**FIELDS, 'external_reference': 'new-reference'})
    assert exhausted.status_code == 429
    assert exhausted.json()['error']['resets_at'] is not None
    assert proposal_client.get(response.headers['location']).status_code == 200
    assert proposal_client.delete(response.headers['location'], headers=headers(proposal_client)).status_code == 204


def test_existing_matter_reference_resolves_without_provider(proposal_client, monkeypatch):
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.proposal_allowance import quota_reset
    from private_client_graph.persistence.seeds.evergreen import EVERGREEN_ID, seed_evergreen
    seed_evergreen()

    def unexpected(*args, **kwargs):
        raise AssertionError('An existing reference must never invoke the model')

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', unexpected)
    response = submit(proposal_client, fields={**FIELDS, 'external_reference': ' pc/2026/0142 '})
    assert response.status_code == 409
    assert response.json()['error']['existing_resource'] == {
        'resource_kind': 'matter', 'resource_id': str(EVERGREEN_ID), 'location': f'/api/matters/{EVERGREEN_ID}',
    }
    assert quota_reset(limit=1, window_seconds=86400) is None


@pytest.mark.parametrize('failure_kind,code,retryable', [
    ('transient', 'provider_failed', True),
    ('credentials', 'provider_failed', False),
    ('invalid_output', 'invalid_extraction', True),
    ('invalid_graph', 'invalid_graph', True),
])
def test_failed_analysis_consumes_one_attempt_without_saved_state(
    proposal_client, monkeypatch, failure_kind, code, retryable,
):
    import httpx
    from openai import APIConnectionError, AuthenticationError
    from langchain_core.exceptions import OutputParserException
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.proposal_allowance import quota_reset
    calls = []

    def extract(source, *, llm):
        calls.append(source)
        if failure_kind == 'transient':
            raise APIConnectionError(request=httpx.Request('POST', 'https://model.test'))
        if failure_kind == 'credentials':
            raise AuthenticationError('provider-secret', response=httpx.Response(401,
                request=httpx.Request('POST', 'https://model.test')), body=None)
        if failure_kind == 'invalid_output':
            raise OutputParserException('provider-secret')
        return ExtractionResult.model_validate({'relationships': [{
            'source_name': 'Alice Example', 'relationship_type': 'parent_of',
            'target_name': 'Ben Example', 'supporting_text': 'invented evidence',
        }]})

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    response = submit(proposal_client)
    error = response.json()['error']
    assert error['code'] == code
    assert error['retryable'] is retryable
    assert 'provider-secret' not in response.text
    assert calls == [SOURCE]
    assert quota_reset(limit=1, window_seconds=86400) is not None
    assert proposal_client.get('/api/matter-proposals').json() == []
    assert proposal_client.get('/api/matters').json() == []
    assert submit(proposal_client).status_code == 429
    assert calls == [SOURCE]


def test_model_construction_failure_does_not_spend_an_attempt(proposal_client, monkeypatch):
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.proposal_allowance import quota_reset

    calls = []

    def construct_model(**kwargs):
        calls.append('construct')
        raise ValueError('provider-secret')

    def extract(source, *, llm):
        calls.append('invoke')
        return ExtractionResult(relationships=[])

    monkeypatch.setattr(matter_proposals, 'ChatDeepSeek', construct_model)
    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    response = submit(proposal_client)

    assert response.status_code == 503
    assert response.json()['error']['code'] == 'analysis_unavailable'
    assert 'provider-secret' not in response.text
    assert calls == ['construct']
    assert quota_reset(limit=1, window_seconds=86400) is None
    assert proposal_client.get('/api/matter-proposals').json() == []


@pytest.mark.parametrize(
    'provider_status,retryable',
    [
        (400, False),
        (408, True),
        (429, True),
        (499, False),
        (500, True),
        (503, True),
    ],
)
def test_provider_http_failure_retryability_preserves_consumed_attempt(
    proposal_client, monkeypatch, provider_status, retryable,
):
    import httpx
    from openai import APIStatusError
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.proposal_allowance import quota_reset

    calls = []

    def extract(source, *, llm):
        calls.append(source)
        raise APIStatusError(
            'provider-secret',
            response=httpx.Response(
                provider_status,
                request=httpx.Request('POST', 'https://model.test'),
            ),
            body=None,
        )

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    response = submit(proposal_client)

    assert response.status_code == 502
    assert response.json()['error']['code'] == 'provider_failed'
    assert response.json()['error']['retryable'] is retryable
    assert 'provider-secret' not in response.text
    assert calls == [SOURCE]
    assert quota_reset(limit=1, window_seconds=86400) is not None
    assert proposal_client.get('/api/matter-proposals').json() == []
    assert submit(proposal_client).status_code == 429
    assert calls == [SOURCE]


def test_unknown_commit_is_resolved_by_reference_before_retry(proposal_client, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.database import database_engine
    calls = []

    def extract(source, *, llm):
        calls.append(source)
        return ExtractionResult(relationships=[])

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text', extract)
    dialect = database_engine().dialect
    real_commit = dialect.do_commit
    commits = []

    def lose_ack(connection):
        real_commit(connection)
        commits.append(1)
        if len(commits) == 2:  # allowance committed first; proposal commit acknowledgement is lost
            raise OperationalError(None, None, Exception('connection lost'))

    monkeypatch.setattr(dialect, 'do_commit', lose_ack)
    response = submit(proposal_client)
    assert response.status_code == 503, response.text
    assert response.json()['error']['outcome_unknown'] is True
    assert 'unknown' in response.json()['error']['message']
    retry = submit(proposal_client)
    assert retry.status_code == 409
    owner = retry.json()['error']['existing_resource']
    assert proposal_client.get(owner['location']).status_code == 200
    assert calls == [SOURCE]


def test_known_rollback_reports_no_saved_proposal(proposal_client, monkeypatch):
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError
    from private_client_graph.application import matter_proposals
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import find_reference
    from private_client_graph.persistence.proposal_allowance import quota_reset

    monkeypatch.setattr(matter_proposals, 'extract_relationships_from_text',
                        lambda source, *, llm: ExtractionResult(relationships=[]))
    engine = database_engine()

    def reject_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO matter_proposals'):
            raise IntegrityError(statement, parameters, Exception('database rejected insert'))

    event.listen(engine, 'before_cursor_execute', reject_insert)
    try:
        response = submit(proposal_client)
    finally:
        event.remove(engine, 'before_cursor_execute', reject_insert)
    assert response.status_code == 503
    error = response.json()['error']
    assert error['outcome_unknown'] is False
    assert 'No Matter Proposal was saved' in error['message']
    assert proposal_client.get('/api/matter-proposals').json() == []
    assert find_reference('Example/48') is None
    assert quota_reset(limit=1, window_seconds=86400) is not None
