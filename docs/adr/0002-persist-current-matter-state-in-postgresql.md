# Persist current Matter state in PostgreSQL

The JSONB graph-storage choice below is superseded for the next persistence slice by [ADR 0008](0008-enforce-canonical-provenance-and-aggregate-integrity.md). PostgreSQL, explicit migrations, and insert-only initialization remain in force. The historical implementation described here remains current until that slice is implemented.

The practitioner application persists each complete current Matter in PostgreSQL rather than treating committed benchmark fixtures or application-local files as its runtime datastore. Matter identity and authoritative source use ordinary columns, while the current `CanonicalGraph` is stored atomically as JSONB and validated through the existing domain model; this creates a durable write-model foundation without relationalising graph semantics or pre-empting a future Matter timeline.

## Consequences

PostgreSQL is used wherever persistence is integration-tested, schema changes use explicit immutable Alembic migrations, and deployment applies migrations before an explicit insert-only synthetic seed. Persistence remains concrete and narrowly scoped: no graph database, repository hierarchy, event store, incomplete-Matter lifecycle, or history model is introduced.
