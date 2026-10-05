---
name: Private Client Graph
description: Evidence-led editorial presentation with a contained professional review workspace.
colors:
  ledger-green: "#173e38"
  paper: "#f6f6f1"
  white: "#ffffff"
  burgundy: "#773b46"
  evidence-gold: "#efdda0"
  muted-ink: "#52665f"
  green-hover: "#28584f"
  frame-border: "#d5d9d2"
typography:
  display:
    fontFamily: '"Newsreader Display", "Newsreader", Georgia, serif'
    fontSize: "clamp(64px, 8.2vw, 130px)"
    fontWeight: 400
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  body:
    fontFamily: '"Public Sans", Arial, sans-serif'
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  action: "22px"
  frame: "5px"
spacing:
  gutter: "clamp(24px, 4.5vw, 72px)"
  frame-inset: "18px"
components:
  public-primary-action:
    backgroundColor: "{colors.ledger-green}"
    textColor: "{colors.white}"
    rounded: "{rounded.action}"
    padding: "12px 25px"
  public-primary-action-hover:
    backgroundColor: "{colors.green-hover}"
  demonstration-frame:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.frame}"
    padding: "{spacing.frame-inset}"
---

# Design System: Private Client Graph

## Overview

**Creative North Star: "Evidence Folio"**

A precise, document-led editorial world pairs warm paper and large serif type
with restrained professional controls. Exact Evidence supplies the visual
emphasis; space and full-width tonal changes establish hierarchy.

This record captures the implemented Public Showcase foundations. It does not
replace the practitioner interface's existing density or component styles. The
approved first surface and its intentional adaptations remain in
[the landing direction](docs/design/public-landing-visual-direction.md).

The approved [practitioner workflow and PC monogram](docs/design/practitioner-matter-workflow-design.md)
extend the separate Matter Ledger system. They are design references awaiting
application integration; the public surface foundations recorded here remain
unchanged.

**Key Characteristics:**

- Document texture alongside live, selectable text.
- Generous editorial spacing around a bounded working interface.
- Restrained annotation and Evidence emphasis.

## Colors

Ledger green anchors headings, primary actions, and dark editorial surfaces.
Paper and white separate the document and surrounding canvas. Burgundy identifies
editorial annotations and visible keyboard focus; Evidence gold highlights exact
supporting source words. Muted ink supports captions and availability text.

## Typography

Newsreader Display supplies public display text, source excerpts, and italic
annotations at weight 400. Public Sans supplies navigation and interface text.
Self-hosted font declarations and assets live in `web/src/styles/fonts.css` and
`web/src/styles/fonts/`. The existing Newsreader weight 500 remains available for
the practitioner shell; the new display faces do not replace it.

The display token describes the desktop hero. Individual chapter headings and
mobile layouts have their own observed responsive sizes; do not apply the hero
scale to product controls.

## Layout

Public content uses a maximum width of 1440px and fluid outer gutters. Full-width
editorial backgrounds can surround that constrained content. Keep substantial
space around the actual review workspace so it remains a distinct working
surface. The demonstration stacks its caption above its frame at 1100px; mobile
layouts further simplify at 700px and 650px according to the component.

## Elevation & Depth

Depth comes from the paper image, tonal surfaces, and fine borders. The public
frame and actions do not add box shadows. The paper texture is decorative;
readable source text remains HTML.

## Shapes

Actions have softly rounded corners, while the demonstration frame uses a small
radius. Person notation is circular; Trust notation is triangular. Editorial
Trust-role connectors are fine lines without arrowheads or implied flow.

## Components

The public primary action uses Newsreader Display with a green fill and a
minimum desktop height of 58px. Hover deepens its fill; keyboard focus uses a
visible burgundy outline. Mobile actions retain a minimum height of 48px.
Navigation links have at least 44px height and underline on hover.

Evidence highlights preserve wrapping with cloned box decoration. The synthetic
case label is small, spaced uppercase text. The demonstration frame reuses
`ReviewWorkspace`, `SourcePanel`, and `AnalysisControls`; its local styling
adjusts spacing without replacing review behavior. Analysis remains an explicit
choice, with sample and live outcomes identified separately.

Public anchor links use native smooth scrolling. Reduced-motion preferences
restore instant anchor navigation and remove the action's brief color transition.

## Do's and Don'ts

- Do retain exact source text as selectable HTML.
- Do preserve readable product controls inside editorial framing.
- Do retain the Trust triangle and visible keyboard focus.
- Don't use the hero illustration as a substitute for the working review UI.
- Don't imply direction or flow on editorial Trust-role connectors.
- Don't convert synthetic demonstration content into production or accuracy claims.
