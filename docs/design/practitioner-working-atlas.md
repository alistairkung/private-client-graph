# Working Atlas

The practitioner application uses the Research Workbench home’s visual
foundations in `web/src/`. The [root design record](../../DESIGN.md) records the
shared tokens and the public landing and research directions.

## Foundations

- Use the shared frame, masthead, paper, border and action tokens from
  [workspace.css](../../web/src/styles/workspace.css). Warm yellow identifies
  the active exact Evidence span.
- Newsreader sets display headings. Public Sans sets body text, metadata and
  controls. Proper names, source titles and exact quotations remain
  backend-authoritative.
- Paper panels use fine rules and 16px corners. Standard controls use 10px
  corners. Long names and filenames wrap, and keyboard focus remains visible.

## Composition and interaction

The horizontal masthead keeps Matters, Review and New proposal visible at
phone widths. On compact screens, a disclosure holds the language and account
controls. At 380px and below, it also holds Curated examples. The notices below
the masthead state that only synthetic or fictional material is allowed and
that Sources, Matter Proposals and Matters are publicly readable, including
proposals awaiting confirmation.

Matters (`/app`) lists accepted Matters. Review (`/app/review`) lists proposals
awaiting confirmation. Each page uses a divided paper list with its own search
by reference or title. The Review badge counts pending proposals across the
shared queue, independent of search. The count refreshes on practitioner path
changes. An empty queue offers New proposal. Search and the badge appear when
proposals are available.

The review workspace keeps Graph or List and the Evidence inspector beside an
independently scrolling Sources reader in a single paper frame. Canonical
Person nodes use circular notation. Trust nodes use a full-size triangle with
its name below.
One-Trust layout places settlors above, beneficiaries below, trustees beside the
Trust and direct family context near its role holder. These are presentation
preferences without additional domain meaning. Separate polylines preserve each
canonical relationship; parent arrows differ from arrowless Trust roles and
symmetric family connectors. Routes clear the Trust caption and unrelated nodes;
label placement reserves space for earlier labels and rejects unrelated connector
routes after all routes have been computed. Thin leaders associate offset labels
with their own claim. The generic layout uses Dagre.
Fit includes nodes, captions, all route points and connector labels. Selection
and language changes preserve the camera. Page scrolling does not zoom the graph.

Each connector label is a keyboard-operable button with the full relationship
as its accessible name. Diagram entity names use bounded two-line previews;
the full canonical name remains in the title, accessible name, entity inspector
and List view. Every connector also has a textual equivalent in List view.
Selecting a relationship atomically selects its first Evidence ID and its Source
ID and smoothly reveals that exact passage with complete preceding lines
where space permits. Desktop
selection keeps focus on the graph/list; phone selection opens Sources and moves
focus to the quote. Evidence entries preserve backend order, text, titles and identifiers.
Identically titled sources remain distinct by ID. The source reader highlights
the first exact occurrence only; an unlocatable quote produces an explicit
location error rather than an approximate match. Returning to the relationship
restores its originating view and the current canonical relationship button,
including when the diagram renderer has recreated its label portal.

At 900px and below, Relationships and Sources become separate views. The readable
relationship list opens by default; the complete pannable graph remains available. Evidence activation
opens Sources and focuses the exact highlight (or source heading). Relationship
selection provides the same direct source access. The return
action retains the relationship selection. Intake and whole-proposal dialogs
stack at phone width.

Graph and List use a draggable segmented control with complete clickable targets
and roving keyboard tabs. Its highlight tracks the pointer directly, then settles
with a heavily damped spring. Both working views remain mounted: switching keeps
the camera, query and scroll positions. Hover, keyboard focus and selection
emphasize the claim and its endpoints without relayout or camera movement.

Sources keep stable numbered tabs, including distinct documents with identical
titles. Tabs identify supporting Evidence for the selected relationship. Choosing
a supporting source reveals its first matching passage in canonical order;
unrelated sources remain available with their remembered reading position. The
active tab is brought into the horizontal strip without moving the outer page.
Only the document body receives a brief handoff fade; titles and exact quotations
always update together. Long tab titles are bounded, with full text available in
the document heading and native title.

Motion answers work across the application: 120ms Evidence opacity changes,
an interruption-safe 180ms source underline, 160ms route acknowledgement,
280ms decelerating source reveal, short menu transitions and native dialog
entrance/exit. Pressed controls compress subtly; ledger arrows acknowledge
hover; source rows settle into place.
No graph drift, automatic selection zoom, decorative entrance sequence or
animated edge flow. Reduced motion removes translation/scale and snaps the view
control immediately and reveals source passages instantly while keeping brief
opacity feedback. Direct reader input cancels scrolling; a new selection
retargets from the current position.

Application links retain native URLs while navigating without a document reload.
Tab-memory retains the separate Matters and Review searches, review context,
intake fields/PDFs and terminal recovery messages. Reload/close clears this
presentation state. Sign-out also resets mounted values and removes the draft
unload warning. In-flight submissions keep their current workflow open. No review state is persisted to
the backend or browser storage.

## Workflow boundaries

The proposal page starts with the source method when both methods are available.
PDF intake and Workspace Source discovery use the same centered width and
Public Sans scale for form headings and fields. The PDF form collects Matter
identity, Sources and synthetic-material confirmation.
Workspace discovery uses the available width for connection setup, scope and
results. Intake accepts only explicitly confirmed synthetic or fictional PDF
sources.
Source IDs survive local title edits and removal of other sources. The frontend
checks count, total size and obvious filename type; the unchanged backend owns
actual PDF acquisition and validation. Confirm/discard applies to the entire
proposal with an explicit decision dialog. Proposal details link back to Review.
Discard returns there, and confirmation opens the accepted Matter. Unknown
mutation outcomes retain context and direct the practitioner to check Matters.
Safe mapped errors never render provider diagnostics.

English and Simplified Chinese cover the visible workflow; language preference
switches preserve in-memory intake and review state. There are no live provider
calls in frontend unit or integration tests. Authentication and CSRF remain the
existing same-origin API contract.
