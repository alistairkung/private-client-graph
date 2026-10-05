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
        "PCG_SHOWCASE_LIVE_ENABLED": "false",
        "DEEPSEEK_API_KEY": "local-development-model-substitute",
        "DATABASE_URL": "postgresql://pcg:local-only@database/pcg",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_local_app_uses_real_callback_and_session(monkeypatch):
    _configure_local_environment(monkeypatch)

    from local_development.server import create_local_app

    app = create_local_app(origin="https://localhost:8443")
    client = TestClient(app, base_url="https://localhost:8443")

    protected = client.get("/app", follow_redirects=False)
    assert protected.status_code == 303
    login = client.get(protected.headers["location"], follow_redirects=False)
    provider = client.get(login.headers["location"], follow_redirects=False)
    callback = client.get(provider.headers["location"], follow_redirects=False)

    assert urlsplit(provider.headers["location"]).path == "/auth/callback"
    assert callback.status_code == 303
    assert callback.headers["location"] == "/app"
    assert "__Host-pcg-session" in callback.headers["set-cookie"]
