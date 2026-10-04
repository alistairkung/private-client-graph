# Web application guidelines

Read this guide before adding or changing the API or frontend.

The goal is a clean, compositional web layer over the existing tested Python core. The web application should expose the pipeline, not reimplement it.

## Architecture boundary

Prefer this dependency direction:

```text
frontend
   ↓
API / application orchestration
   ↓
existing domain pipeline
   ├── extraction
   ├── graph construction
   └── evaluation
```

The frontend should not decide relationship semantics, provenance rules, graph canonicalisation, or evaluation behaviour.

API code should call the existing domain functions rather than duplicate their logic.

Changes to core semantics require explicit review under `AGENTS.md`.

## Repository structure

Keep backend and frontend in the same repository unless a concrete deployment or ownership need justifies a split.

Prefer clear package boundaries over unnecessary repositories.

A reasonable direction is:

```text
private_client_graph/
  models/
  application/
  api/
  ...

web/
  components/
  hooks/
  lib/
  types/
  ...
```

Treat this as guidance rather than a requirement to create directories before they are needed.

## Backend style

- Keep meaningful domain models in focused files.
- Keep domain models independent from HTTP or UI concerns.
- Keep routes/controllers thin.
- Put multi-step use-case orchestration in an application layer when route code would otherwise become procedural domain logic.
- Reuse existing extraction, graph-construction, and evaluation functions.
- Do not introduce repository patterns, service hierarchies, dependency injection, or persistence abstractions until a concrete requirement earns them.

A route should read approximately as:

```python
request -> application/domain call -> response
```

not as a second implementation of the pipeline.

## Frontend composition

Pages should primarily compose meaningful UI concepts.

Prefer a shape such as:

```text
CasePage
├── SourcePanel
├── GraphView
├── EvidencePanel
└── EvaluationSummary
```

over one page containing data fetching, graph transformation, selection state, evidence rendering, metrics formatting, and large amounts of JSX.

Extract a component when it represents a meaningful UI responsibility or is genuinely reusable.

Do not split trivial markup into tiny generic components merely to reduce file length.

Keep graph rendering, evidence display, and evaluation display as separate concerns.

## State and data flow

- Prefer explicit props and typed data over hidden global state.
- Keep API/data-fetching concerns separate from presentational components where practical.
- Keep deterministic transformations in small testable functions rather than embedding them in JSX.
- Add shared state only when multiple parts of the application genuinely need it.
- Do not introduce Redux, complex state machines, or other state infrastructure before the UI earns that complexity.

## Testing strategy

The goal is high-value behavioural coverage, not a unit test for every React component.

### Usually do not unit test

Purely presentational components generally do not require dedicated unit tests when they only render supplied props.

Examples:

- layout wrappers;
- static headings;
- typography components;
- simple metric cards;
- visual-only separators.

Avoid tests whose main assertion is effectively “React rendered the text I passed in.”

### Require focused tests

Add tests for:

- deterministic graph-to-UI transformations;
- API client/request behaviour;
- meaningful component state or interaction;
- edge selection -> evidence display behaviour;
- non-trivial formatting or derived presentation logic;
- error and empty states where behaviour matters.

Prefer testing observable behaviour rather than component implementation details.

### Targeted test pyramid

Treat deterministic application behaviour and stochastic model quality as separate testing concerns.

```text
                 Live model evaluations
                 benchmark cases
                      ↑
             Browser E2E tests
          model boundary substituted
                      ↑
          API / integration tests
                      ↑
    Backend + frontend deterministic
                unit tests
```

The layers have different jobs:

- **Deterministic unit tests** protect graph construction, evaluation rules, frontend transformations, and meaningful component behaviour.
- **API/integration tests** protect contracts and orchestration across deterministic boundaries.
- **Browser E2E tests** protect the real product journey while substituting only the stochastic model boundary.
- **Live model evaluations** measure extraction quality over benchmark cases. They are evaluation runs, not ordinary deterministic CI assertions.

CI should not depend on the model returning the same extraction on every run.

For deterministic E2E tests, substitute the extraction/model boundary with a known `RelationshipCandidate` fixture. Case fixtures such as `expected_extraction.json` are appropriate candidates where they represent the intended extraction contract.

Keep the rest of the path real wherever practical:

```text
browser
→ frontend
→ API
→ known extraction fixture
→ real deterministic graph construction
→ real deterministic evaluation
→ frontend result
```

Do not mock the final canonical graph merely to make the browser test easier; doing so would skip important application behaviour.

Live-model testing should instead run the real extraction pipeline and record benchmark metrics such as relationship precision, recall, F1, and provenance accuracy. These runs may be manual, scheduled, or part of a dedicated evaluation workflow as the benchmark grows.

The guiding rule is:

> CI stops stochasticity at the model boundary. Live model behaviour is measured through benchmark evaluation rather than asserted as deterministic application behaviour.

### Critical end-to-end flow

The Case 01 vertical slice should eventually have a small browser E2E test covering the core user journey, for example:

```text
open Case 01
→ source is visible
→ run extraction
→ graph is displayed
→ select a relationship
→ supporting evidence is shown
→ evaluation metrics are displayed
```

A small number of high-value integration/E2E tests is preferable to exhaustive shallow component tests.

Backend `pytest` coverage remains required.

## Agent implementation freedom

Coding agents may have broad implementation freedom inside the web/API layer when these boundaries are respected.

They may:

- create and refactor frontend components;
- implement styling and responsive layout;
- add thin API/application orchestration;
- add focused frontend tests;
- choose straightforward libraries when justified.

They should not silently change:

- extraction prompts/contracts;
- graph semantics;
- evaluation semantics;
- provenance rules;
- ground-truth fixtures.

If a web feature appears to require such a change, surface that dependency before implementing it.

## Keep abstractions earned

Do not add features simply because a deployed application often has them.

Examples that are out of scope until required include:

- authentication/OAuth;
- database persistence;
- graph databases;
- generalized multi-user workspaces;
- advanced global state;
- plugin architectures;
- temporal reconciliation UI.

Build the smallest vertical slice that exposes the already-tested core well, then let concrete product and benchmark failures drive the next layer of complexity.
