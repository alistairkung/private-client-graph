# Public landing experience: Follow the source

> **Status:** Historical design. Its visual composition is superseded by the
> [approved Evidence Folio direction](public-landing-visual-direction.md).
> The full-page scope below is not renewed implementation authorization.
>
> **Scope:** Public product/research presentation at `/`, including the real
> synthetic demonstration and a restrained practitioner-interest invitation.
>
> **Direction:** Follow the source. This document records the selected direction
> and supporting decisions for implementation ticketing; it does not reopen
> alternative landing-page concepts.

## Purpose

Private Client Graph reconstructs reviewable family and trust relationships from
source material while preserving Evidence for each relationship. The public
landing experience should explain that proposition through the actual product,
make its research methodology visible, and invite informed practitioner interest.

The page should feel professional, editorial, restrained, confident, and
appropriate for private-client practice. Its credibility comes from inspectable
product behavior and honest research scope, not commercial claims.

The relationship graph is the primary visual asset. Source material, exact
Evidence, and actual synthetic practitioner-product captures provide the rest of
the story. Do not introduce stock photography, decorative networks, fake product
screens, generic feature-card grids, testimonials, logos, pricing, or invented
adoption, accuracy, security, or compliance claims.

## Relationship to existing guidance

Read this alongside:

- [Project glossary](../../GLOSSARY.md).
- [Web application guidelines](../WEB_APP_GUIDELINES.md).
- [Original Public Showcase slice](case-01-professional-review-web-slice.md).
- [Matter Ledger visual specification](matter-ledger-visual-spec.md).
- [Trust-structure presentation](trust-structure-presentation.md).
- [Matter Intake](matter-intake-slice.md).
- [Professional review and evaluation separation](../adr/0001-separate-professional-review-from-benchmark-evaluation.md).
- [Public and practitioner journey separation](../adr/0003-separate-public-showcase-from-practitioner-application.md).
- [Authoritative Source text](../adr/0005-treat-extracted-pdf-text-as-the-authoritative-source.md).
- [Professional confirmation](../adr/0006-require-professional-confirmation-before-current-matter-state.md).

This approved presentation design supersedes the earlier requirement to retain
Georgia and the existing showcase composition at `/`. Newsreader and Public Sans
now extend to the public experience; the practitioner shell and account control
remain exclusive to `/app`.

It also extends the original first-slice public presentation with a research
methodology and evaluation-in-progress section. Evaluation remains separate from
Professional Review: no scoring is added to the review workspace, practitioner
workflow, or showcase analysis response. No domain or evaluation semantics change.

## Information architecture

`/` remains the Public Showcase journey, expanded into the full landing narrative
with the real demonstration embedded. `/app` remains the separate authenticated
Practitioner Application.

- Provide anchors for the demonstration and evaluation chapter.
- Keep a quiet **Practitioner application** link to `/app` in the public header.
- Let the existing server boundary handle authentication when required; the
  public page does not inspect session state or render an account menu.
- Prefer **Expand demonstration** inline before adding a dedicated `/demo`
  route. Expansion must preserve the loaded result and review selection.
- A future dedicated route requires a concrete navigation or sharing need and
  must reuse the same showcase orchestration and shared review implementation.

## Narrative

```text
Understand the proposition and see the Evergreen graph
    -> follow source passages and their relationships
    -> inspect the real graph and exact Evidence
    -> understand machine proposal versus professional acceptance
    -> ask how well the system recovers relationships
    -> understand methodology and evaluation in progress
    -> express practitioner interest
    -> explore the demonstration or open the practitioner prototype
```

### 1. Opening: understand the relationships

Approved headline:

> See the relationships. Read the evidence.

Supporting copy should explain family and trust relationships drawn from
synthetic source material, with supporting passages available for review.
Keep the complete Evergreen graph legible beside a narrower, left-aligned text
column. Give the graph approximately three-fifths of the desktop opening width.

The primary action is **Explore the demonstration**. The practitioner route is
secondary. The demand-validation invitation does not belong in the hero.

Before explicit sample loading, a clearly labeled capture of the actual sample
graph may supply the hero visual. Do not create an independent decorative graph
implementation or present the capture as interactive or newly extracted output.

Display prominently near the opening:

> Synthetic research prototype. Do not use real client information.

### 2. Guided source-to-relationship scene

Use Case 01's actual synthetic attendance note and supplied relationships to
explain three moments:

1. Alice's connection to Evergreen establishes the settlor relationship.
2. The family passage establishes spouse and parent relationships.
3. The beneficiary passages establish Bob's and Carol's distinct Trust roles.

Bob's family relationships do not themselves establish his beneficiary role.
Carol's beneficiary role establishes no family connection. These distinctions
make the explanation specific to this product without introducing new facts.

On desktop, use one bounded sticky scene with source material and graph alongside
short narrative passages. Keep the complete graph structurally stable and every
relationship available. Progressively emphasize the relevant relationship,
Evidence, and exact source passage rather than simulating graph construction.

- Label this as a guided sample walkthrough, not live extraction.
- Preserve existing node identities, connector meanings, and graph layout.
- Do not add missing roles or relationships to complete a visual pattern.
- Resolve emphasis against the supplied graph and Evidence; do not independently
  interpret source prose in the frontend.
- Do not rewrite or truncate the authoritative source used for exact matching.
- Do not force the Case 01 guided sequence onto a live result that differs from
  the sample. Live results remain available through ordinary review.

Keep this scene short and provide immediate access to the real interaction,
including a **Skip to interactive demonstration** link. Essential information
must not depend on scrolling through animation states.

### 3. Inspect the real demonstration

Suggested invitation:

> Choose a relationship. Read what supports it.

Embed the existing shared relationship-review implementation at a generous width.
Visitors can inspect the graph, select any relationship, inspect all attached
Evidence, and see the active exact supporting passage highlighted in the source.

**Load sample analysis** remains an explicit action. It uses the backend-owned
ideal-extraction fixture and current deterministic graph construction. It is not
a live model run, prior-run replay, or automatic fallback.

Present live analysis as a secondary option near the workspace, for example under
**Analysis options**. Retain accurate mode labels, availability, pending states,
errors, and explicit retry behavior. Never silently substitute sample analysis
for live analysis. No automatic model call is triggered by visiting or scrolling
the landing page.

Once a visitor interacts with the review controls, narrative-controlled selection
stops. Subsequent page scrolling must not overwrite their selection. Inline
expansion and collapse retain the result, selected relationship, and active
Evidence, with predictable keyboard focus.

### 4. Professional judgment and the practitioner workflow

Suggested heading:

> A proposed graph still needs professional judgment.

Use actual synthetic captures of Create Matter, Matter Proposal review, the
whole-graph confirmation action, accepted Matter review, and the Matter Ledger
where useful. Captures illustrate existing product behavior; they are not public
intake or confirmation controls.

```text
One synthetic text-layer PDF
    -> finalized Authoritative Source text
    -> AI interpretation and deterministic graph construction
    -> durable Matter Proposal
    -> inspection of graph and exact Evidence
    -> explicit whole-graph confirmation
    -> accepted Matter state
```

The PDF is an acquisition format. Evidence is highlighted in the extracted
Authoritative Source text, not on the original PDF page. Do not imply document
storage, OCR, or PDF-coordinate highlighting.

`MatterProposal.proposed_graph` is mechanically valid machine-proposed state.
Confirmation copies it unchanged into `Matter.current_graph`, the professionally
accepted current state. Do not imply per-relationship decisions, correction,
partial acceptance, or guaranteed legal or semantic correctness.

Keep the graph visually unchanged across the illustrated confirmation boundary.
Avoid a verified stamp or success treatment that conflates acceptance with proof
of correctness. The public sample is not saved as a Matter. The pre-accepted
Evergreen seed must not be presented as a recorded confirmation event.

Weave the architecture principles into the relevant transitions:

- **Interpretation:** the model proposes relationships from natural language.
- **Mechanical checks:** code handles IDs, normalization, references, structural
  validation, graph construction, and exact quote occurrence.
- **Professional judgment:** a practitioner decides whether to accept the whole
  proposal.

Exact quote occurrence is not proof that a quote semantically supports a claim.
Use short annotations rather than three generic architecture cards.

### 5. Evaluation as a substantial research chapter

The transition from trying the product is:

> How well does it recover the relationships?

Give this chapter meaningful page space and a navigation anchor. Explain the
methodology before presenting the eventual metric register. Initial status copy:

> Evaluation is in progress. Representative aggregate results are not yet
> available.

```text
Define the answer key, then author synthetic source material
                    |
         +----------+-----------+
         |                      |
Source given to extractor      Answer key and approved Evidence
         |                      |
Extraction and deterministic   |
graph construction             |
         +----------+-----------+
                    |
          Deterministic comparison
                    |
       Relationship and provenance metrics
```

The answer key is hidden from the extractor. It is not inferred retrospectively
from model output. Evaluation is an offline research path, not a scoring step
applied to professionally accepted Matters.

| Measure | Initial result | Explanation |
| --- | --- | --- |
| Relationship precision | — | How many predicted relationships match the answer key |
| Relationship recall | — | How many expected relationships were recovered |
| F1 | — | The balance of precision and recall |
| Provenance accuracy | — | Among correct relationships, how many include at least one approved Evidence span |
| Evaluation-set size | — | Cases included in the published evaluation |

Expose placeholders accessibly as **Not yet published**. They are not zeros,
loading skeletons, animated counters, or failed requests. Do not promote isolated
Case 01 results into general product-performance claims.

Design the register so representative results can replace placeholders without
redesigning the section. Reserve room for publication scope, case coverage,
model/run configuration, evaluation date, and aggregation method. Show genre or
challenge breakdowns only when real evaluation data supports them.

Unresolved aggregation or publication methodology must not block the initial
placeholder section. Publishing representative results is later research work.
The section should make clear how benchmark cases, approved Evidence, and measured
results contribute to the finished public project.

### 6. Practitioner-interest invitation

Place this after evaluation, once visitors have encountered the proposition,
interactive demonstration, professional-review boundary, and research method.

Approved working copy:

> **Could this support your practice?**
>
> If you work in or around private-client practice, get in touch to explore the
> prototype, discuss the research, or arrange a demonstration.

Action: **Email about the project**, opening a pre-addressed email to the supplied
project contact. This names what happens next; it does not promise immediate
prototype access, a booked appointment, or automatic admission to the allowlist.

Supporting instruction:

> Please keep your message free of client information.

Use a quiet, left-aligned composition. Do not add a waitlist, newsletter, contact
database, upload form, pricing, trial, urgency, scarcity, or claimed customer
interest. The destination email address is the only outstanding contact dependency.
Do not invent it or ship a nonfunctional placeholder link.

This action is a lightweight demand-validation experiment. The meaningful signal
is an actual practitioner starting a conversation or requesting a demonstration.
Opening an email composer does not prove that a message was sent. CTA clicks, if
measured later, indicate interest but establish neither practitioner identity nor
qualified demand. Initial implementation requires no new analytics platform or
tracking infrastructure; received inquiries can inform subsequent product choices.

### 7. Final routes and limitation

Finish with **Explore the demonstration** and **Open practitioner prototype**,
alongside this full-size statement:

> Synthetic research prototype. Do not use real client information.

Keep the same limitation prominent near the opening and demonstration. It must
not be confined to small footer text.

Future direction is optional and limited to a short, explicitly future-facing
paragraph. iManage may be described as a practitioner-requested acquisition
direction, never an available integration. Do not imply native email ingestion,
multi-document reconciliation, historical state, enterprise tenancy, or readiness
for confidential client data.

## Visual system

Extend the existing practitioner identity without importing its application shell.

| Token | Value | Role |
| --- | --- | --- |
| Ledger ink | `#173E38` | Primary text, brand, actions |
| Ledger paper | `#F6F6F1` | Page ground |
| Surface | `#FFFFFF` | Source and product surfaces |
| Muted ink | `#59655F` | Supporting text |
| Burgundy | `#773B46` | Keyboard focus and restrained interface emphasis |
| Evidence gold | `#F6DC8F` | Exact source highlight only |

Retain existing graph colors, connector conventions, selection treatment, and
structural rule colors. Evidence gold is not a general marketing accent.

- Use bundled Newsreader 500 for editorial headings and Public Sans 400/600 for
  explanations, navigation, controls, and metrics.
- Preserve the document-oriented serif source treatment and sans-serif graph labels.
- Starting type scale: hero `64/68px` desktop and `40/44px` mobile; section headings
  `36/42px`; narrative `18/28px`; supporting interface text `14/20px`.
- Keep prose left aligned, around 55–68 characters wide.
- Use an eight-pixel spacing rhythm and roughly 96–128px between major desktop
  chapters, reducing spacing appropriately on narrow screens.
- Use structural rules only where they separate meaningful content. Avoid
  decorative numbering, uppercase eyebrows, single-word headline accents,
  gradients, oversized rounded cards, and unnecessary shadows.

Spend visual ambition on the single stable source-to-relationship scene. Remove
flying entities, repeated entrance animations, and animated acceptance effects.

## Responsive behavior and accessibility

- Desktop uses one bounded sticky explanatory scene followed by ordinary flow.
- Mobile replaces pinning with short sequential source/relationship explanations
  followed by the real review workspace. Keep graph, Evidence, and source legible
  without requiring a miniature desktop layout.
- Reduced-motion presentation remains complete and attractive without animated
  transitions or completing scroll-driven states.
- Preserve accessible relationship names, selection state, Evidence controls,
  visible keyboard focus, logical heading order, and predictable focus on expansion.
- Color alone must not communicate selection, relationship type, or publication state.
- Do not trap page scrolling in the graph or source. Validate source auto-scrolling
  within sticky layouts and the ability to return from the passage to the selection.
- Ensure static narrative and captions explain the journey even when the interactive
  demonstration is unavailable. Report loading failures honestly and offer the
  existing recovery path rather than silently substituting an image for live UI.

## Frontend ownership and reuse

Keep landing narrative ownership in the showcase feature and shared review
responsibilities in the review feature. Preserve explicit typed data flow; no
global state framework or generic scrollytelling infrastructure is required.

| Existing implementation | Intended reuse |
| --- | --- |
| `features/review/ReviewWorkspace.tsx` | Shared relationship-to-Evidence selection behavior |
| `features/review/GraphView.tsx` | Real graph renderer and relationship controls |
| `features/review/graph-view.ts` | Existing presentation transformation and exact Evidence location |
| `features/review/SourcePanel.tsx` | Authoritative source and exact highlight |
| `features/review/EvidencePanel.tsx` | Evidence choices and active item |
| `features/showcase/useCaseAnalysis.ts` | Explicit sample/live orchestration |
| `features/showcase/AnalysisControls.tsx` | Availability, pending, retry, and error behavior |
| Practitioner intake, Proposal, Matter, and Ledger screens | Actual synthetic captures only on the public page |

Likely new presentation responsibilities are a public narrative shell, a small
guided-scene coordinator, an embedded/expanded review presentation, the evaluation
publication section, and captioned practitioner captures. Extract only meaningful
responsibilities; do not build a second authoritative graph or Evidence model.

Practitioner page components fetch authenticated data and include mutations.
Do not mount them publicly. Captures must come from actual synthetic product
states and omit account information. Authentic capture acquisition is an
implementation preparation task, not permission to fabricate unavailable screens.

## Boundaries and implementation risks

Preserve extraction contracts, relationship semantics, deterministic validation,
canonical identity, provenance, evaluation rules, benchmark ground truth,
authentication, API contracts, and persistence behavior. No schema change is
required by this presentation design.

The primary implementation risks are:

- competing page and source scrolling inside a sticky region;
- graph refitting or layout movement during responsive changes and expansion;
- narrative selection overriding user interaction;
- applying a curated sample sequence to a differing live result;
- making a long introduction delay access to the real demonstration;
- implying that sample output is measured live accuracy or professionally accepted state.

## Acceptance and verification

Implementation is complete when:

1. `/` tells the approved continuous story with the actual graph as its primary visual.
2. Sample loading is explicit, live analysis is secondary, and execution modes and
   failures remain truthful with no automatic model invocation or silent fallback.
3. Guided emphasis preserves the complete graph and stops controlling selection
   after visitor interaction.
4. The real shared review experience retains relationship selection, all Evidence
   choices, and exact source highlighting; inline expansion preserves state.
5. Genuine practitioner captures explain whole-proposal confirmation without
   exposing authenticated actions or inventing unsupported workflow.
6. A substantial methodology and evaluation-in-progress section ships independently
   of later aggregate results, with accessible placeholders and correct metric meanings.
7. A functioning late-stage email action reaches the supplied contact and accurately
   describes its behavior, without collecting client material or implying adoption.
8. Final product routes and the exact synthetic-only limitation are prominent.
9. Mobile, keyboard, reduced-motion, and unavailable-demo states remain understandable
   and usable without completing the guided sequence.

Follow the repository's testing strategy during implementation. Add focused tests
for meaningful guided-selection behavior, interaction handoff, expansion state,
and any deterministic presentation mappings. Retain the real sample-path browser
journey through graph construction and exact highlighting, and cover the new
high-value landing interactions without replacing existing practitioner coverage.
Verify desktop and mobile screenshots, keyboard navigation, reduced motion, source
scrolling, and graph resizing. Run `uv run pytest` and the required frontend checks.
Purely presentational text and wrappers do not need shallow render-only tests.

## Outstanding input

Supply the public project contact email before wiring the interest action.
All visual and product decisions above are approved. Later evaluation publication
criteria and aggregation methodology are separate research work and do not block
the placeholder implementation.
