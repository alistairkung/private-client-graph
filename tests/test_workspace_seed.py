"""Offline operator checks at the Google HTTP boundary."""

import pytest
from httpx2 import Client, MockTransport, Response

from local_development.workspace_pilot.seed import seed


def test_seed_rejects_other_identity_before_any_workspace_request(tmp_path):
    def respond(request):
        assert request.url.host == "openidconnect.googleapis.com"
        return Response(200, json={"sub": "other", "email_verified": True, "email": "other@gmail.com"})

    with Client(transport=MockTransport(respond)) as http, pytest.raises(ValueError, match="account"):
        seed(http, tmp_path, "pilot@gmail.com")
    assert not list(tmp_path.iterdir())


def test_seed_and_repeat_verify_original_payloads_and_reject_drift(tmp_path):
    from email import policy
    from email.parser import BytesParser
    from hashlib import sha256
    import json
    from pathlib import Path

    corpus = Path(__file__).parent / "fixtures/alder-trust-v1"
    fixture = json.loads((corpus / "corpus.json").read_text())
    original = (corpus / fixture["appointment_media"]["path"]).read_bytes()
    responses = {}
    writes = []

    def respond(request):
        path = request.url.path
        if path.endswith("/userinfo"):
            return Response(
                200, json={"email_verified": True, "email": "pilot@gmail.com", "sub": "pilot-sub"}
            )
        if request.method == "GET":
            if path.endswith(("/files", "/messages", "/labels")):
                return Response(200, json={path.split("/")[-1]: []})
            row = responses[path.rsplit("/", 1)[-1]]
            return Response(200, json=row)
        assert request.method == "POST"
        key = f"google-{len(writes) + 1}"
        writes.append(path)
        if path.startswith("/upload/"):
            mime = (
                b"Content-Type: " + request.headers["Content-Type"].encode() + b"\r\n\r\n" + request.content
            )
            metadata, binary = BytesParser(policy=policy.default).parsebytes(mime).iter_parts()
            assert binary.get_payload(decode=True) == original
            row = json.loads(metadata.get_payload(decode=True))
            row["sha256Checksum"] = sha256(original).hexdigest()
        else:
            row = json.loads(request.content)
        if path.endswith("/messages"):
            assert request.url.params["internalDateSource"] == "dateHeader"
            row.setdefault("threadId", key)
            row["internalDate"] = "1767600000000"
        if path.endswith("/files"):
            row.update(shared=False, trashed=False)
        responses[key] = row
        return Response(200, json={"id": key})

    with Client(transport=MockTransport(respond)) as http:
        first = seed(http, tmp_path, "pilot@gmail.com")
        assert len(writes) == 17
        assert seed(http, tmp_path, "pilot@gmail.com") == first and len(writes) == 17
        assert (tmp_path / "manifest.json").stat().st_mode & 0o077 == 0
        sibling = responses[first["ids"]["07"]]
        assert sibling["threadId"] == responses[first["ids"]["06"]]["threadId"]
        assert sibling["labelIds"] == ["INBOX"]
        responses[first["ids"]["appointment"]]["sha256Checksum"] = "changed"
        with pytest.raises(ValueError, match="Drive object drift"):
            seed(http, tmp_path, "pilot@gmail.com")
        assert len(writes) == 17


def test_uncertain_create_stops_repeat_before_another_write(tmp_path):
    from httpx2 import ReadTimeout

    writes = []

    def respond(request):
        if request.url.path.endswith("/userinfo"):
            return Response(
                200, json={"email_verified": True, "email": "pilot@gmail.com", "sub": "pilot-sub"}
            )
        if request.method == "GET":
            return Response(200, json={"labels": []})
        writes.append(request.url.path)
        raise ReadTimeout("response lost")

    with Client(transport=MockTransport(respond)) as http:
        with pytest.raises(ReadTimeout):
            seed(http, tmp_path, "pilot@gmail.com")
        with pytest.raises(ValueError, match="Unresolved create"):
            seed(http, tmp_path, "pilot@gmail.com")
    assert len(writes) == 1


def test_private_launcher_excludes_seed_controls_and_operator_credentials(tmp_path):
    import json
    from local_development.workspace_pilot.server import configure

    ids = {
        key: key
        for key in (
            "folder-1",
            "folder-2",
            "alder-label",
            "appointment",
            "deed",
            "minutes",
            "shortcut",
            "other",
        )
    }
    ids.update({f"{i:02d}": f"mail-{i}" for i in range(1, 10)})
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "corpus": "alder-trust-v1",
                "sub": "pilot-sub",
                "email": "pilot@gmail.com",
                "ids": ids,
            }
        )
    )
    for name, path in (("signin", "callback"), ("discovery", "workspace/callback")):
        (tmp_path / (name + ".json")).write_text(
            json.dumps(
                {
                    "web": {
                        "client_id": name,
                        "client_secret": name,
                        "redirect_uris": ["https://localhost:8444/auth/" + path],
                    }
                }
            )
        )
    settings = configure(tmp_path)
    assert settings["PCG_GOOGLE_SUB_ALLOWLIST"] == settings["PCG_WORKSPACE_SUBJECT"] == "pilot-sub"
    assert set(settings["PCG_WORKSPACE_MESSAGE_IDS"].split(",")) == {
        f"mail-{i}" for i in (1, 2, 3, 4, 5, 6, 8, 9)
    }
    assert set(settings["PCG_WORKSPACE_FILE_IDS"].split(",")) == {"appointment", "deed", "minutes"}
    assert settings["PCG_GOOGLE_CLIENT_ID"] == "signin" and settings["PCG_WORKSPACE_CLIENT_ID"] == "discovery"


def test_google_check_requires_visible_controls_before_claiming_isolation(tmp_path):
    import json
    from local_development.workspace_pilot.check import check

    ids = {f"{i:02d}": str(i) for i in range(1, 8)}
    ids.update({"alder-label": "label", "folder-1": "folder"})
    (tmp_path / "manifest.json").write_text(json.dumps({"ids": ids, "sub": "s", "email": "pilot@gmail.com"}))

    def respond(request):
        if request.url.path.endswith("userinfo"):
            return Response(200, json={"email_verified": True, "sub": "s", "email": "pilot@gmail.com"})
        assert "labelIds" not in request.url.params
        assert request.url.params["maxResults"] == "2"
        if "pageToken" not in request.url.params:
            return Response(200, json={"messages": [{"id": "1"}], "nextPageToken": "second"})
        return Response(200, json={"messages": [{"id": "2"}]})

    with (
        Client(transport=MockTransport(respond)) as client,
        pytest.raises(ValueError, match="positive control missing"),
    ):
        check(client, tmp_path, "pilot@gmail.com")
