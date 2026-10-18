from fastapi.testclient import TestClient

from private_client_graph.api.app import app, create_app


client = TestClient(app)


def test_healthcheck_reports_unavailable_without_database_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_built_frontend_is_served_from_the_application(tmp_path, authenticated_client):
    (tmp_path / "index.html").write_text("<h1>Deployed workspace</h1>")
    deployed_client = authenticated_client(create_app(tmp_path))

    for path in ("/", "/app", "/app/", "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369"):
        response = deployed_client.get(path)
        assert response.status_code == 200
        assert "Deployed workspace" in response.text

    assert deployed_client.get("/api/case-01").status_code == 404
    assert deployed_client.post("/api/case-01/analysis", json={"mode": "sample"}).status_code in (404, 405)
    assert deployed_client.get("/unknown").status_code == 404


def test_retired_showcase_analysis_routes_are_unavailable(monkeypatch):
    from private_client_graph.pipeline import Pipeline

    def forbidden(*args, **kwargs):
        raise AssertionError("Retired HTTP routes must not execute analysis")

    monkeypatch.setattr(Pipeline, "run", forbidden)
    monkeypatch.setattr(Pipeline, "run_from_extraction", forbidden)
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/api/showcase/case-01", "/api/showcase/case-01/analysis"):
        assert path not in paths
        assert client.get(path).status_code == 404
        for mode in ("sample", "live"):
            assert client.post(path, json={"mode": mode}).status_code in {404, 405}
