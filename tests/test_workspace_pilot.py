"""Offline pilot contract through the protected HTTP boundary."""

from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from httpx2 import MockTransport, Response

from google_boundary import make_google_boundary, sign_in
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE

ROOT = "/api/matter-proposals/discovery/"
CALLBACK = "/auth/workspace/callback"
SCOPES = "openid https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/drive.readonly"


@pytest.fixture
def pilot(monkeypatch):
    config = dict(
        ENABLED="true",
        CLIENT_ID="pilot.apps.googleusercontent.com",
        CLIENT_SECRET="pilot-secret",
        SUBJECT="synthetic-sub",
        MAILBOX="pilot@example.test",
        FOLDER="pilot-folder",
        LABEL="pilot-label",
        FOLDER_NAME="Alder Trust",
        LABEL_NAME="Alder correspondence",
        FILE_IDS="appointment",
        MESSAGE_IDS="06",
    )
    for key, value in config.items():
        monkeypatch.setenv("PCG_WORKSPACE_" + key, value)
    app = create_app()
    make_google_boundary().install(app)
    client = TestClient(app, base_url="https://testserver", follow_redirects=False)
    assert sign_in(client).status_code == 303
    return client, app


def post(client, path, body=None):
    return client.post(
        ROOT + path,
        json=body or {},
        headers={"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]},
    )


def test_private_connection_is_separate_from_sign_in(pilot):
    client, _ = pilot
    assert client.get("/api/access").json()["workspace_connection"] is True
    assert post(client, "connection").json()["connected"] is False
    assert (
        post(
            client, "start", {"terms": "Alder Trust", "label": "pilot-label", "folder": "pilot-folder"}
        ).status_code
        == 409
    )


def install_google(app, *, subject="synthetic-sub", scopes=SCOPES):
    from local_development.google import GoogleBoundary

    google = GoogleBoundary(subject=subject, client_id="pilot.apps.googleusercontent.com")

    def respond(request):
        response = google.respond(request)
        if request.url.path == "/token":
            assert b"code_verifier=" in request.content
            return Response(200, json={**response.json(), "expires_in": 300, "scope": scopes})
        return response

    app.state.workspace_pilot.oauth.client_kwargs["transport"] = MockTransport(respond)


def begin(client):
    response = post(client, "connect")
    assert response.status_code == 200
    params = parse_qs(urlsplit(response.json()["url"]).query)
    assert params["access_type"] == ["online"] and params["code_challenge_method"] == ["S256"]
    assert set(params["scope"][0].split()) == set(SCOPES.split())
    return {"state": params["state"][0], "code": params["nonce"][0]}


@pytest.mark.parametrize(
    "subject,scopes,outcome",
    [
        ("synthetic-sub", SCOPES, "ready"),
        ("other", SCOPES, "account"),
        ("synthetic-sub", "openid", "permissions"),
    ],
)
def test_verified_grant_and_one_use_callback(pilot, subject, scopes, outcome):
    client, app = pilot
    install_google(app, subject=subject, scopes=scopes)
    params = begin(client)
    assert client.get(CALLBACK, params=params).headers["location"].endswith("=" + outcome)
    assert post(client, "connection").json()["connected"] is (outcome == "ready")
    assert client.get(CALLBACK, params=params).headers["location"].endswith("=invalid")
    assert "local-google-access-token" not in str(client.cookies)


def test_item_denial_preserves_connection_but_revocation_retires_previous_search(pilot):
    client, app = pilot
    install_google(app)
    status = 200
    reads = []

    def respond(request):
        assert request.headers["authorization"] == "Bearer local-google-access-token-never-store"
        path = request.url.path
        reads.append(path)
        if path.endswith("/messages"):
            return Response(status, json={"messages": [{"id": "stray"}, {"id": "06"}]})
        if path.endswith("/files"):
            row = {
                "parents": ["pilot-folder"],
                "mimeType": "application/pdf",
                "trashed": False,
                "version": "1",
                "name": "Test",
            }
            return Response(200, json={"files": [dict(row, id="appointment"), dict(row, id="stray")]})
        return Response(403)

    app.state.workspace_pilot.transport = MockTransport(respond)
    client.get(CALLBACK, params=begin(client))
    body = {"terms": "Alder Trust", "label": "pilot-label", "folder": "pilot-folder"}
    start = post(client, "start", body).json()
    assert start["view"]["returned_messages"] == ["06"] and start["view"]["failed"] == ["06"]
    assert [f["id"] for f in start["view"]["files"]] == ["appointment"]
    assert all("stray" not in path for path in reads)
    selection = {"session": start["session"], "candidates": [{"kind": "pdf", "id": "appointment"}]}
    assert post(client, "preview", selection).json()["error"]["code"] == "source_unavailable"
    assert post(client, "connection").json()["connected"]
    status = 401
    assert post(client, "start", body).json()["error"]["code"] == "workspace_reconnect"
    assert not post(client, "connection").json()["connected"]
    client.get(CALLBACK, params=begin(client))
    assert post(client, "preview", selection).status_code == 409


def test_logout_and_expiry_cannot_resume_private_access(pilot, monkeypatch):
    client, app = pilot
    install_google(app)
    client.get(CALLBACK, params=begin(client))
    expires = post(client, "connection").json()["expires"]
    with monkeypatch.context() as clock:
        clock.setattr("private_client_graph.api.workspace_pilot.time", lambda: expires + 1)
        assert not post(client, "connection").json()["connected"]
    params = begin(client)
    headers = {"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]}
    client.post("/auth/logout", headers=headers)
    assert client.get(CALLBACK, params=params).status_code == 401
    assert post(client, "connection").status_code == 401


def test_oauth_transaction_cannot_cross_logins_or_survive_logout(pilot):
    from private_client_graph.api.auth import SESSION_COOKIE

    client, app = pilot
    install_google(app)
    params = begin(client)
    other = TestClient(app, base_url="https://testserver", follow_redirects=False)
    sign_in(other)
    assert other.get(CALLBACK, params=params).headers["location"].endswith("=invalid")
    old_cookie = client.cookies[SESSION_COOKIE]
    headers = {"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]}
    assert client.post("/auth/logout", headers=headers).status_code == 204
    client.cookies.set(SESSION_COOKIE, old_cookie, domain="testserver.local", path="/")
    assert post(client, "connect").status_code == 401
    assert client.get(CALLBACK, params=params).status_code == 401


def test_workspace_actions_require_origin_csrf_and_current_allowlist(pilot, monkeypatch):
    client, _ = pilot
    assert client.post(ROOT + "connect", json={}).status_code == 403
    assert (
        client.post(
            ROOT + "connection",
            headers={"origin": "https://elsewhere.test", "x-csrftoken": client.cookies[CSRF_COOKIE]},
        ).status_code
        == 403
    )
    monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "other-sub")
    assert post(client, "connection").status_code == 403
