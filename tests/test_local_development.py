"""Public-boundary coverage for the protected local-development server."""

from urllib.parse import urlsplit

from fastapi.testclient import TestClient


def _configure_local_environment(monkeypatch):
    values = {
        "PCG_GOOGLE_CLIENT_ID": "local-development.apps.googleusercontent.com",
        "PCG_GOOGLE_CLIENT_SECRET": "local-development-google-secret",
        "PCG_SESSION_SECRET": "local-development-session-secret-at-least-32-characters",
        "PCG_TRUSTED_ORIGIN": "https://localhost:8443",
        "PCG_GOOGLE_SUB_ALLOWLIST": "local-development-subject",
        "PCG_SESSION_SECONDS": "3600",
        "PCG_PROPOSAL_ANALYSIS_LIMIT": "1000",
        "PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS": "86400",
        "DEEPSEEK_API_KEY": "local-development-model-substitute",
        "DATABASE_URL": "postgresql://pcg:local-only@database/pcg",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_local_app_uses_real_callback_and_session(monkeypatch):
    _configure_local_environment(monkeypatch)

    from local_development.server import create_local_app

    from private_client_graph.application import matter_proposals

    for name in ("_extract_proposal", "_extract_proposal_sources"):
        monkeypatch.setattr(matter_proposals, name, getattr(matter_proposals, name))
    app = create_local_app(origin="https://localhost:8443")
    client = TestClient(app, base_url="https://localhost:8443")

    assert client.get("/api/access").json() == {"can_write": False, "sign_in_available": True}
    login = client.get("/auth/login?next=/app", follow_redirects=False)
    provider = client.get(login.headers["location"], follow_redirects=False)
    callback = client.get(provider.headers["location"], follow_redirects=False)

    assert urlsplit(provider.headers["location"]).path == "/auth/callback"
    assert callback.status_code == 303
    assert callback.headers["location"] == "/app"
    assert "__Host-pcg-session" in callback.headers["set-cookie"]


def test_discovery_actions_are_private_and_bound_to_the_login(monkeypatch, caplog):
    import logging

    from local_development.server import create_local_app
    from private_client_graph.api.app import create_app
    from private_client_graph.api.auth import CSRF_COOKIE
    from private_client_graph.application import matter_proposals

    _configure_local_environment(monkeypatch)
    for name in ("_extract_proposal", "_extract_proposal_sources"):
        monkeypatch.setattr(matter_proposals, name, getattr(matter_proposals, name))
    origin = "https://localhost:8443"
    root = "/api/matter-proposals/discovery/"
    app = create_local_app()
    client = TestClient(app, base_url=origin)
    def post(endpoint, body):
        return client.post(root + endpoint, json=body, headers={
            "origin": origin, "x-csrftoken": client.cookies[CSRF_COOKIE]})

    client.get("/api/access")
    for endpoint in ("start", "inspect", "follow-up", "preview", "import"):
        assert post(endpoint, {}).status_code == 401
        assert client.get(root + endpoint).status_code in {404, 405}
    client.get("/auth/login")
    assert client.get("/api/access").json()["workspace_discovery"] is True
    body = {"terms": "Alder Trust", "folder": "folder-1", "label": "alder-label"}
    assert post("start", {**body, "label": "INBOX"}).status_code == 422
    caplog.set_level(logging.INFO, logger="httpx2")
    started = post("start", body).json()
    private = {"session": started["session"]}
    revision = started["view"]["revision"]
    post("inspect", private).raise_for_status()
    old = {**private, "revision": revision, "query": "Alice Reed"}
    first = post("follow-up", old)
    assert first.json()["messages"] == ["08"]
    assert post("follow-up", old).json() == first.json()
    preview = post("preview", {**private, "candidates": [{"kind": "email", "id": "06"}]})
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "no-store"
    assert "Mara Voss" in preview.json()["sources"][0]["text"]
    assert all(value not in caplog.text for value in ("Alice Reed", "Mara Voss", "googleapis.com", private["session"]))
    assert post("import", {**private, "preview": preview.json()["token"],
                           "metadata": {"external_reference": "LOCAL", "matter_title": "Test"}}).status_code == 422
    post_login = TestClient(app, base_url=origin)
    post_login.get("/auth/login")
    assert post_login.post(root + "inspect", json=private, headers={
        "origin": origin, "x-csrftoken": post_login.cookies[CSRF_COOKIE]}).status_code == 404
    assert not any(route.path.startswith(root) for route in create_app().routes if hasattr(route, "path"))
