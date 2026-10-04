from pathlib import Path

import pytest

from private_client_graph.application import pdf_acquisition
from private_client_graph.application.pdf_acquisition import (
    PdfAcquisitionError,
    extract_pdf_source,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_acquisition_returns_the_exact_finalized_source_from_a_real_pdf():
    source = extract_pdf_source((FIXTURES / "synthetic-proposal.pdf").read_bytes())

    assert source == "Alice Example is the parent of Ben Example."


def test_pages_keep_unicode_and_spacing_with_only_minimal_normalization():
    source = extract_pdf_source((FIXTURES / "normalization.pdf").read_bytes())

    assert source == (
        "  Résumé\tA  B\nwrapped-\nword\n\n\u00a0\u200dend  "
        "\n\nSecond page.\n"
    )


@pytest.mark.parametrize("extra_bytes", [0, 1])
def test_upload_size_limit_is_inclusive(extra_bytes):
    pdf = (FIXTURES / "synthetic-proposal.pdf").read_bytes()
    pdf = pdf.ljust(10 * 1024 * 1024 + extra_bytes, b" ")

    if extra_bytes:
        with pytest.raises(PdfAcquisitionError) as caught:
            extract_pdf_source(pdf)
        assert caught.value.code == "pdf_too_large"
        assert "10 MiB" in caught.value.message
        assert not caught.value.retryable
    else:
        assert extract_pdf_source(pdf) == "Alice Example is the parent of Ben Example."


@pytest.mark.parametrize("pdf", [b"", b"This is text, not a PDF."])
def test_a_pdf_signature_is_required(pdf):
    with pytest.raises(PdfAcquisitionError) as caught:
        extract_pdf_source(pdf)

    assert caught.value.code == "invalid_pdf"
    assert not caught.value.retryable


@pytest.mark.parametrize("filename", ["malformed.pdf", "malformed-text-stream.pdf"])
def test_a_malformed_pdf_is_reported_without_parser_details(filename):
    with pytest.raises(PdfAcquisitionError) as caught:
        extract_pdf_source((FIXTURES / filename).read_bytes())

    assert caught.value.code == "invalid_pdf"
    assert caught.value.message == "Select a valid text-layer PDF."
    assert not caught.value.retryable


def test_encrypted_pdfs_are_rejected_without_requesting_a_password():
    with pytest.raises(PdfAcquisitionError) as caught:
        extract_pdf_source((FIXTURES / "encrypted.pdf").read_bytes())

    assert caught.value.code == "encrypted_pdf"
    assert "unencrypted" in caught.value.message
    assert not caught.value.retryable


@pytest.mark.parametrize("filename", ["fifty-pages.pdf", "fifty-one-pages.pdf"])
def test_page_limit_is_inclusive(filename):
    pdf = (FIXTURES / filename).read_bytes()

    if filename == "fifty-one-pages.pdf":
        with pytest.raises(PdfAcquisitionError) as caught:
            extract_pdf_source(pdf)
        assert caught.value.code == "pdf_too_many_pages"
        assert "50 pages" in caught.value.message
    else:
        assert extract_pdf_source(pdf) == "\n\n".join(["A"] * 50)


@pytest.mark.parametrize(
    "filename",
    ["source-at-limit.pdf", "source-over-limit.pdf", "page-separator-over-limit.pdf"],
)
def test_finalized_source_character_limit_is_inclusive(filename):
    pdf = (FIXTURES / filename).read_bytes()

    if filename != "source-at-limit.pdf":
        with pytest.raises(PdfAcquisitionError) as caught:
            extract_pdf_source(pdf)
        assert caught.value.code == "source_too_long"
        assert "100,000" in caught.value.message
    else:
        assert extract_pdf_source(pdf) == "A" * 100000


def test_character_limit_counts_normalized_unicode_characters_not_bytes():
    source = extract_pdf_source((FIXTURES / "normalized-source-at-limit.pdf").read_bytes())

    assert source == "é" * 99999 + "\n"


@pytest.mark.parametrize(
    "filename",
    ["no-pages.pdf", "blank.pdf", "whitespace.pdf", "controls-only.pdf", "image-only.pdf"],
)
def test_pdfs_without_non_whitespace_text_are_rejected_without_ocr(filename):
    with pytest.raises(PdfAcquisitionError) as caught:
        extract_pdf_source((FIXTURES / filename).read_bytes())

    assert caught.value.code == "pdf_not_extractable"
    assert "OCR is unsupported" in caught.value.message
    assert not caught.value.retryable


def test_unexpected_acquisition_service_failure_is_safe_and_retryable(monkeypatch):
    def unavailable_reader(*args, **kwargs):
        raise RuntimeError("private parser diagnostic")

    monkeypatch.setattr(pdf_acquisition, "PdfReader", unavailable_reader)

    with pytest.raises(PdfAcquisitionError) as caught:
        extract_pdf_source((FIXTURES / "synthetic-proposal.pdf").read_bytes())

    assert caught.value.code == "pdf_acquisition_failed"
    assert caught.value.retryable
    assert "private parser diagnostic" not in str(caught.value)
