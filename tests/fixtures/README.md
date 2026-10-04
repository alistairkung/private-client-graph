# Synthetic PDF acquisition fixtures

All PDFs in this directory were generated locally for deterministic intake tests.
They contain no real client material and are not benchmark ground truth.

- `synthetic-proposal.pdf` is a one-page Helvetica document containing exactly
  `Alice Example is the parent of Ben Example.` It also drives the browser and
  API intake journeys.
- `normalization.pdf` has two pages with Unicode, repeated spaces, a tab,
  CRLF/CR/LF line endings, wrapped-word punctuation, and invalid controls. Its
  explicit ToUnicode map preserves these extraction inputs without mocking the
  PDF parser. The expected finalized value is a literal in the acquisition test.
- `fifty-pages.pdf` and `fifty-one-pages.pdf` have one `A` per page.
- `source-at-limit.pdf` and `source-over-limit.pdf` contain 100,000 and 100,001
  `A` characters, respectively. Their text streams are compressed.
- `normalized-source-at-limit.pdf` contains 99,999 `é` characters followed by
  CRLF and NUL, producing exactly 100,000 Unicode characters after normalization.
- `page-separator-over-limit.pdf` has 50,000 `A` characters on its first page and
  49,999 `B` characters on its second, exceeding the source limit only when the
  two-character page separator is included.
- `no-pages.pdf`, `blank.pdf`, `whitespace.pdf`, `controls-only.pdf`, and
  `image-only.pdf` exercise distinct non-extractable inputs. The image-only PDF
  contains a small grayscale image and no text layer.
- `encrypted.pdf` is the synthetic proposal encrypted with a fixture-only
  password; acquisition must reject it without prompting for a password.
- `malformed.pdf` has a PDF signature but no valid PDF structure.
  `malformed-text-stream.pdf` has a valid document structure and an unterminated
  text string, exercising failure during text extraction.

The admission tests pad the small proposal PDF with trailing whitespace in
memory to exercise the 10 MiB upload boundary without a large stored fixture.
