# Public research publication — editorial refinement and shared visualizations

The owner's 2026-10-17 refinement request supersedes the dashboard-like composition
of the initial design C implementation. This remains the public presentation slice
of [#148](https://github.com/alistairkung/private-client-graph/issues/148), on PR
#152. The verified snapshot, export contract, semantics and security boundary are
unchanged. No new experiment, paid provider call, merge or deployment is included.

The subsequent owner-approved comp C for genuine Workbench reuse extends the
standalone study with broad architecture and results bands. It preserves the
editorial refinement and complete study content. The current shared ownership,
public adapters and evidence are recorded in
[Shared research visualizations](shared-research-visualizations.md).

## Composition and ownership

The landing page tells the story in Persuade mode: hero → relationship/Evidence
approach → full-width measured research chapter → existing synthetic demonstration.
The research chapter pairs large editorial type with the two measured F1 values,
then explains the narrow name corrections, exploratory comparison and synthetic
data limits. The independently reviewed wording is immediately qualified: checks
used separate AI validators within internal development, not external human or
institutional validation. Disclosures are ordinary visible text in both languages.

At the owner’s follow-up request, public navigation collapses into a labelled
hamburger dropdown at 1350px and below, including language controls and the
prototype notice. The four links and language controls remain inline on wider
desktop layouts. The compact brand and Menu stay on one row; responsive brand
and logo sizing preserves their proportions, while Menu, dropdown links and
language buttons share one text scale. Escape restores focus to the toggle;
route selection, outside pointer interaction and resizing close the dropdown.

The standalone route uses Read mode, with eight chapters: research question;
extraction architecture; evaluation methodology and A′ control; measured results;
Case 03 failure analysis; additional case findings; limitations and resource
trade-offs; reproducibility. Writing introduces each interactive component. The
full ten-case comparison, saved diagnostic failures and per-call usage remain
inspectable without turning the opening into a dashboard.

Shared presentation lives in `web/src/shared/research/`:

- `AnalysisPipeline`: the complete Workbench stage rail, including expandable
  `PipelineNode` stages, connectors, the separate evaluation annotation, local
  interaction state and stage navigation. Workbench `Pipeline` supplies private
  configuration fields and editing callbacks; public `ResearchArchitecture`
  supplies a frozen published configuration without those callbacks.
- `RunPerformanceChart`: the complete Workbench F1 chart, including tabs, input
  filtering, point inspection and retained-Run selection. Workbench `RunChart`
  adapts private Run records; public `PublishedPerformance` supplies published
  measurements through `visual-data.ts`. Neither adapter duplicates rendering.
- `OutcomeMatrix`: the Workbench comparison table, reused for aggregate and
  case-level results. Workbench callers retain their existing navigation links.
- `EvidenceInspector`: the Workbench's exact frozen-Source inspector, localized
  through the existing catalogue. Its original import remains a compatibility
  re-export for internal consumers and tests.

`RecordedGraph` narrowly adapts published canonical state to the existing shared
`GraphView`, joining selected edges to retained outcomes by exact endpoint names
and relationship type. It does not construct or score graphs. The Workbench does
not currently have its own separate graph canvas; this renderer is shared with
the public demonstration and practitioner review.

No operational Workbench shell, client or execution control is imported by the
public adapters. Both routes still consume one verified publication; download
bytes and digest remain unchanged. English and Simplified Chinese translate only
presentation, preserving original Sources, names, quotations and identities.

Architecture and results use comp C's pale sage chapter bands and broad white
figure areas. The original Workbench figures mount directly inside them; the
comp's iframe isolation was only a review device. Figure notes use three columns
on desktop and stack on mobile. Stage rails and retained-Run lists retain local
horizontal scrolling. The recorded metric table remains inspectable below the
chart, and the graph/Evidence chapters retain their existing content.

The shared pipeline retains its original stage, resolver-slot and connector width
transitions. Shared reduced-motion rules remove those transitions and restore
instant rail scrolling. The former public-only transition override was removed;
public and Workbench figures now use the same animation and reduced-motion code.

## Historical editorial direction contract

This contract records the earlier editorial refinement. The current genuine-reuse
extension follows the scoped comp C contract linked in
[Shared research visualizations](shared-research-visualizations.md).

### THESIS

The landing tells the story; the standalone study explains it; interactive
retained evidence substantiates it. Narrative leads, and the tools appear where
they resolve a reader's question.

### OWN-WORLD

Preserve Evidence Folio: ledger green and warm paper, Newsreader editorial type,
Public Sans controls, fine rules and gold only on exact Evidence. No new identity,
framework, icon language, raster or global design tokens.

### STORY

Problem → approach → measurable graph → narrow correction → limitations →
inspect/download. A perfect F1 is qualified by the small synthetic dataset,
post-hoc comparison and exact-name scoring.

### FIRST VIEWPORT

The study opens with its title, a readable research premise, visible synthetic
limitations and section navigation. The research question precedes results.
The landing chapter has a full-width green ground, large headline and shared
baseline for the two measured values, followed by readable limitations and CTA.

### FORM

A focused owner-directed editorial refinement of C (original seed 3d55ccce), with
its paired case inspection retained below the explanation. The signature moment
is selecting Bea in the original graph, then Beatrice Ng in the resolved graph,
and finding the same documentary quote. One restrained scroll-linked landing
reveal is progressive enhancement, disabled under reduced motion; no scroll
hijacking. This is a code-led refinement of the supplied composition, with no
new generated comp or paid asset work.

### FINISH

unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Acceptance and review

Tests cover read-only pipeline exploration, canonical-state adaptation, selected
edge → retained outcome → exact Source highlighting, unchanged quotes across
conditions, bilingual narrative order, snapshot values/download identity, public
network isolation, local table scrolling and both viewport classes. Existing
public demo, authenticated practitioner and Workbench journeys retain regression
coverage. Full landing scroll and actual English/Chinese desktop/mobile captures
are inspected together.

The genuine-reuse finish review inspected all 29 supplied current captures and
identified one material finish defect: the opening disclosure exceeded its
intended reading measure because a structural selector won the cascade. The
selector now uses `:where`, allowing the 75ch paragraph limit to apply while
keeping figures broad. The reviewer inspected all five corrected recaptures and
returned **ship at the scored-fix scope**, with no visible regression. The full
review found no other material defect. This verdict does not claim a numerical
comp-diff result or completion of the Impeccable CLI phases; see the linked shared
visualization record for validation and the remaining review-metadata limits.

## Historical editorial and header reviews

During the earlier editorial refinement, the detector reported the inherited
Workbench stage-width transition when its CSS moved into the shared stage.
Public stage styling then disabled that transition. That public-only treatment
is historical and has been superseded by the complete shared pipeline described
above.

The fresh full editorial review confirmed Evidence Folio fidelity and the requested
narrative composition, then identified mobile graph framing and excessive empty
desktop case-detail depth. Both were corrected, including the case-index flex
shrink regression. The final targeted verdict scored those findings resolved and
returned **ship at the scored-fix scope**. This is not a second whole-surface audit.

The owner subsequently rejected the compact header because Menu dropped onto a
second row and requested consistent scaling. The correction is confined to
`public-header.css`: no wrapping, automatic brand width, responsive brand type and
logo sizing, a shared 1rem navigation text scale and an em-sized hamburger. The
fresh independent header-alignment review inspected the owner's rejected example
and all 24 replacement captures, returning **ship for the header correction**
with no material fixes. This separate, scoped verdict supersedes the earlier
header review and its two-row composition.

The documentation comparison checked `PRODUCT.md`, the incumbent `DESIGN.md`,
`.impeccable/design.json`, `ResearchResultsApp.tsx`, `ResearchSummary.tsx`, their
stylesheets, the shared pipeline presentation, and `PublicHeader.tsx` with its
stylesheet against the owner's refinement request. The build preserves Evidence
Folio's ledger-green/paper palette, Newsreader Display/Public Sans pairing,
burgundy focus treatment and gold exact-Evidence emphasis. The study's larger
chapter type and the landing's paired figures are local editorial adaptations,
not additions to the global token system. The compact Menu includes all four
links, both language controls and the prototype notice at 1350px and below.

Editorial capture evidence is indexed in `research-editorial/screenshots.json`
(20 captures) in the task's visualization directory. The documentation pass
visually sampled the English
desktop and Chinese mobile landing chapters, English desktop and Chinese mobile
full studies, and English mobile and Chinese desktop graph/Evidence views. These
show the retained editorial palette, readable synthetic limitations and stacked
mobile graph/Evidence framing. Their headers and the eight earlier captures in
`research-editorial/navigation-screenshots.json` are historical evidence, not the
final header reference.

Final header evidence is indexed in `header-alignment/screenshots.json` (24
captures): both routes and languages at 320, 390, 640 and 1024px, with open-menu
views at 320 and 640px. The documentation follow-up compared the rejected owner
screenshot and current CSS with four replacement samples: English research open
menu at 320px, Chinese landing closed header at 390px, English research closed
header at 640px and Chinese landing open menu at 640px. They show the aligned
single-row brand/Menu and one dropdown containing both navigation and language
controls. Fourteen focused browser tests passed with alignment, non-overlap,
font-scale and header-height assertions; the header remains at most 90px tall
across those tested widths. The fresh reviewer inspected the full capture set;
this documentation pass sampled it. Full Python validation passed (752 tests),
and the production build passed. A separate CI test locale leak was isolated in
`CaseWorkspace.test.tsx` without a production behavior change. Browser acceptance
also covers keyboard, dismissal, route, resize and locale interactions.

`PRODUCT.md`, `DESIGN.md`, the sidecar and global configuration remain unchanged.
The existing root layout record describes a 1440px content maximum and narrower
fluid gutter, while the incumbent public CSS uses a 1280px maximum and
`clamp(24px, 8vw, 128px)` gutter. The sidecar also retains earlier header breakpoint
and navigation examples. These pre-existing documentation differences are
reported without repair or canonization in this ordinary focused extension.
No new raster, asset or global design token was introduced.
