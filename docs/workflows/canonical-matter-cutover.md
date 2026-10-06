# Canonical Matter persistence cutover

## Release boundary

The combined #84/#85 release replaces authoritative JSONB state for accepted
Matters and pending Matter Proposals. Do not run an old application against the
new schema, or activate the intermediate `0005` application/schema pair.

Migration `0005` converts accepted Matters; `0006` converts pending proposals.
Each copies stored values, verifies exact reconstruction and forces deferred
constraints before dropping its legacy graph/source columns. Existing graph IDs,
list order, source titles, Evidence document labels and external-reference claims
are preserved. Neither conversion reads fixtures or invokes extraction.

Alembic's online environment wraps the complete `upgrade head` chain in one
PostgreSQL transaction. An upgrade from `0004` therefore commits both conversions
or neither. If an environment already applied `0005`, a failed `0006` leaves it at
`0005`; keep application access stopped until the compatible release is ready.
Applied migrations remain immutable. There are no dual writes or retained legacy
graph authorities after `0006`.

## Database enforcement choices

- Composite Matter-scoped foreign keys protect endpoints, Source attribution and
  support associations. Endpoint/support checks are deferred to commit to allow
  atomic aggregate removal. Source attribution uses an immediate RESTRICT foreign
  key: a referenced Source cannot be deleted and replaced, even within one SQL
  statement. Whole-aggregate deletion remains valid. Names and titles are not
  identity keys.
- An expression-based unique index treats reversed symmetric edges as identical
  while retaining the reviewed endpoint orientation and list order. Typed endpoint
  foreign keys and row checks enforce the existing Person/Trust vocabulary.
- A non-null storage-only support reference on each Relationship has a deferred
  foreign key to one of that Relationship's support associations. At commit it
  proves support exists. It is not primary Evidence and is omitted from domain/API
  projections. Creation inserts both sides in one transaction. This mechanism does
  not introduce a Source/Evidence deletion product workflow.
- Finalized Source identity/text and Evidence attribution/quote are immutable through
  ordinary database writes. An insertion trigger checks exact quote occurrence.
- Exact Source-plus-quote uniqueness compares full text, avoiding B-tree entry
  limits and hash-collision identity. Evidence inserts serialize by updating an
  internal boolean on their Source row before checking for an existing quote.
  This boolean is synchronization machinery, not canonical domain content.
  The subsequent trigger query sees competing commits at Read Committed; stale
  Repeatable Read/Serializable writers must abort. Tests exercise all three levels.
- Nonblank checks use the frozen Unicode whitespace set from the domain contract,
  not the database locale's definition of whitespace. SQL constraints provide the
  structural guarantees; application/domain validation remains complementary.

## Coordinated maintenance procedure

Use this procedure for the combined #84/#85 release. A pre-deploy hook by itself
is not sufficient. Keep automatic deployment/restart disabled during the window.

1. Verify the combined code, migrations, tests and release approval. Take and verify
   a restorable backup of the entire database, including pending proposals and
   reference claims; retain the matching previous application release. Rehearse
   restoration into an isolated database and verify the Alembic revision and both
   stored aggregates before touching the deployment.
2. Stop access to the practitioner application and quiesce **all** old application
   instances and writers, including seed commands and operational scripts. Drain
   active transactions and confirm they cannot restart during migration. Keeping
   an old replica serving while the new version's pre-deploy hook runs is unsafe.
   Remove old instances' database connectivity/credentials for the window, or
   otherwise block their restart and terminate their remaining database sessions.
   The migration connection must remain available. Do not treat an environment
   acknowledgement as proof that these operational steps happened.
3. From the matching release environment, run the full Alembic chain with
   `PCG_MATTER_MIGRATION_QUIESCED=true`. This is an operator acknowledgement, not an
   automatic maintenance switch. A database containing Matters refuses `0005`
   without it; pending proposals similarly guard `0006`. Both migrations take
   exclusive locks on their aggregate root with a bounded lock wait; blocked
   lock acquisition fails rather than proceeding concurrently.
   Existing-data conversion has no statement-duration limit inside the migration.
4. Migration validates persisted facts rather than regenerating benchmark state.
   Missing references, missing support, non-verbatim quotes, duplicate edges or
   Evidence, and any loss/change of graph fields cause failure. Do not repair
   accepted facts silently or bypass constraints to finish the migration.
5. Verify `alembic current` reports `0006`, both root tables have lost their legacy
   graph/source columns, and existing Matter/proposal counts and reference claims
   match the pre-cutover inventory. Each conversion already verified every stored
   graph before removing its JSONB authority. Retain migration logs.
6. After the complete Matter/proposal migration succeeds, run the ordinary explicit
   insert-only Evergreen seed. Start only the matching new application. Verify
   existing Matter review, pending-proposal review, whole confirmation/discard,
   direct entry/refresh, exact Evidence highlighting and public sample analysis.
   Restore access only after these checks pass.

For a failure before commit, PostgreSQL rolls back schema and data together; keep
access stopped while investigating, or resume the matching old release after
confirming the unchanged old schema. After a committed cutover, rollback requires
restoring the complete pre-cutover backup together with the matching old release
while access is still stopped. Restore into a fresh database, verify the old
Alembic revision, both legacy graphs and all claims, then point the matching old
release at that restored database. Do not mix tables from different snapshots.
The automated recovery rehearsal uses a full custom-format `pg_dump`/`pg_restore`
backup and verifies these properties after a completed cutover.
Do not use an automatic downgrade: a legacy graph
cannot generally retain new multi-source facts. Do not introduce dual writes or
partial backup restoration as a workaround. Once writes resume, recovery needs a
fresh plan that accounts for those writes.

## Verification seams

Run the normal full backend suite against disposable PostgreSQL 16, typing and
frontend checks, and browser journeys against a separate freshly migrated/seeded
database. Install PostgreSQL 16 client tools (`pg_dump`, `pg_restore`) on PATH
for the backup-recovery rehearsal; CI includes them. Database tests exercise direct invalid writes, concurrent support
removal, quote uniqueness at each isolation level, long quotes, migration rollback,
Case 01 graph/evaluation equality and explicit multi-source identity preservation.

The current practitioner API is intentionally single-source. Its Matter reader
uses one repeatable-read snapshot for all fact queries and fails safely if asked
to display a multi-source aggregate through that legacy contract. Source-aware
proposal reads also use a consistent snapshot, and confirmation copies one
validated snapshot under the proposal root lock. Source-aware state is available at the persistence boundary for deterministic tests and later
design work; this slice does not expose multi-source acquisition or presentation.
