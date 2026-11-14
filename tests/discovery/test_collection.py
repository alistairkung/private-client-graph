"""A reviewed collection is a one-use, private snapshot of exact provider reads."""
from datetime import datetime, timezone

import pytest

from local_development.workspace import message_response

from private_client_graph.application.discovery import DiscoverySession, WorkspaceScope
from private_client_graph.application.discovery.collection import Candidate, CollectionReview, PreviewProgress, ReviewPreview
from private_client_graph.application.proposal_errors import ProposalFailure

from .exchanges import CORPUS, FILES, MAIL, ROOT, Exchanges, file


def prepare():
    google = Exchanges()
    google.list_mail("Alder Trust", ["06"])
    google.message("06", "metadata")
    google.message("06", "full")
    google.list_files("Alder Trust", ["appointment"])
    discovery = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    discovery.start("Alder Trust")
    return google, CollectionReview(discovery)


def pdf(google, *, content=None):
    media = CORPUS["appointment_media"]
    google.expect(FILES + "/appointment", {}, file("appointment"))
    google.expect(FILES + "/appointment", {"alt": "media"}, content or (ROOT / media["path"]).read_bytes())
    google.expect(FILES + "/appointment", {}, file("appointment"))


def message(google, **kwargs):
    google.message("06", "metadata")
    google.message("06", "full", **kwargs)


PDF = Candidate(kind="pdf", id="appointment")
EMAIL = Candidate(kind="email", id="06")


def test_reading_an_email_checks_access_and_preserves_the_reviewed_collection():
    google, review = prepare()
    pdf(google)
    preview = review.preview([PDF])
    message(google)
    email = review.read_email("06")
    assert email.title == "Alder Trust correspondence 06"
    assert email.text == CORPUS["messages"][5]["body"]
    google.message("06", "metadata", labels=["INBOX"])
    with pytest.raises(ProposalFailure) as denied:
        review.read_email("06")
    assert denied.value.error.code == "source_unavailable"
    pdf(google)
    assert review.approve(preview.token) == preview.sources
    assert not google.steps


def test_envelope_is_private_and_keeps_copied_addresses_and_distinct_dates():
    google, review = prepare()
    record = CORPUS["messages"][5]
    full = message_response(record, "full")
    headers = full["payload"]["headers"]
    headers[:] = [header for header in headers if header["name"] != "Date"]
    headers.extend([
        {"name": "cC", "value": '"Patel, Cora" <cora@example.test>'},
        {"name": "CC", "value": "leo@example.test"},
        {"name": "Bcc", "value": "mara@example.test"},
        {"name": "Date", "value": "Mon, 5 Jan 2026 09:30:00 +0800"},
    ])

    def queue_read():
        google.message("06", "metadata")
        google.expect(MAIL + "/06", {"format": "full"}, full)

    queue_read()
    email = review.read_email("06")
    assert email.sender == "corpus@example.invalid" and email.to == "synthetic@example.test"
    assert email.cc == '"Patel, Cora" <cora@example.test>, leo@example.test'
    assert email.bcc == "mara@example.test"
    assert email.sent_at == datetime(2026, 1, 5, 1, 30, tzinfo=timezone.utc)
    assert email.gmail_timestamp_ms == int(record["internalDate"])
    queue_read()
    assert review.preview([EMAIL]).sources[0].model_dump() == {
        "id": "source_001", "title": record["subject"], "text": record["body"],
    }


@pytest.mark.parametrize("date_header", ["", "unreadable", "Mon, 5 Jan 2026 09:30:00"])
def test_reader_does_not_invent_a_sent_time_or_hidden_recipients(date_header):
    google, review = prepare()
    full = message_response(CORPUS["messages"][5], "full")
    full["payload"]["headers"] = [
        {"name": "Date", "value": date_header}
    ] if date_header else []
    google.message("06", "metadata")
    google.expect(MAIL + "/06", {"format": "full"}, full)
    email = review.read_email("06")
    assert email.sent_at is None and email.gmail_timestamp_ms == int(full["internalDate"])
    assert (email.sender, email.to, email.cc, email.bcc) == ("", "", "", "")


def test_review_revalidates_order_and_issues_distinct_local_source_ids():
    google, review = prepare()
    pdf(google)
    message(google)
    preview = review.preview([PDF, EMAIL])
    pdf(google)
    message(google)
    sources = review.approve(preview.token)
    assert sources == preview.sources
    assert [(s.id, s.title) for s in sources] == [
        ("source_001", "Mara Voss appointment"), ("source_002", "Alder Trust correspondence 06")]
    assert sources[0].text == "Alice Example is the parent of Ben Example."
    with pytest.raises(ProposalFailure):
        review.approve(preview.token)
    assert not google.steps


@pytest.mark.parametrize("change", ["bytes", "message", "denied", "folder", "label", "identity"])
def test_drift_invalidates_preview_before_sources_can_enter_analysis(change):
    google, review = prepare()
    email = change in {"message", "denied", "label", "identity"}
    (message if email else pdf)(google)
    preview = review.preview([EMAIL if email else PDF])
    if change == "bytes":
        pdf(google, content=(ROOT / CORPUS["appointment_media"]["path"]).read_bytes() + b"\n")
    elif change == "message":
        message(google, body="Changed synthetic text")
    elif change == "denied":
        google.expect(MAIL + "/06", {}, {}, 403)
    elif change == "folder":
        google.expect(FILES + "/appointment", {}, {**file("appointment"), "parents": ["elsewhere"]})
    elif change == "identity":
        google.expect(MAIL + "/06", {}, CORPUS["messages"][1])
    else:
        google.message("06", "metadata", labels=["INBOX"])
    with pytest.raises(ProposalFailure):
        review.approve(preview.token)
    with pytest.raises(ProposalFailure):
        review.approve(preview.token)
    assert not google.steps


def test_selection_limits_and_preview_replacement(monkeypatch):
    from private_client_graph.application.discovery import collection

    google, review = prepare()
    for invalid in ([], [EMAIL, EMAIL], [Candidate(kind="email", id=str(i)) for i in range(6)]):
        with pytest.raises(ProposalFailure):
            review.preview(invalid)
    message(google)
    original = review.preview([EMAIL])
    pdf(google)
    current = review.preview([PDF])
    with pytest.raises(ProposalFailure):
        review.approve(original.token)
    pdf(google)
    assert review.approve(current.token) == current.sources

    # Set boundaries to the exact fixture size; the second Source exceeds the total.
    monkeypatch.setattr(collection, "MAX_SOURCE_CHARACTERS", len(CORPUS["messages"][5]["body"]))
    message(google)
    pdf(google)
    with pytest.raises(ProposalFailure, match="100,000 characters"):
        review.preview([EMAIL, PDF])
    monkeypatch.setattr(collection, "MAX_TOTAL_PDF_BYTES", 10)
    pdf(google)
    with pytest.raises(ProposalFailure, match="10 MiB"):
        review.preview([PDF])
    assert not google.steps


def test_pdf_revision_can_be_reviewed_again_and_approved():
    google, review = prepare()
    pdf(google)
    first = review.preview([PDF])
    latest = {**file("appointment"), "name": "Revised appointment", "version": "2"}
    path = FILES + "/appointment"
    for _ in range(3):
        google.expect(path, {}, latest)
        google.expect(path, {"alt": "media"}, (ROOT / CORPUS["appointment_media"]["path"]).read_bytes())
        google.expect(path, {}, latest)
    with pytest.raises(ProposalFailure):
        review.approve(first.token)
    updated = review.preview([PDF])
    assert review.approve(updated.token)[0].title == "Revised appointment"
    assert not google.steps


def test_binary_digest_at_pdf_parser_boundary(monkeypatch):
    from hashlib import sha256

    from private_client_graph.application.discovery import google as reader
    from private_client_graph.application.pdf_acquisition import extract_pdf_source

    digests = []

    def parse(media):
        digests.append(sha256(media).hexdigest())
        return extract_pdf_source(media)

    monkeypatch.setattr(reader, "extract_pdf_source", parse)
    google, review = prepare()
    pdf(google)
    preview = review.preview([PDF])
    pdf(google)
    review.approve(preview.token)
    assert digests == [CORPUS["appointment_media"]["sha256"]] * 2


def test_full_original_collection_plus_followup_can_be_reviewed_and_revalidated():
    google = Exchanges()
    keys = [f"mail{i:02}" for i in range(50)]
    row = CORPUS["messages"][5]

    def queue_mail(key):
        for fmt in ("metadata", "full"):
            google.expect(MAIL + "/" + key, {"format": fmt}, message_response({**row, "id": key}, fmt))

    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    for offset in range(0, 50, 5):
        if offset == 5:
            google.list_files("Alder Trust", [])
        google.list_mail("Alder Trust", keys[offset:offset + 5],
                         token=str(offset) if offset else None,
                         next_token=str(offset + 5) if offset < 45 else None)
        for key in keys[offset:offset + 5]:
            queue_mail(key)
        view = session.inspect_more() if offset else session.start("Alder Trust")
    google.list_mail("Mara Voss", [])
    google.list_files("Mara Voss", ["appointment"])
    session.approve(view.revision, "Mara Voss")

    selected = [Candidate(kind="email", id=key) for key in reversed(keys)] + [PDF]
    review = CollectionReview(session)
    for candidate in selected[:-1]:
        queue_mail(candidate.id)
    pdf(google)
    result = review.preview(selected)
    for count in range(5, 51, 5):
        assert isinstance(result, PreviewProgress)
        assert (result.completed, result.total) == (count, 51)
        with pytest.raises(ProposalFailure, match="Preview the selected Sources again"):
            review.approve(result.continuation)
        used = result.continuation
        result = review.continue_preview(used)
        with pytest.raises(ProposalFailure):
            review.continue_preview(used)
    assert isinstance(result, ReviewPreview)
    for candidate in selected[:-1]:
        queue_mail(candidate.id)
    pdf(google)
    sources = review.approve(result.token)
    assert sources == result.sources
    assert len(sources) == 51
    assert (sources[-1].id, sources[-1].title) == ("source_051", "Mara Voss appointment")
    assert not google.steps


@pytest.mark.parametrize("denied", [False, True], ids=["changed", "access-lost"])
def test_last_batch_identifies_failed_item_and_allows_a_revised_collection(denied):
    google = Exchanges()
    keys = ["01", "02", "03", "04", "05", "06"]

    def queue_message(key, **kwargs):
        google.message(key, "metadata")
        google.message(key, "full", **kwargs)

    google.list_mail("Alder Trust", keys[:5], next_token="page2")
    for key in keys[:5]:
        queue_message(key)
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    session.start("Alder Trust")
    google.list_files("Alder Trust", [])
    google.list_mail("Alder Trust", keys[5:], token="page2")
    queue_message("06")
    session.inspect_more()
    review = CollectionReview(session)
    selected = [Candidate(kind="email", id=key) for key in keys]
    for _ in range(2):
        for key in keys[:5]:
            queue_message(key)
    first = review.preview(selected)
    restarted = review.preview(selected)
    assert isinstance(first, PreviewProgress) and isinstance(restarted, PreviewProgress)
    with pytest.raises(ProposalFailure):
        review.continue_preview(first.continuation)
    queue_message("06")
    ready = review.continue_preview(restarted.continuation)
    assert isinstance(ready, ReviewPreview)
    for key in keys[:5]:
        queue_message(key)
    if denied:
        google.message("06", "metadata", labels=["INBOX"])
    else:
        queue_message("06", body="Changed after review")
    with pytest.raises(ProposalFailure) as changed:
        review.approve(ready.token)
    assert changed.value.error.source_number == 6
    assert changed.value.error.code == ("source_unavailable" if denied else "source_changed")
    with pytest.raises(ProposalFailure):
        review.approve(ready.token)
    for _ in range(2):
        for key in keys[:5]:
            queue_message(key)
    revised = review.preview(selected[:-1])
    assert isinstance(revised, ReviewPreview)
    assert review.approve(revised.token) == ready.sources[:-1]
    assert not google.steps


@pytest.mark.parametrize("over_limit", ["pdf", "characters"])
def test_final_batch_enforces_whole_collection_limit_without_a_publishable_prefix(monkeypatch, over_limit):
    from private_client_graph.application.discovery import collection
    from local_development.workspace import fixture_client

    session = DiscoverySession(fixture_client(), WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"))
    view = session.start("Alder Trust")
    while view.can_inspect_more:
        view = session.inspect_more()
    mail = [Candidate(kind="email", id=key) for key in view.inspected[:4]]
    selected = [Candidate(kind="pdf", id="deed"), *mail, Candidate(kind="pdf", id="minutes")]
    # Both synthetic listing fixtures return the original, identical PDF bytes.
    size = len((ROOT / CORPUS["appointment_media"]["path"]).read_bytes())
    if over_limit == "pdf":
        monkeypatch.setattr(collection, "MAX_TOTAL_PDF_BYTES", size * 2 - 1)
    else:
        texts = {item["id"]: item["body"] for item in CORPUS["messages"]}
        first_batch_chars = len("Alice Example is the parent of Ben Example.") + sum(len(texts[item.id]) for item in mail)
        monkeypatch.setattr(collection, "MAX_SOURCE_CHARACTERS", first_batch_chars)
    review = CollectionReview(session)
    progress = review.preview(selected)
    assert isinstance(progress, PreviewProgress)
    with pytest.raises(ProposalFailure) as oversized:
        review.continue_preview(progress.continuation)
    assert oversized.value.error.code == ("pdf_too_large" if over_limit == "pdf" else "collection_text_limit")
    with pytest.raises(ProposalFailure):
        review.approve(progress.continuation)
    with pytest.raises(ProposalFailure):
        review.continue_preview(progress.continuation)


def test_repeated_previews_share_a_finite_review_budget():
    from private_client_graph.application.discovery import Limits

    google = Exchanges()
    google.list_mail("Alder Trust", ["06"])
    message(google)
    google.list_files("Alder Trust", [])
    session = DiscoverySession(google.http, WorkspaceScope("synthetic@example.test", "alder-label", "folder-1"),
                               Limits(action_requests=4))
    session.start("Alder Trust")
    review = CollectionReview(session)
    for _ in range(6):
        message(google)
        review.preview([EMAIL])
    with pytest.raises(ProposalFailure) as exhausted:
        review.preview([EMAIL])
    assert exhausted.value.error.code == "review_limit"
    assert not google.steps
