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


def test_live_and_sample_preserve_unresolved_aliases_and_share_graph(tmp_path, monkeypatch):
    source = (
        'Alice is a beneficiary of Harbour Trust. '
        'Ali is a trustee of Harbour Trust. Ali is Alice\'s nickname.'
    )
    extraction = ExtractionResult.model_validate({'relationships': [
        {'source_name': 'Alice', 'relationship_type': 'beneficiary_of',
         'target_name': 'Harbour Trust', 'supporting_text': 'Alice is a beneficiary of Harbour Trust.'},
        {'source_name': 'Ali', 'relationship_type': 'trustee_of',
         'target_name': 'Harbour Trust', 'supporting_text': 'Ali is a trustee of Harbour Trust.'},
    ]})
    (tmp_path / 'source.txt').write_text(source)
    (tmp_path / 'expected_extraction.json').write_text(extraction.model_dump_json())
    monkeypatch.setattr(case_analysis, 'CASE', tmp_path)
    monkeypatch.setenv('PCG_RUN_DIR', str(tmp_path / 'runs'))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only')
    monkeypatch.setenv('PCG_PIPELINE_RESOLVER', 'generative')
    calls = []

    def extract(text, *, llm):
        calls.append(text)
        return extraction

    monkeypatch.setattr(case_analysis, 'extract_relationships_from_text', extract)
    monkeypatch.setattr(case_analysis, 'consume_live_slot', lambda config: None)
    config = LiveConfig(enabled=True, limit=1, window_seconds=60)
    sample = case_analysis.analyse_case('sample', config)
    assert calls == []
    live = case_analysis.analyse_case('live', config)
    assert calls == [source]
    assert live.graph == sample.graph
    assert {entity.name for entity in live.graph.entities} == {'Ali', 'Alice', 'Harbour Trust'}
    assert sample.execution.run_artifact_id is None
    retained = tmp_path / 'runs' / live.execution.run_artifact_id
    assert ExtractionResult.model_validate_json(retained.read_text()) == extraction
