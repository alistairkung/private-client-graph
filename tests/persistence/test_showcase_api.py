from pathlib import Path
import httpx
import pytest
from openai import APIConnectionError, AuthenticationError, RateLimitError
from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app

CASE = Path(__file__).resolve().parents[2] / "cases" / "case_01"


@pytest.fixture
def client(database, monkeypatch):
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_ENABLED", "true")
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_LIMIT", "1")
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_WINDOW_SECONDS", "86400")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    return TestClient(create_app())


def test_live_analysis_persists_offline_compatible_extraction(tmp_path, monkeypatch, client):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    extraction = ExtractionResult.model_validate_json(
        (CASE / "expected_extraction.json").read_text()
    )
    invocations = []

    def extract(source, *, llm):
        invocations.append((source, llm))
        return extraction

    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(case_analysis, "extract_relationships_from_text", extract)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "exhausted"
    assert response.status_code == 200
    result = response.json()
    assert result["execution"]["mode"] == "live"
    artifact = tmp_path / result["execution"]["run_artifact_id"]
    assert ExtractionResult.model_validate_json(artifact.read_text()) == extraction
    assert len(result["graph"]["relationships"]) == 6
    assert set(result) == {"execution", "graph"}
    assert len(invocations) == 1
    assert invocations[0][0] == (CASE / "source.txt").read_text()


def test_rejected_live_extraction_is_saved_before_graph_failure(tmp_path, monkeypatch, client):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    extraction = ExtractionResult.model_validate_json(
        (CASE / "expected_extraction.json").read_text()
    )
    extraction.relationships[0].supporting_text = "Not in the authoritative source"
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(
        case_analysis,
        "extract_relationships_from_text",
        lambda source, *, llm: extraction,
    )
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "exhausted"
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
    failure, retryable, tmp_path, monkeypatch, client
):
    from private_client_graph.application import case_analysis

    attempts = []

    def fail(source, *, llm):
        attempts.append(1)
        raise failure

    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(case_analysis, "extract_relationships_from_text", fail)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "exhausted"
    assert response.status_code == 502
    assert set(response.json()) == {"error"}
    assert response.json()["error"]["stage"] == "provider"
    assert response.json()["error"]["retryable"] is retryable
    assert "secret" not in response.text
    assert attempts == [1]
    assert not list(tmp_path.iterdir())




def test_persistence_failure_returns_no_analysis(tmp_path, monkeypatch, client):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    blocked = tmp_path / "not-a-directory"
    blocked.write_text("occupied")
    monkeypatch.setenv("PCG_RUN_DIR", str(blocked))
    monkeypatch.setattr(
        case_analysis,
        "extract_relationships_from_text",
        lambda source, *, llm: ExtractionResult(relationships=[]),
    )
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.status_code == 500
    assert response.json()["error"]["stage"] == "persistence"
    assert response.json()["error"]["retryable"] is False
    assert response.json()["error"]["run_artifact_id"] is None




def test_live_api_uses_real_extraction_with_provider_http_substituted(
    tmp_path, monkeypatch, client
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
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "exhausted"
    assert response.status_code == 200
    assert len(response.json()["graph"]["relationships"]) == 6
    assert len(requests) == 1
    assert json.loads(next(tmp_path.glob("*.json")).read_text()) == payload
    assert "test-only-secret" not in response.text


def test_post_rechecks_advisory_get_and_preserves_sample_and_matter_access(client, monkeypatch, tmp_path):
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    monkeypatch.setattr(
        case_analysis,
        "extract_relationships_from_text",
        lambda source, *, llm: ExtractionResult(relationships=[]),
    )
    assert client.get("/api/showcase/case-01").json()["live_analysis"] == {
        "state": "available", "resets_at": None,
    }
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code == 200
    exhausted = client.get("/api/showcase/case-01").json()["live_analysis"]
    assert exhausted["state"] == "exhausted"
    assert exhausted["resets_at"] is not None
    rejected = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert rejected.status_code == 429
    assert rejected.json()["error"]["live_analysis"] == exhausted
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200
    matters = client.get("/api/matters").json()
    assert len(matters) == 1
    matter_path = f'/api/matters/{matters[0]["id"]}'
    assert client.get(matter_path).status_code == 200
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_ENABLED", "false")
    disabled = TestClient(create_app())
    assert disabled.get("/api/matters").json() == matters
    assert disabled.get(matter_path).json() == client.get(matter_path).json()


@pytest.mark.parametrize("body", [
    {}, {"mode": "unknown"}, {"mode": "live", "source_text": "visitor"},
    {"mode": "live", "prompt": "visitor"}, {"mode": "live", "temperature": 1},
])
def test_rejected_request_does_not_consume_quota(client, body):
    assert client.post("/api/showcase/case-01/analysis", json=body).status_code == 422
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "available"


def test_missing_source_does_not_consume_quota(client, monkeypatch, tmp_path):
    from private_client_graph.application import case_analysis
    from private_client_graph.persistence.showcase_quota import quota_reset

    monkeypatch.setattr(case_analysis, "CASE", tmp_path)
    response = client.post("/api/showcase/case-01/analysis", json={"mode": "live"})
    assert response.json()["error"]["stage"] == "source"
    assert quota_reset(limit=1, window_seconds=86400) is None


def test_provider_configuration_failure_does_not_consume_quota(client, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code == 502
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "available"


def test_concurrent_requests_across_app_instances_bound_provider_attempts(client, monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Lock
    from private_client_graph.application import case_analysis
    from private_client_graph.models import ExtractionResult

    monkeypatch.setenv("PCG_SHOWCASE_LIVE_LIMIT", "3")
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path))
    clients = [TestClient(create_app()) for _ in range(12)]
    start = Barrier(12)
    lock = Lock()
    attempts = []

    def provider(source, *, llm):
        with lock:
            attempts.append(source)
        return ExtractionResult(relationships=[])

    monkeypatch.setattr(case_analysis, "extract_relationships_from_text", provider)

    def request(replica):
        start.wait(timeout=10)
        return replica.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code

    with ThreadPoolExecutor(max_workers=12) as pool:
        statuses = list(pool.map(request, clients))
    assert statuses.count(200) == 3
    assert statuses.count(429) == 9
    assert len(attempts) == 3
    # A new application instance has no in-memory allowance to reset.
    restarted = TestClient(create_app())
    assert restarted.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code == 429
    assert len(attempts) == 3


def test_unavailable_quota_fails_closed_but_sample_still_works(client, monkeypatch):
    from private_client_graph.application import case_analysis

    def unexpected_provider(source, *, llm):
        pytest.fail("Unavailable quota must prevent provider invocation")

    monkeypatch.setattr(
        case_analysis, "extract_relationships_from_text", unexpected_provider
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:1/unavailable")
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"] == "unavailable"
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "live"}).status_code == 503
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200
