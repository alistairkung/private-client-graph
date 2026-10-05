# Matter Ledger visual specification

> **Status:** Approved visual direction; account-menu amendment implemented.
>
> **Applies to:** The practitioner application throughout the authenticated
> `/app` subtree and the Public Showcase entry link at `/`.
>
> **Does not redesign:** The public synthetic showcase at `/`, Canonical Graph
> semantics, relationship selection, Evidence behaviour, or source highlighting.

## Purpose

The Matter Ledger is the visual direction for the practitioner application. It
should feel like a contemporary professional register: calm, precise, and useful
throughout a working day. Its character comes from disciplined typography and
the alignment of Matter references and titles, not from dashboard furniture or
decorative imagery.

The practitioner application is visually related to the Public Showcase but is
not another marketing or demonstration page. The showcase remains expressive,
explanatory, and serif-led. The practitioner application is quieter, denser, and
task-led.

This specification implements the product topology and constraints in
`practitioner-matter-workspace-slice.md`. If this specification and that product
design ever conflict, the product design is authoritative.

## Experience principles

1. **The register is the centre of the application.** The Matter collection is
   presented as aligned professional records, never as a set of cards.
2. **Structure conveys meaning.** Rules separate real columns and records; they
   are not decorative framing.
3. **Recognition precedes exploration.** The external Matter reference and title
   are the only collection fields because they are the only agreed information
   needed to identify a Matter.
4. **Work begins immediately.** Opening a Matter leads directly to the existing
   graph-and-Evidence review workspace, not to an overview or dashboard.
5. **The interface never promises unsupported work.** The account control
   contains only the two available secondary actions. It does not imply a
   profile, settings, notifications, Firm selection, roles, or account
   management.
6. **Synthetic and read-only are boundaries, not badges of progress.** State
   this boundary plainly in the application footer; do not represent it as a
   Matter status.

## Relationship to the Public Showcase

Preserve the current Public Showcase identity at `/`:

- soft sage background;
- deep green brand colour;
- Georgia-led editorial headline;
- generous explanatory composition;
- synthetic demonstration labels and analysis controls;
- current graph, source, and Evidence interaction.

The practitioner application shares only the following family traits:

- the existing Private Client Graph name and brand symbol;
- a deep green primary colour;
- the established gold source-Evidence highlight;
- the existing entity and relationship colours inside the review workspace.

It deliberately differs through:

- a horizontal application shell rather than a showcase masthead and hero;
- a mostly sans-serif interface with restrained serif titles;
- a neutral paper ground rather than the showcase's sage ground;
- aligned register rows rather than rounded content cards;
- compact task copy rather than promotional copy;
- no analysis controls in a Matter workspace.

Keep one quiet text link from the showcase masthead to **Practitioner
application**. Style that link within the existing showcase identity; do not
import the Matter Ledger shell, typography, or account control into `/`. The
link remains visible whether or not the browser holds an authenticated
practitioner session. It navigates to `/app`, where the server-owned
authentication boundary begins sign-in when required.

## Core visual system

### Colour

Use these six core colours for the practitioner shell and Matter collection.
Names are semantic guidance rather than a required CSS naming scheme.

| Token | Value | Use |
| --- | --- | --- |
| Ledger ink | `#173E38` | Primary text, brand, active navigation, links |
| Ledger burgundy | `#773B46` | Keyboard focus and restrained selection emphasis |
| Ledger paper | `#F6F6F1` | Application background |
| Ledger surface | `#FFFFFF` | Register rows and review surfaces |
| Ledger rule | `#C9CEC8` | Header, column, row, and section boundaries |
| Ledger muted | `#59655F` | Secondary text and column headings |

Do not add gradients. Do not use shadows on the shell or Matter list. Distinguish
surfaces through background colour and one-pixel rules.

The existing graph entity colours and gold Evidence highlight belong to the
review workspace and remain unchanged unless separately reviewed. Burgundy is
not a replacement for the Evidence highlight.

### Typography

Use two type families with clearly separated roles:

- **Public Sans** for navigation, body copy, Matter references, column headings,
  state messages, controls, and supporting interface text.
- **Newsreader** for the Matters page title, Matter titles in the register, and
  the Matter workspace title.

Bundle the required WOFF2 font files with the frontend rather than requesting
fonts from a third-party service at runtime. Load only the weights the interface
uses:

- Public Sans 400, 500, and 600;
- Newsreader 500 and 600.

Fallback stacks:

```text
Public Sans: Arial, Helvetica, sans-serif
Newsreader: Georgia, "Times New Roman", serif
```

Use sentence case throughout. Do not use tracked uppercase eyebrows or a
monospace face for Matter references.

| Role | Size / line height | Weight | Notes |
| --- | --- | --- | --- |
| Page title | `32px / 38px` | Newsreader 500 | `28px / 34px` on small screens |
| Matter title | `18px / 26px` | Newsreader 500 | May wrap to two lines |
| Navigation | `14px / 20px` | Public Sans 600 | No letter spacing |
| Body | `15px / 23px` | Public Sans 400 | Maximum readable line length: 70 characters |
| Column heading | `13px / 18px` | Public Sans 600 | Sentence case |
| Matter reference | `14px / 20px` | Public Sans 600 | Use tabular numerals where supported |
| Supporting text | `13px / 20px` | Public Sans 400 | Muted colour |

The authoritative source retains its existing document-oriented serif treatment.
Do not make graph labels or Evidence controls serif.

### Shape and elevation

- Application shell and register: square corners.
- Interactive controls: maximum `3px` corner radius.
- Existing graph and source panels may retain their present shape in the first
  implementation; do not force a full workspace restyle into ticket #21.
- No drop shadows in the shell or Matter collection.
- Do not place the Matter list inside a rounded card.

### Spacing

Use an eight-pixel base rhythm with four-pixel adjustments for type alignment.

- Application content maximum width: `1180px`.
- Wide-screen horizontal page padding: `48px`.
- Standard desktop page padding: `32px`.
- Small-screen page padding: `20px`.
- Main content top padding: `48px`; `32px` on small screens.
- Heading-to-register gap: `32px`.
- Register header height: `40px`.
- Populated Matter row minimum height: `64px`.
- Empty and error register body minimum height: `136px`.

Content is left aligned. Do not centre the page title, introductory copy, list
content, empty state, or error state.

## Practitioner application shell

### Desktop shell

The shell is a single horizontal bar with a `68px` minimum height and a bottom
rule. Its inner content uses the same `1180px` maximum width as the page.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ [mark] Private Client Graph   Matters                    [account]  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ page content                                                         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

- The brand is first and links to `/app`.
- **Matters** is the only primary navigation item and links to `/app`.
- Mark Matters as current on both `/app` and Matter-detail routes.
- Place the circular account-and-application trigger at the far right.
- Do not add placeholder navigation items to balance the header.
- Do not add a profile image, identity text, Firm name, notifications, help, or
  settings.

The current-navigation treatment is a two-pixel Ledger ink rule aligned with the
shell's bottom boundary. It is not a filled pill.

The account control intentionally supersedes the original shell rule that
required **Public showcase** as a persistent far-right text link and prohibited
all avatar or user chrome. The exception is narrow: it consolidates only surface
switching and session termination and creates no broader profile concept.

### Account and application menu

The trigger is a restrained utility control rather than a personalized avatar:

- use a familiar person silhouette with no initials, photograph, presence dot,
  badge, or chevron;
- render a `36px` visible circle within a minimum `44px` square target;
- use a transparent or Ledger surface background, a one-pixel Ledger rule
  border, and a Ledger ink glyph;
- use the stable accessible name **Account and application menu** and expose the
  expanded state programmatically;
- when expanded, use the existing pressed background `#E8ECE8` rather than a
  decorative accent.

Activating the trigger opens one compact popover aligned to its right edge:

```text
┌──────────────────────┐
│ Public showcase      │
├──────────────────────┤
│ Sign out             │
└──────────────────────┘
```

The menu contains exactly those two actions, in that order. **Public showcase**
is an ordinary link to `/`. A meaningful one-pixel rule separates it from the
**Sign out** button because one changes application surface and the other ends
the session. Do not add an Account heading, identity summary, icons, descriptive
copy, or unsupported actions.

The panel uses Ledger surface, a one-pixel Ledger rule border, no shadow, and a
maximum `3px` corner radius. Set its width to `192px`; constrain it to the
viewport with the shell's small-screen margin. Rows are full-width, left-aligned,
at least `44px` high, padded `16px` horizontally, and set in Public Sans 600 at
`14px / 20px`. The panel opens immediately without scale, fade, bounce, or other
decorative motion.

Treat the control as a disclosure with native link and button behaviour, not as
a strict ARIA menu widget. Click, Enter, and Space toggle it. Opening leaves
focus on the trigger so Tab moves naturally to **Public showcase** and then
**Sign out**. Escape closes the panel and returns focus to the trigger. Clicking
outside or moving focus outside the trigger-and-panel region closes it. Do not
trap focus.

Sign out continues to use the existing CSRF-protected logout operation. While
the request is pending, keep the panel open, disable the action, and label it
**Signing out…**. Success navigates to `/`. Failure keeps the panel open,
restores **Sign out**, and places **Could not sign out. Please try again.** in an
alert directly below the action so retry remains available.

### Narrow shell

Below `720px`, use two rows:

```text
┌──────────────────────────────────────────┐
│ [mark] Private Client Graph   [account] │
│ Matters                                  │
├──────────────────────────────────────────┤
```

The first row holds the brand and account trigger. The second row contains the
single current navigation item. Keep both visible; do not introduce a hamburger
menu, bottom sheet, or alternate mobile navigation model. The same popover opens
below the trigger and aligns to the inline end. It remains inside the viewport
with a `20px` minimum edge margin; its two rows are short enough that it needs no
flipping or internal scrolling behaviour.

### Footer

Use one quiet footer line beneath the page content:

```text
Private Client Graph                 Read-only · Synthetic material only
```

On small screens the two phrases stack. This statement describes the boundary of
the entire current application; it must not be rendered as a Matter status chip.

## Matter collection at `/app`

### Page heading

Use exactly:

```text
Matters
Open a Matter to review relationships and the source evidence supporting them.
```

The first line is the page's `h1`. The second is ordinary body copy with a
maximum width of 620px. Do not add an eyebrow, Matter count, welcome message, or
introductory marketing claim.

### Register structure

The register has two columns:

1. **Matter reference** — fixed desktop width of `220px`;
2. **Matter** — consumes remaining width.

```text
Matter reference       Matter
──────────────────────────────────────────────────────────────────────
{external_reference}   {title}
──────────────────────────────────────────────────────────────────────
```

The header and body share exactly the same grid definition. A one-pixel vertical
rule separates the columns on desktop. Horizontal rules define the header and
each record. Do not add zebra striping.

Each populated row is one full-width link to
`/app/matters/{internal_id}`. The internal ID is never visible. The row contains
only `external_reference` and `title`.

Interaction treatment:

- default background: Ledger surface;
- hover background: `#F0F2EE`;
- hover title: underline with an offset of `3px`;
- keyboard focus: a visible `3px` inset Ledger burgundy outline;
- active/pressed background: `#E8ECE8`;
- no trailing arrow, overflow menu, secondary action, or status chip.

The title may wrap to two lines. Do not truncate a title merely to preserve a
single-line row. The reference does not wrap; if an exceptional value is too
long, allow horizontal text overflow to break safely rather than reducing the
font below the specified size.

### Truthful empty state

Before persisted Matters are introduced, render the same register header followed
by one empty register body. Use exactly:

```text
No Matters available
This read-only application does not currently contain any Matters.
```

The first line uses Public Sans 600 at the body size. The second uses supporting
text styling. Align both lines to the Matter-title column on desktop. There is no
illustration, icon, placeholder row, create action, upload action, or call to
contact an administrator.

### Loading and failure states

When Matter persistence is implemented, use the same register body for request
states. Do not use skeleton rows because they resemble fictitious Matters.

Loading copy:

```text
Loading Matters…
```

Collection failure copy:

```text
Matters could not be loaded.
Reload the page to try again.
```

A failure may include a **Reload page** button because it repeats an available
browser action. It must not include sample data or a fallback Matter.

### Small screens

Below `640px`, remove the visible register column header and vertical divider.
Keep the collection semantically structured, but stack the two fields in each
row:

```text
{external_reference}
{title}
────────────────────────────
```

- Reference appears first in muted Ledger ink at `13px / 18px`.
- Title follows with a four-pixel gap.
- Row padding is `16px 0` and minimum target height remains `48px`.
- The empty state aligns to the left edge of the register.

Do not turn rows into detached mobile cards.

## Matter workspace at `/app/matters/{internal_id}`

The practitioner shell remains visible. The page opens directly into the existing
relationship review workspace with its graph, Evidence list, authoritative
source, selection, and exact highlighting behaviour intact.

Above the workspace, render a compact Matter context header:

```text
Back to Matters
{title}
Matter reference: {external_reference}
```

- **Back to Matters** links to `/app` and is the explicit return route.
- The title is the page `h1` in Newsreader.
- The reference is supporting text, not a badge or breadcrumb identifier.
- Do not show the internal UUID.
- Do not add tabs, status, dates, responsible professional, relationship counts,
  analysis mode, reanalysis controls, or an overview section.

The review workspace begins `24px` below this context header. Reuse the existing
responsive two-column-to-single-column transition. Any visual consolidation of
the graph and source panels should be a separate design review; ticket #21 only
needs the shell and route separation.

### Matter loading and not-found states

Loading copy:

```text
Loading Matter…
```

Missing Matter copy:

```text
Matter not found
Return to Matters to choose an available Matter.
```

Provide **Back to Matters** for both missing and failed Matter loads. Do not route
to the Public Showcase as a fallback and do not load Case 01 fixture data.

## Interaction and motion

- Use no entrance animation, staggered row reveal, or ambient motion.
- Open and close the account popover without decorative animation.
- Hover and focus colour changes may use a `100ms` linear transition.
- Navigation must not depend on animation to communicate state.
- Respect `prefers-reduced-motion` by removing non-essential transitions.
- Preserve the existing direct Evidence-scroll behaviour in the review workspace.

## Accessibility requirements

- Use landmarks for header, navigation, main content, and footer.
- Give the primary navigation an accessible label such as
  `Practitioner application`.
- Mark Matters with `aria-current="page"` or `aria-current="true"` as appropriate.
- Implement the account trigger as a native button with a stable accessible
  name, `aria-expanded`, and `aria-controls` referring to the popover.
- Keep the popover's link and button in ordinary document tab order; do not add
  ARIA menu roles or arrow-key-only navigation.
- Support Escape, outside-click dismissal, focus-departure dismissal, and focus
  return to the trigger after Escape.
- The register may use a semantic table or a list with equivalent labelled
  structure. The whole row must expose one clear link, not nested interactive
  controls.
- Keep all body text at or above 13px and interactive text at or above 14px.
- Preserve a minimum `44px` pointer target and a visible keyboard focus indicator.
- Do not communicate current navigation, errors, or selected relationships by
  colour alone.
- Loading messages use an appropriate status region. Failures use an alert region.
- Page titles and focus order must update correctly during direct navigation and
  browser refresh.

## Styling boundary

Practitioner styles must be scoped beneath a dedicated application-shell class or
data attribute. Do not redefine global `h1`, `h2`, `button`, `.panel`, or body
rules in a way that changes the Public Showcase.

Shared brand primitives may be reused intentionally. Layout, typography, register,
and state styles should remain practitioner-specific so the two surfaces can
evolve independently.

The design does not require a general-purpose design-system component library.
Implementation should introduce only meaningful concepts such as:

- practitioner application shell;
- Matter collection;
- Matter row;
- collection state;
- Matter context header.

Names are illustrative; preserve the repository's compositional frontend style.

## Explicit exclusions

Do not add any of the following to make the design appear more complete:

- Matter creation, upload, intake, edit, or delete controls;
- search, filter, sorting, pagination, saved views, or bulk selection;
- Matter counts, relationship counts, clients, trusts, documents, or people in
  the collection;
- review status, progress, priority, assignment, activity, deadline, or date;
- profile identity, Firm selection, notification, help, settings, role, or
  account-management chrome beyond the accepted account and application menu;
- placeholder or duplicate synthetic Matters;
- charts, KPIs, summary tiles, illustrations, or decorative icons;
- AI sparkle marks, gradients, glowing accents, or animated graph motifs;
- live or sample analysis controls within a Matter;
- benchmark, run-artifact, confidence, or evaluation information.

## Design self-review

The initial Matter Ledger direction risked resembling a broadsheet because it
combined serif typography, warm paper, and extensive rules. This specification
corrects that risk by:

- limiting Newsreader to page and Matter titles;
- using Public Sans for all operational information;
- using rules only to encode real register structure;
- avoiding oversized editorial type and multi-column prose;
- using a near-neutral paper colour rather than a pronounced cream;
- making row interaction and application navigation explicit.

The result should read as a professional legal register rendered for the web,
not as a newspaper, luxury brand page, or generic SaaS dashboard.

## Visual acceptance checklist

An implementation is visually complete when:

- `/` retains its existing showcase composition and identity;
- `/app` is visibly a separate practitioner application without appearing to be
  a different brand;
- Matters is the only primary application navigation concept;
- the account trigger is present and usable on every authenticated practitioner
  route and absent from the Public Showcase;
- the menu contains only Public showcase and Sign out, with no implied identity
  or unsupported account capabilities;
- the empty state contains no fake Matter or unsupported action;
- a populated Matter row shows only its external reference and title;
- the Matter list reads as aligned records rather than cards;
- the shell and collection have no gradients or shadows;
- typography follows the roles and scale above;
- keyboard focus is clearly visible on navigation and Matter rows;
- desktop and small-screen layouts retain the same information hierarchy;
- the menu remains inside the narrow viewport and preserves a minimum `44px`
  target for its trigger and actions;
- direct Matter navigation provides a clear route back to `/app`;
- opening a Matter exposes the existing review workspace without analysis
  controls or an intermediate overview;
- read-only synthetic scope is stated without implying a review status;
- no UI element implies functionality beyond the accepted slice.

## Behavioural test boundary

Focused frontend tests should protect the account control's accessible name and
expanded state; click and keyboard opening; Escape, outside-click, and
focus-departure closing; Escape focus return; correct showcase destination; the
existing CSRF-protected sign-out request; pending, success, failure, alert, and
retry behaviour; absence of unsupported items; and continued presence of
**Matters** and the synthetic-only notice.

Browser coverage should retain the existing application journeys while proving
the boundaries that require a real browser: authenticated practitioner to
Public Showcase through the menu; visible Public Showcase entry back to the
Practitioner Application and its server-enforced authentication boundary;
successful sign-out and loss of protected access; failed sign-out with retained
session and usable retry; keyboard access; and availability within the existing
narrow viewport. Do not duplicate every component interaction in Playwright or
replace the existing graph-review, Matter Proposal, and analysis journeys with
navigation-only tests.
