from pathlib import Path

from fastapi.testclient import TestClient

from private_client_graph.api.app import app, create_app


CASE = Path(__file__).resolve().parents[1] / "cases" / "case_01"
client = TestClient(app)


def test_healthcheck_reports_unavailable_without_database_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_built_frontend_is_served_from_the_application(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Deployed workspace</h1>")
    deployed_client = TestClient(create_app(tmp_path))

    for path in ("/", "/app", "/app/"):
        response = deployed_client.get(path)
        assert response.status_code == 200
        assert "Deployed workspace" in response.text

    assert deployed_client.get("/api/case-01").status_code == 404
    assert deployed_client.post("/api/case-01/analysis", json={"mode": "sample"}).status_code in (404, 405)
    assert deployed_client.get("/api/matters/ff985caf-60c5-4e65-a238-f3c26381c369").status_code == 404
    assert deployed_client.get("/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369").status_code == 404
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


def test_live_analysis_persists_offline_compatible_extraction(tmp_path, monkeypatch):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    extraction = ExtractionResult.model_validate_json(
        (CASE / "expected_extraction.json").read_text()
    )
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(case_analysis, "extract_live", lambda: extraction)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 200
    result = response.json()
    assert result["execution"]["mode"] == "live"
    artifact = tmp_path / result["execution"]["run_artifact_id"]
    assert ExtractionResult.model_validate_json(artifact.read_text()) == extraction
    assert len(result["graph"]["relationships"]) == 6
    assert set(result) == {"execution", "graph"}


def test_rejected_live_extraction_is_saved_before_graph_failure(tmp_path, monkeypatch):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    extraction = ExtractionResult.model_validate_json(
        (CASE / "expected_extraction.json").read_text()
    )
    extraction.relationships[0].supporting_text = "Not in the authoritative source"
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(case_analysis, "extract_live", lambda: extraction)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 422
    assert set(response.json()) == {"error"}
    error = response.json()["error"]
    assert error["stage"] == "graph"
    assert error["retryable"] is False
    assert (
        ExtractionResult.model_validate_json(
            (tmp_path / error["run_artifact_id"]).read_text()
        )
        == extraction
    )


import httpx
import pytest
from openai import APIConnectionError, AuthenticationError, RateLimitError


@pytest.mark.parametrize(
    "failure,retryable",
    [
        (
            APIConnectionError(request=httpx.Request("POST", "https://provider.test")),
            True,
        ),
        (
            RateLimitError(
                "secret detail",
                response=httpx.Response(
                    429, request=httpx.Request("POST", "https://provider.test")
                ),
                body=None,
            ),
            True,
        ),
        (
            AuthenticationError(
                "secret detail",
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://provider.test")
                ),
                body=None,
            ),
            False,
        ),
        (ValueError("secret configuration"), False),
    ],
)
def test_provider_failure_has_no_retry_fallback_or_artifact(
    failure, retryable, tmp_path, monkeypatch
):
    from private_client_graph.application import case_analysis

    attempts = []

    def fail():
        attempts.append(1)
        raise failure

    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(case_analysis, "extract_live", fail)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 502
    assert set(response.json()) == {"error"}
    assert response.json()["error"]["stage"] == "provider"
    assert response.json()["error"]["retryable"] is retryable
    assert "secret" not in response.text
    assert attempts == [1]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "body", [{}, {"mode": "other"}, {"mode": "sample", "source_text": "changed"}]
)
def test_request_accepts_only_an_explicit_mode(body):
    response = client.post("/api/showcase/case-01/analysis", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["stage"] == "request"


def test_persistence_failure_returns_no_analysis(tmp_path, monkeypatch):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    blocked = tmp_path / "not-a-directory"
    blocked.write_text("occupied")
    monkeypatch.setenv("PCG_RUN_DIR", str(blocked))
    monkeypatch.setattr(
        case_analysis, "extract_live", lambda: ExtractionResult(relationships=[])
    )
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 500
    assert response.json()["error"]["stage"] == "persistence"
    assert response.json()["error"]["retryable"] is False
    assert response.json()["error"]["run_artifact_id"] is None


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


def test_live_api_uses_real_extraction_with_provider_http_substituted(
    tmp_path, monkeypatch
):
    import json
    from langchain_deepseek import ChatDeepSeek
    from private_client_graph.application import case_analysis

    requests = []
    payload = json.loads((CASE / "expected_extraction.json").read_text())

    def respond(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["messages"][1]["content"] == (CASE / "source.txt").read_text()
        return httpx.Response(
            200,
            json={
                "id": "chat_test",
                "object": "chat.completion",
                "created": 0,
                "model": "deepseek-flash",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_test",
                                    "type": "function",
                                    "function": {
                                        "name": "ExtractionResult",
                                        "arguments": json.dumps(payload),
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as http_client:

        def model(**kwargs):
            assert kwargs["max_retries"] == 0
            assert kwargs["timeout"] == 90
            return ChatDeepSeek(**kwargs, http_client=http_client)

        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-secret")
        monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
        monkeypatch.setattr(case_analysis, "ChatDeepSeek", model)
        response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 200
    assert len(response.json()["graph"]["relationships"]) == 6
    assert len(requests) == 1
    assert json.loads(next(tmp_path.glob("*.json")).read_text()) == payload
    assert "test-only-secret" not in response.text
