"""Order disconnect relative to the last Workspace read and the authorized model dispatch."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from private_client_graph.application import matter_proposals
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.research.live_accounting import read_task, task_state
from workspace_pilot_fixture import pilot, post, ready_publication


@pytest.mark.parametrize(
    "interruption,status,error",
    [
        ("disconnect_during_read", 409, "workspace_reconnect"),
        ("remove_practitioner_during_read", 403, "access_denied"),
        ("disconnect_during_analysis", 201, None),
    ],
    ids=["disconnect_during_read", "remove_practitioner_during_read", "disconnect_during_analysis"],
)
def test_import_authorization_boundary(database, pilot, monkeypatch, interruption, status, error):
    client, app = pilot
    reached, resume = Event(), Event()
    importing = False

    def pause():
        reached.set()
        assert resume.wait(10), "Import did not resume"

    def final_metadata():
        if importing and interruption != "disconnect_during_analysis":
            pause()

    def extract(sources, *, llm):
        if interruption == "disconnect_during_analysis":
            pause()
        return SourcedExtractionResult(relationships=[])

    monkeypatch.setattr(matter_proposals, "extract_relationships_from_sources", extract)
    _, publication = ready_publication(pilot, on_final_metadata=final_metadata)
    ledger = Path(read_task(app.state.proposal_analysis.task_root)["ledger"])
    importing = True
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(post, client, "import", publication)
        try:
            assert reached.wait(10), "Import did not reach the expected boundary"
            if interruption == "remove_practitioner_during_read":
                monkeypatch.setenv("PCG_GOOGLE_SUB_ALLOWLIST", "other-subject")
            else:
                assert post(client, "disconnect").json() == {"connected": False}
        finally:
            resume.set()
        response = pending.result(timeout=10)

    proposals = client.get("/api/matter-proposals").json()
    assert response.status_code == status, response.text
    if error is None:
        assert [p["id"] for p in proposals] == [response.json()["id"]]
        saved = client.get(response.headers["location"]).json()
        assert saved["state"]["sources"] == [
            {
                "id": "source_001",
                "title": "Appointment",
                "text": "Alice Example is the parent of Ben Example.",
            }
        ]
        assert post(client, "import", publication).status_code == 409
        assert task_state(ledger)["used"] == 1
    else:
        assert response.json()["error"]["code"] == error
        assert proposals == []
        assert task_state(ledger)["used"] == 0
