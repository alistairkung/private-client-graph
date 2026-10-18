---
name: Private Client Graph Public Landing
description: Documents gather into a proposed structure, then every relationship returns to its exact Evidence.
colors:
  forest: "#173F31"
  action: "#1E6249"
  ink: "#20372B"
  paper: "#F3F5EF"
  chalk: "#F2F5EF"
  muted-chalk: "#C5D8C8"
  entity-name: "#DCE8CA"
  relationship-selection: "#E3F1B4"
  evidence: "#D4E6A5"
typography:
  display:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "clamp(3.4rem, 6.1vw, 6rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.04em"
  story-heading:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "clamp(30px, 3.6vw, 50px)"
    fontWeight: 400
    lineHeight: 1.12
    letterSpacing: "-0.03em"
  source:
    fontFamily: "Landing Public Sans, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.75
rounded:
  document: "4px"
  evidence: "2px"
  relationship: "22px"
spacing:
  gutter: "5%"
  fan-clearance: "84px animated / 60px static"
---

## Overview

**Creative North Star: “Build the structure. Keep the Evidence.”** The user-approved
story begins with a collection of documents, reveals people and trust relationships,
then opens the full source beside the same graph. The document formats express the
product vision; the working graph and Evidence remain the actual curated synthetic
Case 01 returned by the existing public API.

Forest & Chalk and self-hosted Public Sans remain the visual identity. This public
story is distinct from the practitioner application's Working Atlas workspace.

## Colour and section continuity

The white opening leads into one continuous forest field containing the document
story and the proposal-review explanation. Section spacing stays inside that field.
There is no white margin or empty light panel between those green sections. Light
returns at the substantive research section, followed by the closing invitation and
footer. Colour boundaries signal content changes rather than empty separators.

Pale-green names lift from the paper; selected relationships use light green and a
brighter connector. The approved public demonstration highlights exact source words
in green. The practitioner workspace retains its amber Evidence colour.

## Document montage

“It begins with your documents” introduces attendance notes, emails, time sheets and
legal documents. Consistent authored SVG icons identify the formats. Each paper has
its own internal structure: canonical attendance excerpts, email headers, activity
rows or deed clauses. The fan reserves space above and below so surrounding text
stays readable. The compact product-vision disclosure belongs below the heading.

The scrolling papers lift and sweep from alternating sides before changing front
order, then settle with a small counter-movement. A shared spring softens abrupt
scroll input for the papers alone; their exit opacity and the graph handoff remain
directly tied to scroll position. Animated layouts reserve 84px above the fan on
desktop and 76px on phones so the lifted corners clear the format labels. Static
and reduced-motion layouts keep their original spacing.

The illustrative formats never create Source or Evidence identifiers. Only the
actual attendance excerpts carry measured canonical entity-name anchors.

## Continuous graph and source

A viewport stays pinned while scrolling advances the four papers, gathers the stack,
lifts the names into nodes, and draws connections through SVG masks. The underlying
canonical paths retain their geometry, family dashes and direction arrows. One graph
moves into the final split; there is no replacement graph or simulated loading.

The final desktop composition has graph left and full source right. Phones place
the graph above the source. Relationship labels are buttons with complete accessible
statements and visible selection/focus. The full source preserves all text and
whitespace; exact supporting occurrences have their canonical Evidence identifiers.
Only the document pane moves when selecting a relationship. Reader input cancels
that movement, and selection survives reverse scrolling and language changes.
When review becomes interactive and an unselected relationship is visible, the
connection offers one tactile invitation. After a 350ms pause, a short chalk trace
travels from its source toward the label over 600ms. The capsule outline draws in
as its surface expands 4.5% and settles without overshoot. The capsule then breathes
at a 1.8-second rhythm with a soft chalk halo and 4% expansion; its connection stays
brighter. The outline remains distinct from the filled selected relationship.
The travelling trace plays once; the breathing emphasis continues while visible
until the visitor interacts. The cue never selects a relationship or changes
Evidence. The travelling trace cannot replay after reverse
scrolling or a language change, including when interrupted before completion.

Every relationship responds to mouse or pen attention with at most 2px of spring
movement and a small surface expansion. Its connection sharpens at the same time.
The 44px button and its hit area remain fixed; only the inner surface moves.
Keyboard focus receives the same emphasis, and pointer, touch or keyboard presses
compress the surface before selection reveals the exact Evidence with a 500ms
highlighter sweep. First hover, focus or selection permanently ends the invitation
for the mounted page. Touch has no emulated hover. The static/reduced-motion
alternative keeps a brighter outline, with immediate selection and no spatial
motion or highlighter sweep. No speech bubble or automatic relationship selection
is used.

The interaction uses the existing `motion/react` path drawing and springs. Only
presentation changes; canonical connector paths, family dashes, arrowheads, source
text and Evidence identifiers remain intact.

Phone labels clear measured captions and retain 44px targets, with short leaders
associating displaced labels to their connections. Text reflow keeps the selected
passage visible until the reader takes control.

## Control and responsive alternatives

The document and graph sequence is driven entirely by scrolling. Its 440svh track
finishes the composition at 78% progress, leaving about 75svh of additional scroll
with the completed graph and Source pinned in place. Further scrolling to 82%
triggers the invitation inside that held frame. The graph does not keep translating
or drawing during this hold; scrolling can continue naturally into the next section.
The skip link lands at this invitation point rather than the track's far end.
A persistent “Skip to relationship review” link reaches the finished state and transfers keyboard
focus. Reduced motion, very short viewports and compact phones show the formats,
finished graph and source in normal document flow. Phones at most 800px tall need
that alternative to preserve readable captions and 44px targets. Taller phones
retain the scroll sequence. There are no long blank tracks in the alternative.

English and Chinese interface copy share the same canonical names and source words.
The four document interiors and source pane wrap within the available width. Paper
elevation is soft and offset; the rest of the landing relies on colour and spacing.

## Product truth and scope

Keep the curated synthetic disclosure visible. No upload, automatic extraction,
provider call, mutation or automatic professional acceptance belongs in this public
story. The curated examples, research publication and practitioner entry remain linked
on the same origin. The legacy `/demo` journey redirects to `/app`.
The approved throwaway reference is preserved on `codex/landing-documents-prototype`;
production imports no prototype files or global prototype stylesheet.
