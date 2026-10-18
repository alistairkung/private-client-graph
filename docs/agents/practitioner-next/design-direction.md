# Practitioner-next design direction

## Decision: Working Atlas

Operate mode. A solicitor's working atlas of a Matter: a calm blue-grey application frame surrounds a bright relationship drawing and a persistent source reading surface. The memorable element is the connected relationship-and-Evidence workspace, not a decorative brand header. Matter identity, state and source context remain visible while the practitioner moves between assertions and their support.

This is an independent visual world for `practitioner-next/`. PRODUCT.md supplies product truth; DESIGN.md describes the separate Public Showcase and is context only. Existing `web/` supplies workflow truth, not styling. This planning deliverable creates no UI, comps or existing design-file changes. The lead's explicit selected-direction assignment replaces the skill's interactive concept tournament. Existing Impeccable sidecar drift is reported, not repaired.

## Why this direction

The product's unique mechanism is the reversible journey from a proposed relationship to exact supporting source text and back. Give that journey most of the viewport. Replace the public site's paper/serif/green editorial world with cool mineral surfaces, compact humanist type, disciplined rows and a decisive cobalt selection. Avoid dashboard metric cards, oversized welcome text, ornamental gradients and status colors that imply professional acceptance.

The source panel is a reading surface, the graph a drawing surface, and the application frame a navigation surface. Their different densities communicate their jobs. No decorative imagery is needed.

## Product scope and flow priority

The explorer's current-route inventory takes precedence over older slice documents:

1. **Identify work:** `/app` shows pending Matter Proposals, then accepted Matters. External reference leads each row; title supplies context. A pending proposal opens its review; an accepted Matter opens current state. Use actual returned data only; no invented activity, responsibility, timestamps or counts.
2. **Review:** source-aware graph and Evidence are the main workspace. Select a connector or its equivalent relationship row, activate the first Evidence item, show every Evidence item and open the correct source with one active exact highlight. Choosing another item changes source/highlight as required. A visible return action restores focus to the selected relationship.
3. **Start a proposal:** `/app/matter-proposals/new` contains Matter reference/title, one or multiple titled PDF Sources, the existing explicit synthetic confirmation and the existing analysis submission. Match the real API's constraints and field names. Do not silently choose sample analysis or retry analysis.
4. **Complete a proposal:** inspect saved graph and Evidence, then explicitly confirm the complete proposal or discard it using existing workflows. Professional acceptance applies to the whole proposal; no individual edge acceptance or editing affordance.
5. **Account and language:** retain actual OIDC sign-in/out and en/zh-CN parity. Use a compact language control and standard account menu; do not add users, roles, tenancy or permissions UI.

Match existing backend capabilities exactly. This design authorizes no new non-synthetic intake, new mutation endpoint, domain rule, relationship semantics or acceptance state.

## Desktop structure

At 1440px, use a 224px application rail, a 64px Matter heading and a working area that fills remaining height. The rail has the product wordmark, Matters, New proposal and a clear synthetic environment label; account/language controls sit at its foot. Avoid unrelated navigation roots for People, Trusts or Documents.

```text
┌──────────────────┬────────────────────────────────────────────────────┐
│ Private Client   │ Matters / external reference      Language  Account │
│ Graph            ├────────────────────────────────────────────────────┤
│                  │ Matter title                  Current / Proposal   │
│ Matters          │ external reference       [Confirm proposal*] [...] │
│ New proposal     ├────────────────────────────┬───────────────────────┤
│                  │ Relationships     [Fit]   │ Sources [source title]│
│                  │                           │                       │
│                  │    connected diagram      │ selectable source text│
│                  │    complete labels        │ exact active highlight│
│                  │                           │                       │
│                  ├────────────────────────────┤                       │
│                  │ Selected relationship     │                       │
│                  │ Evidence 1 / Evidence 2    │                       │
│ Synthetic only   │ exact quote / source title │ [Back to relationship]│
└──────────────────┴────────────────────────────┴───────────────────────┘
```

`*` Only a saved proposal has confirm/discard controls. Keep current and proposed state unmistakable in text and in the heading, without imposing an unearned review-progress model. The graph and source columns use approximately 56:44 of the content width; minimum readable source width 340px. Selection detail grows naturally below the graph with an independent scroll region only where necessary. The source has its own scroll region and remains open while inspecting Evidence. No nested scroll region inside an Evidence quote.

The ledger is a proper full-width list/table, not a grid of cards. Pending and current sections use headings and genuine row separators. Single records remain a single row, without filler. At narrower desktop widths collapse the rail to a menu, preserving the workspace's reading width.

## Phone structure

Below 900px use one primary content column. The Matter header has a menu, shortened identity and overflow actions. Use accessible tabs **Relationships** and **Sources**, with selected relationship context retained across tabs. Evidence selection switches to Sources and scrolls the active quote into view; a persistent **Back to relationship** action restores the relationship tab and keyboard focus. Do not shrink the desktop two-pane view until both sides are unreadable.

```text
┌──────────────────────────┐
│ Menu  Matter reference ...│
│ Matter title     Proposal│
│ Relationships | Sources │
├──────────────────────────┤
│ Fit graph     List view  │
│                          │
│ diagram or relationship  │
│ list in available width  │
├──────────────────────────┤
│ Selected relationship    │
│ Source title             │
│ Evidence quote           │
│ View in source           │
└──────────────────────────┘
```

Provide a relationship list equivalent to the graph at every width, especially phone. A diagram may pan within its own labelled viewport; it must not cause page overflow. List rows use full canonical endpoint names and human-readable relationship labels. Intake fields stack; PDF Source rows keep filename/title/remove available without a horizontal table. Confirmation/discard dialogs fit phone height and retain native scrolling.

## Tokens and craft rules

| Role | Value | Use |
| --- | --- | --- |
| Ink | `#1D2B3C` | Main text and diagram labels |
| Secondary ink | `#536579` | Supporting text; never disabled primary information |
| Frame | `#EAF0F5` | Application surround and secondary toolbar |
| Surface | `#FFFFFF` | Graph, forms, lists and source surface |
| Cobalt | `#2358BA` | Primary action, selected relationship, focus-related emphasis |
| Evidence | `#FFF0A6` | Exact source highlight with dark ink |

Use `#CCD7E1` for structural borders, `#B42332` for errors/destructive actions, `#216748` for completed outcomes, and `#8A5B12` for warnings. Status always includes text/icon, never color alone. Primary focus uses a 2px cobalt outline offset 3px; on a cobalt button use a white separation ring plus the cobalt outer ring. Verify actual text/background pairs against WCAG AA.

Typography: IBM Plex Sans where a licensed/self-hostable font asset is available; otherwise `"Segoe UI", Arial, sans-serif` with identical hierarchy. Use this one family throughout, including headings and source text; do not block implementation on a font download. 13px secondary metadata, 14px navigation/compact labels, 15px main UI, 16px source prose at 1.65 line height, 22px Matter title, 28px ledger title. Source measure 60–72ch. At phone width keep inputs at least 16px. Use tabular numerals for Evidence position and technical numeric references only, never monospace as decoration.

Spacing: 4/8/12/16/24/32px; 24px content gutters desktop and 16px phone. Controls at least 44px high. Radius 6px on controls and 8px on dialogs; panels meet with shared straight boundaries. Use shadow only for overlays. Sentence case throughout; avoid uppercase eyebrows. Headings align left. Bold is reserved for the current location and primary identification.

## Graph and Evidence contract

Use one visible node per canonical entity. Person is a compact circular marker with adjacent name; Trust is a larger triangle marker and adjacent name. Keep all supplied family relationships visible. For exactly one Trust, provisional role placement puts settlors above, beneficiaries below and trustees alongside; multiple roles remain one person with separate selectable connectors. No Trust or multiple Trusts use the existing generic layout rules.

Trust-role connectors have labels and no arrowheads. `parent_of` retains parent-to-child direction. Spouse/sibling connectors remain symmetric. Family links use slate strokes; Trust-role links use stronger ink. Selection adds cobalt plus increased stroke/label emphasis, while unselected relationships remain readable. Never infer assets, ownership, priority, absence of a trustee, or additional legal meaning from placement. Every relationship retains an accessible full textual equivalent.

Evidence detail starts with the full relationship statement and exact source title, then selectable Evidence entries and exact quotes. Selecting a quote does not modify its text. Highlight only the active matched span; a numbered position such as “Evidence 1 of 3” is navigation, not a quality score. If an exact match cannot be located, show the quote with a clear source-location error rather than an approximate highlight.

## Interaction and motion handoff

Motion exists only in response to work. Selection should feel immediate: update connector and Evidence together, then reveal/scroll the source target. Use 140–180ms color/background transitions and 180–220ms drawer/tab transitions; no entrance sequence, automatic graph drifting, pulsing nodes or staggered form fields. Preserve graph positions when selecting a relationship. Do not re-fit the camera with every selection.

Source scrolling may be smooth for a user-triggered Evidence jump if it does not obscure the destination. With reduced motion, switch tabs, scroll and focus instantly and remove spatial transitions. Detailed motion implementation belongs to the motion specialist; these are product constraints, not a claim that premium examples were consulted.

## State and accessibility acceptance

- Loading preserves layout with short skeletons; source and graph remain blank placeholders until real data arrives. Busy labels identify the actual operation. Announce completion/errors in a restrained live region.
- Empty ledger explains that no synthetic Matters/proposals are available; offer only the supported new-proposal action. Empty graph explains there are no returned relationships without inventing conclusions about the family or Trust.
- Intake preserves all recoverable field values and server validation messages. Duplicate reference errors offer the actual existing Matter link when returned. Unknown outcomes follow current backend instructions; no automatic resubmission that may duplicate a request.
- Confirm/discard uses explicit action names, describes whole-proposal impact and returns to the correct post-action route. During submission prevent repeated action and preserve the review context on failure.
- Source selection, long filenames, long Matter/entity names, multiple Evidence items, no matches, missing Matter/proposal, expired authentication and API failure all receive usable states. Never hide complete names behind permanent truncation.
- Use semantic links for navigation, buttons for actions, form labels and fieldsets, native dialogs/portalled menus, visible focus and at least 44px primary touch targets. Escape closes overlays; focus returns to their trigger. Menu/tab controls expose state to assistive technology.
- Keyboard users can reach every relationship through the list and perform the same Evidence/source journey. Graph connector pointer hit areas are wider than strokes. Do not require drag, hover, color recognition or diagram geometry to complete a task.
- Maintain en/zh-CN translation parity for every new label and status. Avoid fixed widths built around English labels. Use existing locale behavior and number/date formatting; do not invent translated proper names or source quotes.

## Implementation stop conditions and evidence

Implementer should prove ledger → proposal/current review → relationship → exact Evidence → return focus, new proposal through existing synthetic intake, explicit whole-proposal confirm/discard, and account/language journeys. Verify desktop and phone, keyboard, long content and reduced motion in the bounded QA cycle. Use deterministic API fixtures for browser tests, clearly labelled as isolated UI fixtures, then unchanged-backend integration checks. No live provider call is required for this design.

References: explorer current-route inventory; PRODUCT.md; DESIGN.md (context only); `docs/design/practitioner-matter-workspace-slice.md`; `docs/design/case-01-professional-review-web-slice.md`; `docs/design/trust-structure-presentation.md`. Three scoped design references read; no external visual references, UI edits, nested delegation, paid application-provider calls or motion lookups.
