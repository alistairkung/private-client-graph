---
version: 1
slug: "practitioner-next-src-landing-landingpage-tsx"
primary_target: "practitioner-next/src/landing/LandingPage.tsx"
related_targets:
  [
    "practitioner-next/src/landing/landing.css",
    "practitioner-next/src/landing/DocumentStory.tsx",
    "practitioner-next/src/landing/document-story.css",
    "practitioner-next/src/landing/StoryGraph.tsx",
    "practitioner-next/src/landing/SourceReview.tsx",
  ]
---

# Landing direction: documents become relationships, with Evidence intact

Scope: independent public `/`, continuing draft PR #158 stacked on #157.
Existing original frontend, practitioner components, backend, APIs, domain,
database, original tests and deployment remain read-only. Visitor mode: **Persuade**.
Private-client practitioners should understand the proposed structure, inspect its
Evidence, and reach the existing public research or practitioner prototype.

## User-approved direction

The Lissom org-chart reference led to the initial two-capability demonstration.
The user subsequently approved a separate scroll prototype, explicitly replacing
the small tabbed frame with a continuous story. “It begins with your documents”
introduces attendance notes, emails, time sheets and legal documents. Papers flick
as the visitor scrolls, gather, release names into a graph, and draw connections.
At the bottom, the same graph shares a split view with the complete source and
selectable exact Evidence. That approved composition is the authority; there is
no new visual-world tournament.

The prototype is preserved at `codex/landing-documents-prototype`, commit
`15288805f7dea7c723d2b73f7a4772db2a307dde`. Production code is written separately.

## Visual contract

Preserve Forest & Chalk and Public Sans. A white opening leads into one forest
field covering the document story and proposal-review explanation. The former
70px desktop / 45px phone margin between green sections exposed an empty white
strip; remove that margin and keep spacing inside the sections. Return to a light
surface only at the research section, with its actual content.

Documents use distinct internal structures and one SVG icon language. Reserve the
fan's full extents so format names and the scroll hint remain clear. Names travel
above the fading paper. Masked line drawing preserves canonical dashes and arrows.
The final reader keeps the full source, stable identifiers and precise highlights.
Phones stack graph and source; reduced motion and short viewports use normal flow.

## Motion and truth

Scroll is the only story clock. Keyboard users can skip directly to relationship
review. Relationship selection survives reversing, resizes and locale changes;
only the source pane scrolls, and manual reader input cancels its movement.

The montage labels the additional document formats as product vision. The public
GET `/api/showcase/cases/case-01` supplies the actual curated synthetic graph and
Evidence. Do not invent documents, identifiers or support for its relationships.
No upload, model call, analysis POST, mutation or automatic professional acceptance.
Public demo, research, practitioner entry, language and real retry remain available.

## Verification and scope

Use one batched desktop/phone inspection and one correction/confirmation batch.
Verify partial drawing, name origins, full-source exact highlights, default reveal,
selection retention, keyboard skip/focus, live reduced motion, language, retry,
destinations and continuous section backgrounds. Run focused tests, full new-app
units/build/browser coverage and required `uv run pytest`, then independent source
review and draft-PR handoff. Do not merge or deploy. At most two active children,
one runtime writer, no nested delegation, paid application-provider calls 0/5.
