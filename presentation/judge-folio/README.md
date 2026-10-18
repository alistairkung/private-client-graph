# Private Client Graph judge folio

A bilingual portrait editorial product/research publication for independent reading
in the university competition's Private Wealth category. English occupies pages
1-20; the complete Simplified Chinese edition follows on pages 21-40.
The finished submission is [the PDF](../../output/pdf/private-client-graph-judge-folio.pdf),
1,931,700 bytes, comfortably below the strict 20,000,000-byte limit.
See [DIRECTION.md](DIRECTION.md) for the concepts and approved format decision,
[PROVENANCE.md](PROVENANCE.md) for sources, [PANEL_REVIEW.md](PANEL_REVIEW.md) for
the four simulated judges' feedback and revisions, and [QA.md](QA.md) for final review.

## Reproduce and check the submission

From the repository root, with Python 3.12 or newer:

```sh
uv run --no-project --with-requirements presentation/judge-folio/requirements.txt \
  python presentation/judge-folio/build.py
uv run --no-project --with-requirements presentation/judge-folio/requirements.txt \
  python presentation/judge-folio/verify.py
uv run --no-project --with-requirements presentation/judge-folio/requirements.txt \
  python presentation/judge-folio/test_localization.py
```

Output: `output/pdf/private-client-graph-judge-folio.pdf`.
Add `--sample` to rebuild the four representative English checkpoint pages,
`--english-only` for a twenty-page English editorial review copy, or use
`--output /path/to/copy.pdf` for a comparison build.
The build is offline after dependencies are installed. It reads project fonts,
existing product captures and the immutable published research JSON; it invokes
no application, provider, evaluator or production mutation. Text, chart captions
and diagrams remain editable in `pages.py`, `product_pages.py`,
`research_pages.py` and `editorial_pages.py`. `build.py` owns page order; shared
geometry and typography live in `layout.py`. Original research records and
screenshots are never modified.

Reviewed Simplified Chinese copy lives in `zh_product.json` and `zh_research.json`.
`localization.py` requires an explicit translation for every non-numeric rendered
string, so changed English copy cannot silently leave untranslated Chinese pages.
Documentary quotations, personal names and original screenshot pixels retain
their English evidence; Chinese captions explain them. Page references and
bookmarks follow the continuous forty-page numbering.

For visual inspection:

```sh
pdftoppm -scale-to 1080 -png \
  output/pdf/private-client-graph-judge-folio.pdf \
  presentation/judge-folio/.build/full
```

Fonts are converted from the existing licensed WOFF2 files and subset-embedded:
Public Sans and Newsreader for English, Noto Sans SC and Noto Serif SC for Chinese.
Public Sans's Latin subset lacks the mathematical prime, so that single glyph
uses the project's Newsreader font. The output is selectable vector text with
real hyperlink annotations, not a collection of page screenshots.

## Boundaries

- Application, evaluation, benchmark and private experiment records are read-only.
- No paid model calls are authorized or made for this task.
- Existing untracked Remotion and practitioner-next work is not included.
- Full production followed the user's approved rendered-sample checkpoint.
- The finished submission must be strictly below 20,000,000 bytes.

The build uses fixed PDF metadata for reproducibility. This is not a PDF/UA
accessibility claim; the PDF currently has selectable text but is not tagged.
