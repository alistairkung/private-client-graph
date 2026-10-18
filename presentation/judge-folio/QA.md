# Final validation

Reviewed 18 October 2026. Final publication: 40 pages, 720 x 900 points,
1,931,700 bytes (1.93 decimal MB); strict limit is below 20,000,000 bytes.
English occupies pp. 1-20; the complete Simplified Chinese edition follows on
pp. 21-40. Machine-readable integrity results and final SHA-256 are in
`validation.json`.

## Creative and scientific review

The author approved the four-page rendered checkpoint and visual direction
before full production. The five-step case-led development method, twenty-scenario
hypothesis roadmap, five authored development cases, ten separate held-out cases,
and baseline plus constrained resolver remain explicit.

Four independent agent reviewers simulated two technical and two Private Wealth
industry judges, calibrated to a university hackathon. `PANEL_REVIEW.md` records
their feedback and revisions: earlier category/use-case framing, the built-system
summary, a concrete inspection task, clearer resolver constraints, the correction
example before aggregates, the full roadmap after completed findings, and a
practical demo route. These are simulated reviews, not actual judge endorsements.
The technical reviewer re-inspected revised pp. 12, 13, 14 and 20 and returned
**SHIP**, with no remaining blockers.

The original English edition received a complete rendered-page review and an
independent source-evidence review. Changed English compositions were inspected
again after this round. An independent bilingual reviewer inspected every Chinese
page and the translation copy. A quotation/caption collision on p. 22 was fixed
by preserving original Latin typography for English-only quotations. Wording on
p. 37 now distinguishes replaying saved results from obtaining the same response
on a new model call. Both rebuilt pages passed re-inspection: **SHIP**.

## Artifact checks

- Poppler successfully rendered every final page. The language order and matching
  content sequence were checked, with continuous numbering and localized routes.
- The PDF reopens with strict parsing; all 42 bookmarks (two language roots plus
  forty page entries) resolve correctly, and every page has the expected size.
- Text is selectable and searchable. All fonts drawing text are embedded; unused
  default Helvetica is ignored. No replacement, black-square or null glyphs were
  found. Build-time glyph checks reject unsupported characters before output.
- Documentary quotations remain verbatim in the translated edition. Chinese
  captions explain their original-English status; authentic screenshots remain
  untouched. Translation lookup fails for missing copy rather than silently
  falling back to English.
- A second build to a different output path is byte-for-byte identical. Font
  conversion retains original timestamps; PDF metadata is fixed.
- The eighteen unique hyperlink destinations are unchanged from the successful
  18 October HTTP checks recorded in `link-checks.json`. Research links need
  browser-style GET/HTML requests; HEAD returned 404. Pinned targets were also
  checked against Git.
- Publication JSON SHA-256 is unchanged. Metrics, case chart values, exact alias
  passage, endpoint edits and approved/returned spans use that JSON directly.
- Original screenshot pixels remain intact; clipping is performed by the PDF.
  Historical/local/curated/retained observations carry provenance captions.

## Repository validation and self-review

`uv run pytest`: **531 passed, 208 skipped**. Skips are PostgreSQL persistence and
integration tests requiring a disposable `TEST_DATABASE_URL`, not configured for
this document-only task. No application or evaluation behaviour changed.

Focused publication tests: **5 passed**, including missing-copy rejection,
unsupported-language rejection, continuous page numbering, English quotation
layout stability within the Chinese edition, and missing-glyph rejection.
The forty-page artifact verifier also passes all integrity and evidence checks.

The complete changed source was reviewed against `docs/CODE_STYLE.md` and the
repository boundaries after validation. Page content remains in focused modules;
explicit translation copy and strict lookup are separate from drawing mechanics.
The quotation-layout fix is covered by a regression test. No domain, evaluation
or application abstractions were added, and no material readability concern
remains.

## Practical qualifications

The publication is an independently readable bilingual editorial case study.
It is not PDF/UA tagged; no accessibility-conformance claim is made. Original
product detail crops are slightly softer than vector text but legible. Experimental
limitations and the synthetic-only product boundary are stated in both editions.

Paid provider calls for this task: **0**. No production changes, research reruns,
benchmark mutations, deployment or automatic merge.
