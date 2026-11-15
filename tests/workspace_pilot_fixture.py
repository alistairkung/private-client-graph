"""Signed test login, mocked OAuth exchange and a reviewed synthetic Workspace PDF."""

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from httpx2 import MockTransport, Response

from google_boundary import make_google_boundary, sign_in
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE

ROOT = "/api/matter-proposals/discovery/"
CALLBACK = "/auth/workspace/callback"
SCOPES = (
    "openid https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/drive.readonly"
)


@pytest.fixture
def pilot(monkeypatch):
    config = dict(
        ENABLED="true",
        CLIENT_ID="pilot.apps.googleusercontent.com",
        CLIENT_SECRET="pilot-secret",
        SUBJECT="synthetic-sub",
        MAILBOX="pilot@example.test",
        FOLDER="pilot-folder",
        LABEL="pilot-label",
        FOLDER_NAME="Alder Trust",
        LABEL_NAME="Alder correspondence",
        FILE_IDS="appointment",
        MESSAGE_IDS="06",
    )
    for key, value in config.items():
        monkeypatch.setenv("PCG_WORKSPACE_" + key, value)
    app = create_app()
    make_google_boundary().install(app)
    client = TestClient(app, base_url="https://testserver", follow_redirects=False)
    assert sign_in(client).status_code == 303
    return client, app


def post(client, path, body=None):
    return client.post(
        ROOT + path,
        json=body or {},
        headers={"origin": "https://testserver", "x-csrftoken": client.cookies[CSRF_COOKIE]},
    )


def install_google(app, *, subject="synthetic-sub", scopes=SCOPES, fail_exchange=False):
    from local_development.google import GoogleBoundary

    google = GoogleBoundary(subject=subject, client_id="pilot.apps.googleusercontent.com")

    def respond(request):
        response = google.respond(request)
        if request.url.path == "/token":
            if fail_exchange:
                return Response(400, json={"error": "invalid_grant"})
            assert b"code_verifier=" in request.content
            return Response(200, json={**response.json(), "expires_in": 300, "scope": scopes})
        return response

    app.state.workspace_pilot.oauth.client_kwargs["transport"] = MockTransport(respond)


def begin(client):
    response = post(client, "connect")
    assert response.status_code == 200
    params = parse_qs(urlsplit(response.json()["url"]).query)
    assert params["access_type"] == ["online"] and params["code_challenge_method"] == ["S256"]
    assert set(params["scope"][0].split()) == set(SCOPES.split())
    return {"state": params["state"][0], "code": params["nonce"][0]}


def ready_publication(pilot, *, on_final_metadata=None):
    """Serve one PDF and optionally pause its final, post-download metadata response."""
    client, app = pilot
    install_google(app)
    row = {
        "id": "appointment",
        "parents": ["pilot-folder"],
        "mimeType": "application/pdf",
        "trashed": False,
        "version": "1",
        "name": "Appointment",
    }
    media = (Path(__file__).parent / "fixtures/synthetic-proposal.pdf").read_bytes()

    downloaded = False

    def respond(request):
        nonlocal downloaded
        if request.url.path.endswith("/messages"):
            return Response(200, json={"messages": []})
        if request.url.path.endswith("/files"):
            return Response(200, json={"files": [row]})
        assert request.url.path.endswith("/files/appointment")
        if request.url.params.get("alt") == "media":
            downloaded = True
            return Response(200, content=media)
        if downloaded and on_final_metadata:
            on_final_metadata()
        downloaded = False
        return Response(200, json=row)

    app.state.workspace_pilot.transport = MockTransport(respond)
    client.get(CALLBACK, params=begin(client))
    old_generation = post(client, "connection").json()["generation"]
    session = post(
        client, "start", {"terms": "Alder Trust", "label": "pilot-label", "folder": "pilot-folder"}
    ).json()["session"]
    preview = post(
        client, "preview", {"session": session, "candidates": [{"kind": "pdf", "id": "appointment"}]}
    ).json()
    assert preview["sources"] == [
        {"id": "source_001", "title": "Appointment", "text": "Alice Example is the parent of Ben Example."}
    ]
    publish = {
        "session": session,
        "preview": preview["token"],
        "publish_synthetic": True,
        "metadata": {"external_reference": "SYN-180", "matter_title": "Alder"},
    }
    return old_generation, publish
