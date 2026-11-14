"""Offline pilot contract through the protected HTTP boundary."""

import pytest
from fastapi.testclient import TestClient
from httpx2 import MockTransport, Response

from google_boundary import make_google_boundary, sign_in
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE

from workspace_pilot_fixture import CALLBACK, ROOT, SCOPES, begin, install_google, pilot, post, ready_publication


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


@pytest.mark.parametrize(
    "case,outcome", [("cancel", "cancelled"), ("exchange", "invalid"), ("nonce", "invalid")]
)
def test_failed_consent_does_not_establish_a_grant(pilot, case, outcome):
    client, app = pilot
    install_google(app, fail_exchange=case == "exchange")
    params = begin(client)
    if case == "cancel":
        params = {"state": params["state"], "error": "access_denied"}
    elif case == "nonce":
        params["code"] = "different-nonce"
    assert client.get(CALLBACK, params=params).headers["location"].endswith("=" + outcome)
    assert not post(client, "connection").json()["connected"]


@pytest.mark.parametrize(
    "envelope",
    [
        {"errors": [{"reason": "insufficientPermissions"}]},
        {"details": [{"reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT"}]},
    ],
)
def test_explicit_grant_level_403_retires_connection(pilot, envelope):
    client, app = pilot
    install_google(app)
    app.state.workspace_pilot.transport = MockTransport(lambda _: Response(403, json={"error": envelope}))
    client.get(CALLBACK, params=begin(client))
    body = {"terms": "Alder Trust", "label": "pilot-label", "folder": "pilot-folder"}
    assert post(client, "start", body).json()["error"]["code"] == "workspace_reconnect"
    assert not post(client, "connection").json()["connected"]


def test_restart_requires_new_login_and_grant_and_rejects_previous_preview(pilot):
    original, _ = pilot
    _, old_import = ready_publication(pilot)
    restart = create_app()
    make_google_boundary().install(restart)
    client = TestClient(restart, base_url="https://testserver", cookies=original.cookies)
    response = post(client, "connection")
    assert response.status_code == 401 and response.json()["error"]["code"] == "sign_in_required"
    assert not client.get("/api/access").json()["can_write"]
    assert sign_in(client).status_code == 303
    assert not post(client, "connection").json()["connected"]
    assert post(client, "import", old_import).json()["error"]["code"] == "workspace_reconnect"
    install_google(restart)
    client.get(CALLBACK, params=begin(client), follow_redirects=False)
    assert post(client, "connection").json()["connected"]
    assert post(client, "import", old_import).json()["error"]["code"] == "unknown_discovery"


def test_private_http_diagnostics_are_redacted_and_ordinary_logs_resume(pilot, caplog):
    import logging
    from private_client_graph.api.workspace_logging import private_request

    client, app = pilot
    transport = logging.getLogger("httpx2")
    auth = logging.getLogger("authlib.oauth2.client")
    access = logging.getLogger("uvicorn.access")

    def respond(request):
        assert private_request.get()
        transport.warning("private transport diagnostic")
        auth.warning("private authorization diagnostic")
        access.warning("%s %s %s", "client", "GET", CALLBACK + "?code=private")
        return Response(503)

    app.state.workspace_pilot.oauth.client_kwargs["transport"] = MockTransport(respond)
    assert post(client, "connect").status_code == 503
    auth.warning("ordinary auth diagnostic")
    access.warning("%s %s %s", "client", "GET", "/health")
    assert "ordinary auth diagnostic" in caplog.text and "/health" in caplog.text
    assert "private transport" not in caplog.text and "private authorization" not in caplog.text
    assert "?code=private" not in caplog.text


def test_disconnect_retires_ready_preview_and_reconnect_requires_another_search(pilot):
    client, _ = pilot
    old_generation, publish = ready_publication(pilot)
    assert not post(client, "disconnect").json()["connected"]
    assert client.get("/api/access").json()["can_write"]
    client.get(CALLBACK, params=begin(client))
    assert post(client, "connection").json()["generation"] != old_generation
    assert post(client, "import", publish).json()["error"]["code"] == "unknown_discovery"


def test_anonymous_pilot_has_no_discovery_capability_or_private_reads(pilot):
    _, app = pilot
    anonymous = TestClient(app, base_url="https://testserver")
    assert "workspace_discovery" not in anonymous.get("/api/access").json()
    for path in ("connection", "connect", "preview", "import"):
        assert post(anonymous, path).status_code == 401
