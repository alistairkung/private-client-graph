"""The public showcase is fixed/read-only even on a live-capable deployment.

The former public live-execution API is deliberately closed. Quota persistence
and internal live orchestration remain covered by their own focused suites.
"""
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import pytest
from private_client_graph.api.app import create_app


@pytest.mark.parametrize("enabled", ["true", "false"])
def test_public_routes_never_execute_a_provider_or_use_its_allowance(monkeypatch, enabled):
    from private_client_graph.application import case_analysis, showcase_live
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_ENABLED",enabled)
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_LIMIT","1")
    monkeypatch.setenv("PCG_SHOWCASE_LIVE_WINDOW_SECONDS","86400")
    monkeypatch.setenv("DEEPSEEK_API_KEY","test-only")
    monkeypatch.setenv("DATABASE_URL","postgresql://localhost:1/unavailable")
    def forbidden(*args, **kwargs):
        pytest.fail("Public navigation must not invoke providers or quota storage")
    monkeypatch.setattr(case_analysis,"extract_relationships_from_text",forbidden)
    monkeypatch.setattr(showcase_live,"consume_live_slot",forbidden)
    client=TestClient(create_app())
    assert client.get("/api/showcase/case-01").json()["live_analysis"]["state"]=="disabled"
    for case in ("case-01","case-04","case-05"):
        assert client.get(f"/api/showcase/cases/{case}").status_code==200
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(lambda _: client.post("/api/showcase/case-01/analysis",json={"mode":"live"}).status_code,range(8)))
    assert statuses==[403]*8
    assert client.post("/api/showcase/case-01/analysis",json={"mode":"sample"}).status_code==200
    assert client.get("/api/matters").status_code in (401,503)
    assert client.get("/api/matter-proposals").status_code in (401,503)


@pytest.mark.parametrize("body", [{},{"mode":"unknown"},{"mode":"sample","source_text":"visitor"},{"mode":"live","prompt":"visitor"}])
def test_showcase_rejects_visitor_source_and_execution_overrides(body):
    client=TestClient(create_app())
    assert client.post("/api/showcase/case-01/analysis",json=body).status_code==422
