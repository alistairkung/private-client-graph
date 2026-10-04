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
