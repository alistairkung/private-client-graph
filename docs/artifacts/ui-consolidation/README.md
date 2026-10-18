# UI consolidation review evidence

Captured from the combined production `web/dist` build and the real local API,
using a migrated/seeded disposable database. Google and extraction boundaries
use the existing test substitutes. All shown records are synthetic; no paid
provider call or production mutation was made.

- [Document montage](landing-documents-desktop.png)
- [Landing graph beside full Source and exact Evidence](landing-evidence-desktop.png)
- [Phone transition from forest story into substantive content](landing-boundary-phone.png)
- [Practitioner graph, Evidence and independently scrolling Source](practitioner-evidence-desktop.png)
- [Phone Source and selected exact Evidence](practitioner-evidence-phone.png)
- [Hillcrest corroboration across two Sources](curated-multiple-sources-desktop.png)
- [Retained research graph and Source inspection](research-evidence-desktop.png)
- [Short landing walkthrough](landing-walkthrough.webm)

Visual review caught the added publication notice pushing the desktop Evidence
panel below the viewport. The final capture shows the corrected layout; strict
bounds assertions cover both persisted Matter and curated multi-source review.
The landing keeps one forest field through the story and acceptance explanation,
then changes to a substantive light research section. Phone wrapping, exact
highlights and the distinct retained research presentation were also inspected.

See the [parity and launch guide](../../workflows/ui-consolidation.md).

## Linux phone-label regression

[Before](landing-labels-linux-before.png) · [After](landing-labels-linux-after.png)

The official Linux Playwright runtime reproduced two parent labels overlapping
at 320px: 2.39px horizontally and 6px vertically. The diagonal label now sits
higher on its existing connector. Both captures use the actual Linux font
metrics; the regression additionally reserves 60px-wide labels and tests
fractional positioning. Source selection and all collision limits remain intact.
