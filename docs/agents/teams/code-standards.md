# Code Standards & Agent Governance

## Purpose and ownership

Maintain repository engineering and agent organisation conventions. The
`standards_architect` is accountable for decisions and integration, following the
[shared standard](../teams.md). This is the first registered team.

## Scope and non-goals

Accept standards audits, instruction conflicts, team organisation, delegation
contracts and focused enforcement. Hand product features, benchmark changes,
infrastructure deployment and extraction semantics to their task owners. Do not
change protected policy as an incidental standards cleanup.

## Roles

| Role | Definition | Responsibility |
| --- | --- | --- |
| Lead — Standards Architect | [standards_architect](../../../.codex/agents/standards_architect.toml) | Decide conventions, allocate capability, coordinate and integrate |
| Repository Conventions Auditor | [conventions_auditor](../../../.codex/agents/conventions_auditor.toml) | Produce a factual scoped inventory and instruction audit |
| Agent Systems Architect | [agent_systems_architect](../../../.codex/agents/agent_systems_architect.toml) | Design boundaries, configuration, discovery and handoffs |
| Engineering Standards Reviewer | [engineering_standards_reviewer](../../../.codex/agents/engineering_standards_reviewer.toml) | Independently evaluate consequential changes on demand |

## Model and reasoning policy

The lead applies [orchestrator-owned allocation](../teams.md#orchestrator-owned-capability-allocation)
before each delegation. Select capability and effort from the task, not the role
name. An inventory can use Low; an architectural decision can warrant High even
when performed by the same role. The shared config is a fallback only.

## Tools and skills

Use repository file/search tools, local Codex configuration/catalogue inspection,
`gh`, and deterministic Python validation. No new MCP dependency is required.
Use [domain documentation](../domain.md) and
[issue-tracker guidance](../issue-tracker.md) when applicable. Existing portable
skills remain optional task procedures; [code-review](../../../.agents/skills/code-review/SKILL.md)
is available when a full two-axis review is requested. Its parallel workflow must
fit the shared concurrency limit. Specialist prompts cannot grant tools or
permissions beyond the parent runtime.

## Handoffs

The lead receives a standards objective, base revision and acceptance criteria.
It supplies the [shared input contract](../teams.md#delegation-and-handoffs).

1. Auditor maps the scoped ecosystem once and returns factual references.
2. Systems architect uses those findings to compare a small number of approaches;
   lead selects the simplest compatible option.
3. Lead assigns disjoint implementation ownership and integrates changes.
4. Reviewer independently inspects the complete consequential diff and tests;
   lead resolves actionable findings and performs the final completion gate.

Outputs are the standard/configuration change, audit and migration notes,
validation evidence with requested-versus-observed settings, and a draft PR.
The reviewer does not spawn a second review team.

## Repository boundaries

Own shared agent organisation guidance, the native role format,
`.codex/config.toml` defaults, this team's contract/roles and
`tools/validate_agent_teams.py` with its tests. Each registered team owns its own
contract, adjacent workflow/reference material and role instruction content.
Coordinate shared convention changes here; a team owns its scoped implementation.
Shared engineering rules in root AGENTS and CODE_STYLE require explicit review of policy changes.
Existing portable skills keep their current procedures and entry points; coordinate
before changing them. Pipeline/application/UI/domain semantics are outside scope.

## Delegation limits

At most two concurrent children. Children do not delegate. Assign one editor per
file. Native CLI config caps concurrent children where loaded; the desktop
collaboration surface exposes its own limit and requires the lead to keep the
stricter cap. No-recursion and file ownership are workflow rules, not sandboxes.

## Completion and validation

All required team-contract sections are present, native roles have no fixed model
or effort, and links/registration validate. Run the validator and full pytest suite;
run the runtime smoke when changing agent controls. Independently review any
standards or validator implementation change. Complete CODE_STYLE's final-diff
gate and open a draft PR with validation results and Code Quality Review. Hand
back with pending CI identified; do not merge.

## Escalation

Explain and seek direction for protected policy changes, breaking agent behavior,
or unsupported tooling with no adequate supported fallback. Obtain approval for
reasoning above High and experiments beyond the shared task allowance. Routine
model selection and reversible governance edits stay within the lead's remit.
