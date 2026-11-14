from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from httpx2 import Client, MockTransport, ReadError, Response, SyncByteStream

from private_client_graph.application.discovery import DiscoverySession, Limits, WorkspaceScope

from private_client_graph.application.discovery.google import ReadFailure, WorkspaceReader
from private_client_graph.application.discovery.limits import Action, LimitReached, Usage

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
    google.list_mail("Alder Trust", ["05", "03", "04", "02", "01"], next_token="mail-p2")
    for i in ("01", "02", "03", "04", "05"):
        google.message(i, "metadata")
        google.message(i, "full")
    google.list_files("Alder Trust", ["deed", "shortcut", "other"], next_token="drive-p2")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    first = session.start("Alder Trust")
    assert first.pending == () and first.more_pages
    assert len(first.inspected) == 5
    assert {f.id for f in first.files} == {"deed"}
    assert first.suggestions[0].query == "Alice Reed"
    google.list_mail("Alice Reed", ["08"])
    google.list_files("Alice Reed", [])
    session.approve(first.revision, "Alice Reed")
    google.list_mail("Alder Trust", ["07", "06"], token="mail-p2")
    google.message("06", "metadata")
    google.message("06", "full", body=CORPUS["alternate_resignation"] if lead == "Ben Wong" else None)
    google.message("07", "metadata")
    google.list_files("Alder Trust", ["minutes"], token="drive-p2")
    second = session.inspect_more()
    assert {f.id for f in second.files} == {"deed", "minutes"} and not second.more_pages
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
    google.message("06", "metadata")
    google.message("06", "full", labels=["INBOX"])
    google.message("07", "metadata")
    google.expect("/gmail/v1/users/synthetic@example.test/messages/08", {"format": "metadata"},
                  {"id": "08", "labelIds": ["alder-label"], "internalDate": "1767657600000"})
    google.expect("/gmail/v1/users/synthetic@example.test/messages/09", {"format": "metadata"}, {}, 403)
    google.list_files("Alder Trust", [])
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
    assert view.can_inspect_more and view.more_pages and view.stop_reason == "Action request limit"
    google.message("01", "metadata")
    view = session.inspect_more()
    assert not view.can_inspect_more
    assert view.more_pages and view.stop_reason == "Session request limit" and view.pending == ("01",)

    google = Exchanges()
    google.list_mail("Alder Trust", ["01"])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                               Limits(action_bytes=8, session_bytes=8))
    view = session.start("Alder Trust")
    assert not view.can_inspect_more
    assert view.bytes == 0 and view.stop_reason == "Session byte limit" and view.inspected == ()
    assert not google.steps


def test_concurrent_approval_and_three_execution_limit():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01", "06", "08", "09"])
    for i in ("01", "06", "08", "09"):
        google.message(i, "metadata")
        google.message(i, "full")
    google.list_files("Alder Trust", [])
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
    google.expect("/gmail/v1/users/synthetic@example.test/messages/01", {"format": "metadata"},
                  {"id": "01", "labelIds": "alder-label-unrelated", "internalDate": "1"})
    google.list_files("Alder Trust", [])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    view = session.start("Alder Trust")
    assert view.inspected == () and view.failed == ("01",)
    assert not google.steps


def test_followup_message_preview_cannot_supply_a_recursive_lead():
    google = Exchanges()
    google.list_mail("Alder Trust", ["01"])
    google.message("01", "metadata")
    google.message("01", "full")
    google.list_files("Alder Trust", [])
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


def test_first_original_page_can_be_inspected_with_more_pages_and_a_tight_budget():
    google = Exchanges()
    google.list_mail("Alder Trust", ["02"], next_token="more")
    google.message("02", "metadata")
    google.message("02", "full")
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                               Limits(action_requests=3))
    first = session.start("Alder Trust")
    assert first.inspected == ("02",) and first.more_pages
    assert first.stop_reason == "Action request limit"

    google.list_mail("Alder Trust", ["01", "02"], token="more")
    google.message("01", "metadata")
    google.message("01", "full")
    second = session.inspect_more()
    assert second.inspected == ("02", "01") and second.more_pages

    google.list_files("Alder Trust", ["deed"])
    final = session.inspect_more()
    assert not final.more_pages and final.pending == ()
    assert [item.id for item in final.files] == ["deed"]
    assert not google.steps


@pytest.mark.parametrize("size", [9000, 10000])
def test_complete_unframed_pdf_fits_the_byte_budget(size):
    body = (ROOT / CORPUS["appointment_media"]["path"]).read_bytes().ljust(size, b" ")

    class Chunks(SyncByteStream):
        def __iter__(self):
            yield body[:8192]
            yield body[8192:]

    with Client(transport=MockTransport(lambda _: Response(200, stream=Chunks()))) as http:
        action = Action(Limits(action_bytes=10000), Usage())
        reader = WorkspaceReader(http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
        assert reader.read("https://example.test/pdf", {}, action) == body
        assert action.used.bytes == size


@pytest.mark.parametrize("allowance, first, excess", [(8, 8, 1), (10000, 8192, 8192)])
def test_unframed_overflow_charges_one_excess_chunk_and_stops(allowance, first, excess):
    class Chunks(SyncByteStream):
        def __iter__(self):
            yield b"x" * first
            yield b"x" * excess
            pytest.fail("read beyond the chunk that established overflow")

    with Client(transport=MockTransport(lambda _: Response(200, stream=Chunks()))) as http:
        action = Action(Limits(action_bytes=allowance), Usage())
        reader = WorkspaceReader(http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
        with pytest.raises(LimitReached, match="Action byte limit"):
            reader.read("https://example.test/pdf", {}, action)
        assert action.used.bytes == action.session.bytes == first + excess


@pytest.mark.parametrize("length, suffix, expected_bytes", [
    ("3", b"!", 4),        # More bytes arrive after the declared end.
    ("5", b"", 3),         # Early EOF.
    (None, None, 3),       # Read failure after a partial chunk.
])
def test_incomplete_or_misframed_read_charges_consumed_bytes(length, suffix, expected_bytes):
    class Chunks(SyncByteStream):
        def __iter__(self):
            yield b"abc"
            if suffix is None:
                raise ReadError("stream interrupted")
            if suffix:
                yield suffix
                pytest.fail("read beyond the declared length mismatch")

    headers = {"Content-Length": length} if length else {}
    with Client(transport=MockTransport(lambda _: Response(200, headers=headers, stream=Chunks()))) as http:
        action = Action(Limits(), Usage())
        reader = WorkspaceReader(http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
        with pytest.raises(ReadFailure):
            reader.read("https://example.test/pdf", {}, action)
        assert action.session.bytes == expected_bytes


def test_pending_original_hits_are_inspected_before_advancing_the_mail_cursor():
    google = Exchanges()
    google.list_mail("Alder Trust", ["06", "05", "04", "03", "02", "01"], next_token="p2")
    for key in ("01", "02", "03", "04", "05"):
        google.message(key, "metadata")
        google.message(key, "full")
    google.list_files("Alder Trust", [])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    first = session.start("Alder Trust")
    assert first.pending == ("06",) and first.more_pages

    google.message("06", "metadata")
    google.message("06", "full")
    second = session.inspect_more()
    assert second.pending == () and second.more_pages
    assert second.inspected == ("01", "02", "03", "04", "05", "06")

    google.list_mail("Alder Trust", ["06", "07"], token="p2")
    google.message("07", "metadata")
    final = session.inspect_more()
    assert final.skipped == ("07",) and not final.more_pages
    assert final.inspected == second.inspected
    assert not google.steps
