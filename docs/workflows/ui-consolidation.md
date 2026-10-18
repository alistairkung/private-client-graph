# Production UI consolidation

This is phase two of the accepted refactor, based on merged authorization PR 159
(`e2450895`). The approved practitioner and landing experience from draft PRs
157/158 (`8ea7ca9b`) now builds inside `web/`, the existing production frontend
package. The separate prototype archive is not imported. The source drafts and
their original checkout remain untouched.

## Routes and build ownership

| Destination | Production surface |
| --- | --- |
| `/` | Approved document montage, scroll-drawn graph and full-source Evidence landing story |
| `/app` | Public persisted Matter and pending-proposal collections |
| `/app/matters/{uuid}` | Accepted Matter graph/list, Sources and Evidence |
| `/app/matter-proposals/{uuid}` | Public pending review; protected confirmation/discard |
| `/app/matter-proposals/new` | Sign-in-gated synthetic PDF intake |
| `/app?example=case-04` | Curated multi-source examples in the same review workspace; never accepted Matter state |
| `/research-results` | Retained published research, original artifact download and recorded comparisons |

The curated query route uses the existing `/app` HTML route, including refresh
and browser history. Existing `/demo*` redirects remain unchanged. Landing,
account and research links use this same origin; no standalone frontend port or
`VITE_PCG_SHOWCASE_URL` is required.

Docker still installs/builds only `web/` and serves `web/dist`. One production
entry chooses lazy route bundles; there is one locale provider/catalogue and
one Motion configuration. The Research Workbench retains its independent
`web/research/` entry and build. No backend, API, domain, database, fixture or
migration changes are part of this consolidation.

## Preserved workflows and coverage

| Capability | Coverage / disposition |
| --- | --- |
| First anonymous visit and seeded Evergreen | `public-access.spec.ts`; actual persistence, exact Evidence, no Google request |
| Full pending Source reading without decisions | `public-access.spec.ts`; real intake then anonymous review and rejected mutation |
| Capability loading, failure and retry | Shared access lifecycle units and real-browser failure/deferred-response recovery |
| Authenticated intake, PDF validation and source bundling | Ported practitioner/API-contract suites; existing Google/model boundaries only are substituted |
| Whole-state confirmation/discard, duplicate references and uncertain outcomes | Ported practitioner/interaction suites plus unchanged Python persistence coverage |
| Graph geometry, all selectable claims, view dragging/keyboard switching | Ported graph/interaction tests and deterministic layout units |
| Exact, source-specific Evidence and smooth source reveal | Source-navigation suite, including five documents, repeated/unrelated Sources and interruption/reduced motion |
| In-tab camera/search/reading/draft memory | Interaction and session-state tests; sign-out/expiry clears session-owned drafts |
| Hillcrest corroboration and trustee replacement | `showcase-sources.spec.ts`, using real curated Case 04/05 in the approved workspace |
| Landing document-to-graph story, boundaries, locale and reduced motion | Ported landing tests; illustrative formats remain labelled product vision |
| Published research and artifact integrity | Retained public-research tests; only landing discovery navigation is adapted |
| Private Research Workbench, replay and authorized substituted execution | Retained research unit, history, execution and substituted-provider browser configurations |

The old production Matter/intake/review/showcase screens and their obsolete
selector tests are replaced by the approved components and behavioral coverage.
Research still uses the old recorded graph/source presentation: these narrowly
needed renderers and deterministic helpers live under
`features/public-research/recorded-review/`, with their protections retained.
They are not a second practitioner application. Font files retain their license
notices. Curated Sources and research artifacts remain backend authoritative.

## Access and product boundaries

The application consumes `GET /api/access` at its practitioner boundary.
Loading/error are distinct from confirmed unavailable sign-in, and a failed
check exposes retry while public reads continue. Only confirmed write eligibility
exposes intake and proposal decisions. Backend allowlist, session expiry, Origin
and CSRF protection remain authoritative. Auth failures on actions refresh access
and clear session-owned drafts; safe read failures do not create auth retry loops.
Busy and uncertain mutations keep their navigation/recovery protections.

Full stored Source text, including pending proposals before confirmation, is
public under ADR 0011. Upload disclosure and synthetic-only confirmation remain
visible. This does not authorize real client data. Curated review has no
confirmation/discard actions and does not claim professional acceptance.

## Launch and verification

Use the existing combined local environment:

```bash
docker compose --profile practitioner up --build application
```

Open `https://localhost:8443/` for the landing, `/app` for public Matters, and
`/research-results` for the publication. Accept the development certificate
warning manually. The existing local Google/model substitutes require no paid
provider credentials. See [application setup](application-setup.md) for migration,
explicit Evergreen seeding and lower-level development.

```bash
uv run pytest
npm --prefix web test
npm --prefix web run build
npm --prefix web run test:research
npm --prefix web run build:research
```

The existing CI browser configurations exercise the combined static production
build against a migrated/seeded disposable PostgreSQL database. Optional recording
specs are excluded from ordinary functional gates. From `web/`, with the same
test database environment, refresh recordings explicitly:

```bash
PCG_RECORD_DEMO=1 PCG_RECORD_LANDING=1 npx playwright test landing-walkthrough.spec.ts --project=desktop
```

Generated captures go to ignored `web/artifacts/`; selected review evidence and
final validation results are linked from the PR. No merge or deployment is
performed by this task.

## Team and task accounting

The lead owns integration, browser tests, documentation, review evidence and PR
delivery. One Sol/medium implementer owns production source; Luna/low supplies a
bounded read-only migration inventory. An on-demand Sol/high reviewer inspects
the complete diff and deletion boundaries. At most two children run concurrently,
with no nested delegation. This uses actual generic-agent model arguments rather
than assuming a role name loads an agent configuration.

The approved Motion choreography is carried forward; this is not another design
exploration. Existing source references and reduced-motion behavior remain in
the source drafts' design records. No premium runtime package is added. Shared
paid application-provider usage is **0/5**. Selected [screenshots and a short browser recording](../artifacts/ui-consolidation/README.md)
are retained for review. Nothing is claimed merge-ready while CI is pending.

## Validation and review

- Full Python suite: **739 passed**; application/research mypy: **92 files clean**.
- Production frontend: **163 unit tests passed**; Research Workbench: **26 passed**.
  TypeScript and both production/research builds passed.
- Combined production browser suite: **82 passed**, with 10 explicit recording or
  viewport-variant skips. This includes anonymous persisted Evergreen review,
  anonymous pending full-Source reading, protected decisions, deferred access
  recovery, authenticated intake, both locales and curated Case 04/05.
- Retained research history: **16 passed**, with its two existing narrow-only skips.
  Offline execution: **27 passed**; authorized substituted-provider execution:
  **6 passed**. No live paid provider is used by these suites.
- Deployment image built and passed a local read-only smoke check: landing,
  Matter/detail/query routes, public research, persisted Evergreen, curated
  catalogue and truthful unavailable-sign-in capability.
- Opt-in landing recording: **1 passed**; the short recording is linked above.

The first browser pass exposed an unsupported new path and a notice-height
regression. The final implementation uses the existing query-capable `/app`
route, closes the phone menu on query navigation and sizes desktop review from
actual available space. Existing geometry assertions remain strict, including a
new curated-workspace bounds assertion. Obsolete landing-only selectors were
removed from retained research tests; landing discovery and all publication
behavior still have coverage. Concurrent local runners initially collided in
Playwright's default artifact directory; isolated output directories avoid that
harness failure without changing Research Workbench code or assertions.

An independent complete-source/deletion review and the lead's final-diff review
found no remaining material readability or scope concern. Review restored the
font license notice, record-specific title ownership and phone query-menu
behavior. No backend, domain, schema, fixture or migration changes are included.
