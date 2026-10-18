# Working Atlas

The production practitioner application uses the approved **Working Atlas**
direction in Operate mode. Its implementation lives in `web/src/`. See the
[root design record](../../DESIGN.md) for the landing and research boundaries.

A pale green application frame and deep forest rail surround two different
working surfaces: a relationship drawing and a persistent, selectable source
reader. The user-selected **Forest & Chalk** palette uses green for deliberate
selection; warm yellow identifies only the active exact Evidence
span. No image, activity metric, invented status or decorative animation competes
with the work.

## Foundations

- Ink `#20372B`, secondary ink `#566B5D`, frame `#E9F0EA`, surface `#FFFFFF`.
- Rail `#173F31` with text `#E5EFE7` and secondary text `#C0D4C6`.
- Structural border `#C7D3C8`, control border `#7D9283`, action/selection `#1E6249`,
  Evidence `#FFF0A6`, error `#B42332`.
- One humanist system family: Segoe UI, then Arial/sans-serif, as permitted by the
  approved direction. Proper names, source titles and exact quotations remain
  backend-authoritative.
- Main interface 15px; secondary metadata 12–13px; source reading 16px with
  generous leading; Matter title 22px; ledger title 28px.
- Straight panel boundaries, 6px controls, 8px dialogs. Elevation is reserved for
  menus, the mobile rail and dialogs. Focus uses a green 2px outline; the dark
  rail uses a light outline. White account menus restore dark text and green focus.
- Content wraps, including long names and filenames. Controls are at least 44px
  except the compact secondary view switch, whose surrounding region is separate
  from primary workflow actions.

## Composition and interaction

The desktop rail is 176px; the phone header is 52px. The synthetic-environment
and public-source notices sit above the remaining review workspace. Their actual
height, including wrapping, must not push the Evidence controls below the viewport. The ledger is a compact divided list with pending proposals
first, collapsing an empty pending section to one line. The review workspace
keeps the drawing, compact Evidence inspector and independently scrolling source
text within a stable frame. Canonical Person nodes
use circular notation; Trust nodes use a full-size triangle with its name below.
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
ID and smoothly reveals that exact passage inside the source reader. Desktop
selection keeps focus on the graph/list; phone selection opens Sources and moves
focus to the quote. Evidence entries preserve backend order, text, titles and identifiers.
Identically titled sources remain distinct by ID. The source reader highlights
the first exact occurrence only; an unlocatable quote produces an explicit
location error rather than an approximate match. Returning to the relationship
restores its originating view and the current canonical relationship button,
including when the diagram renderer has recreated its label portal.

Below 900px, Relationships and Sources become separate views. The readable
relationship list opens by default; the complete pannable graph remains available. Evidence activation
opens Sources and focuses the exact highlight (or source heading). Relationship
selection provides the same direct source access. The return
action retains the relationship selection. Intake and whole-proposal dialogs
stack at phone width. Account and language controls remain in the menu.

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
280ms decelerating source reveal, short menu/rail transitions and native dialog entrance/exit. Pressed controls
compress subtly; ledger arrows acknowledge hover; source rows settle into place.
No graph drift, automatic selection zoom, decorative entrance sequence or
animated edge flow. Reduced motion removes translation/scale and snaps the view
control immediately and reveals source passages instantly while keeping brief
opacity feedback. Direct reader input cancels scrolling; a new selection
retargets from the current position.

Application links retain native URLs while navigating without a document reload.
Tab-memory retains ledger search, review context and intake fields/PDFs, including
terminal recovery messages. Reload/close clears this presentation state; sign-out
also resets mounted values and removes the draft unload warning. In-flight
submissions keep their current workflow open. No review state is persisted to
the backend or browser storage.

## Workflow boundaries

Intake accepts only explicitly confirmed synthetic or fictional PDF sources.
Source IDs survive local title edits and removal of other sources. The frontend
checks count, total size and obvious filename type; the unchanged backend owns
actual PDF acquisition and validation. Confirm/discard applies to the entire
proposal with an explicit decision dialog. Unknown mutation outcomes retain
context and direct the practitioner to check Matters. Safe mapped errors never
render provider diagnostics.

English and Simplified Chinese cover the visible workflow; language preference
switches preserve in-memory intake and review state. There are no live provider
calls in frontend unit or integration tests. Authentication and CSRF remain the
existing same-origin API contract.
