---
name: Private Client Graph Public Landing
description: Build a proposed trust structure, then trace each relationship to its source.
colors:
  primary: "#1E6249"
  forest: "#173F31"
  ink: "#20372B"
  muted-ink: "#566B5D"
  frame: "#E9F0EA"
  line: "#C7D3C8"
  white: "#FFFFFF"
  paper-text: "#E5EFE7"
  paper-muted: "#C0D4C6"
  connector: "#A6C4B1"
  evidence: "#FFF0A6"
  selection: "#E5EFE7"
typography:
  display:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "clamp(3.4rem, 6.1vw, 6rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "clamp(2.3rem, 4vw, 3.8rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  tight: "2px"
  paper: "3px"
  control: "4px"
  capability: "10px"
spacing:
  base: "4px"
  small: "8px"
  medium: "16px"
  large: "24px"
components:
  action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
    height: "48px"
  action-hover:
    backgroundColor: "{colors.forest}"
  source-paper:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "20px"
  capability-tab-selected:
    backgroundColor: "{colors.frame}"
    textColor: "{colors.forest}"
    rounded: "{rounded.capability}"
    padding: "21px 19px"
---

## Overview

**Creative North Star: “Build the structure. Keep the Evidence.”** The landing page introduces two connected capabilities: a language-model-assisted trust structure builder, followed by exact Evidence review. A short capability rail leads into one shared source-and-graph stage, where the same returned synthetic material supports both explanations.

Forest & Chalk carries across this public surface, with self-hosted Public Sans giving the headline and source a distinct voice from the practitioner app's system-font typography. A white source paper sits within a forest demonstration field. The builder reveals entities and relationships around the source; the Evidence view replaces the excerpt display with the selected claim's exact passage while retaining the paper, graph, and selected relationship.

**Key Characteristics:**

- Builder-first headline and action lead into an immediately explorable synthetic example.
- Two capability tabs switch the explanation while preserving the same source, structure, and selection.
- A four-second illustrative construction sequence reveals the returned graph, with replay and pause controls.
- Exact source words remain inspectable; professional acceptance remains a separate explicit decision.

## Colors

Forest owns the demonstration region. Ink and muted ink carry reading and supporting text. The action green marks primary actions and selected controls. Pale green fills the active capability and selected relationship state, while warm yellow is reserved for the exact Evidence span. Light paper text and connector tones maintain contrast within the dark stage.

**The Evidence Color Rule.** Use warm yellow for the exact supporting words; use pale green and a brighter connector for selected controls and relationships.

## Typography

- **Display** (600, responsive 3.4rem–6rem, 1.02 leading): Public Sans headline, tightly tracked and capped at 18ch.
- **Headline** (600, responsive 2.3rem–3.8rem, 1.1 leading): major section headings.
- **Title** (600, 22px, 1.2 leading): capability tab titles.
- **Body** (400, 16px, 1.5 leading): general copy; source reading uses 16px and 1.55 leading on wide screens, 14px below 1100px, and 15px on phones.
- **Label** (400, 13px): navigation and compact interface text; source metadata uses 10px.

The self-hosted Public Sans files provide regular and semibold weights, with Segoe UI and sans-serif fallbacks. Headings use restrained negative tracking; source text stays at normal tracking and wraps within the paper.

**The Source Reading Rule.** Keep the quoted passage more prominent than its metadata, and give the exact supporting words their own highlight.

## Layout

The masthead and opening use 5% page gutters. On wide screens, the opening places its headline beside the description and action. The demonstration starts as a two-column composition: a two-item capability rail beside the shared source-paper and graph stage. Beneath it, selectable relationship claims form a six-column rail.

At 1100px and below, the capability rail and stage tighten; the source and graph columns become equal, with smaller source type and paper padding. At 700px and below, the capability tabs become a two-column row above the source paper and graph, the demonstration uses a stacked layout, and claims form two columns. The source paper grows with its excerpt content from a 320px desktop minimum and 290px phone minimum; the selected Evidence overlay scrolls inside the source-reading area while the paper and locator remain in place. At 1700px and above, the opening gains vertical space and the paper centers its contents.

**The Shared Stage Rule.** Keep source, graph geometry, active relationship, and capability-specific explanation within one stage so switching capabilities preserves context.

## Elevation & Depth

The page is mostly flat; contrast comes from color fields, borders, and spacing. The white source paper alone uses a soft shadow (`0 12px 32px #06261730`) to lift it from the forest stage. Capability selection uses a moving pale-green inset indicator instead of adding elevation.

## Shapes

Forms are mostly square with small purposeful rounding: action controls use 4px corners, the source paper 3px, entity name plates 2px, and capability tabs 10px. People are circles and trusts are triangles. Fine rules divide source metadata and relationship choices. Focus uses a visible 2px outline with a 5px offset, switching to a light outline over the forest stage.

## Components

### Actions

- **Shape:** compact, lightly rounded rectangle (4px).
- **Primary:** action green with white text, 12px 18px padding, 48px minimum height, and the authored arrow icon.
- **Hover / Focus:** forest hover; visible green focus outline, or light outline on the forest stage.

### Capability Tabs

The two tabs are “Build the trust structure” and “Trace the Evidence.” Desktop stacks them in a left rail with title, short supporting copy, and a pale-green moving indicator. On phones they sit side by side above the demonstration; the supporting copy is hidden to keep each target compact. Arrow keys switch tabs, with Home and End selecting the first or last tab.

### Source and Relationship Demonstration

The source paper contains the actual source title, a canonical excerpt view for construction, and a selected-Evidence view that overlays an independently scrollable passage. Entity names can be marked within canonical excerpts; exact supporting text uses the warm Evidence highlight. A persistent locator remains below the reading area. The adjacent diagram uses circles for people, triangles for trusts, thin connectors, a brighter selected relationship, dashed family links, and an arrow for parent direction. Relationship choices name both endpoints and their canonical relationship.

### Construction Playback

The builder reveals source, entities, and relationships over a four-second linear clock. Replay and Pause/Resume controls operate that clock. Choosing Evidence or selecting a relationship settles the diagram immediately; playback pauses when the drawing leaves view or the document becomes hidden. Reduced motion displays the complete structure immediately.

## Do's and Don'ts

### Do:

- **Do** keep the two capability tabs attached to one source and graph stage.
- **Do** describe construction as an illustrative synthetic sequence, not live analysis.
- **Do** keep exact Evidence visually distinct from selected relationships.
- **Do** keep source and locator stable while the Evidence passage scrolls within its reading area.
- **Do** honor keyboard operation and reduced-motion preferences.

### Don't:

- **Don't** imply that the synthetic example is measured customer output or a professional judgment.
- **Don't** use Evidence yellow as a general accent or selection color.
- **Don't** add upload, live-analysis, or automatic-acceptance affordances to this public demonstration.
- **Don't** carry the landing page's headline and capability-rail composition into the separate Working Atlas practitioner surface.
