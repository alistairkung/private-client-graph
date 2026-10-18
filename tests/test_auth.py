"""Public synthetic reads and fail-closed practitioner mutations."""
import base64
import json
import time

import pytest
from fastapi.testclient import TestClient
from google_boundary import make_google_boundary, sign_in
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import SESSION_COOKIE, CSRF_COOKIE


@pytest.fixture
def google_client(tmp_path, monkeypatch):
    from private_client_graph.api import app as api_module
    from private_client_graph.api import matter_proposals
    monkeypatch.setattr(api_module, "list_matters", lambda: [])
    monkeypatch.setattr(matter_proposals, "list_proposals", lambda: [])
    (tmp_path / "index.html").write_text("public shell")
    app = create_app(tmp_path)
    google = make_google_boundary()
    google.install(app)
    return TestClient(app, base_url="https://testserver", follow_redirects=False), google


def assert_public_reads(client):
    assert client.get("/app").status_code == 200
    for path in ("/api/matters", "/api/matter-proposals"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == []


def headers(client):
    return {"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]}


def test_anonymous_reads_and_access_do_not_claim_identity(google_client):
    client, _ = google_client
    assert_public_reads(client)
    response = client.get("/api/access")
    assert response.json() == {"can_write": False, "sign_in_available": True}
    assert response.headers["cache-control"] == "no-store"
    assert SESSION_COOKIE not in client.cookies


def test_google_login_allowlist_removal_and_logout(google_client, monkeypatch):
    client, _ = google_client
    response = sign_in(client, next_path="/app/matters/example")
    assert response.status_code == 303
    assert response.headers["location"] == "/app/matters/example"
    cookie = response.headers["set-cookie"]
    assert "httponly" in cookie.lower() and "secure" in cookie.lower()
    payload = json.loads(base64.b64decode(client.cookies[SESSION_COOKIE].split(".")[0]))
    assert set(payload) == {"sub", "expires"}
    assert client.get("/api/access").json()["can_write"] is True
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "another-subject")
    assert_public_reads(client)
    assert client.get("/api/access").json()["can_write"] is False
    assert client.post("/api/matters", headers=headers(client)).status_code == 403
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "test-subject")
    assert sign_in(client).status_code == 303
    assert client.post("/auth/logout", headers=headers(client)).status_code == 204
    assert_public_reads(client)
    assert client.get("/api/access").json()["can_write"] is False


@pytest.mark.parametrize("claims", [
    {"iss": "https://evil.example"}, {"aud": "other-client"},
    {"exp": 1}, {"nonce": "incorrect"}, {"sub": ""},
])
def test_invalid_google_identity_never_creates_write_access(google_client, claims):
    client, google = google_client
    google.claims = claims
    assert sign_in(client).status_code == 401
    assert_public_reads(client)
    assert client.get("/api/access").json()["can_write"] is False


def test_invalid_signature_and_state(google_client):
    client, google = google_client
    google.bad_signature = True
    assert sign_in(client).status_code == 401
    assert client.get("/auth/callback?state=unknown&code=anything").status_code == 401


def test_subject_not_email_authorizes(google_client):
    client, google = google_client
    google.claims = {"sub": "not-allowed", "email": "test-subject"}
    assert sign_in(client).status_code == 403
    assert_public_reads(client)
    assert client.get("/api/access").json()["can_write"] is False


def test_expired_session_preserves_reads_and_revokes_writes(google_client, monkeypatch):
    client, _ = google_client
    assert sign_in(client).status_code == 303
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now + 800)
    assert client.get("/api/access").json()["can_write"] is True
    monkeypatch.setattr(time, "time", lambda: now + 901)
    assert_public_reads(client)
    assert client.get("/api/access").json()["can_write"] is False
    assert client.post("/api/matters", headers=headers(client)).status_code == 401


@pytest.mark.parametrize("state", ["anonymous", "expired", "denied", "tampered", "allowed"])
def test_security_gates_precede_every_mutation_side_effect(google_client, monkeypatch, state):
    from private_client_graph.api import app as api_module
    from private_client_graph.api import matter_proposals
    client, _ = google_client
    if state in {"expired", "denied", "allowed"}:
        assert sign_in(client).status_code == 303
    if state == "expired":
        now = time.time()
        monkeypatch.setattr(time, "time", lambda: now + 901)
    if state == "denied":
        monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "another-subject")
    if state == "tampered":
        client.cookies.set(SESSION_COOKIE, "forged")
    client.get("/app")  # Issue a CSRF cookie even to anonymous readers.
    def forbidden(*args, **kwargs):
        pytest.fail("Mutation side effect ran before security gates")
    monkeypatch.setattr(api_module, "confirm_matter", forbidden)
    monkeypatch.setattr(matter_proposals, "analyse_proposal", forbidden)
    monkeypatch.setattr(matter_proposals, "analyse_proposal_sources", forbidden)
    monkeypatch.setattr(matter_proposals, "discard_proposal", forbidden)
    monkeypatch.setattr(matter_proposals, "proposal_form", forbidden)
    routes = [("POST", "/api/matters"), ("POST", "/api/matter-proposals"),
              ("DELETE", "/api/matter-proposals/00000000-0000-0000-0000-000000000001")]
    for index, (method, path) in enumerate(routes):
        for bad_headers in ({}, {"origin": "https://testserver"},
                            {**headers(client), "origin": "https://evil.example"},
                            {**headers(client), "x-csrftoken": "forged"},
                            {**headers(client), "host": "evil.example"}):
            assert client.request(method, path, headers=bad_headers).status_code in {400, 403}
        if state != "allowed":
            expected = 403 if state == "denied" and index == 0 else 401
            assert client.request(method, path, headers=headers(client)).status_code == expected


@pytest.mark.parametrize("name,value", [
    ("PCG_GOOGLE_CLIENT_ID", ""), ("PCG_GOOGLE_CLIENT_SECRET", ""),
    ("PCG_SESSION_SECRET", "short"), ("PCG_SESSION_SECONDS", "0"),
    ("PCG_SESSION_SECONDS", "forever"), ("PCG_TRUSTED_ORIGIN", "http://testserver"),
    ("PCG_TRUSTED_ORIGIN", "https://testserver/path"), ("PCG_GOOGLE_SUB_ALLOWLIST", ""),
    ("PCG_TRUSTED_ORIGIN", "https://*"), ("PCG_TRUSTED_ORIGIN", "https://bad host"),
    ("PCG_TRUSTED_ORIGIN", "https://testserver:99999"),
])
def test_bad_auth_configuration_preserves_reads_and_closes_writes(google_client, monkeypatch, tmp_path, name, value):
    monkeypatch.setenv(name, value)
    # Check both configuration becoming invalid and invalid initial configuration.
    clients = [google_client[0], TestClient(create_app(tmp_path), base_url="https://testserver")]
    for client in clients:
        assert_public_reads(client)
        assert client.get("/api/access").json() == {"can_write": False, "sign_in_available": False}
        assert client.get("/auth/login").status_code == 503
        for method, path in (("POST", "/api/matters"), ("POST", "/api/matter-proposals"),
                             ("DELETE", "/api/matter-proposals/example")):
            assert client.request(method, path).status_code in {403, 503}


def test_unsafe_return_url_is_replaced(google_client):
    client, _ = google_client
    assert sign_in(client, next_path="https://evil.example").headers["location"] == "/app"
