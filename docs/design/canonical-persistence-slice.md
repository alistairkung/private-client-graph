# Canonical persistence slice

Status: agreed architecture boundary, reviewed and accepted on 2026-10-07. Ready for the existing ticket-authoring workflow; implementation and migration have not been performed or authorized by this design-only task. See [ADR 0008](../adr/0008-enforce-canonical-provenance-and-aggregate-integrity.md).

## Purpose and scope

Replace serialized graph authority with relational canonical facts protected by database-enforced integrity, for both Matter Proposals and accepted Matters. Provenance integrity and aggregate isolation are domain requirements independent of stochastic extraction performance. CanonicalGraph remains a deterministically reconstructed domain/presentation representation with no separately persisted identity or lifecycle.

The deterministic substrate must support multiple explicitly identified Sources. Prove this with controlled fixtures supplying Entity identity; do not introduce multi-document practitioner intake, extraction orchestration, or entity resolution. Preserve existing single-source practitioner journeys. Establish Case 01 equivalence and the controlled multi-source persistence baseline before subsequent extraction experiments. The current Case 04 PR lacks source-qualified provenance and cannot alone establish that baseline; existing evaluation metrics remain unchanged.

ADR 0008 replaces ADR 0002's JSONB graph-storage choice for the next persistence slice while retaining PostgreSQL, explicit migrations, and insert-only initialization. ADRs 0005 and 0006 continue to govern finalized source text and whole-proposal professional acceptance; this design evolves their single-source/storage assumptions without changing those semantics. The current implementation remains JSONB until the separate implementation task completes.

## Canonical facts and cardinality

Each Matter owns its Sources, Entities, Relationships, and their provenance. Each Matter Proposal owns a separate proposed set with the same structural guarantees.

| Fact | Identity and relationships |
| --- | --- |
| Source | Explicit identity within its owner; stores finalized text and title. Matching titles or text do not merge separately designated Sources or prove independent corroboration. |
| Entity | Identity within its owner, independent of name; retains type and exact name. Duplicate names are representable. |
| Evidence | Belongs to exactly one Source; identity is Source plus exact quote text, not an occurrence/span. One item may support multiple Relationships. |
| Relationship | Connects two existing Entities under the same owner; identity is endpoint identities plus supported relationship type. Symmetric types ignore endpoint order; directed types preserve it. Each Relationship has one or more Evidence associations. |
| Support association | Connects a Relationship to Evidence under the same owner, once per pair. |

Persist all facts and any reference/order metadata necessary to reconstruct the reviewed graph exactly. Preserve Source text and titles even when the graph is empty. Graph-local IDs need not be database primary keys. Relationship storage keys, if useful, do not introduce a new product lifecycle. Source attribution must resolve through explicit identity, never through a potentially duplicate display title. Preserve legacy Evidence document labels without conflating them with Source titles.

## Deferred — entity-resolution/extraction design

Exact-name grouping is not a permanent semantic identity rule. A later Case 03-driven design review must define and evaluate entity resolution in both directions: merging different surface forms that refer to one real-world entity and keeping identical names separate when they refer to different entities. The persistence model must support both outcomes. Practitioner confirmation of proposed identity resolution should be considered separately from benchmark correctness.

For this persistence slice, Entity identity is Matter-local and independent of name, and duplicate names must be representable. Persistence and reconstruction preserve supplied Entity identities and references rather than regrouping Entities by name. The controlled two-source persistence acceptance fixture supplies explicit Entity identities so that it does not accidentally test entity resolution.

The existing exact-name builder remains a Case 01 compatibility path, not the adopted multi-source identity policy. The current name-based evaluator can establish Case 01 regression equivalence but cannot establish correct identity handling for distinct same-name Entities; persistence acceptance must inspect the reconstructed identity distinctions and references directly. The future extraction and evaluation contracts remain deferred, including the hypothesis that the model proposes entity correspondence evaluated against hidden identity ground truth.

## Reviewed graph preservation

Confirmation and persistence round trips preserve the reviewed graph's observable Entity and Evidence IDs, list ordering, values, and associations. Internal database keys may differ, but reconstruction must not renumber observable references, regroup Entities by name, or reorder the reviewed graph. This preserves the existing whole-proposal confirmation contract without assigning independent persisted identity to CanonicalGraph.

## Canonical integrity requirements

Canonical persistence must protect structural and referential invariants through PostgreSQL constraints wherever they naturally express the rule; application validation complements rather than replaces those guarantees. The same structural guarantees apply to durable Matter Proposals and accepted Matters, scoped to their respective aggregate. Professional acceptance remains a separate distinction.

- Provenance integrity: every Evidence item resolves to its Source, and every Relationship–Evidence association resolves at both ends without duplicate associations.
- Aggregate isolation: related Sources, Evidence, Entities, and Relationships belong to the same Matter or the same Matter Proposal. Existence of referenced records alone is insufficient.
- Provenance completeness: every committed Relationship has at least one supporting Evidence association. Direct creation of a zero-support Relationship, or removal of final support while retaining the Relationship, must fail. Empty graphs remain valid. Individual Source/Evidence deletion is not a supported product operation; its future behaviour is deferred below.
- Verbatim provenance: each Evidence quote occurs exactly in its referenced Source's finalized text. Enforcement covers changes to quote text, Source reference, and Source text. Whether the quote semantically supports a Relationship remains outside this guarantee.

Direct database writes must be tested for dangling Evidence-to-Source and Relationship-to-Entity references, dangling or duplicate Relationship–Evidence associations, endpoints from different aggregates, Relationship/Evidence scope mismatches, and Evidence/Source scope mismatches. Tests must also cover removal of final support while retaining a Relationship and violations of verbatim provenance. Detailed enforcement mechanisms remain under design.

## Ownership keys

Repeat aggregate ownership scope where it enables ordinary composite foreign keys to enforce isolation. Relationship endpoints reference Entities under the same owner; Evidence references a Source under the same owner; and each Relationship–Evidence association references both records under its owner. Repeated scope values are constrained to agree rather than independently asserting ownership. Apply the same guarantee to proposal-owned state without allocating Matter identity before confirmation. This repetition is justified by reference integrity, not a blanket convention to add ownership columns to every table.

## Proposal boundary and confirmation transaction

Use separate proposal-owned and Matter-owned persistence structures, with real foreign keys to their respective aggregate roots. Accept the repeated schema/constraints in exchange for explicit ownership boundaries and preservation of the copy-and-consume lifecycle. Share cohesive domain validation and reconstruction logic where useful; do not introduce a generic repository framework or a polymorphic owner registry.

Proposal creation atomically persists its complete source/graph facts and external-reference claim after successful analysis. Whole-proposal discard removes its owned facts and claim atomically without retaining history.

Confirmation locks and reloads the proposal, validates the reviewed state, allocates the Matter identity, copies all reviewed facts and associations unchanged into Matter-owned records, transfers the external-reference claim, and consumes the proposal and its children in one transaction. No extraction, name-based reconstruction of candidates, or new identity resolution occurs during confirmation. A known rollback leaves the proposal intact and creates no partial Matter. Preserve concurrent confirmation/discard behaviour and the existing ambiguous-outcome handling after a lost commit acknowledgement; do not add replay-success semantics.

## Provenance-field immutability

PostgreSQL rejects updates to a persisted Source's finalized text and to an Evidence item's Source reference or exact quote. Validate verbatim quote occurrence when Evidence is created; subsequent rewrites of these fields are prohibited rather than supported as a correction workflow. Deletion remains subject to reference integrity and provenance completeness. Whole-proposal confirmation can copy reviewed facts unchanged into Matter-owned records, then consume the proposal. This restriction introduces neither history nor supersession and does not prohibit deletion of whole aggregates.

## Deferred — Source/Evidence deletion semantics

This slice introduces no operation for deleting individual Sources or Evidence. A future design must determine how deletion affects dependent accepted Relationships: possible choices include rejecting deletion, atomically removing Relationships that lose their support, or introducing a separately modelled provisional/unsubstantiated state. Unsubstantiated or practitioner-created Relationships without documentary Evidence require an explicit domain change and are excluded from this slice.

**Future hypothesis:** the product may need a distinct practitioner-asserted/unsubstantiated relationship concept. If introduced, it should be semantically explicit rather than represented by accidentally permitting ordinary Relationships to have zero Evidence.

Until then, persisted Relationships require support, and bypassing writes must not leave a committed zero-support Relationship. The enforcement mechanism remains an implementation decision to resolve against the agreed schema and supported transactions: proposal creation, whole-proposal confirmation and consumption, whole-proposal discard, migration, and Evergreen initialization. No individual-association deletion ergonomics or witness-reference mechanism has been approved.

## Migration boundary

A brief maintenance window and one coordinated cutover are acceptable. Pause application access and writes, validate and decompose persisted Matters and pending Matter Proposals, verify exact reconstruction, and activate the new application against the new canonical representation. Remove old graph storage as part of the coordinated change, without permanent dual writes or competing authoritative representations.

Migration uses persisted state rather than regenerated benchmark fixtures, preserves reviewed proposal contents, and aborts on invalid state rather than silently repairing it. Evergreen remains insert-only. The rollout must explicitly prevent the old application from accessing an incompatible schema; the pre-deploy migration hook alone does not establish this protection.

Implement the eventual schema change through new Alembic migrations; never edit applied migration history. Validate stored graph references and invariants explicitly, since current Pydantic shape validation alone does not establish full graph integrity. Exact pre/post reconstruction must be verified before legacy authoritative graph storage is removed.

## Regression and acceptance criteria

- Case 01 semantic input follows the existing deterministic construction policy, then the new persistence path and reconstruction. Entity/Evidence IDs, list ordering, names, types, endpoint direction, symmetric-edge normalization, quotes, document labels, and support associations match the reviewed graph exactly; the complete evaluation result remains equal.
- The controlled multi-source fixture uses explicit Entity identities. One semantic Relationship supported from two Sources reconstructs once with both provenance items. Identical quotes in different Sources remain distinct; repeated identical quotes in one Source share Evidence; shared Evidence can support multiple Relationships.
- Distinct same-name Entities remain distinct through persistence and reconstruction. Explicitly shared Entity references across Sources remain shared. These are identity-preservation tests, not entity-resolution evaluation.
- All seven dangling-reference, duplicate-association, and cross-aggregate rejection cases are exercised through direct database writes for both storage families. Also test zero-support insertion, removal of final support while retaining the Relationship, non-verbatim Evidence, provenance-field update rejection, and duplicate canonical edges including reversed symmetric endpoints.
- Retain supported relationship types, endpoint-type compatibility, no-self-relationship rules, and exact text semantics. Database enforcement must cover naturally expressible structural rules without changing domain interpretation.
- Exercise successful and failed proposal creation, unchanged confirmation, whole discard, concurrent terminal actions, transaction rollback, empty graphs, and Evergreen idempotence. No partial aggregate or failed reference-claim transfer may commit.
- Prove new constraints under relevant concurrent bypassing writes, not just sequential application calls. Migration tests cover existing Matters and pending proposals, exact reconstruction, and rejection of invalid stored state. Existing practitioner API/browser journeys remain protected.

## Implementation obligations and non-goals

No further product decision is implied by the choice of enforcement mechanism. Compare the smallest credible mechanisms for minimum support, exact Evidence uniqueness, quote occurrence, endpoint types, and immutable provenance fields against the supported transactions. A witness reference has not been selected. Do not assume a deferred count check is concurrency-safe. Account for long quote text when enforcing exact uniqueness; a hash alone must not redefine text equality. Resolve and test these mechanics before shipping an implementation.

Keep probabilistic extraction, deterministic validation/construction, evaluation, application orchestration, persistence, and presentation responsibilities distinct. Reconstruction reads canonical database facts without fixtures, model calls, name-based regrouping, or authoritative state hidden only in a derived graph.

Excluded: non-synthetic data enablement; new extraction/evaluation contracts; alias or homonym resolution; individual Source/Evidence deletion workflows; relationship editing or partial confirmation; practitioner-asserted/unsubstantiated Relationships; temporal state, contradictions, supersession, confidence, audit/history, graph versions, graph databases, organisation Entities, document integrations, queues, event sourcing, CQRS, and permanent JSONB/relational dual authority. Deferred domain hypotheses are recorded above and are not implementation scope.
