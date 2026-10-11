# Research Workbench: approved continuous workspace

Status: Comparison bench B approved on 2026-10-11. Connector rail A is selected;
the final inline-settings and always-visible insertion refinement awaits explicit
final approval, as clarified by the user. This handoff includes the whole design
for review and implementation planning, not implementation or execution authority.
See the [complete illustrated design reference](research-workbench-complete-design-reference.md)
for the sidebar, full-page composition, pipeline interaction states, input picker,
responsive layouts, Execution and Evaluation.
The final correction gives the Stop-after-current-attempt button explicit dark
text on a light surface, including hover and a contrasting keyboard focus ring.

This revision supersedes the history-first entry point and detached stage
inspector in earlier visual explorations. Preserve the existing functional and
safety contracts in `research-workbench.md`, `shared-analysis-pipeline.md`,
`research-workbench-visual-design.md`, and the approved issue specifications.
It does not supersede domain semantics or expand execution authority.

## Visual source of truth

Start with the [complete visual reference](research-workbench-complete-design-reference.md);
the isolated analysis and console images below are only parts of the full design.

- [Approved interactive design archive](assets/research-workbench-approved-prototype.zip).
  Extract and serve its directory with a local static HTTP server. It is an
  isolated design prototype, never production frontend code.
- [Comparison and Evidence](assets/research-workbench-approved-analysis.png).
- [Corrected running console](assets/research-workbench-approved-running.png).

The archive defaults to B. Alternative approaches and scenario controls remain
for review context; omit these design-only controls from production. Existing
historical data is embedded for demonstration. No requests execute experiments.
Do not port the mockup's global variables, DOM rewriting, example counters,
synthetic authority values or embedded dataset into the application.

## Workspace and navigation

The pipeline workspace is the primary entry point. Preserve the persistent
sidebar with New experiment, recent experiments, historical search/browse and a
clear selected experiment. History opens frozen configuration and retained
results in the same workspace, read-only. Keep compact benchmark input selection
with all available inputs initially selected and customization in a modal.

One continuous workspace carries Configure → Review frozen plan → Authorize when
required → Execute → Evaluate → Inspect. Maintain experiment identity in the URL;
back/forward navigation and refresh recover authoritative state from the backend.
The browser never owns execution, invents completion or automatically retries.

## Pipeline interaction contract

Use the approved cream/green Connector rail, subtle dot grid, horizontal desktop
flow and compact node summaries. Preserve fixed Extract → Resolve → Build order.
Label graph construction “Build relationship graph”. Distinguish model-driven
from deterministic operations; saved replay bypasses extraction. Required stages
have no removal controls. Evaluation is downstream and outside the Shared
Analysis Pipeline.

Only alias resolution is optional today. The eligible connector has an always
visible outlined +, centered within a fixed 44px target. Hover or keyboard focus
scales its visual circle subtly and fills it dark green with a white plus; no
layout shift. Clicking opens only the supported capability at that position.
Insertion replaces the + with the generative resolver node. Its × maps to no-op,
reconnecting its neighbors. No arbitrary ordering, dragging or generalized stage
registry. Future-stage stress tests are not production capabilities.

Selecting a node expands settings inside that node; only one is expanded at a
time. The connector axis remains at the node header's center. Settings unfold
below it, the selected node widens, and neighboring nodes move horizontally.
Use a bounded scrollable settings area and horizontal canvas viewport with
explicit previous/next controls. Collapse retains values. Settings, focus and
scroll position must survive ordinary rerenders. Respect reduced motion.

Resolver strategies remain no-op and generative full-source. Shared model
settings remain experiment-wide. Resolver repetitions are explicitly an
**experiment measurement** setting, even when edited inside the resolver node;
they must not become a resolver implementation parameter or stage topology.
Bind real settings to existing contracts and validate supported values. Never
infer supported models or numeric bounds from the prototype's illustrative inputs.

## Execution: Comparison bench B

Use a compact dark-green status/control block on the left and frozen workload,
attempt accounting and usage details on the right. Show planned extraction calls,
resolver calls and observations with their different units. The progress bar
represents observation coverage, not provider-call count. Label valid/completed,
failed, uncertain and remaining values precisely according to API semantics.
Do not sum overlapping categories or conflate scored observations with attempts.

| State | Presentation and authorized interaction |
| --- | --- |
| Draft | Server-calculated preview; review/freeze plan; no execution implied. |
| Frozen | Immutable identity/digest and workload; freezing grants no authority. |
| Authorization required | Explicit task allowance, used/uncertain attempts, invocation cap and proposed change; affirmative consent when required by existing contracts. |
| Authorized | Distinct “not started” status; separate Start action and server revalidation. |
| Running | Authoritative status and available progress; Stop after current attempt. |
| Stop requested | Acknowledge request immediately; do not claim stopped until backend confirms. |
| Stopped/interrupted | Retain available results; explicit continuation review, never automatic resume. |
| Failed | Retain failure details and available observations; no fabricated metrics. |
| Complete | Retained execution accounting and available results. |
| Historical import | Frozen configuration and retained results; no execution authority or controls. |

Continuation reuses the existing backend authorization rules; the mockup's
mandatory example consent is not a new universal permission policy. Preserve
idempotency, immutable plans and uncertain-attempt accounting. Do not reset
allowances by navigating, refreshing, retrying or creating a UI view.

Provider disclosure shows recorded token usage, latency with its sample count and
missing count, and estimated cost with pricing/coverage provenance. Distinguish
unknown from zero, unpriced attempts from free calls, estimated spend from an
invoice, and an invocation cap from a monetary guarantee. Current stage appears
only when authoritative telemetry supports it; otherwise say unavailable.

## Evaluation: Comparison bench B

On desktop, keep the baseline/treatment outcome matrix, metrics and repetition
variability on the left; keep the relationship/Evidence inspector on the right.
On narrow screens these become a single ordered reading flow. Scope selectors
identify input/cohort and treatment repetition. All labels and metrics retain
that scope when users switch observations.

The matrix contains matched (TP), extra (FP) and missing (FN) relationships. There
is no defined true-negative universe. Display precision, recall, F1 and provenance
accuracy from evaluator outputs; never reimplement evaluation in JavaScript.
Provenance accuracy is distinct from overall classification accuracy.

Selecting a matrix cell filters individual relationships. Selecting one shows
expected and predicted support, with exact Evidence quotes and a link/action to
highlight their retained occurrences in frozen Source. Missing relationships
have no predicted relationship; do not fabricate support. Keep Source identity,
input cohort and repetition clear throughout inspection. Preserve Unicode offset
semantics and exact quote matching.

Expose repetition variability and baseline deltas without implying an average
or statistical conclusion not supplied by the retained results. Partial and failed
runs expose available observations with explicit coverage. Missing metrics are
unavailable, not zero. Never label partial aggregates as final.

## Real-data acceptance fixture

Use the retained Issue #92 artifact without executing providers:

- 5 extraction calls, 33 resolver calls, 44 scored observations.
- 38 valid attempts, zero recorded provider failures and uncertain attempts.
- Input tokens 70,307; output tokens 3,449; mean provider latency 0.918922 seconds
  across 38 recorded attempts; estimated spend USD 0.004279962 from frozen pricing.
- Authored Case 03 baseline TP6/FP1/FN1; treatment TP7/FP0/FN0.
- Baseline precision/recall/F1 0.857143; treatment 1.0; provenance accuracy 1.0.
- Baseline missing Jonathan Tan spouse_of Rebecca Tan links to exact expected
  Source quotations, including “Rebecca confirmed that she and Jonathan Tan are
  spouses.” Show no predicted relationship for this missing edge.

Other observations must retain their own stored values. These are historical
fixture facts, not promises about new runs or current provider pricing.

## Implementation plan and verification gate

1. Inspect current React routes/components and versioned API contracts against
   this handoff. Record genuine missing fields before implementation; do not
   invent endpoints, database schemas, stage registries or permission models.
2. Compose a shared draft/history workspace and URL selection state. Preserve the
   sidebar, pipeline semantics and compact input picker.
3. Implement accessible node insertion/bypass and inline settings using current
   plan configuration contracts. Keep measurement and provider settings at their
   actual experiment scope.
4. Bind Comparison bench execution states to server authority and lifecycle,
   including loading, unavailable, failure and stop-requested states.
5. Bind comparison, repetition selection and integrated Evidence inspection to
   retained evaluator results and exact Source support.
6. Run the mandatory self-review in `docs/CODE_STYLE.md`; follow the current
   backend/frontend/database/E2E requirements in `docs/WEB_APP_GUIDELINES.md`,
   including `uv run pytest` for implementation work. Add meaningful deterministic
   behavior tests, not tests that merely mirror markup.

Acceptance checks include keyboard/touch insertion; visible focus and contrast;
required-stage immutability; reduced motion; expansion without overlaps;
freeze-without-authorization; explicit start/continuation; backend-owned refresh
recovery; stop acknowledgement; unknown telemetry; partial results; all three
outcome categories; baseline/repetition switching; exact Unicode Source Evidence;
read-only imported history; 390px, 1024px and wide desktop layouts. Use deterministic
fixtures/mocks for lifecycle transitions. Do not make paid calls for design QA.

Implementation must follow repository branch and review conventions, produce a
reviewable PR with the Code Quality Review section, and never merge automatically.
This design handoff itself changes no production behavior or backend contracts.
