# Reserve external Matter references across Proposals and Matters

Within one Prototype Tenant, a canonical external Matter reference may identify at most one Matter Proposal or Matter. Because those are deliberately separate resource types and PostgreSQL cannot enforce one ordinary unique constraint across both tables, a narrow `external_matter_reference_claims` table owns the canonical reference as its primary key and points to the current resource kind and UUID.

## Consequences

Matter Proposal creation atomically inserts its claim, confirmation moves the claim to the newly created Matter while consuming the proposal, and discard removes both. The database primary key is authoritative for concurrent races across application replicas. The claim is only a uniqueness reservation: it is not a route identity, persisted Firm or Tenant, generalized identity registry, or assertion that Private Client Graph governs the externally supplied display value.
