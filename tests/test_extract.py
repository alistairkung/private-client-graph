import json
from pathlib import Path

import httpx
import pytest
from langchain_deepseek import ChatDeepSeek
from pydantic import ValidationError

from private_client_graph.extract import (
    extract_relationships,
    extract_relationships_from_text,
)
from private_client_graph.models import ExtractionResult
from private_client_graph.extraction import cli


CASE_01 = Path(__file__).resolve().parents[1] / "cases" / "case_01"


@pytest.mark.parametrize("outcome", ["valid", "invalid_type", "no_tool_call"])
def test_extraction_uses_tool_schema_and_parses_response(outcome):
    # Stub only HTTP: exercise the real SDK schema conversion and Pydantic parsing.
    expected = json.loads((CASE_01 / "expected_extraction.json").read_text())
    payload = json.loads(json.dumps(expected))
    if outcome == "invalid_type":
        payload["relationships"][0]["relationship_type"] = "cousin_of"
    requests = []

    def respond(request):
        requests.append(request)
        body = json.loads(request.content)
        assert request.url == "https://api.deepseek.com/v1/chat/completions"
        assert body["model"] == "deepseek-flash"
        assert body["messages"][1] == {
            "role": "user",
            "content": (CASE_01 / "source.txt").read_text(encoding="utf-8"),
        }
        tool = body["tools"][0]["function"]
        assert tool["name"] == "ExtractionResult"
        schema = tool["parameters"]
        assert set(schema["properties"]) == {"relationships"}
        candidate = schema["properties"]["relationships"]["items"]
        assert set(candidate["required"]) == {
            "source_name", "relationship_type", "target_name", "supporting_text"
        }
        message = {"role": "assistant", "content": ""}
        if outcome != "no_tool_call":
            message["tool_calls"] = [{
                "id": "call_test", "type": "function",
                "function": {"name": "ExtractionResult", "arguments": json.dumps(payload)},
            }]
        return httpx.Response(200, json={
            "id": "chat_test", "object": "chat.completion", "created": 0,
            "model": "deepseek-flash",
            "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as http_client:
        llm = ChatDeepSeek(
            model="deepseek-flash", api_key="test-only", max_retries=0,
            http_client=http_client,
        )
        if outcome == "valid":
            result = extract_relationships_from_text(
                (CASE_01 / "source.txt").read_text(encoding="utf-8"), llm=llm
            )
            assert isinstance(result, ExtractionResult)
            assert result.model_dump() == expected
        else:
            error = ValidationError if outcome == "invalid_type" else RuntimeError
            with pytest.raises(error):
                extract_relationships_from_text(
                    (CASE_01 / "source.txt").read_text(encoding="utf-8"), llm=llm
                )
    assert len(requests) == 1


@pytest.mark.parametrize("model", ["deepseek-flash", "test-explicit"])
def test_cli_loads_dotenv_without_exposing_key(tmp_path, monkeypatch, capsys, model):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    from types import SimpleNamespace
    from langchain_core.runnables import RunnableLambda

    arguments = ["extract"] if model == "deepseek-flash" else ["extract", "--model", model]
    monkeypatch.setattr("sys.argv", arguments)
    source_path = tmp_path / "cases" / "case_01" / "source.txt"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("Synthetic text with {literal braces}.")
    calls = []

    def invoke(prompt):
        calls.append(prompt.to_messages()[1].content)
        return ExtractionResult(relationships=[])
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=test-local-secret\n")

    def fake_llm(**kwargs):
        assert kwargs["api_key"].get_secret_value() == "test-local-secret"
        assert kwargs["max_retries"] == 0
        assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
        assert kwargs["model"] == model
        return SimpleNamespace(with_structured_output=lambda schema, **options: RunnableLambda(invoke))

    monkeypatch.setattr(cli, "ChatDeepSeek", fake_llm)
    cli.main()
    assert calls == [source_path.read_text()]
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"relationships": []}
    assert "test-local-secret" not in captured.out + captured.err
    saved_runs = list((tmp_path / "runs" / "case_01").glob("*.json"))
    assert len(saved_runs) == 1
    assert saved_runs[0].read_text(encoding="utf-8") == captured.out
