# Use the deployment as the synthetic prototype tenant

The Matter Intake prototype is limited to synthetic material and uses one isolated deployment as its tenancy boundary. Named allowlisted practitioners authenticate through Google OIDC at the Practitioner Application boundary, and every allowed practitioner can access all Matter Proposals and Matters in that deployment; the prototype therefore introduces no persisted Firm or Tenant model, per-user ownership, assignments, roles, or per-resource access-control lists.

## Consequences

The Public Showcase remains public, while the entire `/app` subtree and every `/api/matter-proposals*` and `/api/matters*` operation require an authenticated allowlisted identity. This is a deliberately narrow prototype authorization model, not the eventual multi-firm production architecture and not sufficient protection for real confidential client information. Supporting real client data or multiple firms requires a separate design for tenancy, Matter ownership and authorization, provider and data handling, retention, operational security, and other applicable controls rather than incremental relaxation of this boundary.
