import pytest

from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app


def test_provider_key_alone_leaves_live_disabled(monkeypatch):
    monkeypatch.delenv("PCG_SHOWCASE_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    client = TestClient(create_app())
    assert client.get("/api/showcase/case-01").json()["live_analysis"] == {
        "state": "disabled", "resets_at": None,
    }
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code == 503
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200


@pytest.mark.parametrize("name,value", [
    ("PCG_SHOWCASE_LIVE_LIMIT", None),
    ("PCG_SHOWCASE_LIVE_LIMIT", "0"),
    ("PCG_SHOWCASE_LIVE_LIMIT", "-1"),
    ("PCG_SHOWCASE_LIVE_LIMIT", "1.5"),
    ("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", None),
    ("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", "0"),
    ("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", "nan"),
    ("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", "2147483648"),
    ("PCG_SHOWCASE_LIVE_ENABLED", "yes"),
    ("DEEPSEEK_API_KEY", ""),
])
def test_invalid_enabled_configuration_fails_when_creating_app(monkeypatch, name, value):
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_ENABLED", "true")
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_LIMIT", "2")
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", "3600")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    if value is None:
        monkeypatch.delenv(name, raising=False)
    else:
        monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        create_app()


def test_disabled_defaults_need_neither_provider_nor_quota_configuration(monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "PCG_SHOWCASE_LIVE_ENABLED", "PCG_SHOWCASE_LIVE_LIMIT", "PCG_SHOWCASE_LIVE_WINDOW_SECONDS"):
        monkeypatch.delenv(name, raising=False)
    client = TestClient(create_app())
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "disabled"
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200
