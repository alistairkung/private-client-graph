# Make synthetic Matter reads public and authenticate actions

The synthetic prototype exposes Matters and pending Matter Proposals, including their full Sources, Canonical Graphs and Evidence, to every reader; only currently allowlisted Google identities may create, upload, analyse, confirm, discard or otherwise change shared state. This supersedes ADR 0004's whole-application authentication boundary while retaining its single-deployment Prototype Tenant and strictly synthetic scope. One real Practitioner Application replaces the separate simulated demo, so public reading and authenticated actions share the same state and workflow.

## Consequences

- Expired, invalid or absent sessions and unavailable authentication do not prevent reading; authenticated actions fail closed and retain origin and CSRF protections.
- Readiness reflects database-backed reading availability. A public capability response reports action eligibility and sign-in availability without identity information.
- The simulated demo and unused legacy showcase-analysis interface are retired. Curated synthetic examples and the research publication remain public; shared pipeline and domain semantics remain unchanged.
- All signed-in uploads are still synthetic or fictional, and their resulting proposals and Matters are publicly readable. Real client information still requires a separate tenancy, authorization and data-handling design.
