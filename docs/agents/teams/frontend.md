# Frontend Engineering

## Purpose and ownership

The `frontend_architect` leads UI work under the [shared team standard](../teams.md).
Own browser presentation and interaction for the public showcase, Practitioner
Application and research UI. Ask Codex to “use the Frontend team for the task objective”;
the root reads the lead role and assigns only the specialists the task needs.
This contract registers capabilities; it starts no product redesign.

## Scope and non-goals

Accept UI composition, UX, accessibility, responsive layout, client state,
localisation, browser request handling and motion. Follow the
[web guidelines](../../WEB_APP_GUIDELINES.md). Backend-owned contracts supply
relationship, identity and provenance semantics; UI displays them faithfully.
Backend handlers, persistence, extraction and evaluation belong to the
[Backend team](backend.md). New data-handling capability or protected semantic
changes require the repository's explicit design/authorization gates.

## Roles

| Capability | Native role | Responsibility |
| --- | --- | --- |
| Lead and orchestrator | [frontend_architect](../../../.codex/agents/frontend_architect.toml) | Scope, architecture, task allocation, integration and handoff |
| UX and visual design | [frontend_designer](../../../.codex/agents/frontend_designer.toml) | User flows, hierarchy, typography, accessible states and responsive intent |
| Frontend implementation | [frontend_engineer](../../../.codex/agents/frontend_engineer.toml) | React/TypeScript composition, state, API clients and feature-owned tests |
| Motion and interaction | [frontend_motion_designer](../../../.codex/agents/frontend_motion_designer.toml) | Purposeful animation, reduced motion, lifecycle and browser performance |
| Independent review | [frontend_reviewer](../../../.codex/agents/frontend_reviewer.toml) | Design/interaction correctness, accessibility, boundary and regression review |

## Model and reasoning policy

The lead applies [dynamic allocation](../teams.md#orchestrator-owned-capability-allocation)
for every delegation: assess ambiguity, complexity, creative/architectural
judgment and work type; consult the active catalogue; select the least expensive
likely reliable model and independently select supported effort. Record rationale
and requested/observable settings in the shared handoff. Roles have no model or
effort pins. Reuse economical shared defaults only as the supported fallback;
escalation and exceptional-effort approval follow the shared policy.

## Tools and skills

Use existing React, TypeScript, Vitest, Testing Library and Playwright commands.
Browser tools inspect real layout, keyboard/focus, Source highlighting and motion
when those boundaries change. The tracked
[frontend-design skill](../../../.agents/skills/frontend-design/SKILL.md) supports
visual design; consult relevant design/accessibility and Motion skills from the
active catalogue when available. Use their actual instructions and supported tools;
missing optional plugins are reported, not silently made repository dependencies.
No additional runner or MCP configuration is installed by this team definition.

## Handoffs

Use the [shared handoff contract](../teams.md#delegation-and-handoffs), adding user
journey, affected viewports/locales, accessible states, API inputs/errors, synthetic
fixtures and observable acceptance criteria.

1. Lead identifies the affected feature and existing tests once; shares findings.
2. Designer defines the necessary UX states; involve motion only for a relevant
   interaction. The lead names one implementation owner per path.
3. Engineer implements the authorised slice and meaningful behavioural tests.
   For an API gap, return the proposed contract to the root for Backend assignment.
4. An independent reviewer inspects consequential UI/state changes and browser
   evidence. Lead resolves findings and completes repository validation.

Output: changed paths, design/contract decisions, checks and visual evidence where
relevant, known limitations, model observations and shared provider-call usage.
For cross-team work, use the [interface handoff](backend.md#handoffs). The root
coordinates both teams' specialists directly; delegated leads do not spawn teams.

## Repository boundaries

Own this contract and the five linked frontend role files. Implementation scope
is `web/src/` and `web/research/`, their colocated tests, styles and static assets.
The frontend owns browser-client types and request/error presentation; the backend
owns serialized API behavior. Contract changes require one agreed request/response
example and coordinated edits on each side. `web/e2e/` and `web/*-e2e/`, shared
fixtures and tooling get one explicitly assigned task owner; there is no shared
concurrent writer. Confirm a path exists before assigning work.

Code Standards owns shared conventions/defaults/validation. QA, when available,
advises on cross-cutting test strategy; feature teams retain their tests. The QA
team proposed in PR #169 is not a prerequisite for using this team. Independent
review for consequential work is a task responsibility, not a new approval queue.
CI/deployment and unmerged alternative frontends are outside default scope.

## Delegation limits

At most two concurrent children across the whole root task, including Backend or
QA specialists. Children do not delegate. Reuse findings, serialize overlapping
edits, and invoke only needed capabilities. Native/prompt-fallback loading and
permission/configuration visibility follow the shared
[runtime procedure](../runtime-verification.md); role instructions grant no sandbox.

## Completion and validation

Acceptance criteria cover meaningful loading/error/empty/success and interaction
states for the changed journey. Run focused tests and the web guide's applicable
unit/build/browser checks, plus `uv run pytest`. Preserve real browser coverage
where jsdom cannot prove the failure. Inspect the complete diff under CODE_STYLE;
review consequential work independently and hand back a draft PR with Code Quality
Review, local results and pending CI. Setup validation uses the existing team
validator/tests and the [delegation smoke record](../frontend-backend-verification.md).

## Escalation

Return API/domain changes to the root for Backend ownership. Seek direction for
protected semantics, non-synthetic data, breaking API contracts or changes outside
the authorised slice. Report unavailable tools/config controls; use supported
fallbacks. Budget and effort escalation follow the shared standard. No merge,
deployment or next product iteration is authorised by this configuration.
