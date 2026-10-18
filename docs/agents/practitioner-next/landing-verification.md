# Landing delivery and verification

Branch `codex/landing-evidence-motion`, draft PR #158, is stacked on PR #157's
Forest & Chalk commit `97e1d99015164af2cfbee85cb9b946035b235468` as requested.
The independent public page lives at https://127.0.0.1:5443/; `/app` retains the
practitioner application. Existing `web/`, practitioner components, backend,
APIs, domain, database, original tests and deployment are unchanged.

## Two-capability story

The user's Lissom org-chart reference led to a tabbed feature showcase:
**Build the trust structure**, then **Trace the Evidence**. The first now
reveals actual returned entities and all six canonical relationships from source
excerpts. The second inspects the same graph and the selected exact passage.
The previous finished-graph intro and repetitive scroll walkthrough were removed.
Forest & Chalk remains the selected visual identity.

Source excerpts are deduplicated canonical supporting text, ordered by their
actual occurrence in the corresponding Source. They are never rewritten or
inferred in the frontend. The demonstration persistently identifies itself as an
illustrative synthetic sequence, not live analysis. Visiting or replaying the
page makes no model call or mutation. Professional acceptance remains a separate
explicit decision.

## Function and interaction checklist

- [x] Existing public GET loads without sign-in; no automatic analysis or upload.
- [x] Default Builder reveals entities and all six actual connections progressively.
- [x] Replay resets presentation only; Pause/Resume preserves playback position.
- [x] Construction waits for at least 20% of the drawing to enter the viewport.
- [x] Offscreen/hidden playback pauses; deliberate user pause persists on return.
- [x] Initial and live reduced-motion preferences show the complete graph immediately.
- [x] Evidence selection cancels construction; returning to Builder retains completion.
- [x] Pointer and roving keyboard tabs work with arrows, Home and End.
- [x] Completion retains owned playback focus on Replay without stealing other focus.
- [x] Every canonical claim reveals its exact Evidence, source identity and identifier.
- [x] Source/graph geometry and chosen relationship persist across capability changes.
- [x] Evidence selection resets only internal source scrolling and retains control focus.
- [x] Source excerpt paragraphs end naturally; both modes retain the same paper height.
- [x] Connectors reach actual endpoint glyphs and retain family dashes/parent arrows.
- [x] English/Chinese switching preserves exact words and selected Evidence.
- [x] Retry uses the real backend without fabricated fallback; public/app routes work.
- [x] Desktop/phone controls fit and keyboard focus remains visible.
- [x] Existing practitioner journeys pass the unchanged-backend regression suite.

## Review and corrections

One batched desktop/phone inspection, one correction batch and confirmation.
Independent source review found two P2 issues: Motion's installed reduced-motion
hook snapshots the initial preference, and removing Pause/Resume on completion
lost keyboard focus. An explicit reactive media-query subscription now settles
playback within 500ms of a preference change; a callback ref transfers focus to
Replay only when the removed playback control owned focus. Both findings were
independently confirmed **resolved**, with no remaining material readability or
boundary concerns.

The visual reviewer found a cropped source line and an offscreen skip-link
capture overlapping the phone disclosure. Complete canonical excerpts now size
the source paper naturally, and the skip link uses clipped hiding until focus.
The same reviewer scored both corrections **resolved**, disposition **ship**.
Its verdict covers those scored fixes. A QUALITY BAR reference card was not
available, so no comparison against that card is claimed. Generic agents used
the bundled Impeccable reviewer/documenter instructions; dedicated role types
were unavailable. Review captures are actual browser output, not generated comps.

Root completed the mandatory full changed-diff self-review, including both new
modules, revised tests, deleted walkthrough/styles, documentation and artifacts.
Playback, canonical presentation, source identity and selection remain separate
responsibilities. Consolidated obsolete/overridden CSS and preserved canonical
stroke patterns. No material readability issue was deliberately retained.

## Local validation

- Required `uv run pytest`: **752 passed**, 106.40s, disposable PostgreSQL.
- Final frontend units: **89 passed in 19 files**, including 17 landing tests.
- Typecheck, production build, source/E2E/entry formatting and whitespace: passed.
- Full real-backend browser suite: **52 functional checks + landing recording
  passed** (53 total), three opt-in/redundant recordings skipped.
- After correction, all **16 affected desktop/phone functional checks and the
  refreshed recording passed**. Two keyboard cases were rerun after adding a
  page-ready wait before the first Tab; both passed in 2.0s. Live reduced-motion
  settling is asserted within 500ms, rather than accepting natural completion.
- Successful journeys retain the real API, canonical construction and persistence;
  only existing synthetic Google/model boundaries are substituted. The isolated
  503 route tests retry without replacing successful data with a UI fixture.
- Separate lazy landing/practitioner entries remain intact. Landing JS is
  22.45 kB / 8.57 kB gzip plus shared runtime; dependency directive warnings are
  nonblocking. No runtime MotionScore or production-provider check is claimed.

## Usage and evidence

This continuation reused the Motion handoff without new lookups or source reads.
Earlier authenticated landing research used two concept queries, one source
lookup, one premium and one free source read; Smooth Tabs/Path Drawing mechanisms
were reused from already inspected sources. No premium runtime dependency or key
was added. Shared paid application-provider usage remains **0/5**, including all
attempts and continuations.

Economical delegation: one Motion handoff, three implementation turns, two
engineering review turns, two visual review turns and one design-documentation
turn. At most two active children; one runtime writer. Motion/implementation used
Sol/medium, final source review Sol/high, visual/documentation Luna/low. Root
owned browser tests, integration and delivery. No nested delegation/processes.

Artifacts in `practitioner-next/artifacts/`:

- `landing-builder-{desktop,phone}.png`: actual full-page Builder captures.
- `landing-{desktop,phone}.png`: actual full-page Evidence captures.
- `landing-chrome.jpg`: live Chrome capability stage.
- `landing-walkthrough.webm`: construction → Evidence → claim inspection recording.

Raster captures carry origin metadata. Launch/recording instructions are in
`practitioner-next/README.md`; the built surface has its own DESIGN.md and sidecar.
No merge, deployment or replacement of the original site.
