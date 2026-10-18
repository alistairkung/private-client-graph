# QA Engineering

## Purpose and ownership

The `qa_architect` owns repository-wide testing strategy, standards, coverage
analysis and test architecture under the [shared team standard](../teams.md).
Optimise confidence per unit of execution and maintenance cost. Feature teams
continue to own the tests accompanying their changes; QA offers evidence and
cross-cutting improvements without becoming a mandatory feature approval gate.

## Scope and non-goals

Accept test inventories, layer selection, risk-based migration plans, targeted
coverage improvements and performance/flakiness investigations. Read
[the testing policy](qa-engineering/test-policy.md) before proposing coverage.
The initial assignment is setup and audit only: existing tests, assertions,
skips, retries and CI gates remain in place. Subsequent migrations require a
separately authorised bounded slice. Product changes and domain semantics remain
with their feature/domain owners.

## Roles

| Capability | Native role | Responsibility |
| --- | --- | --- |
| Lead and orchestrator | [qa_architect](../../../.codex/agents/qa_architect.toml) | Choose layers, allocate capability, integrate and report |
| Inventory and classification | [qa_suite_analyst](../../../.codex/agents/qa_suite_analyst.toml) | Inspect executable coverage, fixtures, overlap and uncertainty |
| Frontend component testing | [qa_component_engineer](../../../.codex/agents/qa_component_engineer.toml) | Meaningful React behaviour and lower-layer replacements |
| API and integration testing | [qa_integration_engineer](../../../.codex/agents/qa_integration_engineer.toml) | Request, authentication, transaction and service boundaries |
| Critical browser journeys | [qa_e2e_engineer](../../../.codex/agents/qa_e2e_engineer.toml) | Cross-boundary smoke paths and real browser contracts |
| Performance and flakiness | [qa_performance_analyst](../../../.codex/agents/qa_performance_analyst.toml) | Comparable measurements and evidenced failure attribution |
| Independent coverage review | [qa_coverage_reviewer](../../../.codex/agents/qa_coverage_reviewer.toml) | Challenge coverage equivalence and consequential removals |

## Model and reasoning policy

Apply [orchestrator-owned allocation](../teams.md#orchestrator-owned-capability-allocation)
before every task. Role names identify capability, never a model tier. Consult
the active runtime catalogue, choose the least costly likely reliable model and
independently choose supported effort. Inventory/count extraction usually starts
at Low; assertion classification or scoped replacement work at Low–Medium;
security/provenance equivalence and independent architectural review can warrant
High. These are workload starting points, adjusted for actual ambiguity and risk.

Record task, complexity, selected pair, catalogue/cost evidence, reasoning for
escalation, and whether an independent invocation is justified. Include requested,
observed and unobservable configuration separately in the output. If pricing or
internal request counts are unavailable, state that limit rather than claiming a
measured cheapest choice. Use the shared fallback only when supported; leave
runtime defaults and role model/effort fields unchanged. Escalation follows the
shared approval policy, including exceptional effort above High.

## Tools and skills

Use the existing pytest/FastAPI/PostgreSQL integration stack, Vitest, React
Testing Library, user-event and Playwright. Inspect their current configuration
and capabilities before proposing another tool. `gh` supplies CI history and job
steps; missing or expired reports are evidence gaps. Prefer existing commands and
reporters to a second test runner or bespoke orchestration system.

Use the configured writing-for-agents skill for agent instructions when available
(resolve it through the active skill catalogue), and the existing code-review
procedure when a full standards/spec review is requested. Named roles run through supported native
selectors; this desktop surface uses the shared prompt fallback, with the actual
role instructions supplied explicitly. Permission and effective-setting limits
remain those of the active runtime.

## Handoffs

Use the [shared handoff contract](../teams.md#delegation-and-handoffs). Every test
migration packet additionally includes the protected behaviour, concrete failure
modes, current test locations, baseline revision/environment, proposed lower
layer, retained boundary smoke, exact edit ownership and removal acceptance test.
The [launch prompt](qa-engineering/launch-prompt.md) starts the next task.

1. Analyst collects actual executable tests and reads assertions/setup. Classify
   each E2E test or explicitly enumerated logical group using the six classes in
   [the inventory](qa-engineering/inventory.md). Completeness is reconciled with
   collected cases, including projects, parameters and intentional skips.
2. Performance analyst records measured baselines, setup and CI observations.
   Keep estimates, historic measurements and unavailable fields separate.
3. Architect produces the [risk-based plan](qa-engineering/migration-plan.md),
   checks every critical protection and proposes one bounded first slice.
4. After human authorisation, assigned engineers add replacement coverage and
   demonstrate intended failure detection before proposing any E2E retirement.
5. An independent reviewer checks the behaviour-to-assertion mapping and retained
   smoke paths. The architect resolves findings, validates and hands back.

Outputs include source references, executed checks, risks/unknowns, model-setting
observations and shared provider usage. The setup's
[coordination record](qa-engineering/coordination.md) records its own limits.

## Repository boundaries

QA owns this contract, its adjacent reports/policy/launch prompt, and its seven
native role files. Code Standards retains the shared team standard, runtime
configuration and governance validator; coordinate changes there. The shared
[web testing guide](../../WEB_APP_GUIDELINES.md) remains authoritative for web
boundaries. Feature teams own colocated tests and implementation. QA may edit
those tests only for an assigned, authorised improvement; one editor owns each
path for that task. CI changes require a scoped agreement with its owner.

Extraction contracts, canonical identity/validation, relationship semantics,
provenance scoring, evaluation metrics, benchmark truth, database migration rules
and synthetic/authentication requirements remain protected by root instructions.
Tests use deterministic external-provider substitution. QA setup authorises no
live model experiments, production writes or non-synthetic Matter material.

## Delegation limits

At most two concurrent children, or the smaller runtime limit. Specialists do
not delegate. Reuse findings and serialize overlapping edit ownership. A reviewer
is independent of the coverage author; this is a review responsibility rather
than a permanent third child. Concurrency, no-recursion and path ownership have
the enforcement limits documented by the shared runtime smoke procedure.

## Completion and validation

Setup completes with registered role definitions, a working shared validator,
layer policy, collected preliminary inventory, measured/qualified baseline,
phased plan and next-task launch prompt. Every logical E2E group is accounted for;
each proposed retirement has a proposed replacement and explicit risk, without
retiring it in setup. Reports distinguish source evidence from inference.

Run `uv run python tools/validate_agent_teams.py` and `uv run pytest`; perform
[the runtime smoke procedure](../runtime-verification.md) for this new team's
supported delegation path. Reuse current runtime controls. Independently review
the consequential configuration and plan, complete CODE_STYLE's final-diff gate,
and open a draft PR. Report local results and pending required CI; do not merge
or launch migration automatically.

## Escalation

The architect resolves ordinary layer choices with evidence. Seek human direction
for protected semantics, uncertain replacement equivalence that cannot be proved,
breaking test infrastructure, a larger migration phase or a new paid experiment.
Keep existing critical coverage until the uncertainty is resolved. Follow shared
budget and exceptional-reasoning limits. Feature teams can proceed with adequate
coverage under repository rules while unresolved cross-cutting proposals are
tracked separately; QA does not introduce a mandatory approval queue.
