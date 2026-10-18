# Working Atlas

The independent practitioner application uses the **Working Atlas** direction
in Operate mode. This document applies only to `practitioner-next/`; the root
DESIGN.md remains the Public Showcase's visual authority.

A cool slate application frame surrounds two different working surfaces: a
relationship drawing and a persistent, selectable source reader. Cobalt marks a
deliberate selection; warm yellow identifies only the active exact Evidence
span. No image, activity metric, invented status or decorative animation competes
with the work.

## Foundations

- Ink `#1D2B3C`, secondary ink `#536579`, frame `#EAF0F5`, surface `#FFFFFF`.
- Structural border `#CCD7E1`, action/selection `#2358BA`,
  Evidence `#FFF0A6`, error `#B42332`.
- One humanist system family: Segoe UI, then Arial/sans-serif, as permitted by the
  approved direction. Proper names, source titles and exact quotations remain
  backend-authoritative.
- Main interface 15px; secondary metadata 12–13px; source reading 16px with
  generous leading; Matter title 22px; ledger title 28px.
- Straight panel boundaries, 6px controls, 8px dialogs. Elevation is reserved for
  menus, the mobile rail and dialogs. Focus uses a cobalt 2px outline.
- Content wraps, including long names and filenames. Controls are at least 44px
  except the compact secondary view switch, whose surrounding region is separate
  from primary workflow actions.

## Composition and interaction

The desktop rail is 224px (190px at compact desktop widths); the shell heading
is 64px. The ledger is a divided list with pending proposals first. The review
workspace gives its width to the graph and source text. Canonical Person nodes
use circular notation; Trust nodes use a full-size triangle with its name below.
One-Trust layout places settlors above, beneficiaries below, trustees beside the
Trust and direct family context near its role holder. These are presentation
preferences without additional domain meaning. Separate polylines preserve each
canonical relationship; parent arrows differ from arrowless Trust roles and
symmetric family connectors. Routes clear the Trust caption and unrelated nodes;
label placement reserves space for earlier labels. The generic layout uses Dagre.
Fit includes nodes, captions, all route points and connector labels. Selection
and language changes preserve the camera. Page scrolling does not zoom the graph.

Each connector label is a keyboard-operable button with the full relationship
as its accessible name. Diagram entity names use bounded two-line previews;
the full canonical name remains in the title, accessible name, entity inspector
and List view. Every connector also has a textual equivalent in List view.
Selecting a relationship atomically selects its first Evidence ID and its Source
ID. Evidence entries preserve backend order, text, titles and identifiers.
Identically titled sources remain distinct by ID. The source reader highlights
the first exact occurrence only; an unlocatable quote produces an explicit
location error rather than an approximate match. Returning to the relationship
restores its originating view and the current canonical relationship button,
including when the diagram renderer has recreated its label portal.

Below 900px, Relationships and Sources become separate views. The readable
relationship list opens by default; the complete pannable graph remains available. Evidence activation
opens Sources and focuses the exact highlight (or source heading). The return
action retains the relationship selection. Intake and whole-proposal dialogs
stack at phone width. Account and language controls remain in the menu.

Motion answers work: 120ms Evidence opacity changes, an interruption-safe 180ms
source underline spring and a 180ms native-dialog entrance. No graph drift,
automatic selection zoom, decorative entrance sequence or animated edge flow.
Reduced motion removes layout/translation and keeps only brief opacity changes.

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
