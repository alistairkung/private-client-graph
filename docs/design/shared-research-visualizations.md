# Shared research visualizations

The owner's 2026-10-17 selection of comp C and subsequent production approval
extend the existing Evidence Folio world. The Public Research Results route uses
the original Workbench pipeline and performance chart with read-only adapters.
The full study, public header, graph/Evidence inspection, publication bytes and
download contract remain in place. This is a presentation refactor and local
composition change; it does not change extraction, validation, graph identity,
evaluation or provenance semantics.

## Source ownership

Paths below are repository-relative.

| Responsibility | Owning source |
| --- | --- |
| Pipeline rendering and local expansion, insertion-menu, focus and rail-navigation state | `web/src/shared/research/AnalysisPipeline.tsx` |
| Expandable stage primitive | `web/src/shared/research/PipelineNode.tsx` |
| Chart rendering, tabs, input filter and hover/focus inspection | `web/src/shared/research/RunPerformanceChart.tsx` |
| Shared translation callback contract and default text formatting | `web/src/shared/research/presentation.ts` |
| Shared Simplified Chinese visualization copy | `web/src/shared/research/visual-catalogue.ts` |
| Scoped Workbench figure styles | `web/src/shared/research/research-visual.css`, `analysis-pipeline.css`, `pipeline-node.css`, `run-performance-chart.css` |
| Workbench configuration and editing adapter | `web/research/configuration/Pipeline.tsx` |
| Workbench private Run-to-presentation adapter | `web/research/workspace/RunChart.tsx` |
| Frozen publication-to-presentation adapters | `web/src/features/public-research/visual-data.ts` |
| Public figure composition and local selection | `web/src/features/public-research/ResearchArchitecture.tsx`, `PublishedPerformance.tsx` |
| Chapter integration and framing | `web/src/features/public-research/ResearchStory.tsx`, `RunComparison.tsx`, `public-research.css` |

The former Workbench `Pipeline` and `RunChart` files now adapt their callers to
the shared components. They no longer own duplicate figure markup or chart
mechanics. `Pipeline` still owns proposal changes and the `InputFields` /
`PipelineFields` slots. `RunChart` copies retained private Run fields into the
flat `PerformanceRun` contract. Selection is supplied by each caller through
`selected` / `select`; the shared chart keeps only its local inspection, tab and
filter state.

The public page's separately composed stage chain has been replaced by
`AnalysisPipeline`. The shared pipeline owns the full rail, connectors, optional
resolver slot, stage expansion, evaluation separator and navigation. Sharing the
primitive alone is no longer the reuse boundary. The public chart likewise uses
the full `RunPerformanceChart`; the existing `OutcomeMatrix` remains available
under the recorded metric table disclosure.

The shared pipeline and chart import React, local presentation contracts and styles. They
do not import the Workbench application, private API client, execution dialogs
or private Run contracts. The public route imports this layer and its own
publication adapters. Workbench callers supply editing callbacks and fields;
the public pipeline supplies neither. A stage inspection or retained-Run
selection changes local presentation state and grants no execution authority.

## Published data boundary

`publishedPerformanceRuns()` copies `micro_f1`, coverage and nullable provider
cost from the verified public snapshot. It does not calculate evaluation metrics
or reconstruct a private Run record. For the fixed v1 A / A′ / B publication,
A is fresh extraction, A′ and B use saved extraction, and only B has the resolver.
Model identity comes from the published calls, falling back to A's published
extraction model when a replay has no calls. `publishedPipeline()` supplies these
frozen descriptions and the published experiment's single resolver repetition.

Private scope identity and lifecycle are absent from the publication and stay
`null`. The chart explicitly renders unavailable scope and omits absent
lifecycle. Coverage determines the displayed complete/provisional score state;
it does not manufacture a lifecycle. The published experiment is not labelled as
a Workbench recorded demonstration.

All three published Runs are eligible for F1 by Run. A and B retain unknown
provider cost and are excluded from F1 vs Cost with the Unpriced explanation.
Only A′ has a known zero cost. Missing prices never become zero. The chart keeps
its discrete points, 0–1 F1 scale and no-trend qualification. Workbench fixture
scores and private scope IDs differ from this ten-case experiment; compare their
presentation and behavior rather than treating those fixture values as public
results.

## Approved C integration and motion

Architecture and results use the selected composition's sage chapter ground
(`#e8ede5`) around broad white figure areas. The existing paper (`#f6f6f1`), green
ink (`#173e38`), Newsreader Display editorial type and Public Sans controls remain.
The public inner width is at most 1280px; narrative paragraphs keep their reading
measure while the figures use the available band width. The opening disclosure
now respects 75ch through the structural selector's `:where` specificity fix.
These describe this local extension, not new global tokens.

Production mounts shared React components directly; the composition rig's
iframes are not part of the shipping route. The public pipeline uses the shared
persistent appearance, matching the Workbench's compact rectangular stage
treatment. White figure notes form three columns on wide screens and stack at
800px and below. Below 760px the shared chart reduces its inset and plot height.
Stage rails retain horizontal scrolling and Previous/Next controls; retained-Run
lists scroll locally.
The existing narrative, cases, graph/Evidence and metric details remain after the
figures rather than the comp's abbreviated continuation copy.

The shared stage, resolver-slot and connector widths retain the original 240ms
transition with `cubic-bezier(0.16, 1, 0.3, 1)`. Under reduced motion the shared
styles remove those transitions and the insertion control transition, and rail
scrolling becomes instant. The former public-only stage-transition override has
been removed. The detector's inherited width-transition warnings and square
chart-tab underline warning are recorded in the review; they did not prompt a
redesign of the owner's original Workbench figures.

## Evidence and reproduction

The task-local packet and reports are under
`.impeccable/review/shared-reuse/`: `review-input.md`, `finish-review.md`,
`finish-verdict.md`, `validation.json` and `detector.json`. Durable capture copies
and their provenance sidecars are in
`/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-shared-visuals/`.
The direction contract is
`.impeccable/surfaces/es-public-research-researchresultsapp-tsx-0be7d079.md`.
Approved composition references are in `.impeccable/mocks/research-reuse/`.

The documentation pass compared the owning source and incumbent `PRODUCT.md`,
`DESIGN.md` and `.impeccable/design.json` with the approved
`comp-c-architecture.png` / `comp-c-results.png` and eight durable capture samples:

- `public-wide-first-viewport.png`, `public-wide-architecture.png`,
  `public-wide-results.png`: corrected disclosure, retained introduction, sage
  bands, white figures, stage rail and original plot controls.
- `desktop-shared-pipeline-component-public-en.png` and
  `desktop-shared-pipeline-workbench.png`: the same stage/connector geometry,
  with editing authority supplied only by the Workbench caller.
- `desktop-shared-chart-workbench.png`: original chart treatment and retained
  Run interaction, with intentionally different fixture scores.
- `mobile-shared-pipeline-public-zh-CN.png` and
  `mobile-shared-chart-public-zh-CN.png`: translated controls, rail/list scrolling,
  stacked notes and explicit unavailable scope.

The independent finish reviewer inspected all 29 supplied current captures. Its
only material finding was the disclosure measure. After the specificity fix,
the reviewer inspected five replaced captures and returned **ship at the
scored-fix scope**, with no visible regression. The reports remain the authority
for that assessment; this documentation pass sampled the evidence rather than
repeating a whole-surface audit.

Recorded validation: 752 Python tests, 122 public frontend tests, 26 Workbench
unit tests, 32 public-results/header browser checks, 12 Workbench browser checks,
three final retained-Run journeys, and both TypeScript/production builds passed.
The public build scan found no internal Workbench endpoints or execution-dialog
strings. The public browser journeys allow only `GET /api/research-results` and
the existing exact-artifact download. The public build and 32 browser checks were
rerun after the disclosure fix; the other counts are the earlier full validation.
No paid provider calls, merge or deployment occurred.

To reproduce the focused checks from `web/`, use:

```bash
npm test -- src/features/public-research/ResearchArchitecture.test.tsx
npm run test:research
npm run build
npm run build:research
npx playwright test e2e/public-research.spec.ts e2e/language-header.spec.ts
npx playwright test --config playwright.execution.config.ts workspace.spec.ts
```

The browser checks require a migrated disposable PostgreSQL database through
`DATABASE_URL`; follow the repository's web test setup and
`docs/WEB_APP_GUIDELINES.md`. Repository validation remains `uv run pytest`.
This documentation pass did not rerun tests or make live calls.

## Limits and incumbent drift

The user approved comp C and the production plan in chat. Impeccable's CLI state
still awaits a browser receipt at `plates`, despite owing no raster plates. The
final `build-phase finish --disposition ship` attempt was refused because
`plates`, `hero`, `sections`, `motion` and `responsive` are not closed. This is
incomplete tool bookkeeping; the human approval and independent scored-fix
verdict do not establish completion of those machine gates. No receipt was
fabricated.

Numerical comp-diff reports and paired crops, a separate quality-bar card, and a
concept-roll receipt were not supplied. No measured reproduction-fidelity or
verified seed-origin claim follows from these captures. Screenshots and
comparison boards are evidence only; no new raster product asset is shipped.

`PRODUCT.md`, root `DESIGN.md`, `.impeccable/design.json` and global configuration
remain authoritative and unchanged. The incumbent root layout record's 1440px
maximum / narrower gutter differs from the existing public CSS's 1280px maximum
and `clamp(24px, 8vw, 128px)` gutter; the sidecar retains earlier header breakpoint
and navigation examples. These pre-existing documentation differences are
reported without repair or promotion into new global guidance in this focused
extension.
