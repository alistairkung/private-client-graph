# Agent instructions

Read this file before making changes in this repository.

## Required guidance

Always read:

- `docs/CODE_STYLE.md`

Also read, when relevant:

- `docs/WEB_APP_GUIDELINES.md` for API or frontend work;
- `docs/workflows/synthetic-case-authoring.md` for benchmark-case changes.

## Core architecture

Keep these responsibilities separate:

1. probabilistic semantic extraction;
2. deterministic validation and graph construction;
3. deterministic evaluation;
4. application/API orchestration;
5. presentation/UI.

Do not move domain semantics into API handlers or frontend code.

## Protected semantics

Do not change the following without explicit instruction:

- extraction contracts;
- supported relationship semantics;
- deterministic validation rules;
- graph canonicalisation and identity semantics;
- evaluation metrics;
- provenance-scoring rules;
- benchmark ground truth.

If a requested feature appears to require one of these changes, explain why before changing it.

## Durable application guardrails

### Non-synthetic Matter data

Do not add capabilities that accept, store, mutate, or process user-supplied or
non-synthetic Matter information until authentication, Matter authorization,
tenancy/data ownership, and appropriate data-handling requirements have been
explicitly designed. This includes Matter creation, source upload or ingestion,
source editing, non-synthetic Matter data, graph mutation, and persisted
practitioner review-state mutation.

The current unauthenticated practitioner application is permitted only while it
remains read-only and synthetic. This guardrail does not require authentication
for the current slice.

### Database migrations

Represent every database schema change with an explicit Alembic migration and
ship and review it with the feature that requires it; a migration does not need
a separate pull request. Treat merged or applied migrations as immutable. Make
later schema changes in new migrations rather than editing history, and never
bypass Alembic by mutating the production schema directly.

## Engineering principles

- Prefer composition over large functions, modules, pages, or components.
- Keep public/high-level code readable top-down; move mechanics into focused private helpers or components.
- Keep domain models focused and in appropriate files.
- Keep API handlers thin: parse input, call application/domain code, serialize output.
- Keep frontend pages compositional; extract meaningful reusable components.
- Prefer deterministic code whenever behaviour is mechanically checkable.
- Follow existing project patterns before introducing new abstractions.
- Do not add infrastructure for hypothetical future requirements.

## Tests

Every deterministic behavioural change requires tests.

Before completing implementation work, run:

```bash
uv run pytest
```

For web-app work, follow the testing strategy in `docs/WEB_APP_GUIDELINES.md`.

Do not weaken or delete tests merely to make a change pass.

## Git

- Work on a feature branch.
- Never commit directly to `main`.
- Keep changes scoped to the requested task.
- Respect required CI checks.
- Do not merge automatically.

## Agent skills

### Issue tracker

Issues and specs are tracked in GitHub Issues using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repository with a root glossary and system-wide ADRs. See `docs/agents/domain.md`.
