# Domain Docs

How engineering skills should consume this repository’s domain documentation.

## Before exploring, read these

- `GLOSSARY.md` at the repository root.
- Relevant ADRs under `docs/adr/`.

If either location is absent, proceed silently. Domain documentation is created lazily when terminology or decisions are resolved.

## File structure

This is a single-context repository:

```text
/
├── GLOSSARY.md
└── docs/
    └── adr/
```

## Use the glossary’s vocabulary

Use domain terms as defined in `GLOSSARY.md` in issue titles, specifications, tests, and implementation discussions. Avoid synonyms that the glossary explicitly rejects.

If a required concept is absent, reconsider whether new language is necessary or note the gap for domain-modeling work.

## Flag ADR conflicts

If proposed work contradicts an existing ADR, surface the conflict explicitly instead of silently overriding the decision.
