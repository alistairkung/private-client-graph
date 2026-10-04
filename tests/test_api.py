from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from private_client_graph.api.app import app, create_app


CASE = Path(__file__).resolve().parents[1] / "cases" / "case_01"
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


def test_case_detail_is_authoritative_and_sample_builds_real_graph(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path / "runs"))
    detail = client.get("/api/showcase/case-01")
    assert detail.status_code == 200
    assert detail.json()["source_text"] == (CASE / "source.txt").read_text()
    assert "synthetic" in detail.json()["notice"].lower()
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "sample"})
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {"execution", "graph"}
    assert result["execution"] == {"mode": "sample", "run_artifact_id": None}
    assert len(result["graph"]["relationships"]) == 6
    assert len(result["graph"]["entities"]) == 5
    assert all(item["document"] == "source.txt" for item in result["graph"]["evidence"])
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize(
    "body", [{}, {"mode": "other"}, {"mode": "sample", "source_text": "changed"}]
)
def test_request_accepts_only_an_explicit_mode(body):
    response = client.post("/api/showcase/case-01/analysis", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["stage"] == "request"


@pytest.mark.parametrize(
    "missing_file,stage",
    [("source.txt", "source"), ("expected_extraction.json", "sample")],
)
def test_unavailable_case_files_have_stage_aware_errors(
    tmp_path, monkeypatch, missing_file, stage
):
    from private_client_graph.application import case_analysis

    for filename in ("source.txt", "expected_extraction.json"):
        if filename != missing_file:
            (tmp_path / filename).write_text((CASE / filename).read_text())
    monkeypatch.setattr(case_analysis, "CASE", tmp_path)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "sample"})
    assert response.status_code == 500
    assert response.json()["error"]["stage"] == stage
    assert response.json()["error"]["retryable"] is False
