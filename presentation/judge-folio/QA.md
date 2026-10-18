# Final validation

Reviewed 18 October 2026. Final publication: 20 pages, 720 x 900 points,
1,648,196 bytes (1.65 decimal MB); strict limit is below 20,000,000 bytes.
Machine-readable integrity results and the final SHA-256 are in `validation.json`.

## Creative and scientific review

The user approved the four-page rendered checkpoint and visual direction before
full production. Subsequent author clarification is incorporated: the five-step
case-led development method, twenty-scenario hypothesis roadmap, five authored
development cases, ten separate held-out cases, and baseline plus constrained
resolver as the hackathon's measured slice.

The lead and an independent critic inspected all twenty actual rendered pages.
Review found a page 8 heading overlap, stale reading-route page numbers, and two
clarity improvements (held-out case labels and directional endpoint corrections).
All were fixed; the critic inspected the rebuilt affected pages and returned
**SHIP**, with no remaining blocking visual or substantive finding.

A separate read-only evidence reviewer checked claims, source targets and the
presentation source against published JSON, cases/README, current implementation
and ADRs. Verdict: **PASS**, with no material factual or maintainability defect.
The stale sample-only provenance inventory was expanded after this review.

## Artifact checks

- Poppler successfully rendered every final page. The last metadata/font-timestamp
  reproducibility change produced pixel-identical PNGs to all twenty reviewed pages.
- The PDF reopens with strict parsing; all twenty bookmarks and page dimensions
  are present. Text is selectable and searchable, including the A-prime glyph.
- Every font actually drawing text is embedded. Unused default Helvetica is
  ignored by the font check. No replacement, black-square or null glyphs were
  found in extracted text.
- A second build to a different output path was byte-for-byte identical. Font
  conversion retains original timestamps; PDF metadata is fixed.
- All eighteen unique hyperlinks resolve to HTTP 200. The two research links
  require browser-style GET/HTML requests; HEAD returned 404. Results are recorded
  in `link-checks.json`. Pinned repository targets were also checked against Git.
- Publication JSON SHA-256 is unchanged. Metrics, case chart values, exact alias
  passage, endpoint edits and approved/returned spans use that JSON directly.
- Original screenshot pixels remain intact; clipping is performed by the PDF.
  Historical/local/curated/retained observations carry their provenance captions.

## Repository validation and self-review

`uv run pytest`: **531 passed, 208 skipped**. Skips are PostgreSQL persistence and
integration tests requiring a disposable `TEST_DATABASE_URL`, not configured for
this document-only task. No application or evaluation behaviour changed.

The full changed source was reviewed against `docs/CODE_STYLE.md` and repository
boundaries after validation. Fixes included a shadowed result variable during
integration, grouped text runs for meaningful PDF text extraction, a two-line
heading guard, and stable font-conversion timestamps. Page content remains in
focused modules; no domain, evaluation or application abstractions were added.
No material readability concerns remain.

## Practical qualifications

The publication is an English, independently readable editorial case study. It is
not PDF/UA tagged; no accessibility-conformance claim is made. Original product
detail crops are slightly softer than vector text but legible. Experimental
limitations and the synthetic-only product boundary are stated in the document.

Paid provider calls for this task: **0**. No production changes, research reruns,
benchmark mutations, deployment or automatic merge.
