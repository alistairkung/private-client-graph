# Setup and delivery verification

Verified 2026-10-18 (Hong Kong). Setup started on `codex/practitioner-agent-team`
from `9907029e`, after fetching and fast-forwarding local main. Existing untracked
root package/Motion/presentation artifacts were preserved and excluded from the PR.
The user's subsequent instruction expanded setup into a greenfield frontend,
with existing application sources and tests remaining read-only.

## Installed capabilities

- CLI `codex-cli 0.162.1`; official custom-agent docs describe standalone TOML
  under `.codex/agents/` with name, description and developer instructions.
- Generated app-server JSON schema from this exact CLI; initial strict startup
  caught unsupported `mcp_servers.*.type` keys in the pre-existing local config.
  Removed those keys, retaining both hosted URLs. Final strict startup and
  `config/read(cwd=repo)` succeeded: `gpt-6.1-sol` / `high`, two child threads,
  `max_depth=1`, default child `gpt-6-luna` / `low`.
- `model/list` returned GPT-6.1 Sol, GPT-6 Astra, GPT-6 Sol, GPT-6 Luna,
  GPT-5.6 Sol/Terra/Luna. All chosen model/effort combinations are listed as
  supported; current chosen models accept text and images. This establishes
  availability, not exact per-token price or guaranteed effective execution.
- `codex debug prompt-input` showed three total concurrency slots (root + two
  children). It does not expose the custom role catalog or actual child model.
- This desktop chat exposes generic `collaboration.spawn_agent` with explicit
  model/effort and fresh-context controls, but no custom `agent_type` argument.
  Used the documented generic fallback: explicit model/effort, then read the
  named TOML. Automatic custom-role selection has not been observed here.
- Per-role tool scopes and read-only restrictions are instructions. Parent
  sandbox, approvals and MCP connections are inherited. No credit-meter or
  per-role sandbox enforcement is claimed.

## Explorer smoke test

One explorer was spawned with fresh context and explicitly requested
`gpt-6-luna`, effort `low`. It read `pcg_explorer.toml`, repository guidance and
workflow, used focused shell reads, and returned practitioner entry points,
API/auth/CSRF contracts and a parity inventory. A bounded follow-up in the same
context found graph controls, account/locale details, PDF limits and the fictional
source prompt. It made no changes, recursive delegations or provider calls.

Requested specialist/instructions/tool access are observed through tool actions
and the returned report. The child cannot inspect its effective model/effort and
the spawn result does not expose it; requested settings are not proof of actual
execution settings. At most two children were active at once during delivery.
The current chat predates the new config; the CLI's depth/thread enforcement is
verified by effective config, not by deliberately launching excess paid agents.

## Design and Motion tools

The existing local frontend-design and Impeccable skills were read. Impeccable
context ran successfully for the UX/implementation roles; it reported pre-existing
DESIGN sidecar drift, which was left untouched. Root PRODUCT.md, DESIGN.md and
`.impeccable/` were not rewritten.

Motion+ `search-motion-source` successfully returned premium Accordion references.
The motion specialist additionally read full Modal: Shared layout and Family-style
Dialog source resources. See `motion-spec.md` for their URLs and adaptations.
No key was added to the repository, no account transitions were saved and no
premium runtime package was needed. Runtime MotionScore profiling was not run;
its dedicated audit tooling is not exposed in this session.

Browser capability: CUA browser/tab inspection and screenshots, plus the new
app's Playwright Chromium tests, traces, screenshots, reduced-motion emulation
and video capture. Actual UI evidence and parity results are recorded in
`practitioner-next/README.md` and `parity.md`.

## Shared usage ledger

- Setup smoke: one Luna/low explorer; one bounded follow-up reused its context.
- Direction: one Sol/medium UX role, bounded to one selected direction.
- Motion: one Sol/medium role; one docs concept search, two source lookups,
  two actual premium resource reads, plus root's one setup source lookup.
- Implementation: one Sol/medium writer; no competing implementation.
- Paid application-provider invocations: **0 of 5**. Deterministic local Google
  and extraction substitutes are used for integration and browser testing.
- Codex account usage is separate; no precise credit cost is observable here.
- Visual cycles and final reviewer results are appended below after validation.

## Initial delivery validation and review

- Required `uv run pytest` with disposable PostgreSQL: **752 passed** (104.61s),
  including persistence coverage; no tests skipped for a missing database.
- New frontend: typecheck and production build passed; **33 unit tests passed**.
  Prettier check passed across source, tests and configuration. npm audit reported
  zero vulnerabilities. Vite retains a nonblocking bundle-size warning
  (approximately 637 kB minified / 206 kB gzip for the main bundle) and dependency
  `use client` directive warnings; no runtime performance certification is claimed.
- Final real-backend Chromium pass: **18 parity tests plus one opt-in recording
  passed** in 19.9s across desktop (1512×982) and phone (390×844). The extra phone
  recording was deliberately skipped; it is not a missing functional check.
- Live Chrome inspection succeeded after the user accepted the local certificate.
  Verified Matter navigation, graph relationship selection, exact source highlight
  and focus into the selected Evidence. The Codex embedded browser initially
  rejected the self-signed certificate; no automated interstitial bypass was used.
- Three bounded visual passes: initial screenshots/QA identified tiny phone graph
  labels and a source-footer overlay; correction made phone list the default,
  compacted desktop geometry and restored the footer to document flow. Live
  confirmation also found handle wrappers consuming label space, fixed with
  non-layout fragments. The last batch added deterministic obstacle avoidance
  and regression coverage; no further aesthetic refinement was started.
- Final engineering review covered the complete staged diff. It found uncertain
  decision errors being cleared by modal dismissal and reciprocal edges sharing
  a curve. Errors now remain in the workspace and block both mutations when
  needed; connector orientation/obstacle routing has focused regression tests.
- Code Quality Review: extracted Evidence, relationship-list and decision
  components, formatted JSX/styles and reviewed all final changed paths for
  boundaries, readability, accidental changes and debugging residue. No material
  readability concern was deliberately retained. Finite routing may still have
  connector collisions on larger/dense graphs; the complete searchable list,
  pan/zoom and fit controls remain available.
- Existing `web/`, backend/domain/database, existing tests, deployment and existing
  CI workflow files have no diff. A separate new Practitioner Next CI workflow
  runs new-app checks using PostgreSQL and the existing synthetic boundaries.

Additional usage: one Luna/low visual reviewer and one Sol/high engineering
reviewer, with a bounded engineering follow-up; one implementer context reused
for the review fixes. At most two child agents active concurrently, no recursive
spawns and **zero paid application-provider calls** throughout. The walkthrough
and final screenshots are in `practitioner-next/artifacts/`.

## Graph correction after practitioner feedback

The user identified the new graph as a regression. Compared the original live
Evergreen drawing with the new application, then reused one Sol/medium
implementer, one Sol/medium UX assessment, one Luna/low mechanical assessment and
one Sol/high engineering reviewer. At most two children ran concurrently; no
recursive delegation or paid application-provider invocation occurred.

- Replaced the quadratic connector pipeline with local presentation modules for
  relationship metadata, Trust/family placement, node geometry and general graph
  layout. Original `web/` files were read-only references; no cross-app imports.
- Restored spouse alignment and family context around a full Trust triangle.
  Separate canonical routes retain parent direction, distinct multiple roles
  and reciprocal claims. Node, caption, route-point and connector-label extents
  all participate in Fit graph. Selection/locale preserve the camera; ordinary
  page scrolling no longer changes zoom.
- Actual desktop inspection found beneficiary routes crossing the Trust caption;
  bottom-role routes now clear the caption through side corridors. The final
  desktop and phone screenshots were visually inspected after this correction.
- Engineering review found unbounded names escaping fixed footprints. Bounded
  two-line diagram previews now retain full names in DOM text, title, accessible
  names and the existing inspector/List. The Trust footprint reserves the gap
  and both caption lines. Focused regression tests cover this policy.
- Real-backend browser checks exposed stale graph-label DOM references during
  return from Evidence. Focus now resolves the selected canonical relationship
  in its originating view after the current label portal mounts.
- Impeccable's independent baseline layout detector returned no source findings;
  it cannot validate rendered graph routing. One attempted new-app baseline
  screenshot was blank and was excluded from delivered evidence. The original
  graph reference and actual corrected screenshots are retained.
- Final required `uv run pytest`: **752 passed** in 110.50s with disposable
  PostgreSQL. New frontend: **41 unit tests**, typecheck and production build
  passed. Final browser run: **20 parity checks plus one refreshed recording
  passed** in 21.3s; the extra phone recording was intentionally skipped.
- Code Quality Review: reviewed the complete graph follow-up diff and all new
  modules against repository boundaries. Removed superseded routing code and
  kept layout, geometry, rendering and Evidence focus responsibilities clear.
  Finite route candidates remain a deliberate limit for unusually dense graphs;
  the complete relationship list remains available. Build warning: approximately
  645 kB minified / 209 kB gzip main bundle. No runtime performance claim.

The original frontend, backend, database, domain contracts, original tests,
deployment and existing CI remain unchanged. Refreshed screenshots and the
walkthrough live in `practitioner-next/artifacts/`.
