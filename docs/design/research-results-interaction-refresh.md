# Research results: Forest & Chalk interaction refresh

## Scope and direction

The public `/research-results` page is a **Read** surface with interactive
inspection. It answers what changed when the same frozen extractions were
processed with and without generative entity resolution, then lets the reader
inspect the retained graphs, relationships and exact Evidence.

This continues `codex/refresh-research-results` from `01acde3e`, preserving the
initial uncommitted redesign. It brings the publication into the landing and
Matter application's Forest & Chalk language: Public Sans, forest `#173F31`,
action `#1E6249`, ink `#20372B`, pale green framing and white reading surfaces.
The opening leads with the single alias mapping applied to two endpoints, places
the micro-F1 comparison beside its caveat, and links directly to Case 03.
The overview also distinguishes baseline extraction in the practitioner
application from the resolver comparison in this research.

The full 0–1 chart scale, numeric Run ordering, native selectors and disclosures,
artifact download, bilingual UI and public read-only access remain. Publication
labels A / A′ / B and their descriptions appear directly on chart controls and
inspection titles, supplied by the public adapter. The shared chart retains its
existing numbered labels for Workbench consumers.

## Premium source inspection and decisions

On 2026-10-18, both `search-motion-docs` on `Motion` and
`search-motion-source` on `MotionPlus` succeeded. Full authenticated source was
read for [Smooth Tabs](https://examples.motion.dev/react/smooth-tabs)
(`motion://examples/react/smooth-tabs`) and
[Segmented toggle](https://motion.dev/ui/components/segmented-toggle)
(`motion://ui/react/segmented-toggle`, including its theme dependency).
No configuration changes, reinstallation or credentials were needed. These are
source-informed decisions, not a MotionScore certification; no runtime
MotionScore audit was performed. No premium source files or runtime dependency
are added to the repository.

| Opportunity | Decision | Reason and behavior |
| --- | --- | --- |
| Architecture and recorded-graph Run controls | Refine | One instance-scoped selection surface follows a physical spring, stiffness 1218 / damping 70 / mass 1, informed by the premium snap. The .985 press scale remains subtle enough for long labels. State changes immediately and rapid reversals retarget the spring. |
| Chart mode tabs | Refine | Use the same selection spring, while axes and recorded contents update immediately. Preserve tab semantics, keyboard selection and visible focus. |
| Selected chart observation | Reject travelling ring | A ring moving between discrete observations can suggest a trajectory. The selected point gets a local opacity response; point coordinates and metrics never interpolate. |
| Run cards | Retain stable content | Labels identify the public conditions directly. Selection changes styling without moving the numbers or scaling the cards. |
| Graph and Source | Retain continuity | Keep unchanged relationship selection across Runs. Preserve an open Source only for an identical retained outcome; clear stale inspection when the relationship or outcome changes. |
| Metric and usage disclosures | Retain native behavior | Long tables expand immediately. Height choreography would move the reading target and delay access. |
| Native selects | Retain | Their keyboard and platform behavior is useful; an animated custom menu adds no demonstrated benefit. |

Smooth Tabs' 50px directional content travel, blur and sequential exit are
rejected for research contents: they delay comparison and obscure exact values.
Segmented toggle's .96 press and 1.08 stretch are also rejected because the long
research labels should remain stable. The selected shared-layout technique uses
the already installed `motion/react`; importing the complete Motion UI theme and
Base UI layer is not warranted for this bounded page.

Reduced motion disables travelling indicators and press transforms. Selection,
focus, Source access and chart contents remain immediate. Keyboard activation
uses native buttons and tab semantics. Primary controls retain 44px targets.
Phone Run cards stack so all three conditions remain discoverable. Wide tables
stay inside labelled, focusable scroll regions with translated instructions.

## Research accuracy and boundaries

The unchanged authoritative input is
`private_client_graph/published/research-results.v1.json`. The latest supplied
folio, `/Users/alistair/projects/FTEC/private-client-graph.pdf`, was reviewed as
evidence. The academic reviewer confirmed:

- 10 project-authored held-out synthetic cases, 14 Sources and 39 expected
  relationships; A/A′ micro-F1 94.87%, B 100%.
- One Bea → Beatrice Ng alias mapping corrects two Case 03 endpoints and accounts
  for the entire gain. A′ is an exact replay control, not independent replication.
- B's approved-quote check is 36/39; its Source/quote-pair check is 37/41. They
  assess different populations, not interchangeable confidence measures.
- The comparison is small, post-hoc and exploratory, without repeated trials or
  uncertainty estimates. It establishes no production reliability.
- B's usage counts resolver attempts only; reused extractions are lineage. A′
  has zero provider calls. Missing costs remain Unpriced.

The overview now explicitly compares the same frozen extractions with and
without resolution. Legacy summary wording avoids implying independent external
validation. Backend contracts, domain semantics, evaluation rules, ground truth,
publication bytes and synthetic-data boundaries are unchanged.

## Verification and team ledger

The existing evidence and logs were retained. Earlier validation supplied with
the handoff: 739 Python tests, 170 frontend and 26 Workbench unit tests, both
builds, 88 application and 16 Workbench browser checks, followed by 22 focused
research browser checks. These are earlier results, not a claim about the final
resumed diff.

The resumed pass uses the role definitions read with `git show` from
`origin/codex/practitioner-agent-team`, adapting their former practitioner-only
scope to this route. The tool exposes generic delegation, so model and effort
were supplied explicitly: explorer and visual QA on Luna/low; UX, motion,
implementer and academic reviewer on Sol/medium; engineering on Sol/high. The
lead owns integration, documentation, validation and the draft PR. At most two
children are active, with one delegated code writer and no child delegation.
The resumed run made seven initial specialist assignments, then three bounded
follow-ups: the implementer fixed the discovered narrow-layout defect, the
engineering reviewer checked that delta, and visual QA confirmed the current
phone/table captures. There were no model escalations.

The resumed design investigation used one Motion concept search, one premium
source search and two distinct premium resources, read five times across the
lead and motion reviewer. No model escalation or paid application-provider call
was used. Shared paid application-provider usage remains **0/5** across the
entire task. Browser review is bounded to one inspection batch and one
confirmation batch after any fixes, in addition to deterministic regression tests.

The Impeccable context command interpreted `/research-results` as a filesystem
root; the existing PRODUCT.md, DESIGN.md, code and screenshots were therefore
read directly. No unrelated context repair was attempted. An attempt to obtain
the previous disposable database's connection credentials was rejected by
automatic approval review; a fresh disposable local test database with explicit
test-only credentials was created instead.

Final validation and selected before/after evidence are recorded in the
[evidence index](../artifacts/research-refresh/README.md). The draft PR records
the complete-diff Code Quality Review and CI state. This task does not merge or
deploy the redesign.
