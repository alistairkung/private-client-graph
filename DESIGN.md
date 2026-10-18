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
---

# Design system: Private Client Graph

The approved **Forest & Chalk** design now belongs to the single production
frontend in `web/`. Phase two carries the approved designs from drafts 157/158
into the existing application build; it does not introduce another visual direction.

- [Working Atlas](docs/design/practitioner-working-atlas.md) defines the
  practitioner workspace, graph/list interaction, Source reader and Evidence.
- [Document story](docs/design/landing-document-story.md) defines the landing's
  document montage, scroll-drawn graph and final split Source view.
- [Consolidation guide](docs/workflows/ui-consolidation.md) records routes,
  public-read/protected-write behavior, parity coverage and local launch.

The landing uses self-hosted Public Sans; the practitioner uses Segoe UI with
Arial/sans-serif fallback. Source text, names, relationship identities and
Evidence remain backend authoritative. Animation acknowledges work and preserves
context. Reduced-motion preferences expose the complete story without scroll
choreography and make Source reveals immediate.

Public research uses Public Sans and the same Forest & Chalk palette, with a
reading-led overview, restrained spring selection controls and stable recorded
values. The [research interaction brief](docs/design/research-results-interaction-refresh.md)
records its Motion+-informed decisions, research caveats and verification.
It retains the recorded comparison renderers and original artifact download.
Its required older renderers live
under `web/src/features/public-research/recorded-review/`; they are not a second
practitioner application. The earlier [public landing direction](docs/design/public-landing-visual-direction.md)
remains a historical record of the replaced landing.
