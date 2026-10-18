"""Check the finished PDF's integrity and retained-evidence contract offline."""

import hashlib
import json
import re
from urllib.parse import urlparse

from pypdf import PdfReader
from pypdf.generic import ContentStream

from build import FULL_PAGES
from layout import HEIGHT, ROOT, WIDTH


PUBLICATION_SHA256 = "7f2c9370e0799aa639ca5cfbd08826591c81f6186da1d928d2ef190c3ff5b927"


def verify(path):
    size = path.stat().st_size
    assert 0 < size < 20_000_000, "Submission must be strictly below 20 MB"
    reader = PdfReader(path, strict=True)
    assert not reader.is_encrypted
    assert len(reader.pages) == len(FULL_PAGES)
    assert len(reader.outline) == len(FULL_PAGES)
    texts, links, fonts = [], set(), set()
    for number, page in enumerate(reader.pages, start=1):
        assert tuple(float(value) for value in page.mediabox) == (0, 0, WIDTH, HEIGHT)
        text = page.extract_text()
        assert len(text) > 500, f"Page {number} has no substantial selectable text"
        assert not any(glyph in text for glyph in ("\ufffd", "\u25a0", "\x00"))
        texts.append(text)
        fonts.update(_check_embedded_text_fonts(page, reader))
        for reference in page.get("/Annots", []):
            annotation = reference.get_object()
            url = annotation.get("/A", {}).get("/URI")
            if url:
                parsed = urlparse(url)
                assert parsed.scheme == "https" and parsed.netloc
                links.add(url)

    full_text = re.sub(r"\s+", " ", " ".join(texts))
    for required in (
        "Author a case hypothesis", "Build development test cases",
        "Build a separate held-out test set", "Measure and plot in the Workbench",
        "Build the surrounding application", "20 roadmap scenarios",
        "5 authored development cases", "10 separate held-out cases",
        "94.87%", "100%", "36/39", "37/41", "9,821 tokens",
        "not an independent replication", "post-hoc", "unpriced",
    ):
        assert required in full_text, f"Missing required content: {required}"

    publication = ROOT / "private_client_graph/published/research-results.v1.json"
    assert hashlib.sha256(publication.read_bytes()).hexdigest() == PUBLICATION_SHA256
    return {
        "pdf": str(path.relative_to(ROOT)), "pages": len(reader.pages),
        "bytes": size, "limit_bytes_exclusive": 20_000_000,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "page_size_points": [WIDTH, HEIGHT], "bookmarks": len(reader.outline),
        "embedded_text_fonts": sorted(fonts), "unique_links": sorted(links),
        "publication_sha256": PUBLICATION_SHA256,
        "checks": "Passed integrity, size, selectable text, glyphs, fonts, bookmarks and required content. Link destinations need separate network or repository verification; layout needs visual review.",
    }


def _check_embedded_text_fonts(page, reader):
    """Check fonts actually used to draw text, excluding unused default Helvetica."""
    fonts = page["/Resources"]["/Font"]
    used = set()
    current = None
    for operands, operator in ContentStream(page.get_contents(), reader).operations:
        if operator == b"Tf":
            current = operands[0]
        elif operator in (b"Tj", b"TJ", b"'", b'"'):
            font = fonts[current].get_object()
            descriptor = font.get("/FontDescriptor")
            assert descriptor is not None, f"Unembedded text font: {font}"
            descriptor = descriptor.get_object()
            assert any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
            used.add(str(font["/BaseFont"]))
    return used


if __name__ == "__main__":
    print(json.dumps(verify(ROOT / "output/pdf/private-client-graph-judge-folio.pdf"), indent=2))
