# Agent teams

Read this standard when creating or changing a team, or orchestrating delegated
work. Start with [AGENTS.md](../../AGENTS.md) and [CODE_STYLE.md](../CODE_STYLE.md);
they remain authoritative. Team instructions refine workflow within those rules.
Task instructions supply the current objective, base revision and acceptance
criteria; they do not implicitly authorize changes to protected semantics.

## Discover and invoke

A **team** is a named workflow with an accountable lead, explicit scope, ownership,
and completion contract. A **specialist** supplies one capability within that
workflow; it is not a separate team or a fixed intelligence tier.

| Team | Contract and workflow | Accountable lead |
| --- | --- | --- |
| Code Standards & Agent Governance | [code-standards](teams/code-standards.md) | `standards_architect` |
| Frontend Engineering | [frontend](teams/frontend.md) | `frontend_architect` |
| Backend Engineering | [backend](teams/backend.md) | `backend_architect` |
| QA Engineering | [qa-engineering](teams/qa-engineering.md) | `qa_architect` |

Read the matching contract, then its linked role definitions. If no team fits,
work directly or propose a narrowly scoped team; do not create one per task.
A request to use a team authorizes its bounded specialist workflow. Merely seeing
this index does not request delegation.

To invoke: ask Codex to “use the Code Standards team for <objective>”. The root
agent acts as lead and reads its role instructions. When the runtime supports
named roles, select the native role. Otherwise, read the role TOML and include its
`developer_instructions` verbatim in the specialist's task prompt. This latter
path works with this desktop session's `collaboration.spawn_agent`, which has no
named-role parameter. A filename alone does not load a role on that surface.

## File placement and inheritance

| Layer | Location | Responsibility |
| --- | --- | --- |
| Shared engineering instructions | root `AGENTS.md`, `docs/CODE_STYLE.md`, linked domain/workflow docs | Repository rules, referenced rather than copied |
| Team orchestration | `docs/agents/teams/<team-id>.md` | Purpose, ownership, workflow and handoffs |
| Codex configuration | `.codex/config.toml`, `.codex/agents/<role-id>.toml` | Supported runtime defaults and specialist capabilities |
| Reusable portable skills | `.agents/skills/<skill-name>/SKILL.md` | Existing reusable procedures; skill UI metadata stays in `agents/openai.yaml` |
| Team-specific prompts and references | team contract first; adjacent `<team-id>/` folder only when needed | Disclosed material linked by its consuming workflow |
| Task instructions | delegation prompt or issue | Current assignment and temporary ownership |

Use kebab-case team IDs and snake_case role IDs; role filename matches `name`.
Role IDs are repository-wide unique. Team contracts link roles explicitly; skills
remain discoverable by their own descriptions. A team-owned reusable skill still
lives in `.agents/skills/`, prefixed with the team ID only when needed to avoid a
name collision. Its owning team links it. Do not copy a skill into team folders.
`agents/openai.yaml` describes skill UI/invocation; it is not a specialist config.

## Orchestrator-owned capability allocation

Before **every** delegation, the orchestrator records a short decision:

1. Classify complexity, ambiguity, required reasoning depth, creative judgment
   and architectural judgment; identify mechanical, exploratory, implementation
   or evaluative work.
2. Consult the active tool's model catalogue and supported effort values. On the
   verified CLI, `codex debug models` refreshes the catalogue; `--bundled` is an
   offline fallback and does not establish account access. Tool schemas can
   expose a different catalogue. Use that surface's supported identifiers.
3. Choose the least expensive available model likely to finish reliably, then
   independently choose reasoning effort. Use current catalogue descriptions and
   official pricing where available; record uncertain relative cost rather than
   invent prices. A stronger model at Low can be more economical than repeated
   attempts with a weaker model at High.
4. State whether independent review merits another invocation. Pass explicit
   model and reasoning settings at spawn time wherever supported. Role files
   must omit fixed `model` and `model_reasoning_effort` values: in the documented
   native runtime they can override the orchestrator's request.
5. Verify effective configuration from runtime metadata where available. Record
   requested, observed and unobservable fields separately. An accepted request,
   a role's self-report or parent configuration alone does not prove the child's
   effective settings.

| Task category | Starting effort, adjusted for actual task |
| --- | --- |
| Inventory, discovery, simple checks | Low |
| Straightforward implementation, docs, focused tests | Low–Medium |
| Complex implementation, UX, motion, investigation | Medium |
| Architectural decisions, difficult debugging, independent critical review | High |
| Exceptional deeper reasoning | Extra High (`xhigh`) only with explicit justification and human approval |

Treat `max`, `ultra` and any level above High as exceptional too. Routine model
selection within the established budget needs no additional approval. Higher
capability and higher effort are separate choices; roles have no permanent model
or effort assignment. Validate the selected model/effort pair against the current
catalogue, not a checked-in model-name list.

The project config provides one economical **fallback** for omitted spawn settings,
independent of specialist role. Confirm its pair is available on the active
runtime before relying on it. Explicit task choices override these defaults.
If the runtime lacks model/effort overrides, report that limit and use its
supported default or inherited settings for a small bounded task; otherwise keep
work on the lead or use an explicitly selected `codex exec --model ... -c
model_reasoning_effort=...` session. A new CLI session is a separate session, not a
native child. Do not emulate overrides through invented config keys, mutate role
files per task, or silently retry at a different cost.

## Delegation and handoffs

Delegate when a bounded, non-overlapping task benefits from specialist expertise
or independent review after accounting for context and cost. Reuse the lead's
inventory and prior findings. The lead owns integration and decisions; children
return evidence and recommendations within their assignment.

Every input handoff states: objective and acceptance criteria; selected role and
its instructions; worktree/base; relevant prior findings and file pointers;
read-only or exact files owned for editing; chosen model/effort and rationale;
remaining task budget; expected output and stopping condition; and “do not
delegate”. A concise output returns findings or changes with paths, checks and
results, unresolved risks, configuration observations, and provider-call usage.
Never include credentials or unrelated client information in a handoff.

At most **two concurrent subagents per orchestrator**, or the runtime's smaller
limit. Reuse or close completed agents where supported. No recursive delegation
unless the user explicitly authorizes it; a specialist asked to lead another
team returns a proposed handoff to the root. Distinct teams collaborate through
root-assigned, disjoint ownership. For overlapping proposed edits, serialize work
and agree on one owner before dispatch. Ownership declares review responsibility,
not permission to bypass repository guardrails.

If an agent fails, inspect why before retrying: narrow the assignment, supply
missing context or change capability once justified. Do not repeat ineffective
agents at identical settings. Focus costly independent review on consequential
diffs. Apply the existing [provider-call allowance](../../AGENTS.md) across the
whole task, not separately per agent or retry. Keep a shared task ledger before
paid experiments; coordination usage and any unobservable billing are reported
separately, never represented as measured provider-call counts.

## Add, validate and evolve a team

1. Copy [the team contract](team-template.md) into `teams/<team-id>.md`; replace
   every placeholder. Assign one accountable lead and explicit ownership.
2. Add native role TOMLs using the supported three fields in the existing roles.
   Describe capability and boundaries, link shared rules, and leave model/effort
   selection with the orchestrator. Register every role in a team contract.
3. Add the team to the index above. Reuse existing skills; new skills require
   their own invocation description and supporting validation.
4. Run `uv run python tools/validate_agent_teams.py` and `uv run pytest`. The
   existing Python CI job runs the deterministic governance tests. Also perform
   the [runtime smoke procedure](runtime-verification.md) when controls change.
5. Inspect the complete diff, then obtain the consequential independent review
   required by the contract. Ship through a draft PR with Code Quality Review.

The validator enforces contract sections, unique/registered roles, local links,
non-empty role fields, the shared agents-table keys and economical fallback
policy. It flags identical role instructions. An optional runtime catalogue checks
model/effort compatibility without a live inference. Semantic ownership overlap,
duplicate meanings in skills, stale findings, account access, and runtime config
precedence require review; static checks do not prove them. Other runtime settings
(such as MCP servers) remain outside this narrow validator and require Codex
strict parsing when changed. CI must stay offline.

Keep existing skill entry points intact. Change a team and its references in one
PR; mark replacements before deleting obsolete roles, and check other teams for
reuse. Review orphan/duplicate-role validation and the [audit](ecosystem-audit.md)
when updating integrations. Major migrations need separate review when they
could disrupt existing workflows.
