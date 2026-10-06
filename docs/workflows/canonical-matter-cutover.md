# Canonical Matter persistence cutover

## Release boundary

Issue #84 is integration-only. Do not merge or deploy it independently onto the
normal deployment branch. Issue #85 must complete constrained proposal storage,
pending-proposal conversion and the combined release verification first. This
intermediate implementation preserves the current proposal journeys through a
JSONB-proposal-to-relational-Matter adapter; it is not the approved final storage
model for proposals.

Migration `0005` belongs to the Matter implementation. It creates the Matter
fact tables, converts existing stored Matters, verifies exact graph reconstruction,
checks deferred support constraints, and removes the old Matter graph/source
columns in one PostgreSQL transaction. Applied migrations remain immutable.
Pending proposals and external-reference claims are preserved by this migration.
The proposal migration and final combined cutover remain #85's responsibility.

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

Use this procedure only for the approved combined #84/#85 release, with #85's
proposal steps incorporated. A pre-deploy hook by itself is not sufficient.

1. Verify the combined code, migrations, tests and release approval. Take and verify
   a restorable backup of the entire database, including pending proposals and
   reference claims; retain the matching previous application release.
2. Stop access to the practitioner application and quiesce **all** old application
   instances and writers, including seed commands and operational scripts. Drain
   active transactions and confirm they cannot restart during migration. Keeping
   an old replica serving while the new version's pre-deploy hook runs is unsafe.
3. From the matching release environment, run the full Alembic chain with
   `PCG_MATTER_MIGRATION_QUIESCED=true`. This is an operator acknowledgement, not an
   automatic maintenance switch. A database containing Matters refuses `0005`
   without it. The migration takes an exclusive Matter table lock with a bounded
   lock wait; blocked lock acquisition fails rather than proceeding concurrently.
   Existing-data conversion has no statement-duration limit inside the migration.
4. Migration validates persisted facts rather than regenerating benchmark state.
   Missing references, missing support, non-verbatim quotes, duplicate edges or
   Evidence, and any loss/change of graph fields cause failure. Do not repair
   accepted facts silently or bypass constraints to finish the migration.
5. After the complete Matter/proposal migration succeeds, run the ordinary explicit
   insert-only Evergreen seed. Start only the matching new application. Verify
   existing Matter review, pending-proposal review, whole confirmation/discard,
   direct entry/refresh, exact Evidence highlighting and public sample analysis.
   Restore access only after these checks pass.

For a failure before commit, PostgreSQL rolls back schema and data together; keep
access stopped while investigating, or resume the matching old release after
confirming the unchanged old schema. After a committed cutover, rollback requires
restoring the complete pre-cutover backup together with the matching old release
while access is still stopped. Do not use an automatic downgrade: a legacy graph
cannot generally retain new multi-source facts. Do not introduce dual writes or
partial backup restoration as a workaround. Once writes resume, recovery needs a
fresh plan that accounts for those writes.

## Verification seams

Run the normal full backend suite against disposable PostgreSQL 16, typing and
frontend checks, and browser journeys against a separate freshly migrated/seeded
database. Database tests exercise direct invalid writes, concurrent support
removal, quote uniqueness at each isolation level, long quotes, migration rollback,
Case 01 graph/evaluation equality and explicit multi-source identity preservation.

The current practitioner API is intentionally single-source. Its Matter reader
uses one repeatable-read snapshot for all fact queries and fails safely if asked
to display a multi-source aggregate through that legacy contract. Source-aware
state is available at the persistence boundary for deterministic tests and later
design work; this slice does not expose multi-source acquisition or presentation.
