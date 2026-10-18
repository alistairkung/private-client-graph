# Landing delivery and verification

Draft PR #158 on `codex/landing-evidence-motion` continues the user's requested
stack on #157. The independent public page lives at https://127.0.0.1:5443/;
`/app` keeps its existing practitioner workflows. Original `web/`, backend, APIs,
domain, database, original tests and deployment are unchanged.

## Accepted experience

The user approved the isolated document-to-graph prototype for integration.
The landing now introduces “It begins with your documents”: attendance notes,
emails, time sheets and legal documents flick as the visitor scrolls, gather,
and release actual canonical names into the family and Trust drawing. SVG masks
draw the relationships, then that same graph shares a split view with the full
source and exact supporting Evidence. Phone layouts stack graph and source.

The added formats are explicitly illustrative product vision. The working graph
and supporting quotes still come only from the existing public Case 01 GET.
There are no fabricated Source/Evidence identifiers, uploads, model calls,
mutations or automatic professional acceptance.

The approved throwaway reference is preserved on branch
`codex/landing-documents-prototype`, commit
`15288805f7dea7c723d2b73f7a4772db2a307dde`. Production imports none of its files.

## Functionality and interaction checklist

- [x] Public GET loads without sign-in, analysis, upload or mutation.
- [x] Four distinct formats share a scroll-controlled document deck.
- [x] Exact names move from measured source spans into the returned graph.
- [x] Partial SVG masks draw connections while preserving dash/direction roles.
- [x] The same graph moves into full-source review.
- [x] Every canonical claim selects its exact Evidence and Source identifiers.
- [x] Full source text and whitespace remain intact; repeated/overlapping support
      retains all associated Evidence IDs without duplicating source text.
- [x] Source movement is internal, cancellable by reader input and newer selection.
- [x] Keyboard skip/focus, reverse-scroll selection and locale continuity work.
- [x] Initial/live reduced motion and short-height fallback remove the long track.
- [x] Compact phones use a readable in-flow alternative instead of compressed
      relationship targets; taller phones retain the scroll sequence.
- [x] Measured origins update after resize/locale/font changes and clean up safely.
- [x] Failed reads retry the real backend; public and practitioner links remain.
- [x] Story and decision backgrounds meet directly, with zero gap and equal colour.
- [x] Research is the first subsequent light section, with substantive content.
- [x] Existing practitioner journeys pass the unchanged-backend browser suite.

## Inspection, review and corrections

Actual Chrome confirmed the former empty strip: exterior margins of 70px on
desktop and 45px on phones exposed the white page between two forest sections.
Those margins are removed; spacing stays inside the continuous green field.

The initial desktop/phone inspection and independent source review found hidden
arrowheads and overflowing time-sheet content. Directed endpoints now intersect
the measured circle/triangle boundary plus a small external gap, accounting for
the drawing's actual aspect ratio. Unit and rendered-geometry tests protect
visible arrow exposure. The time sheet fits its paper without clipping text.
The source reviewer confirmed its P2 resolved with no new material findings.

Playwright's disabled-animation screenshot option reset native scroll-timeline
styles during capture, producing a misleading image of bare lines over the note.
Captures now preserve running scroll styles. Their phone confirmation exposed
label overlap around the Trust and Alice captions. Labels now use measured
caption widths, short association leaders and separate diagonal/near-vertical
parent placement. Browser assertions confirm all six targets clear captions and
each other at 320, 390 and 700px while retaining 44px targets. Source reflow also
keeps the selected quote visible until manual reader input cancels following.
Compact phones at most 800px tall use the in-flow alternative so that their
shorter viewport cannot compress the captions into relationship targets.

Root reviewed complete source, tests, styles, documentation and artifact scope.
The page composes a document montage, graph and source reader; finite geometry,
source highlighting and lifecycle measurement remain focused. Obsolete tabs,
playback clock and their CSS were removed. No material readability concern is
being deliberately retained.

## Local validation

- Required repository `uv run pytest`: **752 passed**, 106.31s, disposable PG.
- Full independent frontend units: **101 passed in 22 files**.
- Typecheck, production build and source formatting passed.
- Full unchanged-backend browser run: **50 functional checks + one landing
  recording passed** (51 total); three opt-in/redundant recordings skipped.
- First correction confirmation: **14 affected desktop/phone checks + recording
  passed** (15 total), one redundant phone recording skipped, 35.2s.
- Final affected desktop/phone confirmation: **20 functional checks + recording
  passed** (21 total), seven redundant/project-specific cases skipped, 46.6s.
  Includes 320/390px compact phones at 667/760px height, the 800px fallback
  boundary and the animated 844px phone sequence.
- Landing JS: 39.17kB / 14.54kB gzip, separate from the
  practitioner entry. Dependency-directive warnings remain nonblocking.

## CI investigation and handoff

The previous PR head had a failing original research focus assertion in
`web/research/configuration/Pipeline.test.tsx` during `browser-e2e`, making the
aggregate `tests` check fail. Neither that source nor its test differs from the
stack base. The isolated three Pipeline tests and the complete 26-test original
research suite both pass locally. No original code or test was changed to mask
the failure. New-head CI will be reported at handoff; pending checks are not
merge-ready and this task does not merge or deploy.

## Usage and evidence

One Sol/medium implementation context was reused, with one Sol/high independent
source reviewer and a confirmation. Root owns browser verification, visual
inspection, docs and delivery; the implementer also ran focused phone regressions.
The default inspection/correction cycle was extended only for
the material phone-label issue exposed by corrected captures, within the
workflow's three-cycle ceiling. At most two children, one runtime writer, no
nested delegation or paid application-provider invocation: shared usage **0/5**.
No new Motion query, premium source read, runtime dependency or account write was
needed; existing official docs and the approved study informed the sequence.
No runtime MotionScore or production-provider certification is claimed.

Current artifacts in `practitioner-next/artifacts/`:

- `landing-before-empty-strip.jpg`: actual Chrome before reference.
- `landing-documents-{desktop,phone}.png`: document-deck viewports.
- `landing-review-{desktop,phone}.png`: full-source review viewports.
- `landing-boundary-{desktop,phone}.png`: continuous green decision section and
  subsequent substantive research surface.
- `landing-chrome.jpg`: live integrated Chrome review.
- `landing-walkthrough.webm`: short document-to-graph-to-Evidence recording.
- `landing-provenance.json`: capture methods, viewport sizes and file/source hashes.

See README.md for launch/recording instructions and landing-motion.md for exact
phase ranges and source references. The landing's DESIGN.md/sidecar and surface
brief describe the accepted built world; the practitioner design remains separate.
