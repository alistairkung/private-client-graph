---
name: Private Client Graph Public Landing
description: Evidence-led introduction to inspectable family and trust relationships.
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
    fontSize: "28px"
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
    padding: "23px 27px 18px"
---

## Overview

**Creative North Star: “Every relationship. Back to its source.”** The landing page makes the product's evidence-first promise visible: a source passage and a family or trust drawing share one stage, and selecting a claim reveals the exact supporting words. This is a focused public introduction to the synthetic example and practitioner prototype, not a description of all practitioner workflows.

The page carries Forest & Chalk into a distinct public surface. Public Sans gives its large offer and readable source fragment one clear voice. White source paper sits against a forest field; pale green connector lines and selected states stay legible there, while warm yellow marks exact Evidence. The landing voice differs from the practitioner application's system-font typography while retaining its established colors and product terminology.

**Key Characteristics:**

- A direct, oversized offer with the action aligned beside it on wide screens.
- A forest demonstration stage that joins exact source text to selectable relationship claims.
- Quiet explanatory chapters that return to the source-to-claim-to-Evidence thread.
- Professional acceptance remains a decision; the page describes synthetic material candidly.

## Colors

The forest and chalk surfaces establish the demonstration's contrast. Ink carries reading text, muted ink handles secondary explanation, and the primary green marks actions and selected controls. Evidence yellow has a single semantic job: identify the exact supporting passage. On the forest stage, light paper text and connector tones preserve the same contrast logic.

**The Evidence Color Rule.** Reserve warm yellow for the exact Evidence span; relationship selection uses pale green and a stronger connector instead.

## Typography

- **Display** (600, responsive 3.4rem–6rem, 1.02 leading): Public Sans headline, tightly tracked and capped at 18ch in the base layout (the CSS preserves this cap at narrower widths).
- **Headline** (600, responsive 2.3rem–3.8rem, 1.1 leading): major chapter and research headings.
- **Title** (600, 28px, 1.2 leading): walkthrough step titles.
- **Body** (400, 16px, 1.5 leading): explanatory copy; the source fragment is 17px with 1.55 leading on wide screens.
- **Label** (400, 13px): navigation and compact interface text; source metadata and locators use 10px.

Public Sans is self-hosted in regular and semibold weights. Segoe UI and sans-serif are fallbacks. The page uses responsive `clamp()` sizing, restrained negative tracking for headings, and normal tracking for reading text.

**The Source Reading Rule.** Keep the quoted passage more prominent than its metadata, and use the Evidence color only on its exact supporting words.

## Layout

The masthead and opening use 5% page gutters; the opening pairs a 1.5:1 headline-and-copy grid and keeps both visible before the broad demonstration. The source paper and diagram share a two-column mechanism, with claims arranged in a six-column selector below. Later sections alternate open two-column reading layouts, a forest acceptance panel, and a pale green research section.

At 1000px and below, outer gutters tighten, claims become three columns, and walkthrough controls align to the reading edge. At 700px and below, the opening and later chapters stack; the source paper, claim selector, and drawing reorder into a readable vertical sequence, with claims in two columns. The walkthrough's sticky diagram gives way to inline step illustrations. At 1700px and above, the opening gains vertical room and the source paper centers its contents.

Spacing is built from compact 4–24px intervals inside controls and source details, with larger section intervals of 60–100px. The source-to-diagram stage remains the primary spatial anchor.

**The Evidence Thread Rule.** Keep the source, relationship drawing, and selectable claims in one continuous demonstration region so a visitor can follow the evidence without changing contexts.

## Elevation & Depth

The page is mostly flat; contrast comes from large color fields, borders, and spacing. The white source paper alone uses a soft shadow (`0 12px 32px #06261730`) to lift it from the forest stage. Avoid adding elevation to explanatory sections or claim controls.

## Shapes

Forms are mostly square with small, purposeful rounding: the action uses a 4px corner, source paper 3px, entity labels 2px, and person nodes are circles while trusts are triangles. Fine rules divide navigation, source metadata, and claim choices. Focus is shown with a visible 2px green outline and 5px offset, switching to a light outline on the forest stage.

## Components

### Actions

- **Shape:** compact, lightly rounded rectangle (4px).
- **Primary:** green fill, white text, 12px 18px padding, 48px minimum height, and an arrow icon.
- **Hover / Focus:** dark forest hover; visible green focus outline, with a light outline over the forest panel.
- **Light variant:** pale green fill and forest text for the action inside the acceptance panel.

### Navigation

The masthead places the wordmark at left and research, practitioner entry, and language selection at right. The 82px wide header tightens to 70px on narrow screens; research is hidden below 700px while the product entry and language control remain.

### Source and Relationship Demonstration

White source paper contains the source title, contextual text, exact highlighted Evidence and its locator. The adjacent diagram uses circles for people, triangles for trusts, thin connecting paths, and a stronger light path for the selected relationship. Claim buttons repeat both endpoint names and the relationship term; selection updates the source passage and diagram together. On narrow screens, the source, claims, and drawing stack in that order.

### Trace Walkthrough

Three selectable steps explain source words, the proposed claim, and return to its supporting passage. A sticky abstract thread marks the active chapter on wide screens; chapter observation updates the active step unless the visitor has chosen one. On phones, the thread is replaced by small inline illustrations and the chapter text flows normally.

## Do's and Don'ts

### Do:

- **Do** keep exact Evidence visually distinct from relationship selection.
- **Do** describe the example as curated synthetic material and preserve the explicit professional decision boundary.
- **Do** make source, claim, and drawing content available without relying on the opening animation.
- **Do** retain keyboard focus visibility and honor reduced-motion preferences.

### Don't:

- **Don't** imply that the synthetic example is live analysis, measured customer output, or a professional judgment.
- **Don't** use Evidence yellow as a general accent or selected-state color.
- **Don't** carry the landing page's headline composition into the practitioner application's separate Working Atlas surface.
