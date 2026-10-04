from private_client_graph.application import case_analysis
from private_client_graph.application.showcase_live import LiveConfig
from private_client_graph.models import ExtractionResult


def test_live_showcase_configures_model_then_calls_shared_extraction_once(
    monkeypatch,
):
    configured_model = object()
    extraction = ExtractionResult(relationships=[])
    events = []

    def model(**kwargs):
        events.append(("configure", kwargs))
        return configured_model

    def consume(config):
        events.append(("consume", config))

    def extract(source, *, llm):
        events.append(("extract", source, llm))
        return extraction

    config = LiveConfig(enabled=True, limit=1, window_seconds=60)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    monkeypatch.setattr(case_analysis, "ChatDeepSeek", model)
    monkeypatch.setattr(case_analysis, "consume_live_slot", consume)
    monkeypatch.setattr(case_analysis, "extract_relationships_from_text", extract)

    result = case_analysis.extract_live("finalized source", config)

    assert result is extraction
    assert [event[0] for event in events] == ["configure", "consume", "extract"]
    assert events[0][1]["max_retries"] == 0
    assert events[1][1] is config
    assert events[2][1:] == ("finalized source", configured_model)
