# PCG Research Workbench

Status: accepted design handoff. The user accepted all five architectural recommendations. Implementation and experiments await separate authorization; no paid provider calls are authorized for design or implementation.

The goal is a local **hypothesis → configure → execute → evaluate → inspect** loop that strengthens experimental contracts as Benchmark Cases become more complex. Architecture is recorded in [ADR 0010](../adr/0010-keep-research-artifacts-authoritative.md); delivery is tracked in [#100](https://github.com/alistairkung/private-client-graph/issues/100).

## User journeys

Run `docker compose up --build` and open a separate local React + TypeScript research application:

1. **Experiment history:** search runs and configurations, inspect complete/incomplete/failed history, and select historical comparisons.
2. **Experiment configuration:** select synthetic cases, saved-extraction replay or fresh extraction, supported pipeline/model configuration, extraction sample count, resolver repetitions and a bounded execution allowance. Inspect the frozen plan and server-computed maximum attempts before explicitly authorizing execution.
3. **Results inspection:** compare baseline/treatment and historical results; drill from aggregate metrics to samples/repetitions, individual missing/extra Relationships and provenance failures, then exact supporting Evidence in frozen Source text. Inspect identity diagnostics where available, failures, usage, costs, latency and execution provenance.

Expected Evidence and predicted Evidence remain distinct; a missing prediction has no predicted Evidence. Preserve unknown costs, unavailable diagnostics and uncertain/unattempted observations rather than displaying zeros. Do not invent a universal case pass/fail threshold or change evaluation semantics.

## Ownership and contracts

Research UI → thin research API → research orchestration/runner → Shared Analysis Pipeline → existing deterministic evaluators. Evaluation stays downstream of the pipeline. Keep provider observation, authorization, accounting and artifacts in research, outside semantic execution and practitioner workflows.

Immutable manifests, frozen inputs, observations and results, plus append-only authorizations and lifecycle records, retain **all non-derivable state**. Task ledgers remain authoritative for paid calls. PostgreSQL stores only rebuildable research projections with artifact identity, digest and index freshness/integrity. Reuse synchronous SQLAlchemy/PostgreSQL and Alembic; every schema change needs a new migration. Retain artifacts and ledgers together across container restarts. Historical imports are read-only and cannot authorize execution; do not rewrite existing absolute ledger paths in frozen manifests. New executable bundles use stable container storage paths.

The workbench is a consumer-driven test of domain contracts. Expose existing concepts through explicit versioned API contracts, initially `/api/research/v1`, with backend-authoritative schemas and checked TypeScript consumers. Preserve supported historical artifact versions and reject unsupported ones explicitly. A concrete case or capability can justify a missing contract; evolve it deliberately at its owning layer with compatibility decisions and regression tests, rather than UI workarounds or speculative generality.

| Contract | Required content |
| --- | --- |
| Capabilities | Synthetic cases and saved extraction identities/hashes; finite supported PipelineConfig and provider/model settings |
| History/detail | Experiment identity, frozen configuration, artifact/API versions, provenance, lifecycle, integrity and existing domain results |
| Comparison | Matched inputs/truth, configuration/code differences, existing metric summaries and deltas, coverage and unmatched/incompatible observations |
| Plan/preview | Frozen input identities, extraction samples, resolver repetitions, extraction/resolution call maxima, task usage/remaining allowance and invocation cap |
| Authorization/commands | Plan digest, task identity/cap, approved bounded allowance and approval provenance; idempotent start, explicit continuation and stop-after-current-attempt |

React displays server-owned metrics and budgets; it does not evaluate, aggregate experimental costs or account for attempts. Research-specific operational contracts must not change protected extraction, graph, identity, provenance, evaluation or ground-truth semantics.

## Execution and experimental controls

- Reuse the Shared Analysis Pipeline from #97 and existing research runner. Deliberately evolve its study-specific plan constraints into a versioned finite contract while preserving old manifests and budgets. Initially expose the supported `none` and `generative` resolver capabilities; no second evaluation engine or arbitrary pipeline topology.
- Hold each extraction fixed across baseline/treatment and resolver repetitions. Track fresh extraction samples separately from resolver repetitions and preserve authored/historical/fresh cohorts. Historical comparisons disclose changed code/configuration and unmatched inputs.
- Saved replay with generative resolution can still cost calls. Distinguish input mode from provider execution mode. Recorded-provider demonstrations are explicitly labelled and are not live quality measurements.
- Preview extraction calls plus generative-resolution calls server-side, separating the matrix maximum, invocation allowance and task-wide remaining budget. Pricing estimates retain model/date provenance and unknowns; a call bound is not a guaranteed dollar bound.
- One active experiment runs under the local research service's supervision. Browser closure does not terminate it. Stop prevents further dispatch after the current attempt. Restart reconciles artifacts and requires explicit continuation. No queue, distributed workers, automatic resumption, retries or experiment expansion.
- Approval binds the frozen plan digest, task-wide budget and bounded invocation allowance; plan changes invalidate it. Persist approval and every other non-derivable authorization fact in artifacts. Duplicate requests cannot dispatch twice; creating or importing another experiment never resets task spending authority.
- Preserve existing durable reservation-before-dispatch, atomic publication/fsync, bundle/task locking, uncertain-attempt counting, missing-ledger rejection and code/dependency resume checks. Uncertain attempts are never resubmitted. PostgreSQL is not paid-accounting authority.
- Publish only to loopback and protect state-changing requests with appropriate Host/Origin checks. Credentials stay server-side. Live execution requires explicit local enablement and experiment approval.

## Frontend separation and design gate

Use a separate React + TypeScript research application and research backend entry point, reusing PCG tooling, design conventions and appropriate components. Organize cohesive history, configuration and results features; do not build a generic component library prematurely. Research routes and execution controls do not enter the deployed practitioner application.

Read-only history/results and execution controls must be separable in both frontend and backend composition. Read-only composition mounts no execution endpoints, initializes no runner and requires no provider credentials. A future public Research Lab deployment and its publication/security policy are outside this scope.

The user will separately invoke Impeccable against the [frontend design brief #104](https://github.com/alistairkung/private-client-graph/issues/104), with approval tracked in [#105](https://github.com/alistairkung/private-client-graph/issues/105). **All React implementation waits for the approved visual/interaction design and implementation authorization**, then follows that design. Backend work can be authorized independently. This handoff specifies no detailed layouts, styling, component designs or design system, and creates no mockups.

## Three implementation slices

Each ticket includes its backend and React increment, is separately authorizable, and is independently demonstrable and tested once its stated predecessors and frontend design gate are satisfied. Backend acceptance can be verified before visual design approval; a full slice is not complete until its React journey is demonstrated.

1. [#101 — Read-only workbench, PostgreSQL indexing and historical results](https://github.com/alistairkung/private-client-graph/issues/101): Compose, persistent artifact mounts, rebuildable index, versioned read APIs and separate history/results frontend. Demonstrate search → comparison → individual relationship error → exact Evidence. Test PostgreSQL migration/index rebuild, legacy/incomplete/corrupt artifacts, restart persistence and absence of execution capabilities.
2. [#102 — Deterministic configuration and execution](https://github.com/alistairkung/private-client-graph/issues/102): depends on #101. Add finite versioned plans, budget preview, supervised lifecycle and React configuration/controls. Demonstrate saved no-resolution replay and labelled recorded-provider execution through the real pipeline/evaluator into durable inspectable results. Test compatibility, plan freezing, pairing, maximum calls, duplicate/concurrent starts, stop and restart/continuation.
3. [#103 — Explicitly authorized bounded live execution](https://github.com/alistairkung/private-client-graph/issues/103): depends on #102. Add artifact-backed plan-bound approval, task-wide budget enforcement and corresponding React approval/lifecycle controls. Test with substituted providers: stale approvals, cross-bundle caps, copied artifacts, missing ledgers, crash boundaries, uncertain attempts and explicit continuation. A real paid experiment remains a separately authorized task, not a completion requirement.

Test the full contract chain: plan → runner → pipeline → evaluator → artifacts → API → UI. Substitute only stochastic provider boundaries while retaining real graphs and Evidence. Each implementation slice requires relevant backend, PostgreSQL, TypeScript/build/frontend/E2E tests, `uv run pytest`, and the mandatory complete-diff self-review from `docs/CODE_STYLE.md`; PRs include Code Quality Review. No live provider calls are required or authorized for these checks.

Excluded: non-synthetic data, practitioner workflow changes, protected semantic changes, public deployment, paid-accounting migration into PostgreSQL, LangSmith, arbitrary stage registries, drag-and-drop pipelines, speculative plugins and distributed execution.
