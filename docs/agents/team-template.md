# <Team display name>

Copy to `docs/agents/teams/<team-id>.md`. This is a documentation contract, not a
Codex runtime configuration. Link native roles and repository files with relative
Markdown links. Keep each required section non-empty; remove all placeholders.

## Purpose and ownership

<Outcome and accountable lead; link the shared standard in ../teams.md.>

## Scope and non-goals

<Work the team accepts, and adjacent work it hands back.>

## Roles

<Lead and specialists: link each .codex/agents/<role-id>.toml; describe capabilities,
not fixed models or effort.>

## Model and reasoning policy

<Apply ../teams.md; lead selects both per task from the active catalogue, records
rationale and observed configuration, and owns cost/escalation decisions.>

## Tools and skills

<Available tool surfaces, required skills with links, and unavailable controls.
Tool access remains governed by the parent runtime.>

## Handoffs

<Concrete input, output and workflow steps. Reference the shared handoff contract.>

## Repository boundaries

<Exact owned paths or directories, shared paths requiring coordination, and
excluded domains. Check overlap with other teams before registering.>

## Delegation limits

<At most two concurrent children, no recursive delegation without explicit user
authorization, and one editor per file. State runtime enforcement limits.>

## Completion and validation

<Acceptance criteria, focused checks, repository-required tests, independent
review trigger, runtime smoke when controls change, final-diff gate and PR.>

## Escalation

<Protected policy, breaking compatibility, unsupported controls, exhausted budget
and exceptional reasoning approval. Routine selection stays autonomous.>
