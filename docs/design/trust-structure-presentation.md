# Trust-structure relationship presentation

> **Status:** Agreed product design; implementation pending. Professional visual
> conventions are provisional and await practitioner validation.
>
> **Scope:** Presentation in the shared relationship-review workspace. No
> implementation, ontology expansion, or workflow change is authorized by this
> document.

## Purpose

Make the connected relationship view read first as a trust structure, with family
relationships providing visible supporting context. A Trust triangle added to a
generic network is insufficient: the arrangement should help the practitioner
understand explicit Trust roles without changing the underlying Canonical Graph.

The diagram remains one integrated view. Family relationships are neither moved
to a separate view nor hidden by default. They may receive different visual
treatment from Trust roles and need not control the overall arrangement.

## Decision status

| Category | Current position |
| --- | --- |
| Practitioner-validated convention | None established in this exercise. |
| Research-supported hypothesis | Earlier research supplied hypotheses about semantic arrangement, Trust anchors, conventional role positions, and conceptual arrow flow. These are context supplied for the exercise, not independently verified requirements. |
| Product/design decision | Trust structure first; integrated visible family context; one node per canonical entity; every relationship explicit and reviewable; semantic layout for one Trust and generic layout otherwise. |
| Provisional design assumption | Settlors above, beneficiaries below, trustees alongside; flexible placement for multiple-role people; labelled Trust-role connectors without arrows. These choices are not claims of professional convention. |
| Unresolved domain question | What practitioners understand from role position, connectors, and repeated person representations, and whether the integrated arrangement is professionally readable. Validation questions appear below. |

## Presentation rules

### Trust as structural anchor

For a graph with exactly one Trust, arrange role holders relative to that Trust.
An anchor is a reference point for the arrangement, not a requirement that the
Trust occupy the geometric centre or sit below every person.

Use these provisional placement preferences:

- Settlors above the Trust.
- Beneficiaries below the Trust.
- Trustees alongside the Trust, only when an explicit relationship is present.

Placement expresses role grouping. It must not imply asset movement, distributions,
control, ownership, or priority beyond the supplied relationships. Exact sides,
spacing, shapes, colours, and typography belong to the subsequent visual-design
pass.

### Identity and multiple roles

Render exactly one visible node per canonical entity in a populated diagram.
Show every relationship explicitly; do not choose a primary role or merge several
role claims into one selectable relationship.

Someone who is both settlor and beneficiary occupies a flexible position outside
the single-role groups, with separate labelled, independently selectable
connectors. Readability and explicit relationships take priority over preferred
role placement. Their exceptional position adds no domain meaning.

Do not introduce duplicate visual instances speculatively. Revisit this rule
only through a deliberate design decision if practitioner feedback establishes
both a convention of repetition and reliable recognition that the repeated
representations denote the same person.

### Family context

Keep all supplied family relationships visible in the same diagram. Give them
distinct visual treatment without weakening their reviewability.

People without an explicit Trust role sit outside Trust-role groupings, near
their connected family members where practical. Proximity never assigns a role.
A family group disconnected from the Trust occupies a separate area of the same
diagram. Family layout preferences must accommodate the trust-first structure
and the one-node rule.

### Connector meaning

| Canonical relationship | Presentation label | Arrow treatment |
| --- | --- | --- |
| `settlor_of` | Settlor | No arrowhead |
| `beneficiary_of` | Beneficiary | No arrowhead |
| `trustee_of`, when present | Trustee | No arrowhead |
| `parent_of` | Parent of | Parent → child |
| `spouse_of` | Spouse of | Undirected |
| `sibling_of` | Sibling of | Undirected |

Trust-role labels describe the person's role relative to the connected Trust.
Removing arrowheads does not make those canonical relationships symmetric or
reverse their direction. Do not draw conceptual flow arrows that imply facts
the relationship does not establish.

Connector meaning and accessible descriptions must remain unambiguous in both
semantic and generic layouts. The existing legend that arrows point to canonical
targets will need to distinguish directional family connectors from arrowless
Trust roles and symmetric family relationships.

## Layout applicability

| Graph | Layout |
| --- | --- |
| Exactly one Trust | Dedicated semantic trust layout using the preferences above |
| No Trust | Existing generic layout |
| Multiple Trusts | Existing generic layout, including when people have roles in several Trusts |

All layouts retain the same identity, connector, visibility, and Evidence rules.
Do not select an implicit primary Trust, duplicate shared people, or hide
relationships to make a multiple-Trust graph fit a single-Trust template.
Semantic arrangement of multiple Trusts is a recorded presentation limitation,
not an ontology limitation. Existing no-relationships empty-state behaviour is
outside this redesign.

## Transformation boundary

```text
CanonicalGraph
    → professional relationship presentation view model
    → semantic trust layout or generic layout
    → rendering and relationship selection
```

The presentation transformation deterministically derives role groupings,
connector labels, arrow treatment, and layout preferences from supplied entities
and relationships. Keep that transformation testable and separate from rendering;
it does not reinterpret source text or reimplement domain validation.

Every displayed node maps to its exact canonical entity. Every displayed
connector maps to its exact canonical relationship and associated Evidence,
regardless of placement, label, or arrow treatment. The view model is not a
second graph of independently authoritative facts.

Preserve the existing selection interaction: selecting a relationship activates
its first Evidence item, exposes all its Evidence, and highlights the active
exact quote in the source. Selecting another Evidence item moves that highlight.
Preserve keyboard access and selection feedback.

Canonical entity identity, relationship semantics and direction, extraction
contracts and prompts, deterministic validation and canonicalisation, Evidence,
provenance, benchmark ground truth, and evaluation remain unchanged. Matter and
Matter Proposal semantics also remain unchanged; presentation does not alter
whether a graph is proposed or professionally accepted.

This design revises the arrow-presentation requirement in the original
[Case 01 web-slice design](case-01-professional-review-web-slice.md#professional-workflow)
for Trust roles only. It preserves the semantic direction required by that
document and introduces no inverse canonical edges.

## Practitioner-validation questions

The design can proceed provisionally while these questions remain open. Record
answers as practitioner feedback before describing any choice as validated.

1. **Role placement:** For a single-trust diagram showing settlor, trustees and
   beneficiaries, where would you normally place each relative to the Trust?
   Does that placement communicate meaning or simply aid readability?
2. **Connector interpretation:** Are labelled, arrowless Trust-role connections
   clear? If arrows are conventional, what precisely do they mean, and would
   they imply facts beyond a person's role?
3. **Integrated family context:** With Trust roles taking visual priority, are
   family connections readable in the same diagram? What treatment prevents
   family proximity from suggesting a Trust role?
4. **Multiple roles and identity:** Would you show someone holding several roles
   once with several connections, or repeat their name in each role position?
   If repeated, how do readers reliably recognise the same individual? Is our
   single-node, flexible-position approach understandable?
5. **Incomplete represented structure:** Is a diagram with no represented
   trustee relationship understandable as showing only the supplied roles,
   rather than asserting that the Trust has no trustee?

`trustee_of` already exists in the current contracts, although Case 01 does not
exercise it. Do not add a trustee node or relationship to complete an expected
visual pattern. Record feedback about missing represented roles as future
product/ontology evidence, without changing contracts or benchmark fixtures here.
Unsupported future roles, including protector, receive no layout rule in this
design.

## Frontend-design handoff

Develop a professional visual treatment within the agreed presentation model:

- Make the Trust and its explicit roles readable first, while keeping family
  connections visible and distinguishable.
- Make single-role, multiple-role, and family-only placements legible without
  conveying unasserted legal meaning.
- Preserve distinct selectable relationships, accessible descriptions, and
  direct Evidence review, including when endpoints are shared.
- Apply connector conventions consistently in single-Trust and generic layouts.
- Explore concrete supplied-relationship scenarios: Case 01; one person with
  several Trust roles; a family-only relative; a disconnected family group;
  no Trust; and multiple Trusts sharing people. Do not alter benchmark ground
  truth to produce design examples.

Choose exact visual styling in that pass. Do not revisit settled presentation
semantics silently or present the provisional arrangement as practitioner-approved.
Subsequent implementation must test deterministic presentation mappings,
single-Trust eligibility and fallback, identity preservation, separate selection
for multiple roles, and unchanged relationship-to-Evidence behaviour under the
repository's normal testing requirements.

No graph editing, human correction, workflow changes, new extraction behaviour,
timeline/history, multi-document semantics, or new relationship types belong to
this work. The decisions are reversible presentation choices within existing
architecture, so this design adds neither a domain glossary term nor an ADR.
