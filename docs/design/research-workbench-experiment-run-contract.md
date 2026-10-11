# Research Workbench: persistent Experiments and immutable Runs

Status: approved design and required future contract change, 2026-10-12.
The user approved revised direction A, including the connector and copy refinements.
See the [approved handoff](research-workbench-approved-run-workspace.md).
Approval records the intended design; backend and production React implementation
remain separate work.

## Intended model

An **Experiment** is a named persistent research workspace. A **Run** is one
immutable execution of a selected pipeline configuration within that Experiment.
A **Run Draft** is the editable configuration for the next Run. These terms are
recorded in the root glossary.

The performance chart is the history of Runs in the selected Experiment. The
researcher can run without a resolver, add generative resolution, and run again;
both results belong to the same Experiment. A saved extraction or fresh
extraction is an input-mode choice within a Run, not a different meaning of Run.
Repeated execution of an unchanged valid configuration is also permitted by the
intended model: configuration equality does not mean execution identity.

Changing configuration creates or updates only the Run Draft. Selecting an old
point displays that Run's frozen configuration, input identities, code/model
provenance, evaluation and cost beside its results. It never overwrites the draft.
An explicit “Use as next draft” action copies selected settings into the draft;
it does not copy authorization or mutate the selected Run.

## Revised interaction

The pipeline remains the first major element. Its heading reads “Next run” and
contains the primary Run action. An adjacent status explains “Ready”,
“Configuration changed”, or why execution is unavailable. The Run action opens
inline plan review; it does not dispatch work.

Each new Run follows review → freeze → authorize where required → start. A
frozen candidate is locked. Editing it returns to a draft and invalidates its
approval. Paid authority binds the new frozen Run plan and remains constrained
by task-wide accounting; adding a Run or creating an Experiment never resets an
allowance. A saved-extraction, no-resolution replay needs no provider calls and
can skip paid authorization while retaining separate freeze and start actions.

An active Run has explicit monitoring, stop-after-current-attempt and continuation
review. A stopped or interrupted Run continues its original immutable plan;
starting a new Run from a draft is a separate operation. Neither action retries
uncertain attempts automatically. The future backend continues independently
of browser navigation. The prototype only simulates these states.

Once a Run has a scored observation, its aggregate becomes one selectable chart point;
the draft remains available for the next Run. Chart selection drives a separate
frozen-run inspector, TP/FP/FN matrix, relationship selection and exact Evidence
and Source. Completion never means the whole Experiment is closed.

## Required future contract change

Current `workbench/planning.py` freezes a `FiniteExperimentPlan` into an executable
bundle and uses that bundle's identity as the research item. The versioned
execution contracts and supervisor expose start/stop/continue on that plan.
`docs/design/research-workbench.md` explicitly excludes experiment expansion.
These contracts do not represent the intended persistent parent workspace with
independently configured child Runs.

Future implementation must explicitly design and review:

- Separate Experiment identity, name, Run membership and independent Run identity.
- Creation and retention of a new immutable Run plan within an existing
  Experiment, including after previous Runs complete.
- Draft versus frozen Run configuration, input identity, code/model and pricing
  provenance, evaluation outputs and available cost.
- Per-Run lifecycle commands and idempotency, preserving one active execution at
  a time, plan-bound approval and shared task-ledger accounting.
- Versioned history/chart/inspection contracts and a migration strategy for
  existing study bundles. Do not silently relabel all old repetitions as new Runs.
- Durable Experiment metadata and Run associations consistent with ADR 0010's
  artifact authority and rebuildable database index; any database schema change
  requires an explicit Alembic migration.

ADR 0010 currently says “one locally supervised experiment runs at a time”. The
future contract should express this as one active **Run** without changing the
concurrency limit. Its artifact authority, immutable outputs, uncertain-attempt
accounting and explicit continuation requirements remain applicable. Do not
rewrite the accepted ADR as if the future contract were already implemented.

No extraction, relationship, graph identity, evaluation or provenance-scoring
semantics change is required by this UI model.

## Human-readable metadata contract

Required addition, 2026-10-12, before implementation:

- Every newly created Experiment requires a non-blank human-readable name and accepts an optional hypothesis/description. Retain a stable machine-readable Experiment ID separately; display names are not unique identifiers and do not change Run identity.
- Persist the name and optional hypothesis/description in authoritative research artifacts. PostgreSQL only projects them. Rebuilding the index from artifacts must recover these fields without relying on a database backup. Any future edits must preserve historical frozen provenance; editing old immutable manifests is not permitted.
- Benchmark Cases require manually authored human-readable names and descriptions in repository-owned case JSON metadata. Load that metadata through the existing capability/input discovery path; do not infer authored labels from filenames, source text or model output. Keep stable Case IDs separate from display names. Metadata is descriptive and must not change ground truth, evaluation, input matching or Run identity.
- Distinguish the parent Benchmark Case from an individual diagnostic fixture when they exercise different scenarios: retain separate case and fixture IDs and labels, with the scenario description belonging to the correct level. Do not use a fixture's scenario name as the parent case name.
- Freeze the relevant Case name, description, and any selected fixture's scenario metadata alongside the existing input identities in each new Run's experiment provenance. Historical views use this frozen metadata even after repository labels change; the next-run picker uses current repository metadata. Preserve existing semantic input hashes and matching rules rather than conflating a label change with changed ground truth.
- Expose these fields through the existing versioned Research Workbench API, including creation/plan contracts, capabilities, history/detail and comparison/inspection responses where relevant. Keep schemas backend-authoritative and TypeScript consumers checked. PostgreSQL schema changes, if necessary, require a new Alembic migration.
- Support artifacts predating these fields without rewriting their manifests. For example, display `Unnamed experiment · <stable ID>`, `Case <stable ID> · name unavailable`, and `Fixture <stable ID> · name unavailable`. Missing historical descriptions/hypotheses remain unavailable, not invented. Responses must distinguish frozen/authored metadata from a compatibility fallback. Never silently substitute a current repository label for missing historical metadata.

This is a small contract and presentation enhancement. It introduces no case editor, case-management service, user-authored case ingestion, or changes to protected semantics, evaluation metrics or Run identity. The persistent Experiment/Run contract remains a separately required prerequisite; this addition does not implement it.

Acceptance checks must cover required-name validation, optional description, duplicate display names with distinct IDs, artifact-to-index rebuild, repository metadata loading, case-versus-fixture distinction, freezing before repository label changes, historical fallback rendering without manifest writes, versioned API compatibility, and unchanged evaluator outputs and Run identity.

## Comparison and data honesty

The approved [Run aggregate evaluation contract](research-workbench-run-aggregate-evaluation.md)
defines observation-weighted micro-F1, provisional coverage, comparable scope,
exact input matching and incurred provider spend. All available Benchmark Cases
are selected by default. The prototype illustrates one observation per Run;
production must support the specified multi-case aggregation and one point per Run.
Resolver repetitions are not renamed to Runs automatically.

Use discrete selectable points. Never draw a continuous series across unrelated
frozen inputs. Run number is workspace order, not a claim that inputs match.
Show exact input/cohort/configuration identity; distinguish matched saved inputs
from new fresh extractions. Both chart tabs share filters and selected Run.
Unknown F1 or cost is excluded with coverage, never placed at zero. Current-Run
provider cost is distinct from full-pipeline cost: a saved replay can have zero
new provider spend while its original extraction cost is unavailable.

The prototype uses retained Issue #92 evaluator outputs and individual costs as
illustrative outcomes. Its Run grouping, new executions, frozen-plan identities,
authorization and chronology are simulated. Reusing a retained outcome does not
constitute a new measured experiment. The original pilot total remains a source
fact, never a newly accumulated simulated bill. Missing relationships have only
expected Evidence, never fabricated predicted support.

## Design acceptance

- Create/name an Experiment and execute multiple independently configured Runs.
- No-resolver Run → add resolver → review/freeze/authorize/start → new point in
  the same Experiment → inspect either Run → change the draft again.
- Repeat a valid unchanged configuration without overwriting the previous Run.
- Switching historical points leaves the draft byte-for-byte unchanged.
- Frozen and completed Run snapshots do not change when the draft changes.
- Saved and fresh inputs retain distinct comparison identity and cost coverage.
- Keyboard/touch access, readable narrow composition, separate lifecycle actions,
  and exact Evidence remain intact.

## Code Quality Review

Design-only change: repository edits record vocabulary and future requirements;
prototype code is isolated from production. Final-diff review found no production
implementation, authority changes, or claims that the future contract already
exists. No material readability refactors were needed. The interactive mockup was
checked at 1440px and 390px for the multi-run workflow, immutable prior snapshots,
draft preservation, keyboard Evidence inspection, cost exclusions and reload
persistence. Backend tests were not run for documentation-only repository changes.

## Tracking

[Implementation follow-up #115](https://github.com/alistairkung/private-client-graph/issues/115) tracks the metadata contract and collapsible-sidebar refinement, linked from #100, #104, #105 and the Case authoring roadmap #78. Implementation remains separate from this handoff update.
