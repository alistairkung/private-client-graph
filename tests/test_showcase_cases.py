from fastapi.testclient import TestClient
import pytest
from private_client_graph.api.app import create_app
from private_client_graph.canonical_state import validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState


@pytest.mark.parametrize("case_id,count,sources", [("case-01",6,1),("case-04",7,2),("case-05",6,2)])
def test_fixed_cases_expose_valid_source_aware_curated_results(case_id,count,sources,monkeypatch):
    from langchain_deepseek import ChatDeepSeek
    monkeypatch.setattr(ChatDeepSeek, "invoke", lambda *a, **k: pytest.fail("No public provider execution"))
    client=TestClient(create_app())
    response=client.get(f"/api/showcase/cases/{case_id}")
    assert response.status_code==200
    result=response.json()
    assert result["result_kind"]=="curated_ideal_fixture"
    assert "not a measured model result" in result["notice"]
    state=CanonicalState.model_validate(result["state"])
    validate_canonical_state(state)
    assert len(state.sources)==sources
    assert len(state.relationships)==count
    if case_id=="case-04":
        assert any(len(edge.evidence_ids)>1 for edge in state.relationships)
    if case_id=="case-05":
        names={entity.id:entity.name for entity in state.entities}
        assert all("David" not in names[edge.source] for edge in state.relationships if edge.type=="trustee_of")


def test_public_catalog_is_fixed_and_read_only():
    client=TestClient(create_app())
    assert [item["id"] for item in client.get("/api/showcase/cases").json()]==["case-01","case-04","case-05"]
    assert client.get("/api/showcase/cases/unknown").status_code==404
    assert client.post("/api/showcase/cases",json={"source":"visitor data"}).status_code==405
    assert client.post("/api/showcase/cases/case-04",json={"source":"visitor data"}).status_code==405


def test_evergreen_retains_exact_fixture_graph_source_and_identity(monkeypatch, tmp_path):
    from private_client_graph.application.showcase_cases import EVERGREEN, get_showcase_case
    from private_client_graph.canonical_state import reconstruct_graph
    from private_client_graph.graph import build_graph
    from private_client_graph.models import ExtractionResult
    from private_client_graph.persistence import database

    def forbidden(*args, **kwargs):
        pytest.fail("Curated reads must not use database or provider allowance")

    monkeypatch.setattr(database, "database_engine", forbidden)
    monkeypatch.setenv("PCG_PIPELINE_RESOLVER", "generative")
    monkeypatch.setenv("PCG_RUN_DIR", str(tmp_path / "runs"))
    source = (EVERGREEN / "source.txt").read_text()
    extraction = ExtractionResult.model_validate_json((EVERGREEN / "expected_extraction.json").read_text())
    expected = build_graph(extraction.relationships, document="source.txt", source_text=source)
    example = get_showcase_case("case-01")
    assert reconstruct_graph(example.state) == expected
    assert example.state.sources[0].model_dump() == {"id": "source_001", "title": "Attendance note", "text": source}
    assert all(item.source_id == "source_001" for item in example.state.evidence)
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("setting", ["PCG_SHOWCASE_LIVE_ENABLED", "PCG_SHOWCASE_LIVE_LIMIT", "PCG_SHOWCASE_LIVE_WINDOW_SECONDS"])
def test_retired_live_settings_cannot_enable_execution_or_block_curated_reads(monkeypatch, setting):
    monkeypatch.setenv(setting, "invalid legacy configuration")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    assert client.get("/api/showcase/cases/case-01").status_code == 200
    from private_client_graph.pipeline import Pipeline

    def forbidden(*args, **kwargs):
        pytest.fail("Retired live settings must not enable HTTP execution")

    monkeypatch.setattr(Pipeline, "run", forbidden)
    monkeypatch.setattr(Pipeline, "run_from_extraction", forbidden)
    path = "/api/showcase/case-01/analysis"
    assert path not in client.get("/openapi.json").json()["paths"]
    for mode in ("sample", "live"):
        assert client.post(path, json={"mode": mode}).status_code in {404, 405}


@pytest.mark.parametrize("missing", ["source.txt", "expected_extraction.json"])
def test_missing_curated_input_returns_read_failure_without_fallback(tmp_path, monkeypatch, missing):
    from private_client_graph.application import showcase_cases
    for name in ("source.txt", "expected_extraction.json"):
        if name != missing:
            (tmp_path / name).write_text((showcase_cases.EVERGREEN / name).read_text())
    monkeypatch.setattr(showcase_cases, "EVERGREEN", tmp_path)
    response = TestClient(create_app()).get("/api/showcase/cases/case-01")
    assert response.status_code == 503
    assert response.json() == {"error": {"message": "Synthetic case could not be loaded."}}
