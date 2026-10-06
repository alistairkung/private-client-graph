---
status: accepted
---

# Enforce canonical provenance and aggregate integrity

PCG's provenance and professional-review guarantees require canonical persistence to protect structural integrity against writes that bypass application validation. Use separate relational structures for Matter Proposals and accepted Matters, with aggregate-scoped references and database-enforced provenance integrity, support completeness, exact quote occurrence, and immutable Source text/Evidence attribution; reconstruct CanonicalGraph without giving it independent persisted identity. This replaces ADR 0002's JSONB graph-storage choice for the next slice, accepting repeated proposal/Matter structure and focused database enforcement instead of relying on application-only validation or maintaining a second complete graph validator over JSONB.

## Consequences

Entity identity is aggregate-local and independent of name; Sources have explicit identity; Evidence is distinguished by Source and exact quote. Whole-proposal confirmation atomically copies the reviewed facts unchanged into Matter-owned records, transfers the reference claim, and consumes the proposal. A coordinated maintenance-window migration preserves persisted facts and observable graph references/order, with no permanent dual authority.

The [agreed architecture spec](../design/canonical-persistence-slice.md) defines acceptance criteria and deferred decisions. Entity-resolution/extraction design and individual Source/Evidence deletion semantics remain deferred; ordinary persisted Relationships still require Evidence. Minimum-support and other detailed enforcement mechanisms must be selected and tested against supported transactions, including concurrent bypassing writes. This ADR records the agreed direction, not a completed implementation.
