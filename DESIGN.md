---
name: Private Client Graph
description: Forest & Chalk, from documents to relationships and exact Evidence.
colors:
  forest: "#173F31"
  action: "#1E6249"
  ink: "#20372B"
  frame: "#E9F0EA"
  surface: "#FFFFFF"
  border: "#C7D3C8"
  practitioner-evidence: "#FFF0A6"
  landing-evidence: "#D4E6A5"
  workspace-ink: "#173E38"
  workspace-muted: "#52665F"
  workspace-frame: "#ECEFEC"
  workspace-chrome: "#F4F6F2"
  workspace-paper: "#F9FBF8"
  workspace-band: "#EFF4ED"
  workspace-segments: "#E3E8E3"
  workspace-rule: "#D7DFD8"
  workspace-action: "#15584D"
  workspace-action-hover: "#0C473D"
typography:
  workspace-display:
    fontFamily: "Newsreader, Georgia, serif"
  workspace-interface:
    fontFamily: "Public Sans, Arial, sans-serif"
rounded:
  workspace-panel: "16px"
  workspace-control: "10px"
---

# Design system: Private Client Graph

## Overview

**Forest & Chalk** is the visual direction for the public landing, research
results and graph. The practitioner workflow shares its workspace foundations
with the Research Workbench home.

- [Working Atlas](docs/design/practitioner-working-atlas.md) defines the
  practitioner workspace, graph/list interaction, Source reader and Evidence.
- [Document story](docs/design/landing-document-story.md) defines the landing's
  document montage, scroll-drawn graph and final split Source view.
- [Consolidation guide](docs/workflows/ui-consolidation.md) records routes,
  public-read/protected-write behavior, parity coverage and local launch.

The landing uses self-hosted Public Sans. Source text, names, relationship
identities and Evidence remain backend authoritative. Animation acknowledges work
and preserves context. Reduced-motion preferences expose the complete story
without scroll choreography and make Source reveals immediate.

Public research uses Public Sans and the same Forest & Chalk palette, with a
reading-led overview, restrained spring selection controls and stable recorded
values. The [research interaction brief](docs/design/research-results-interaction-refresh.md)
records its Motion+-informed decisions, research caveats and verification.
The [consistency follow-up](docs/design/research-ui-consistency.md) shares the
landing masthead and Matter graph renderer, introduces Motion/Base UI disclosures,
and gives case Evidence a two-pane reader. The original artifact download and
recorded research semantics remain unchanged. The research Source reader lives
under `web/src/features/public-research/recorded-review/`. The earlier [public landing direction](docs/design/public-landing-visual-direction.md)
remains a historical record of the replaced landing.

## Colors

The Research Workbench home and practitioner application consume the shared
workspace tokens from [workspace.css](web/src/styles/workspace.css). A pale
frame, light masthead and paper surfaces establish the workspace. Fine rules
separate regions, and deep teal marks primary actions and selection.

## Typography

The workspace uses Newsreader for display headings and Public Sans for body
text, navigation and controls.

## Shapes

Workspace paper panels use the shared panel radius. Standard controls use the
smaller control radius.
