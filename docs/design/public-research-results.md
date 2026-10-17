# Public research publication — editorial refinement

The owner's 2026-10-17 refinement request supersedes the dashboard-like composition
of the initial design C implementation. This remains the public presentation slice
of [#148](https://github.com/alistairkung/private-client-graph/issues/148), on PR
#152. The verified snapshot, export contract, semantics and security boundary are
unchanged. No new experiment, paid provider call, merge or deployment is included.

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
desktop layouts. Escape restores focus to the toggle;
route selection, outside pointer interaction and resizing close the dropdown.

The standalone route uses Read mode, with eight chapters: research question;
extraction architecture; evaluation methodology and A′ control; measured results;
Case 03 failure analysis; additional case findings; limitations and resource
trade-offs; reproducibility. Writing introduces each interactive component. The
full ten-case comparison, saved diagnostic failures and per-call usage remain
inspectable without turning the opening into a dashboard.

Shared presentation lives in `web/src/shared/research/`:

- `PipelineNode`: the Workbench's actual expandable stage, extracted without its
  editing or execution authority. Public `ResearchArchitecture` supplies only
  frozen narrative and approved model identity.
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

## Direction contract

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

The detector reported the inherited Workbench stage-width transition when its
CSS moved into the shared component. Public stage styling disables that transition;
the existing internal Workbench animation remains unchanged. No detector rerun
is required.

The fresh full editorial review confirmed Evidence Folio fidelity and the requested
narrative composition, then identified mobile graph framing and excessive empty
desktop case-detail depth. Both were corrected, including the case-index flex
shrink regression. The final targeted verdict scored those findings resolved and
returned **ship at the scored-fix scope**. This is not a second whole-surface audit.

A separate fresh header review inspected all eight compact-menu captures, the
owner's reference, and desktop/closed-mobile context. It returned **ship for the
combined hamburger-header refinement**, with no material fixes. Both review scopes
are complete.

The documentation comparison checked `PRODUCT.md`, the incumbent `DESIGN.md`,
`.impeccable/design.json`, `ResearchResultsApp.tsx`, `ResearchSummary.tsx`, their
stylesheets, the shared pipeline presentation, and `PublicHeader.tsx` with its
stylesheet against the owner's refinement request. The build preserves Evidence
Folio's ledger-green/paper palette, Newsreader Display/Public Sans pairing,
burgundy focus treatment and gold exact-Evidence emphasis. The study's larger
chapter type and the landing's paired figures are local editorial adaptations,
not additions to the global token system. The compact Menu includes all four
links, both language controls and the prototype notice at 1350px and below.

Capture evidence is indexed in `research-editorial/screenshots.json` (20 captures)
and `research-editorial/navigation-screenshots.json` (8 captures) in the task's
visualization directory. The documentation pass visually sampled the English
desktop and Chinese mobile landing chapters, English desktop and Chinese mobile
full studies, English mobile and Chinese desktop graph/Evidence views, and the
English mobile open research menu. These show the retained editorial palette,
readable synthetic limitations, stacked mobile graph/Evidence framing and the
single dropdown containing navigation and language controls. Browser acceptance
separately verifies keyboard, dismissal, route, resize and locale interactions.

`PRODUCT.md`, `DESIGN.md`, the sidecar and global configuration remain unchanged.
The existing root layout record describes a 1440px content maximum and narrower
fluid gutter, while the incumbent public CSS uses a 1280px maximum and
`clamp(24px, 8vw, 128px)` gutter. The sidecar also retains earlier header breakpoint
and navigation examples. These pre-existing documentation differences are
reported without repair or canonization in this ordinary focused extension.
No new raster, asset or global design token was introduced.
