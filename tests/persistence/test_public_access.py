"""Public reads preserve complete canonical facts regardless of write authority."""
from pathlib import Path
from uuid import uuid4
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from google_boundary import make_google_boundary, sign_in

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import SESSION_COOKIE
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.persistence.matter_state import insert_matter
from private_client_graph.persistence.proposal_state import insert_proposal


@pytest.mark.parametrize("session_state", ["anonymous", "expired", "denied", "tampered", "no_auth", "broken_auth"])
def test_every_reader_gets_complete_persisted_matters_and_pending_proposals(database, monkeypatch, session_state):
    state = CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[1] / "fixtures/canonical-state.json").read_text()
    )
    matter_id, proposal_id = uuid4(), uuid4()
    engine = create_engine(database)
    with engine.begin() as connection:
        insert_matter(connection, matter_id=matter_id, external_reference="Public/1", title="Synthetic Matter", state=state)
        insert_proposal(connection, proposal_id=proposal_id, external_reference="Public/2", title="Synthetic Proposal", state=state)
    engine.dispose()
    if session_state == "no_auth":
        for name in ("PCG_GOOGLE_CLIENT_ID", "PCG_GOOGLE_CLIENT_SECRET", "PCG_SESSION_SECRET", "PCG_GOOGLE_SUB_ALLOWLIST"):
            monkeypatch.delenv(name, raising=False)
    application = create_app()
    client = TestClient(application, base_url="https://testserver")
    if session_state in {"expired", "denied", "broken_auth"}:
        make_google_boundary().install(application)
        assert sign_in(client).status_code == 303
    if session_state == "expired":
        now = time.time()
        monkeypatch.setattr(time, "time", lambda: now + 901)
    elif session_state == "denied":
        monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "another-subject")
    elif session_state == "tampered":
        client.cookies.set(SESSION_COOKIE, "forged")
    elif session_state == "broken_auth":
        monkeypatch.setenv("PCG_SESSION_SECRET", "invalid")
    assert client.get("/health").status_code == 200
    assert client.get("/api/matters").json() == [
        {"id": str(matter_id), "external_reference": "Public/1", "title": "Synthetic Matter"}
    ]
    assert client.get("/api/matter-proposals").json() == [
        {"id": str(proposal_id), "external_reference": "Public/2", "matter_title": "Synthetic Proposal"}
    ]
    for path, graph_name in ((f"/api/matters/{matter_id}", "current_graph"),
                             (f"/api/matter-proposals/{proposal_id}", "proposed_graph")):
        response = client.get(path)
        assert response.status_code == 200
        detail = response.json()
        assert detail["state"] == state.model_dump(mode="json")
        assert detail[graph_name]["relationships"]
        assert detail[graph_name]["evidence"]
    assert client.get("/api/access").json() == {
        "can_write": False, "sign_in_available": session_state not in {"no_auth", "broken_auth"},
    }


def test_readiness_does_not_depend_on_intake_provider_configuration(database, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("PCG_PROPOSAL_ANALYSIS_LIMIT", "invalid")
    application = create_app()
    assert application.state.proposal_analysis is None
    client = TestClient(application, base_url="https://testserver")
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/matters").json() == []
    assert client.get("/api/matter-proposals").json() == []
