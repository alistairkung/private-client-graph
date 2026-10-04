# Practitioner Matter workspace slice

> **Status:** Accepted design; implementation pending.

## Goal

Turn the deployed Case 01 professional-review experience into part of the smallest believable day-to-day application for a private-client solicitor or adviser, without changing the existing extraction, canonical graph, provenance, evaluation, or graph/evidence-review semantics.

The slice introduces durable Matter state and a focused Matter-navigation journey. It preserves the working Case 01 demonstration as an explicitly separate public showcase.

## Product topology

```text
/                                  public synthetic showcase
/app                               practitioner Matter list
/app/matters/{internal_id}         persisted Matter review workspace
```

The showcase and practitioner application use distinct shells with explicit navigation between them. The practitioner shell contains only the navigation earned by this slice: Matters and a path back to the showcase. Matter detail provides a clear route back to the Matter list.

## Practitioner workflow

The practitioner opens `/app`, identifies a Matter by title and externally supplied firm Matter reference, and opens it directly into the relationship review workspace.

The preloaded Evergreen Matter opens with its current graph already available. The source, graph, relationship selection, Evidence list, and exact source highlighting retain the existing professional-review interaction. Opening a Matter never triggers extraction, sample loading, or reanalysis.

There is no separate Matter overview or document page. The relationship review is the Matter workspace for the currently supported lifecycle.

## Matter model

A Matter is a scoped piece of professional work. It is the primary practitioner-facing product object; people and trusts remain entities in its Canonical Graph rather than becoming navigation roots.

Every persisted and practitioner-visible Matter in this slice is a complete, immediately reviewable snapshot containing:

- an opaque internal UUID owned by Private Client Graph;
- an external Matter reference supplied by a firm's matter-management ecosystem;
- a Matter title;
- one embedded authoritative source with a title and text;
- one current `CanonicalGraph`.

The internal UUID is the route identity. The external Matter reference is display and future integration metadata: Private Client Graph does not generate it or use it as technical identity.

The graph belongs to the Matter. A Matter currently has one authoritative source, so the graph is derived from that source. This constraint does not introduce a document-level product hierarchy and does not define future multi-source merging, supersession, retraction, historical-fact, or current-state semantics.

The complete-Matter constraint describes the only lifecycle currently supported. It is not a permanent rule that a Matter inherently requires a graph; incomplete Matter states must wait for a designed creation and ingestion workflow.

## Matter collection

The slice contains one fully functional synthetic Matter. It does not add placeholder rows or author additional synthetic Matters merely to demonstrate plurality.

`MatterSummary` contains only:

```text
- id
- external_reference
- title
```

The collection exists only to identify and navigate to Matters. Derived relationship information and operational Matter information are future product evolution rather than rejected concepts. Examples include graph-derived counts, instructing party, responsible professional, review status, last activity, deadlines, and attention-required indicators; none receives semantics in this slice.

## Practitioner API

The practitioner API exposes:

```text
GET /api/matters
GET /api/matters/{internal_id}
```

The collection returns `MatterSummary` values. Matter detail returns the complete current review state:

```text
MatterDetail
- id
- external_reference
- title
- authoritative_source
    - title
    - text
- current_graph
```

The authoritative source is an embedded value, not a separately addressable document resource. Source and graph remain one composite response until distinct lifecycle, authorization, size, or access-pattern requirements justify separation.

The response contains no analysis mode, run artifact, benchmark identifier, review status, or analysis history.

## Persisted-state integrity

PostgreSQL owns the complete current Matter state. Matter identity and authoritative-source values use ordinary columns. The current `CanonicalGraph` is stored atomically as JSONB.

The application validates the JSONB value through the existing `CanonicalGraph` model whenever persisted Matter state crosses the application boundary. It also verifies that every Evidence span in the graph occurs verbatim in the Matter's authoritative source before returning or accepting the complete state. PostgreSQL persists domain output; it does not duplicate graph construction or provenance semantics.

Entities, relationships, and Evidence remain inside the Canonical Graph snapshot. They are not relationalised until concrete cross-Matter querying or independent-mutation requirements justify it. Snapshot storage is compatible with a future timeline model but does not prescribe one.

Persistence uses synchronous SQLAlchemy 2 and Alembic. Keep data access concrete and limited to the current operations: listing Matter summaries, loading one complete Matter, and inserting the synthetic seed. Do not add repository interfaces, service hierarchies, generalized dependency injection, or asynchronous database infrastructure.

Every database schema change must have an explicit Alembic migration reviewed with the feature that requires it. A merged or applied migration is immutable; subsequent schema changes require new migrations. Migrations do not require separate pull requests from their features.

## Synthetic initialization

Case 01 fixtures are initialization inputs, not runtime application storage. An explicit seed command:

1. loads the authoritative source and expected extraction fixture;
2. passes the relationship candidates through the existing deterministic graph builder;
3. constructs and validates the complete synthetic Evergreen Matter;
4. inserts it only when its fixed internal UUID is absent.

The seed uses a realistic fictional external Matter reference. It is idempotent and insert-only: later changes to Case 01 fixtures never overwrite persisted Matter state. Normal Matter requests read PostgreSQL only and never fall back to benchmark fixtures.

Schema migrations own database structure. Seeding owns synthetic initialization.

## Public showcase boundary

The existing Case 01 journey remains at `/` as an explicitly labelled public synthetic showcase:

```text
fixed backend-owned Case 01 source
    -> explicit live or sample extraction
    -> deterministic graph construction
    -> transient graph and exact Evidence review
```

Its HTTP contracts move without compatibility aliases to:

```text
GET  /api/showcase/case-01
POST /api/showcase/case-01/analysis
```

`Case 01` remains valid showcase and Benchmark Case terminology. Showcase analysis remains transient, preserves existing live/sample behavior and run-artifact traceability, and never reads or mutates persisted Matter state. Practitioner Matter APIs never call through the showcase. Both flows may call the appropriate existing lower-level domain capabilities.

The fixed showcase source and prompt remain backend-controlled. The showcase accepts no uploaded, pasted, or otherwise arbitrary model input.

## Live-showcase usage control

Sample analysis remains publicly available. Live showcase analysis is disabled by default and requires all of the following deployment configuration:

- explicit live enablement;
- a positive global quota limit;
- a valid fixed-window duration;
- provider configuration.

If live analysis is enabled with missing or invalid quota configuration, application startup fails. Possession of a provider key alone never publishes a spend-bearing endpoint.

The quota uses persistent global fixed UTC time buckets in PostgreSQL. Immediately before each provider invocation, the server atomically consumes one slot. A consumed slot remains consumed whether the provider call succeeds or fails. Requests rejected before the provider boundary do not consume quota.

There is no per-IP tracking, user identity, access code, or generalized rate-limiting framework. The global quota bounds model-account exposure regardless of process restarts or application replicas.

The showcase detail response includes current live-analysis availability and the reset time when exhausted. The analysis endpoint remains authoritative and rechecks the quota atomically. Disabled or exhausted live analysis affects neither sample analysis nor the practitioner application.

## Access boundary

The practitioner application remains unauthenticated only because every Matter is synthetic, the Matter APIs are read-only, and no visitor can submit or persist information.

Authentication and Matter authorization are a hard prerequisite for any future slice that introduces user-supplied, non-synthetic, or mutable Matter data. Matter creation, upload, ingestion, source editing, graph mutation, and review-state mutation must not be added incrementally to the public application before that boundary is designed.

## Deployment

Railway adds a PostgreSQL service connected to the application over private networking through `DATABASE_URL`. The web service remains stateless with respect to Matter data.

The Railway pre-deploy command performs:

```text
alembic upgrade head
explicit idempotent Evergreen seed
```

Failure of either step prevents deployment. The application starts only after schema and synthetic initialization succeed.

`GET /health` represents application readiness and succeeds only when the web process can connect to PostgreSQL and execute a minimal query. It does not encode the presence of a specific synthetic Matter.

## Testing boundary

Persistence integration tests use a real disposable PostgreSQL database; SQLite is not a substitute for PostgreSQL JSONB, UUID, transaction, or migration behavior. Existing domain tests remain database-free.

Deterministic coverage should include:

- applying the Alembic migration chain to an empty PostgreSQL database;
- idempotent insert-only seeding and refusal to overwrite existing Matter state;
- Matter summary and detail serialization;
- missing-Matter behavior;
- Canonical Graph deserialization and source/Evidence integrity failures;
- direct navigation from the Matter list to the persisted review workspace;
- preservation of relationship selection and exact Evidence highlighting;
- showcase and practitioner route separation;
- live disabled-by-default configuration;
- atomic quota consumption, exhaustion, reset-window behavior, and provider-failure consumption;
- continued sample availability and practitioner access when live analysis is unavailable;
- database-aware readiness behavior.

The existing showcase browser journey remains valuable. Add a separate practitioner browser journey that opens `/app`, selects Evergreen, and reviews a relationship and its exact Evidence without invoking extraction.

## Explicitly out of scope

- Matter creation, intake, upload, ingestion, or deletion;
- user-supplied or non-synthetic content;
- authentication, users, firms, tenancy, or Matter authorization;
- client, trust, or document navigation hierarchies;
- review status, acknowledgement, assignment, deadlines, or activity feeds;
- source, graph, relationship, or Evidence editing;
- live reanalysis or updates to persisted Matter state;
- analysis-run history in the practitioner application;
- multiple synthetic Matters or placeholder Matter rows;
- multi-source aggregation, identity reconciliation, contradictions, or temporal semantics;
- relational graph storage, cross-Matter graph queries, or a graph database;
- benchmark or evaluation tooling in the practitioner application;
- changes to extraction contracts, supported relationship semantics, deterministic graph construction, provenance semantics, evaluation metrics, or benchmark ground truth.

## Deferred product evolution

Likely later slices include richer Matter summaries, authenticated Matter creation, source ingestion, review workflow, current-state updates, and a Matter timeline. Those features must earn and define their own semantics rather than treating this slice's complete seeded snapshot as a permanent lifecycle model.
