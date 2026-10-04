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

## Implemented Case 01 showcase boundary

The first web slice is the professional-review path documented in
`docs/design/case-01-professional-review-web-slice.md`:

```text
read-only synthetic source
   -> explicit live or sample extraction
   -> deterministic graph construction
   -> read-only relationship and evidence review
```

It ends at canonical graph construction. The web application does not invoke or
expose benchmark evaluation, even though the existing evaluator remains available
for offline benchmark and development work. A benchmark/evaluation web surface is
deferred to a separate future slice.

The professional-facing analysis response contains execution metadata and the
`CanonicalGraph`. Raw `ExtractionResult` data is persisted for technical
traceability but is not returned to the browser. `EvaluationResult` is neither
produced nor returned by this web workflow.

The next application slice preserves that flow as a public showcase under the
`/api/showcase` namespace and adds a separate persisted practitioner journey.
The authoritative design is
`docs/design/practitioner-matter-workspace-slice.md`:

```text
public showcase
    -> transient live or sample Case 01 analysis

practitioner application
    -> persisted Matter list
    -> complete current Matter review state
```

Do not make either journey call through the other. They share only appropriate
lower-level domain capabilities.

## Repository structure

Keep backend and frontend in the same repository unless a concrete deployment or ownership need justifies a split.

Prefer clear package boundaries over unnecessary repositories.

A small frontend should expose ownership in its directory structure. Keep the
bootstrap and application shell easy to find, colocate each feature's components,
state, API operations, contracts, deterministic transformations, and focused
tests, and retain a shared directory only for contracts or browser
infrastructure genuinely consumed across feature boundaries. For example:

```text
private_client_graph/
  models/
  application/
  api/
  ...

web/
  src/
    main.tsx
    test-setup.ts
    app/
      App.tsx
    features/
      showcase/
        api.ts
        showcase.css
        types.ts
        ...
      matters/
        api.ts
        types.ts
        ...
      review/
        graph-view.ts
        review.css
        ...
    shared/
      canonical-graph.ts
    styles/
      global.css
```

Do not create global `components`, `hooks`, `api`, `lib`, `utils`, or `types`
directories as catch-alls. A feature directory is earned by a coherent product
responsibility, not by file count; do not split a cohesive component merely to
populate the tree. Keep tests beside the behaviour they protect. Keep global
styles limited to application-wide foundations and explicitly shared
presentation, and colocate shell-specific styles and assets with their owning
feature. Avoid barrel files and import aliases unless the dependency graph is
large enough for them to improve navigation demonstrably.

Use a thin FastAPI backend and a React/TypeScript frontend in this repository.
Keep showcase Case 01 fixtures backend-authoritative: the browser reads the source
and requests an explicit execution mode, but never submits or modifies the
document. Practitioner Matter requests read complete current state from
PostgreSQL and never use benchmark fixtures as runtime fallback storage.

## Backend style

- Keep meaningful domain models in focused files.
- Keep domain models independent from HTTP or UI concerns.
- Keep routes/controllers thin.
- Put multi-step use-case orchestration in an application layer when route code would otherwise become procedural domain logic.
- Reuse the existing domain functions needed by each workflow. The current web
  workflow uses extraction and graph construction; offline benchmark workflows
  continue to use evaluation.
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
├── AnalysisControls
├── GraphView
└── EvidencePanel
```

over one page containing data fetching, graph transformation, selection state,
evidence rendering, and large amounts of JSX.

Extract a component when it represents a meaningful UI responsibility or is genuinely reusable.

Do not split trivial markup into tiny generic components merely to reduce file length.

Keep graph rendering and evidence display as separate concerns. Do not add an
evaluation concern to the first professional-review slice.

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

The evaluation layers describe the wider project testing strategy; they do not
imply that benchmark evaluation belongs in the first professional-facing web UI.

CI should not depend on the model returning the same extraction on every run.

For deterministic E2E tests, substitute the extraction/model boundary with a known `RelationshipCandidate` fixture. Case fixtures such as `expected_extraction.json` are appropriate candidates where they represent the intended extraction contract.

Keep the rest of the path real wherever practical:

```text
browser
→ frontend
→ API
→ known extraction fixture
→ real deterministic graph construction
→ relationship selection
→ exact source-evidence highlight
```

Do not mock the final canonical graph merely to make the browser test easier; doing so would skip important application behaviour.

Live-model testing should instead run the real extraction pipeline and record benchmark metrics such as relationship precision, recall, F1, and provenance accuracy. These runs may be manual, scheduled, or part of a dedicated evaluation workflow as the benchmark grows.

The guiding rule is:

> CI stops stochasticity at the model boundary. Live model behaviour is measured through benchmark evaluation rather than asserted as deterministic application behaviour.

### Critical end-to-end flow

Retain the Case 01 browser E2E test covering the core showcase journey:

```text
open Case 01
→ source is visible
→ load sample analysis
→ graph is displayed
→ select a relationship
→ supporting evidence is shown
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

## Matter persistence

The practitioner application uses synchronous SQLAlchemy 2 and Alembic with
PostgreSQL. Keep persistence concrete and scoped to current Matter operations;
do not introduce generalized repositories, service hierarchies, dependency
injection, or asynchronous database infrastructure.

Store the current `CanonicalGraph` atomically as JSONB and validate it through
the existing domain model at the application boundary. Also preserve the
cross-value invariant that every Evidence span occurs verbatim in the Matter's
authoritative source. Do not relationalise graph contents before concrete query
or independent-mutation requirements justify it.

Every schema change requires an explicit Alembic migration. Treat merged or
applied migrations as immutable and create a new migration for later changes.
Persistence integration tests use PostgreSQL, not SQLite.

## Keep abstractions earned

Do not add features simply because a deployed application often has them.

Examples that are out of scope until required include:

- authentication/OAuth for the current synthetic read-only application;
- graph databases;
- generalized multi-user workspaces;
- advanced global state;
- plugin architectures;
- temporal reconciliation UI.

Build the smallest vertical slice that exposes the already-tested core well, then let concrete product and benchmark failures drive the next layer of complexity.

The application is deployed as a combined FastAPI/static-frontend Railway
service. The practitioner slice adds PostgreSQL over private networking and runs
Alembic plus explicit synthetic seeding in a pre-deploy command. The readiness
endpoint must verify database connectivity.

The public showcase keeps fixed backend-owned synthetic input. Live showcase
analysis is disabled by default and, when explicitly enabled, is protected by a
persistent global fixed-window quota. This operational control is separate from
practitioner authentication and authorization.

The unauthenticated practitioner journey is permitted only while it remains
read-only and strictly synthetic. Authentication and Matter authorization are a
hard prerequisite for user-supplied, non-synthetic, or mutable Matter data.
