from fastapi.testclient import TestClient
from private_client_graph.api.app import create_app


def test_practitioner_boundary_is_protected_even_for_unknown_routes(tmp_path):
    (tmp_path / "index.html").write_text("private shell")
    client = TestClient(create_app(tmp_path), base_url="https://testserver", follow_redirects=False)
    for path in ("/app", "/app/future", "/app/matters/example"):
        response = client.get(path)
        assert response.status_code == 303
        assert response.headers["location"].startswith("/auth/login")
    for path in ("/api/matters", "/api/matters/future", "/api/matter-proposals", "/api/matter-proposals/future"):
        assert client.get(path).status_code == 401
    assert client.get("/api/showcase/case-01").status_code == 200

import base64
import json
import time
import pytest
from google_boundary import GoogleBoundary, sign_in
from private_client_graph.api.auth import SESSION_COOKIE, CSRF_COOKIE


@pytest.fixture
def google_client(tmp_path):
    (tmp_path / "index.html").write_text("private shell")
    app = create_app(tmp_path)
    google = GoogleBoundary()
    google.install(app)
    return TestClient(app, base_url="https://testserver", follow_redirects=False), google


def test_google_login_session_allowlist_removal_and_logout(google_client, monkeypatch):
    client, google = google_client
    response = sign_in(client, next_path="/app/matters/example")
    assert response.status_code == 303
    assert response.headers["location"] == "/app/matters/example"
    cookie = response.headers["set-cookie"]
    assert "httponly" in cookie.lower() and "secure" in cookie.lower()
    payload = json.loads(base64.b64decode(client.cookies[SESSION_COOKIE].split(".")[0]))
    assert set(payload) == {"sub", "expires"}
    assert client.get("/app").status_code == 200
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "another-subject")
    assert client.get("/api/matters").status_code == 403
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "test-subject")
    assert sign_in(client).status_code == 303
    headers = {"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]}
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/matters").status_code == 401


@pytest.mark.parametrize("claims", [
    {"iss": "https://evil.example"}, {"aud": "other-client"},
    {"exp": 1}, {"nonce": "incorrect"}, {"sub": ""},
])
def test_invalid_google_identity_never_creates_session(google_client, claims):
    client, google = google_client
    google.claims = claims
    assert sign_in(client).status_code == 401
    assert client.get("/api/matters").status_code == 401


def test_invalid_signature_and_state(google_client):
    client, google = google_client
    google.bad_signature = True
    assert sign_in(client).status_code == 401
    assert client.get("/auth/callback?state=unknown&code=anything").status_code == 401


def test_subject_not_email_authorizes(google_client):
    client, google = google_client
    google.claims = {"sub": "not-allowed", "email": "test-subject"}
    assert sign_in(client).status_code == 403
    assert client.get("/api/matters").status_code == 401


def test_session_expires_despite_activity(google_client, monkeypatch):
    client, _ = google_client
    assert sign_in(client).status_code == 303
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now + 800)
    assert client.get("/app").status_code == 200
    monkeypatch.setattr(time, "time", lambda: now + 901)
    assert client.get("/api/matters").status_code == 401


def test_csrf_and_origin_are_independent_gates(google_client):
    client, _ = google_client
    assert sign_in(client).status_code == 303
    token = client.cookies[CSRF_COOKIE]
    for path in ("/auth/logout", "/api/matters", "/api/matter-proposals"):
        assert client.post(path, headers={"origin": "https://testserver"}).status_code == 403
        assert client.post(path, headers={"origin": "https://evil.example", "x-csrftoken": token}).status_code == 403
        assert client.post(path, headers={"x-csrftoken": token}).status_code == 403
    assert client.post("/api/matter-proposals", headers={
        "origin": "https://testserver", "x-csrftoken": token,
    }).status_code == 422  # passed security; required multipart form is missing
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200
    assert client.get("/app", headers={"host": "evil.example"}).status_code == 400


@pytest.mark.parametrize("name,value", [
    ("PCG_GOOGLE_CLIENT_ID", ""), ("PCG_GOOGLE_CLIENT_SECRET", ""),
    ("PCG_SESSION_SECRET", "short"), ("PCG_SESSION_SECONDS", "0"),
    ("PCG_SESSION_SECONDS", "forever"), ("PCG_TRUSTED_ORIGIN", "http://testserver"),
    ("PCG_TRUSTED_ORIGIN", "https://testserver/path"), ("PCG_GOOGLE_SUB_ALLOWLIST", ""),
])
def test_bad_configuration_fails_readiness_and_private_requests(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    client = TestClient(create_app(), base_url="https://testserver")
    assert client.get("/health").status_code == 503
    assert client.get("/app").status_code == 503
    assert client.get("/api/matters").status_code == 503


@pytest.mark.parametrize("origin", ["https://*", "https://bad host", "https://testserver:99999"])
def test_invalid_trusted_hosts_fail_closed(monkeypatch, origin):
    monkeypatch.setenv("PCG_TRUSTED_ORIGIN", origin)
    client = TestClient(create_app(), base_url="https://testserver")
    assert client.get("/app").status_code == 503


def test_tampered_session_and_csrf_are_rejected(google_client):
    client, _ = google_client
    assert sign_in(client).status_code == 303
    assert client.post("/auth/logout", headers={
        "origin": "https://testserver", "x-csrftoken": "forged",
    }).status_code == 403
    client.cookies.clear()
    client.cookies.set(SESSION_COOKIE, "forged")
    assert client.get("/api/matters").status_code == 401


def test_empty_current_allowlist_and_unsafe_return_url(google_client, monkeypatch):
    client, _ = google_client
    assert sign_in(client, next_path="https://evil.example").headers["location"] == "/app"
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "")
    assert client.get("/api/matters").status_code == 503
    assert client.get("/health").status_code == 503
