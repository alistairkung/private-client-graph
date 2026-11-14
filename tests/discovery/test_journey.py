from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from httpx2 import Client, MockTransport, Response, SyncByteStream

from private_client_graph.application.discovery import DiscoverySession, Limits, WorkspaceScope

from .exchanges import CORPUS, FILES, ROOT, Exchanges, file


def test_empty_search_queries_the_scoped_collections_once():
    requests = []

    def respond(request):
        requests.append(request)
        return Response(200, json={})

    with Client(transport=MockTransport(respond)) as http:
        session = DiscoverySession(http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
        session.start("Alder Trust")

    mail, drive = requests
    assert mail.url.path == "/gmail/v1/users/synthetic@example.test/messages"
    assert mail.url.params["q"] == '"Alder Trust"'
    assert mail.url.params["labelIds"] == "alder-label"
    assert drive.url.params["q"] == (
        "'folder-1' in parents and trashed = false and mimeType = 'application/pdf' "
        "and fullText contains '\"Alder Trust\"'"
    )
    assert session.suggestions == ()


@pytest.mark.parametrize("lead", ["Mara Voss", "Ben Wong"])
def test_followup_then_sixth_original_message_revises_the_shortlist(lead):
    google = Exchanges()
    google.list_mail("Alder Trust", ["05", "03", "07", "01"], next_token="mail-p2")
    google.list_mail("Alder Trust", ["06", "04", "02"], token="mail-p2")
    google.list_files("Alder Trust", ["deed", "shortcut", "other"], next_token="drive-p2")
    google.list_files("Alder Trust", ["minutes"], token="drive-p2")
    for i in ("01", "02", "03", "04", "05"):
        google.message(i, "metadata")
        google.message(i, "full")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    first = session.start("Alder Trust")
    assert first.pending == ("06", "07")
    assert len(first.inspected) == 5
    assert {f.id for f in first.files} == {"deed", "minutes"}
    assert first.suggestions[0].query == "Alice Reed"
    google.list_mail("Alice Reed", ["08"])
    google.list_files("Alice Reed", [])
    session.approve(first.revision, "Alice Reed")
    google.message("06", "metadata")
    google.message("06", "full", body=CORPUS["alternate_resignation"] if lead == "Ben Wong" else None)
    google.message("07", "metadata")
    second = session.inspect_more()
    best = second.suggestions[0]
    assert (best.query, best.origin, best.passage) == (
        lead, "06", f"{lead} will circulate the executed appointment separately.")
    assert best.rationale and second.skipped == ("07",)
    assert "08" not in second.inspected and second.pending == ()
    google.list_mail(lead, [])
    appointment = file("appointment")
    if lead == "Ben Wong":
        appointment = {**appointment, "name": CORPUS["alternate_appointment_title"]}
    google.list_files(lead, [], records=[appointment, file("other")])
    result = session.approve(second.revision, lead)
    assert [f.id for f in result.files] == ["appointment"]
    if lead == "Mara Voss":
        path = FILES + "/appointment"
        media = CORPUS["appointment_media"]
        google.expect(path, {}, file("appointment"))
        google.expect(path, {"alt": "media"}, (ROOT / media["path"]).read_bytes())
        google.expect(path, {}, file("appointment"))
        assert session.preview_pdf("appointment").sha256 == media["sha256"]
    assert result.shortlist == second.suggestions
    assert dict(result.inspected)["06"]
    assert session.approve(first.revision, "Alice Reed").shortlist == first.suggestions
    assert len(session.approvals) == 2
    assert not google.steps


def test_pdf_preview_uses_original_bytes_only_while_file_stays_in_scope():
    google = Exchanges()
    google.list_mail("Alder Trust", [])
    google.list_files("Alder Trust", ["appointment", "other", "shortcut"])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    session.start("Alder Trust")
    for forbidden in ("other", "shortcut", "target"):
        with pytest.raises(ValueError):
            session.preview_pdf(forbidden)
    path = FILES + "/appointment"
    record = file("appointment")
    pdf = CORPUS["appointment_media"]
    google.expect(path, {}, record)
    google.expect(path, {"alt": "media"}, (ROOT / pdf["path"]).read_bytes())
    google.expect(path, {}, record)
    preview = session.preview_pdf("appointment")
    assert preview.sha256 == pdf["sha256"]
    assert preview.text == "Alice Example is the parent of Ben Example."
    google.expect(path, {}, {**record, "parents": ["folder-2"]})
    with pytest.raises(ValueError):
        session.preview_pdf("appointment")
    google.expect(path, {}, record)
    google.expect(path, {"alt": "media"}, (ROOT / pdf["path"]).read_bytes())
    google.expect(path, {}, {**record, "version": "2"})
    with pytest.raises(ValueError):
        session.preview_pdf("appointment")
    assert not google.steps


def test_scope_and_date_are_rechecked_before_consuming_content():
    google = Exchanges()
    google.list_mail("Alder Trust", ["06", "07", "08", "09"],
                     dates=" after:1767571199 before:1767657600")
    google.list_files("Alder Trust", [])
    google.message("06", "metadata")
    google.message("06", "full", labels=["INBOX"])
    google.message("07", "metadata")
    google.expect("/gmail/v1/users/synthetic@example.test/messages/08", {"format": "metadata"},
                  {"id": "08", "labelIds": ["alder-label"], "internalDate": "1767657600000"})
    google.expect("/gmail/v1/users/synthetic@example.test/messages/09", {"format": "metadata"}, {}, 403)
    scope = WorkspaceScope("synthetic@example.test", "alder-label", "folder-1", date(2026, 1, 5), date(2026, 1, 5))
    view = DiscoverySession(google.http, scope).start("Alder Trust")
    assert view.skipped == ("06", "07", "08")
    assert view.failed == ("09",)
    assert view.inspected == view.suggestions == () and view.requests == 7
    assert not google.steps


def test_request_and_byte_exhaustion_report_incomplete_results():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01"], next_token="next")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                               Limits(action_requests=1, session_requests=2))
    view = session.start("Alder Trust")
    assert view.more_pages and view.stop_reason == "Action request limit"
    google.list_mail("Alder Trust", [], token="next")
    view = session.inspect_more()
    assert view.more_pages and view.stop_reason == "Session request limit" and view.pending == ("01",)

    google = Exchanges()
    google.list_mail("Alder Trust", ["01"])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                               Limits(action_bytes=8, session_bytes=8))
    view = session.start("Alder Trust")
    assert view.bytes == 0 and view.stop_reason == "Session byte limit" and view.inspected == ()
    assert not google.steps


def test_concurrent_approval_and_three_execution_limit():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01", "06", "08", "09"])
    google.list_files("Alder Trust", [])
    for i in ("01", "06", "08", "09"):
        google.message(i, "metadata")
        google.message(i, "full")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    view = session.start("Alder Trust")
    assert len(view.suggestions) == 3
    for suggestion in view.suggestions:
        google.list_mail(suggestion.query, [])
        google.list_files(suggestion.query, [])
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: session.approve(view.revision, suggestion.query), range(2)))
        assert results[0] == results[1]
    later = session.inspect_more()
    with pytest.raises(ValueError, match="limit"):
        session.approve(later.revision, later.suggestions[0].query)
    assert not google.steps


def test_malformed_membership_cannot_authorize_a_body_read():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01"])
    google.list_files("Alder Trust", [])
    google.expect("/gmail/v1/users/synthetic@example.test/messages/01", {"format": "metadata"},
                  {"id": "01", "labelIds": "alder-label-unrelated", "internalDate": "1"})
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    view = session.start("Alder Trust")
    assert view.inspected == () and view.failed == ("01",)
    assert not google.steps


def test_followup_message_preview_cannot_supply_a_recursive_lead():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01"])
    google.list_files("Alder Trust", [])
    google.message("01", "metadata")
    google.message("01", "full")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    first = session.start("Alder Trust")
    google.list_mail("Alice Reed", ["08"])
    google.list_files("Alice Reed", [])
    session.approve(first.revision, "Alice Reed")
    google.message("08", "metadata")
    google.message("08", "full")
    assert session.preview_message("08") == "Cora Patel will circulate the signed deed."
    assert session.inspect_more().suggestions == first.suggestions
    with pytest.raises(ValueError):
        session.preview_message("unknown")
    assert not google.steps


def test_streamed_oversize_response_stops_before_pulling_another_chunk():
    class Chunks(SyncByteStream):
        def __iter__(self):
            yield b"12345678"
            pytest.fail("pulled another chunk after exhausting the byte budget")

    def respond(request):
        return Response(200, stream=Chunks())

    with Client(transport=MockTransport(respond)) as http:
        session = DiscoverySession(http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                                   Limits(action_bytes=8))
        view = session.start("Alder Trust")
    assert view.bytes == 8 and view.stop_reason == "Action byte limit"
