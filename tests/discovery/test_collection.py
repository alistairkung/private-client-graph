"""A reviewed collection is a one-use, private snapshot of exact provider reads."""
import pytest

from private_client_graph.application.discovery import DiscoverySession, WorkspaceScope
from private_client_graph.application.discovery.collection import Candidate, CollectionReview
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
    with pytest.raises(ProposalFailure, match="fewer or shorter"):
        review.preview([EMAIL, PDF])
    monkeypatch.setattr(collection, "MAX_TOTAL_PDF_BYTES", 10)
    pdf(google)
    with pytest.raises(ProposalFailure, match="fewer or shorter"):
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
