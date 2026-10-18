# Public Matter access refactor

The user accepted all five interview recommendations on 18 October 2026.
[ADR 0011](../adr/0011-make-synthetic-matter-reads-public.md) records the access
decision; the glossary retains the domain vocabulary.

## Delivery sequence

1. Backend and compatibility PR from updated `main` (`9907029e`): public synthetic
   Matter/proposal reads, protected actions, capability contract, usable read
   readiness, retirement of the simulated demo and obsolete showcase analysis,
   and meaningful replacement coverage.
2. Separate UI consolidation PR after the backend contract passes local
   validation: carry forward the approved Forest & Chalk Matter app and landing
   from drafts #157/#158, consume the same access contract, and retire replaced
   frontend implementation and tests. Preserve the research application and
   canonical fixtures. Coordinate dependent branches without merging them.

The backend work uses `codex/public-matter-reads` in
`/private/tmp/pcg-public-matter-reads`; the landing checkout and user-owned files
remain untouched. No automatic merge, deployment or provider invocation.

## Team and boundaries

- Lead: agreed policy, domain records, integration, final self-review, validation
  evidence and draft-PR delivery.
- Implementer: Sol/medium; one runtime/test writer for the backend and necessary
  current-UI compatibility. Owns focused tests and removal of proven obsolete
  paths. Stops at the assigned phase; no delegation or Git publication.
- Reviewer: Sol/high; independent read-only inspection of the complete diff,
  access-control bypasses, failure paths and retained behavioral coverage.
- Initial inventory: Luna/low, read-only, completed before the interview.

At most two concurrent children, with one runtime writer. Reuse contexts for
adjacent fixes. Shared application-provider allowance: **0/5 used**. Deterministic
tests substitute only existing Google/model boundaries.

## Verification and handoff

Verify anonymous, expired, tampered and removed-allowlist reading; missing auth
configuration; no action side effects before authorization/origin/CSRF checks;
allowlisted actions; capability accuracy; and retired demo redirects. Readiness
must verify PostgreSQL without depending on sign-in availability.

Run required `uv run pytest`, application type checks, affected web unit/build
and real-backend browser checks. Inspect the complete final diff under
CODE_STYLE.md, resolve material findings, and report local results, removed
duplication and current CI in each draft PR. Preserve domain/pipeline semantics,
database contents and immutable migrations. Required CI must pass before merge.

Local validation:

- Required `uv run pytest`: **739 passed**, with disposable PostgreSQL and no
  skipped persistence coverage (111.68s).
- Application/research mypy: **92 source files**, clean.
- Production web units: **121 passed in 28 files**; Research Workbench units:
  **26 passed in 10 files**. Web typecheck, production build and separate
  Research Workbench build passed.
- Complete real-backend desktop/phone browser suite: **68 passed** (16.4s).
- Curated Case 01 JSON matched the pre-refactor response exactly; fixture,
  source/graph identity and public-provider independence have replacement tests.
- Independent complete-diff review: no material correctness, security, scope or
  readability findings. A bounded follow-up confirmed the final seven test/config
  corrections preserve coverage. Root performed the final complete-diff gate.

The first full run exposed an obsolete denied-read assertion, built-static-file
status assumptions for retired routes, and an ambiguous browser navigation
locator. Corrections retained no-provider/no-quota security checks, explicitly
proved retired routes absent from OpenAPI and unable to execute the pipeline,
and selected the intended public navigation link. Both complete suites then
passed. No assertion or test was removed merely to make the suite green.

Historical migration/table definitions and the shared fixed-window helper retain
the dormant showcase namespace; removing historical storage is outside this
no-schema-change refactor. No material readability concern is deliberately
retained in the changed code. Paid application-provider usage remains **0/5**.

The backend draft PR and CI snapshot are reported at handoff; pending checks do
not make the change merge-ready. The UI drafts remain separate and unmerged.

### PR 159 CI follow-up

The first browser job stopped in the Research Workbench unit tests before
Playwright started. The resolver-bypass test waited for the insertion button to
render, then asserted focus before its scheduled animation frame necessarily
ran. Thirty ordinary local repetitions passed; delaying that frame reproduced
the assertion failure. The test now waits for the focus condition and retains
the delayed frame as a regression case, alongside the existing hidden-settings
assertion. Application behavior and CI assertions are preserved. The original
Python and Docker CI jobs passed; the aggregate failure followed the browser job.

Follow-up validation passed: all 739 Python tests; 121 production and 26 research
unit tests; both frontend builds/typechecks; and all four CI browser suites
(68 application, 16 research history, 27 offline execution, 6 substituted-provider
execution). Two existing viewport-specific history skips remain unchanged.
Final follow-up diff review found no material readability or scope issues.
No paid provider calls were made.

## Prepared UI consolidation handoff

Use `web/` as the single production build root: Docker already builds that
package and FastAPI serves `web/dist`. Bring the approved landing and Matter
capabilities from drafts #157/#158 into that source tree, then remove the replaced
production UI and the temporary `practitioner-next/` build/configuration. Keep
the prototype archive separate. Change neither deployment state nor API policy.

- Routes: approved landing at `/`, new Matter application at `/app*`, existing
  research publication at `/research-results`. Legacy `/demo*` keeps the backend
  redirect to `/app`.
- Access: consume `/api/access` once through the shared app boundary; public
  readers can inspect accepted and proposed state, while intake and decisions
  expose sign-in according to the server contract. Mutations retain server
  authorization and CSRF. Preserve readable state after expiry/sign-out and
  clear session-owned drafts appropriately.
- Research: retain `web/research/`, its independent build/configuration, public
  research components and `web/src/shared/research/` modules imported by the local
  Workbench. Inspect imports before removing any old shared file.
- Integration: resolve locale-provider/catalogue and global-style/font ownership
  into one production composition. Include Motion in the production package;
  production builds must not import outside Docker's copied `web/` tree.
- Coverage: port the approved new-app API, intake, review, graph, Evidence and
  landing checks. Adapt policy assertions to public reads. Retain research tests
  and source-attribution/curated-fixture coverage in the appropriate new journeys;
  remove obsolete UI selectors and duplicate tests with the UI they described.

Completion requires one production frontend build, retained research builds,
anonymous and allowlisted real-backend browser journeys, source/Evidence parity,
direct-route refresh, and inspection of the approved visual surfaces. Deliver as
a separate dependent draft PR after the backend contract is locally validated.
