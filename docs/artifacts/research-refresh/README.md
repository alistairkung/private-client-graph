# Research-results refresh evidence

The [interaction brief](../../design/research-results-interaction-refresh.md)
records the design decisions, authenticated Motion+ source inspection and team
ledger. The deployed original was also inspected in a live browser during the
resumed review on 2026-10-18.

## Captures

- [Original desktop page](before-desktop.png): before the redesign.
- [Final desktop opening](final-desktop-opening.png): Forest & Chalk overview,
  exact frozen-input comparison and adjacent research limitations.
- [Final desktop comparison](final-desktop-comparison.png) and
  [final phone comparison](final-phone-comparison.png): explicit A / A′ / B
  identities, discrete points and all three Run cards.
- [Narrow Chinese usage table, final columns](narrow-zh-usage-end.png): keyboard
  scrolling reaches the recorded-cost column and the B cost cell. The test also
  verifies retained focus and document overflow bounds.
- `desktop.png`, `phone-architecture.png` and `phone-comparison.png` are retained
  **initial redesign** captures from the previous chat. They predate the final
  A/A′/B chart labels and premium-informed motion revision.

The larger earlier before/after set remains locally under
`.impeccable/review/research-refresh/`. It is not all committed. Static captures
document layout, not animation timing or interruption behavior.

## Validation

Resumed validation logs are at `/private/tmp/pcg-research-ui-resume-*.log`.

| Check | Result |
| --- | --- |
| Full Python suite with disposable PostgreSQL | 739 passed |
| Frontend unit tests | 171 passed |
| Research Workbench unit tests | 26 passed |
| Production and Research Workbench builds | Passed |
| Final full application browser suite | 90 passed; 10 existing opt-in recording/viewport skips |
| Research Workbench browser suite | 16 passed; 2 existing narrow-only skips |

The first resumed application browser run passed 89 checks and exposed one
280px Chinese desktop overflow failure; 10 opt-in recording/viewport checks were
skipped. It reached the table's final cost column successfully before detecting
the wider page. The overview's intrinsic grid width caused the 12px overflow;
the fix constrains the grid track and reduces score spacing at widths up to
360px. Both 280px checks then passed with the original assertions, followed by
eight focused research checks and four opt-in frame-recording checks.

Forty browser animation frames per sequence were recorded for desktop and phone,
normal and reduced motion. Across all eight sequences, selected state and
resolver visibility agreed in every frame. In normal motion the indicator was
still travelling after the content switched and settled exactly at its target
by the final sampled frame; reduced motion had zero positional error in every
frame. Rapid A′ → B → A′ reversal also retained correct immediate contents.
These observations verify interruption and content continuity, not frame-rate
performance or a MotionScore grade. Raw data: [desktop reversal](run-reversal-frames-desktop-reduced-false.json),
[phone reversal](run-reversal-frames-phone-reduced-false.json),
[desktop reduced motion](run-reversal-frames-desktop-reduced-true.json) and
[phone reduced motion](run-reversal-frames-phone-reduced-true.json); the adjacent
selection-frame files record the first selection in each configuration.

To repeat this bounded evidence capture, run the research interaction browser
tests with `PCG_RESEARCH_EVIDENCE=1` and the repository's disposable database
configuration. The flag adds frame attachments and saves the narrow table image;
ordinary CI execution does not perform those additional frame observations.

The final full application rerun passed all 90 active checks. The resumed static
engineering review and its responsive-fix follow-up found no material readability
or boundary issue. The lead inspected the complete final diff, including new
tests, documentation and evidence; no further refactor was warranted and no
material readability concern was retained. Live desktop visual QA verified the full A/A′/B labels and immediate
selection/focus behavior. Its CUA surface could not emulate phone widths or
reduced motion, so those states are covered by the deterministic browser suite
and its screenshots rather than claimed as manually observed by that reviewer.
Visual QA's final inspection of the current phone/table captures found no
material remaining visual defect.

The Impeccable detector reported three existing border warnings: two transparent
triangle-arrow borders in the retained graph stylesheet and the shared chart's
original tab underline. Those are intentional geometry/selection indicators;
the public tactile variant removes the tab border. No unrelated style change was
made to silence them.

The publication is byte-for-byte unchanged from `01acde3e`. File SHA-256:
`7f2c9370e0799aa639ca5cfbd08826591c81f6186da1d928d2ef190c3ff5b927`.
No paid application-provider calls were made. No MotionScore audit is claimed.
