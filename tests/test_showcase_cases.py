from fastapi.testclient import TestClient
import pytest
from private_client_graph.api.app import create_app
from private_client_graph.canonical_state import validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState


@pytest.mark.parametrize("case_id,count,sources", [("case-01",6,1),("case-04",7,2),("case-05",6,2)])
def test_fixed_cases_expose_valid_source_aware_curated_results(case_id,count,sources,monkeypatch):
    from private_client_graph.application import case_analysis
    monkeypatch.setattr(case_analysis, "extract_relationships_from_text", lambda *a, **k: pytest.fail("No public provider execution"))
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
