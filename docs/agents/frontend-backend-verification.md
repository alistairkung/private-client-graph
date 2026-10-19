# Frontend and Backend team establishment

Base: `a725cfdd`, 2026-10-19. This task adds team contracts/roles and discovery;
it implements no product feature, test migration or new runtime mechanism. QA
PR #169 is independent, and closed unmerged practitioner PR #157 is not imported.
The shared [runtime procedure](runtime-verification.md) remains authoritative.

## Allocation and smoke plan

The root acts as the teams' orchestrator. Before dispatch, it inspected the
installed Codex CLI `0.162.1`, refreshed its catalogue with `codex debug models`
and checked the active collaboration tool schema. Luna supports Low/Medium and
Sol supports High on this surface. The catalogue describes Luna as economical
and Sol as a coding workhorse; numeric prices are not exposed, so these choices
are not claimed as a measured price minimum. Each child receives the selected
role's actual `developer_instructions`, exact read-only scope and a stopping rule.

| Task | Selected specialist | Requested model / effort | Workload and rationale |
| --- | --- | --- | --- |
| Find frontend request/state ownership and propose a Backend handoff | `frontend_engineer` | `gpt-6-luna` / Low | Bounded source discovery with low ambiguity; no new UI/creative decisions or architecture change |
| Trace the matching server admission/application boundary | `backend_application_engineer` | `gpt-6-luna` / Medium | Bounded exploration requiring careful auth/orchestration reasoning; use the existing contract, not new semantics |
| Independent complete-diff governance review after integration | `engineering_standards_reviewer` | `gpt-6.1-sol` / High | Consequential ownership and protected-boundary review; independent of authors, after smoke integration |

At most two children run concurrently. The two discovery tasks have disjoint
sources and share their results through the root. The reviewer runs later; no
recursive delegation or additional team hierarchy is authorised. Leads choose
capability again for future tasks; this table is a dated task record, not a role
configuration or standing assignment.

## Observability and budget

On this desktop surface, spawn accepts explicit `model`, `reasoning_effort` and
`fork_turns = "none"`; it has no native role selector. The supported prompt
fallback supplies role instructions explicitly. Status/results expose task IDs
and outputs, not independent effective model/effort metadata. Requested settings,
accepted spawns and child self-reports do not establish effective settings or
native TOML loading. File-based defaults also do not change this tool's capacity;
the root enforces the two-child limit and no-recursion rule.

Shared task allowance: five application-provider attempts; **zero attempted**.
Smoke/review coordination uses the hosting runtime; its internal request count
and billing are unobservable and are not represented as measured provider calls.
No live extraction, evaluation experiment or separate paid CLI inference is
needed for this configuration task. Remaining allowance is shared, not per team.

## Results

- `frontend_team_smoke` completed via the prompt fallback with requested
  `gpt-6-luna` / `low`. It identified transport/error parsing in
  `web/src/shared/api.ts`, the browser `ServiceError` contract, Intake's UI state
  and supporting feature/client tests, then returned a Backend handoff.
- `backend_team_smoke` completed with requested `gpt-6-luna` / `medium`. It traced
  POST `/api/matter-proposals` through authentication/origin/CSRF middleware and
  the application workflow, returning the matching structured proposal-error
  envelope and existing API/security test pointers.
- The root checked both source mappings against the existing code. These tasks
  demonstrate selecting a specialist, allocating model and effort at delegation,
  supplying actual role instructions and getting usable cross-team findings.
  Both stayed read-only, with no recursive delegation or product changes.
- Effective child settings and native TOML execution remain unverified; this
  surface exposes neither a named-role selector nor independent configuration
  metadata. No accepted request or self-report was counted as verification.

Final validation and independent review are recorded in the PR handoff. Existing
shared governance tests cover registration, required fields, references and the
absence of fixed role models; no additional validator or redundant role-count
assertions were introduced.
