"""Deterministically acquire authoritative text from a request-local PDF."""

from io import BytesIO
import unicodedata

from pypdf import PdfReader
from pypdf.errors import PyPdfError


PAGE_SEPARATOR = "\n\n"
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_SOURCE_CHARACTERS = 100_000


class PdfAcquisitionError(Exception):
    """A safe acquisition failure without file content or parser details."""

    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def extract_pdf_source(pdf: bytes) -> str:
    if len(pdf) > MAX_PDF_BYTES:
        raise PdfAcquisitionError("pdf_too_large", "Select a PDF no larger than 10 MiB.")
    if not pdf.startswith(b"%PDF-"):
        raise PdfAcquisitionError("invalid_pdf", "Select a valid text-layer PDF.")
    try:
        return _read_pdf_source(pdf)
    except PdfAcquisitionError:
        raise
    except PyPdfError:
        raise PdfAcquisitionError(
            "invalid_pdf", "Select a valid text-layer PDF."
        ) from None
    except Exception:
        raise PdfAcquisitionError(
            "pdf_acquisition_failed",
            "PDF text acquisition is temporarily unavailable. Retry with the same PDF.",
            retryable=True,
        ) from None


def _read_pdf_source(pdf: bytes) -> str:
    reader = PdfReader(BytesIO(pdf), strict=True)
    if reader.is_encrypted:
        raise PdfAcquisitionError("encrypted_pdf", "Select an unencrypted text-layer PDF.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise PdfAcquisitionError(
            "pdf_too_many_pages", "Select a PDF containing no more than 50 pages."
        )
    page_texts: list[str] = []
    character_count = 0
    for page in reader.pages:
        text = _normalize_page_text(page.extract_text())
        character_count += len(text) + (len(PAGE_SEPARATOR) if page_texts else 0)
        if character_count > MAX_SOURCE_CHARACTERS:
            raise PdfAcquisitionError(
                "source_too_long",
                "Select a PDF with no more than 100,000 extracted characters.",
            )
        page_texts.append(text)
    source = PAGE_SEPARATOR.join(page_texts)
    if not source.strip():
        raise PdfAcquisitionError(
            "pdf_not_extractable",
            "Select a PDF containing extractable text. OCR is unsupported.",
        )
    return source


def _normalize_page_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(
        character
        for character in normalized
        if character in "\t\n" or unicodedata.category(character) != "Cc"
    )
