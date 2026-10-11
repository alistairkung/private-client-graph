# Research Workbench: implemented workspace

Implementation record, 2026-10-12. This records the research surface implemented
from the [approved workspace handoff](research-workbench-approved-workspace.md)
and [complete design reference](research-workbench-complete-design-reference.md).
It supplements the existing [design system](../../DESIGN.md); it does not replace
its Public Showcase tokens or change practitioner presentation.

## Overview

The research application uses one continuous workspace for configuration, frozen
plan review, execution and retained result inspection. A persistent experiment
sidebar supplies creation, recent history and browsing. URL selections recover
backend-owned plans and retained results; browsing confers no execution authority.

## Colors

Ledger green, warm paper, white working surfaces and muted green metadata retain
the incumbent identity. The pipeline uses a pale green dotted canvas to identify
the editable rail. Dark green execution panels anchor draft and run controls;
light controls remain legible against them. Exact Source Evidence retains gold
emphasis; outcome categories also have explicit text labels.

## Typography

Public Sans carries controls, accounting and comparison tables. Newsreader carries
modest workspace titles and Evidence quotations. Workspace titles are 36px on wide
screens and 30px below 760px; Source quotations use 21px. These are research surface
choices, not replacements for the public display scale.

## Layout

The sidebar is 248px wide, reduces to 210px at 1100px, and becomes a drawer below
760px. The pipeline remains horizontal inside a scrollable viewport with explicit
navigation. One node expands inline at a time; its settings scroll within a
440px maximum height. Execution places a compact status panel beside workload
and accounting. Comparison and Evidence share two columns on wide screens and
stack at 1100px; execution stacks below 760px.

## Elevation & Depth

Fine rules and tonal surfaces provide normal separation. The supported-capability
menu and mobile drawer use localized soft shadows. The pipeline's dots belong to
its working canvas and are not a general page background treatment.

## Shapes

Pipeline nodes use modest rounded corners. The insertion circle sits inside a
fixed 44px target; focus and hover change its inner appearance without moving the
rail. A persistent text action also opens insertion. Reduced motion removes rail
transitions and smooth viewport scrolling.

## Components

- **Pipeline:** fixed Extract → Resolve → Build relationship graph. Saved replay
  bypasses extraction. Resolution supports only no-op and generative full-source;
  removal selects no-op. Evaluation remains outside the Shared Analysis Pipeline.
- **Settings:** provider settings are shared across the experiment. Resolver
  repetitions are experiment measurement, including when edited inside the node.
- **Execution:** server preview precedes freezing. Freezing grants no paid-call
  authority. Live approval preserves #111's atomic **Authorize and start** and
  **Authorize and continue**, without a separate authorized-but-not-started state.
- **Retained history:** frozen configuration and available results are read-only;
  imported history gains no execution controls. Partial coverage is labelled.
- **Comparison and Evidence:** baseline/treatment selection scopes retained
  metrics and matched (TP), extra (FP), and missing (FN) relationships. Individual
  relationships lead to expected/predicted Evidence and exact frozen Source.
- **Usage:** recorded token totals, latency coverage and estimated spend retain
  provenance. Unknown values remain unavailable; unpriced attempts are not free
  calls and estimates are not invoices.

## Do's and Don'ts

- Do keep workload observations, provider attempts and uncertain attempts distinct.
- Do retain explicit consent, immutable plan identity and backend execution state.
- Do preserve input, cohort and repetition context through Evidence inspection.
- Don't invent true negatives, turn unavailable metrics into zero, or calculate
  replacement evaluation semantics in the browser.
- Don't promote prototype stress-test stages or demonstration authority into
  supported capabilities.

Source evidence: `web/research/app/App.tsx`, `app/research.css`,
`app/workspace.css`, `configuration/Pipeline.tsx`, `configuration/Configuration.tsx`,
`configuration/Run.tsx`, `results/Results.tsx`, `results/ComparisonBench.tsx`, and
`results/UsageSummary.tsx` (paths after the first are relative to `web/research/`).
