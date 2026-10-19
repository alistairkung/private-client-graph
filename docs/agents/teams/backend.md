# Backend Engineering

## Purpose and ownership

The `backend_architect` leads Python service and domain implementation under the
[shared team standard](../teams.md). Ask Codex to “use the Backend team for
the task objective”; the root reads the lead role and assigns the capabilities needed.
This contract registers a reusable team; it changes no service behavior.

## Scope and non-goals

Accept API/application orchestration, authentication/admission, persistence,
explicit migrations and authorised pipeline/domain maintenance. Preserve the five
responsibilities in root AGENTS and the [web guidelines](../../WEB_APP_GUIDELINES.md).
Extraction interprets semantics; deterministic code validates/builds/evaluates;
application code orchestrates; UI presents. The team owns implementation within
approved scope, not authority to redefine protected semantics or benchmark truth.
Browser UX belongs to the [Frontend team](frontend.md). Provider experiments,
infrastructure deployment and non-synthetic Matter capability require separate scope.

## Roles

| Capability | Native role | Responsibility |
| --- | --- | --- |
| Lead and orchestrator | [backend_architect](../../../.codex/agents/backend_architect.toml) | Boundaries, contract decisions, task allocation, integration and handoff |
| API and application | [backend_application_engineer](../../../.codex/agents/backend_application_engineer.toml) | Thin HTTP handlers, application workflows, admission and public contracts |
| Persistence and migrations | [backend_persistence_engineer](../../../.codex/agents/backend_persistence_engineer.toml) | PostgreSQL integrity, transactions and explicit immutable Alembic history |
| Pipeline and domain | [backend_pipeline_engineer](../../../.codex/agents/backend_pipeline_engineer.toml) | Fixed shared pipeline and scoped domain maintenance within protected contracts |
| Independent review | [backend_reviewer](../../../.codex/agents/backend_reviewer.toml) | Contract/security, deterministic semantics, persistence and failure review |

## Model and reasoning policy

The lead applies [dynamic allocation](../teams.md#orchestrator-owned-capability-allocation)
before every delegation. Assess task ambiguity, depth, architectural/creative
judgment and work type; consult the active catalogue, select the least costly
likely reliable model and choose supported effort separately. Record the decision,
review justification and requested-versus-observed settings. Simple discovery and
complex transaction reasoning can warrant different choices for the same role.
No role pins model or effort; use shared fallback and escalation rules unchanged.

## Tools and skills

Use existing Python/uv, pytest, FastAPI clients, PostgreSQL, Alembic and mypy
commands. Substitute external stochastic/provider boundaries in deterministic
tests; keep relevant domain validation and database constraints real. Read
[domain docs](../domain.md), the root glossary and relevant ADRs before domain
work. Use existing diagnostic, domain-modeling or TDD skills from the active
catalogue when applicable, following their workflows within the assigned scope.
No additional provider, service framework or MCP dependency is required.

## Handoffs

Use the [shared handoff contract](../teams.md#delegation-and-handoffs). Add concrete
request/response/error examples, action eligibility, exact Source/Evidence identity,
transaction boundaries, compatibility expectations and synthetic fixtures.

1. Lead traces the current public workflow and relevant tests once. Identify any
   protected-policy decision before assigning implementation.
2. Root agrees the HTTP contract with Frontend when both layers change: payload,
   error/status behavior, identity/provenance fields, auth/CSRF/origin assumptions
   and backward compatibility. Each side owns its paths; assign a cross-boundary
   acceptance test to one owner. Neither side invents semantics to unblock itself.
3. Lead assigns application, persistence or pipeline mechanics as needed with
   disjoint ownership; implement deterministic regression coverage with the change.
4. Reviewer independently checks consequential contract, security and persistence
   changes. Lead resolves findings, validates and hands back at the scoped boundary.

Output: implemented contract and paths, tests/results, migration/application risks,
unresolved decisions, model observations and shared provider-call usage. A request
for another team's work returns to the root; children do not recursively delegate.

## Repository boundaries

Own this contract and five linked backend role files. Implementation scope covers
`private_client_graph/` and matching `tests/`; `migrations/` and `alembic.ini` apply
only when a schema change is explicitly in scope. Application/API, persistence,
extraction/pipeline and evaluation remain separate code responsibilities. All
schema changes ship new migrations with the feature; merged/applied history stays
immutable and production schema is never changed directly.

Frontend owns `web/` presentation/client code; browser E2E/server fixtures and
public payload examples require one task-assigned owner. Code Standards owns
shared governance/defaults/validation. QA, when available, supports strategy and
coverage assessment while feature teams own their tests; PR #169 is not a runtime
dependency. CI/deployment, credentials, benchmark ground truth and unmerged
experiments are outside default scope. Protected contract or semantic changes
need explicit instruction even when their files fall within backend paths.

## Delegation limits

At most two concurrent children across the whole root task, including Frontend
or QA specialists. Children do not delegate. Share discovery, keep one editor per
file and serialize intersecting work. Effective permissions and supported
configuration controls follow the shared [runtime procedure](../runtime-verification.md).
The root owns integration, concurrency, escalation and the shared task budget.

## Completion and validation

Every deterministic behavior change has meaningful regression coverage. Run
focused tests, `uv run pytest` and applicable existing type checks. Persistence
work requires the relevant PostgreSQL integration/migration checks; skipped tests
are reported as an evidence gap. For API changes run the web guide's applicable
contract/journey checks. Keep live provider checks separate and budgeted.
Independently review consequential work and complete CODE_STYLE's final-diff gate.
Hand back a draft PR with Code Quality Review, local results and pending CI.
Team setup uses the shared validator/tests and
[delegation smoke record](../frontend-backend-verification.md).

## Escalation

Explain protected semantics or breaking contract changes before implementation.
Seek direction for non-synthetic data, tenancy/authorization redesign, production
operations or work outside the authorised slice. Use supported configuration
fallbacks and shared budget/exceptional-effort approvals. This team grants no
blanket authority to run provider experiments, merge, deploy or start the next
build/evaluate/rebuild iteration.
