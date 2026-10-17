"""The local substitute keeps authenticated PDF intake and persistence real."""
import json
from pathlib import Path

import pytest

from private_client_graph.api.auth import CSRF_COOKIE
from private_client_graph.application import matter_proposals

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.fixture
def local_client(database, monkeypatch, authenticated_client):
    from local_development.server import create_local_app

    # Restore every process-global substitution installed by the development factory.
    for name in ("_extract_proposal", "_extract_proposal_sources"):
        monkeypatch.setattr(matter_proposals, name, getattr(matter_proposals, name))
    monkeypatch.delenv("PCG_PROVIDER_TASK_ROOT", raising=False)
    monkeypatch.delenv("PCG_PROVIDER_AUTHORIZATION", raising=False)
    app = create_local_app(origin="https://testserver")

    def forbidden(*args, **kwargs):
        pytest.fail("Local fixture analysis reached a live provider/accounting boundary")

    for name in ("_construct_model", "extract_relationships_from_text", "extract_relationships_from_sources", "invoke_authorized"):
        monkeypatch.setattr(matter_proposals, name, forbidden)
    return authenticated_client(app)


@pytest.mark.parametrize("mode", ["single", "distinct", "repeated"])
def test_local_pdf_proposal_confirm_and_reopen_without_provider_authority(local_client, mode):
    client = local_client
    headers = {"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]}
    data = {"external_reference": "LOCAL/001", "matter_title": "Local synthetic Matter",
            "synthetic_confirmation": "true"}
    parent = (FIXTURES / "synthetic-proposal.pdf").read_bytes()
    if mode == "single":
        data["source_title"] = "Synthetic note"
        files = [("pdf", ("parent.pdf", parent, "application/pdf"))]
    else:
        data["sources"] = json.dumps([{"id": "first", "title": "Synthetic note"},
                                       {"id": "second", "title": "Synthetic note"}])
        second = parent if mode == "repeated" else (FIXTURES / "multiple-role-proposal.pdf").read_bytes()
        files = [("pdfs", ("first.pdf", parent, "application/pdf")),
                 ("pdfs", ("second.pdf", second, "application/pdf"))]
    response = client.post("/api/matter-proposals", data=data, files=files, headers=headers)
    assert response.status_code == 201, response.text
    proposal = response.json()
    state = proposal["state"]
    assert len(state["relationships"]) == (4 if mode == "distinct" else 1)
    assert len(state["evidence"]) == {"single": 1, "distinct": 4, "repeated": 2}[mode]
    if mode != "single":
        assert [(s["id"], s["title"]) for s in state["sources"]] == [
            ("first", "Synthetic note"), ("second", "Synthetic note")]
        assert {e["source_id"] for e in state["evidence"]} == {"first", "second"}
    assert client.get(response.headers["location"]).json() == proposal
    confirmed = client.post("/api/matters", json={"matter_proposal_id": proposal["id"]}, headers=headers)
    assert confirmed.status_code == 201, confirmed.text
    matter = confirmed.json()
    assert matter["state"] == state
    assert matter["current_graph"] == proposal["proposed_graph"]
    assert client.get(confirmed.headers["location"]).json() == matter
    assert client.get(response.headers["location"]).status_code == 404
