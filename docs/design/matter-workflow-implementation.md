# Matter workflow implementation

The design authority is [approved design PR #76](https://github.com/alistairkung/private-client-graph/pull/76),
extending the [Matter Ledger](matter-ledger-visual-spec.md). This implementation
retains its paper and white surfaces, deep green actions, Newsreader headings,
Public Sans controls, fine rules, and burgundy focus/selection. The public
landing composition and the existing `DESIGN.md` and `.impeccable/design.json`
remain the incumbent visual system; this is an extension, not a new identity.

## Routes and composition

| Route | Implementation decision |
| --- | --- |
| `/app` | Awaiting confirmation precedes Accepted Matters. Both use reference/title registers; Create Matter remains the primary action. |
| `/app/matter-proposals/new` | Dedicated intake page groups Matter details and Source document, with admission limits and synthetic-only confirmation. An empty source title is initially derived from the selected filename and remains editable. |
| `/app/matter-proposals/{id}` | Saved proposal review uses graph and selected Evidence beside Authoritative Source. `ProposalDecision` accepts the complete proposal or provides inline discard confirmation. |
| `/app/matters/{id}` | Accepted relationships remain visible on return visits. A consumed creation notice supplies the success message after confirmation. |

`RelationshipGraph` is the reusable graph surface, composed by `ReviewWorkspace`
in the landing demonstration, saved proposal, and accepted Matter. It owns the
graph heading and legend around `GraphView`, with selected Evidence supplied by
the workspace. `ReviewWorkspace` coordinates relationship selection, exact quote
highlighting, source focus, and return to the selected relationship. The new
surface therefore appears in the working landing demo as well as the practitioner
journey.

Graph rendering preserves the [Trust presentation rules](trust-structure-presentation.md):
one node per canonical entity, upright Trust triangles with labels below,
rectangular people, labelled arrowless Trust roles, directed parent relationships,
and undirected spouse/sibling relationships. Single-Trust semantic layout and
generic fallback remain presentation transformations, not domain inference.

On narrow screens, graph, Evidence, source, and decisions stack in document flow.
The graph starts and recentres selections at readable zoom, with pan, zoom
controls, a relationship selector, and keyboard selection. View in source focuses
the highlighted passage; the source return control focuses the selected
relationship. Inline discard starts focus on Keep intake, restores focus on
cancellation, hides acceptance while confirming discard, and blocks conflicting
terminal requests.

The shared `BrandMark` and favicon use the approved PC monogram as vector assets.
No new raster assets ship. Adjacent product text supplies the header link name;
the repeated monogram is decorative.

## Verification and limits

The implementation record at `.impeccable/review/implementation-record.json`
records 287 backend tests with disposable PostgreSQL, 97 frontend tests, and
25 browser tests at desktop 1440px and mobile 390px. Coverage includes saved
proposal re-entry, whole-proposal acceptance, discard/cancel focus, multiple-role
selection, source navigation, creation notice consumption, and graph geometry.
Rendered evidence is retained locally under `.impeccable/review/`.

These are behavioural checks and rendered reviews, not measured pixel reproduction
of the generated studies. No measured raster specification was produced; the
local implementation record explicitly leaves that gate incomplete. Generated
compositions never override source facts, connector semantics, or established
Ledger tokens. Independent review accepted the mobile readability and evidence
record fixes; that verdict does not certify whole-surface pixel reproduction.
Professional graph conventions remain provisional pending practitioner validation.

Intake remains synthetic-only under existing authentication and data-handling
gates. Navigation does not save an intake draft or individual review progress.
This work changes no API, extraction contract, deterministic validation,
canonical identity, provenance scoring, benchmark truth, or database schema.
