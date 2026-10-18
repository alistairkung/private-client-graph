# Application setup and deployment

Run the synthetic practitioner application locally, configure its production
services, and verify database and authentication behavior. All commands run from
the repository root unless a step explicitly changes directory.

For a first run, use the Docker environment below. Public reading requires
PostgreSQL. Allowlisted actions additionally require Google authentication;
analysis also requires the proposal-analysis settings in this guide. Use only
synthetic or fictional material. Full Source text, proposals and Matters are
publicly readable, including signed-in submissions. See ADR 0011.

The landing, practitioner workspace and research publication share the production
`web/` package. See [UI consolidation](ui-consolidation.md) for route ownership,
preserved workflows and recording instructions. No separate `practitioner-next/`
development server or cross-origin showcase setting is needed.

Existing deployments moving from legacy canonical storage require a coordinated
maintenance window. Follow the [cutover and recovery procedure](canonical-matter-cutover.md)
before activating that release.

- [Protected local development](#protected-local-development)
- [Lower-level local setup and web checks](#lower-level-local-professional-review-setup)
- [Railway deployment](#deploy-to-railway)
- [PostgreSQL initialization and integration tests](#postgresql-initialization-and-integration-tests)
- [Google authentication](#google-authentication)
- [Synthetic Matter Intake](#synthetic-matter-intake)
- [Canonical persistence](#canonical-persistence)

## Protected local development

Docker is the only prerequisite for the normal protected-development workflow.
From a clean checkout, run:

```bash
docker compose --profile practitioner up --build application
```

Open [https://localhost:8443/app](https://localhost:8443/app) and accept the
expected warning for the temporary self-signed development certificate. Read
Matters and pending proposals without signing in. Sign in before creating,
uploading, analysing, confirming or discarding; the local environment substitutes
a synthetic allowlisted Google identity while retaining the real callback, secure session,
authorization, application, and PostgreSQL paths. Proposal analysis also uses a
deterministic local model substitute, so Google, DeepSeek, Railway, and external
PostgreSQL credentials are not required.

For a deterministic multi-document walkthrough, select
`tests/fixtures/synthetic-proposal.pdf` and
`tests/fixtures/multiple-role-proposal.pdf`. The development-only adapter supplies
known candidates for each Source, retaining its ID, title, order and exact quotes.
It replaces external dispatch before model construction or paid authorization;
no provider authority or shared paid-call ledger is needed. Authentication, PDF
validation, graph construction, confirmation and PostgreSQL persistence remain real.
The fixtures demonstrate workflow, not extraction quality on arbitrary documents.

PostgreSQL 16 is health-checked before the application starts. Startup applies
the Alembic migrations and runs the idempotent Evergreen seed before serving the
built frontend. Database state is stored in the named Compose volume and survives
ordinary stops and restarts. Stop the environment without deleting its data with:

```bash
docker compose --profile practitioner down
```

Reset to a clean database by removing the volume:

```bash
docker compose --profile practitioner down -v
```

This development-only, synthetically authenticated environment is strictly for
synthetic or fictional material. Never enter real client or personal data. The
synthetic providers live
only in the development image and cannot be enabled through production application
configuration.

## Lower-level local professional-review setup

Requires Python 3.11+, uv, and Node.js 22.12+ (or 24+). Run from the repository root:

```bash
uv sync --locked
uv run uvicorn private_client_graph.api.app:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd web
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to the local backend. The
Public Showcase reads curated synthetic examples through
`GET /api/showcase/cases` and `GET /api/showcase/cases/{case_id}`. Select a
relationship to inspect its exact supporting Evidence; opening an example never
runs analysis or consumes a provider allowance.

The Practitioner Application at `/app` reads persisted synthetic Matters and
pending Matter Proposals from PostgreSQL. Initialize the database as described
below. No session is needed for full Source text, graphs or Evidence. Reads
remain available with expired or invalid sessions and unavailable authentication.
`GET /api/access` returns only `can_write` and `sign_in_available`, with no
identity information; this advises the UI and never authorizes an action itself.

To create, upload, analyse, confirm or discard, configure Google authentication
and use the combined build behind HTTPS at the exact trusted origin. The current
allowlist, absolute session expiry, CSRF and Origin checks are enforced again by
the backend. Provider credentials and the existing allowance/task authority are
additional gates for analysis. Failed writes never fall back to anonymous access.

The separate simulated `/demo` journey is retired; its old links redirect to
`/app`. Legacy `/api/showcase/case-01` and its live/sample analysis endpoint are
retired too. Curated example fixtures, research publication and the shared
analysis/domain pipeline remain available through their appropriate consumers.

### Web checks

```bash
uv run pytest
uv run mypy private_client_graph/application private_client_graph/api private_client_graph/persistence --follow-imports=silent
cd web
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests build the production frontend and serve it through FastAPI at
HTTPS port 4173. They exercise anonymous reading, explicit sign-in, protected
proposal actions and sign-out at desktop and phone widths. Use a freshly migrated
and seeded disposable database. Only existing Google/model boundaries are
substituted; API orchestration, PDF acquisition, graph construction and
PostgreSQL persistence remain real. CI never needs live provider credentials.
`npm run build` creates the static frontend in `web/dist`.

## Deploy to Railway

The root `Dockerfile` builds the React frontend and serves it with the FastAPI
application as one Railway service. The process listens on Railway's injected
`PORT`; `GET /health` is the deployment readiness endpoint.

Keep the existing GitHub → Railway service and repository root. The committed
`railway.toml` retains the Dockerfile build and configures `/health` plus this
pre-deploy command:

```bash
alembic upgrade head && python -m private_client_graph.persistence.seeds.evergreen
```

The image includes Alembic, migrations, the PostgreSQL driver, and seed inputs.
Ordinary Uvicorn startup performs neither migration nor seeding. Either command
failing stops pre-deploy, so the new application is not started. This hook does
not stop an old replica: upgrades from legacy canonical storage must first follow
the [maintenance procedure](canonical-matter-cutover.md).

**Manual Railway setup before deploying this feature:**

1. Add a PostgreSQL service in the same Railway project/environment.
2. Set the application service's `DATABASE_URL` to the PostgreSQL service's private
   connection reference, normally `${{Postgres.DATABASE_URL}}` (substitute the
   actual service name). Verify its host is the private `*.railway.internal`
   address, not a public proxy URL.
3. Confirm Railway detects root `railway.toml` and displays the pre-deploy command
   and `/health` healthcheck. Keep the existing GitHub deployment source and
   Dockerfile start command. Apply these variables before deploying the PR.
4. After deployment, confirm `/health` returns 200, `/app` shows Evergreen with
   reference `PC/2026/0142`, and `/` still opens curated examples. A redeploy must
   leave persisted Matter values unchanged.

The web service writes no Matter data to its filesystem. `/health` runs `SELECT 1`
against PostgreSQL and returns 503 on missing configuration or a failed database
operation; it does not require Evergreen or any Matter row. Schema compatibility
is established by the pre-deploy migration step.

See Railway's [pre-deploy documentation](https://docs.railway.com/deployments/pre-deploy-command)
and [configuration reference](https://docs.railway.com/config-as-code/reference).
No Railway account provisioning is performed by repository code.

### Public reading and action availability

The public application does not execute showcase analysis. Its curated fixtures
and the research publication remain read-only. Old `PCG_SHOWCASE_LIVE_*` settings
no longer enable a public analysis route. Historical quota migrations remain
immutable; this refactor changes no database schema or stored facts.

`GET /health` checks database-backed read availability. Missing or invalid Google
or proposal-analysis configuration leaves reads usable, while protected actions
return a safe failure. Configure and verify sign-in and the analysis settings
before expecting writes to work; a healthy reading service alone does not certify
those external integrations.

## PostgreSQL initialization and integration tests

Use PostgreSQL 16 (also used in CI). There is no SQLite implementation. For example,
start a disposable local server with Docker:

```bash
docker run --rm --name pcg-postgres -e POSTGRES_USER=pcg \
  -e POSTGRES_PASSWORD=test-only -e POSTGRES_DB=pcg_e2e \
  -p 5432:5432 -d postgres:16
export DATABASE_URL='postgresql://pcg:test-only@127.0.0.1:5432/pcg_e2e'
uv run alembic upgrade head
uv run python -m private_client_graph.persistence.seeds.evergreen
```

The ordinary commands also work with any explicitly configured PostgreSQL server.
The original migration `0001` creates `matters`: UUID primary key, non-null text columns for
external reference, title, source title and text, and a non-null JSONB
`current_graph`. Migration `0005` converts those accepted facts to constrained,
owner-scoped Source, Entity, Evidence, Relationship and support records, verifies
exact reconstruction, then removes the legacy graph/source columns. Migration
`0006` does the same for pending proposals. A single upgrade from `0004` to head
runs both conversions in one transaction. Existing-data
upgrades require the coordinated [maintenance procedure](canonical-matter-cutover.md). Alembic alone owns
schema evolution. Never edit a merged/applied migration; add a new one.

The explicit seed builds the graph from Case 01 source/extraction inputs through
the existing deterministic graph builder and validates the graph and verbatim
Evidence. It inserts UUID `ff985caf-60c5-4e65-a238-f3c26381c369` only if absent.
A PostgreSQL conflict guard also protects concurrent seeds. An existing row is
left wholly unchanged, even if seed inputs later change or disappear. Fixture
files are never consulted by Matter listing; the list API selects only the three
summary columns. `GET /api/matters/{internal_uuid}` returns Matter identity, the embedded
Authoritative Source (`title`, `text`), and `current_graph`. The application
reconstructs and validates relational state through the canonical domain boundary;
the database rejects broken provenance and references. Invalid or unsupported
stored state still produces a safe 503 response; missing Matters return 404 and
invalid UUIDs return 422. Reads never consult fixtures or invoke extraction.

Opening a ledger row navigates directly to `/app/matters/{internal_uuid}`, which
also supports direct entry and refresh in the combined deployment. The shared
review workspace consumes either journey's source and graph, preserving
relationship selection and exact Evidence highlighting. In both the Public
Showcase and practitioner presentation, Trust entities are triangles. A single
Trust anchors a deterministic relationship-led layout: family relationships stay
close to their Person endpoints and Trust relationships use separate approaches
with offset annotation labels. Position still carries no legal significance.
Zero-Trust and multiple-Trust graphs retain the general layout, with Trusts still
rendered as triangles.

For the #23 deployment, no new Railway service, variable, or migration is needed.
Confirm the new deployment uses the committed pre-deploy command above. The first
#22 deployment may predate Railway detecting that command; the new deployment
must run the normal idempotent seed before startup. After deployment, verify
`/app` → Evergreen → relationship selection → source Evidence, refresh the Matter
route, and check the curated Public Showcase. Do not seed through request
handlers or use fixture fallbacks.

For the complete test suite, use a disposable server with a role allowed to create
databases:

```bash
export TEST_DATABASE_URL="$DATABASE_URL"
uv run pytest
uv run mypy private_client_graph/application private_client_graph/api private_client_graph/persistence --follow-imports=silent
cd web
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Each persistence test creates a uniquely named empty PostgreSQL database, applies
the entire Alembic chain using the real CLI, and drops it on completion. It never
resets the database named by `TEST_DATABASE_URL`. Without that variable, persistence
tests report explicit skips; CI always supplies it using a PostgreSQL 16 service.
Existing domain tests remain database-free. Browser tests require `DATABASE_URL`
and an explicitly migrated/seeded disposable database; CI initializes a separate
`pcg_e2e` database before running the real PostgreSQL → API → ledger journey and
the existing showcase journey at desktop and phone widths. No live model calls
are made by CI.


## Google authentication

One deployment is one synthetic Prototype Tenant: everyone can read all Matters
and pending proposals; only current allowlisted Google subjects can change them.
Google OIDC is the only identity provider. No user or session records are
persisted, and no schema migration is needed for this feature.
The application remains unsuitable for real confidential client information.

Before deploying, configure a Google OAuth **Web application** client and register
exactly `https://YOUR_HOST/auth/callback` as an authorized redirect URI. Set these
backend variables in Railway (or your local environment); never commit credentials:

| Variable | Required value |
| --- | --- |
| `PCG_GOOGLE_CLIENT_ID` | Google web client ID ending in `.apps.googleusercontent.com` |
| `PCG_GOOGLE_CLIENT_SECRET` | Secret for that Google client |
| `PCG_GOOGLE_SUB_ALLOWLIST` | Non-empty comma-separated stable Google `sub` identifiers, not email addresses |
| `PCG_SESSION_SECRET` | Independently generated random secret, at least 32 characters; for example generate locally with `openssl rand -hex 32` |
| `PCG_TRUSTED_ORIGIN` | Exact public HTTPS origin, e.g. `https://YOUR_HOST`, without a trailing slash or path |
| `PCG_SESSION_SECONDS` | Optional absolute session lifetime, 60–3600 seconds; default 1800 |

Obtain each subject from a Google-validated identity through your deployment's
controlled enrollment process. There is no public enrollment or email-based access
fallback. Invalid authentication configuration closes sign-in and all protected
actions without preventing public reading. The capability endpoint reports
`sign_in_available: false` and `can_write: false`; readiness still requires
PostgreSQL connectivity. Google validates actual client credentials during the
authorization-code exchange, so verify a real allowlisted sign-in before relying
on authenticated actions.

Use the combined frontend build behind HTTPS for authenticated development and
production. `/app`, `/api/matters*` and `/api/matter-proposals*` permit reads
without a session. Their state-changing operations independently enforce
allowlisting, session expiry, Origin and CSRF. Missing/expired sessions cannot
write; removed subjects cannot write either. Configuration failure fails closed.
The current allowlist is checked for every action; applying deployment environment
changes may require a platform restart. Email never grants access.

Authlib validates Google identity signature, issuer, audience, expiry and nonce;
OAuth state and PKCE protect the code flow. Google tokens are discarded after the
callback. The backend signs a Secure, HTTP-only, SameSite=Lax `__Host-pcg-session`
cookie containing only the subject and an absolute expiry. Activity cannot extend
that deadline. Sign out clears the browser session; without a session store it
does not revoke a separately copied cookie before expiry. Removing a subject from
the allowlist or rotating the session secret invalidates its access.

Practitioner writes, including `POST /auth/logout`, require the exact configured
`Origin` and the signed double-submit CSRF cookie in the `x-csrftoken` header.
The readable `__Host-pcg-csrf` cookie is a CSRF value, never an identity token.
Public reading requires no CSRF token or login. The legacy showcase analysis
POST is removed. Google login/callback use OIDC state/nonce mechanisms.

Deterministic tests use synthetic settings and replace only Google's HTTP boundary
with generated signed identities; they do not introduce a production bypass.
Browser servers generate temporary self-signed HTTPS certificates so secure cookies
are exercised on desktop and phone widths. Browser tests keep the real callback,
session, PostgreSQL, graph, and review flows. Their Google authorization endpoint is
mounted only by test code, which is not copied into the deployment image.

## Synthetic Matter Intake

The public `/app` entry shows accepted Matters and an **Awaiting confirmation**
collection. **Create Matter**, confirmation and discard require allowlisted
sign-in. Upload and analyse produces a durable machine-proposed graph for review;
it does not create a Matter. **Confirm whole graph and create
Matter** copies the reviewed identity, Authoritative Source, and proposed graph
unchanged into a complete Matter, consumes the proposal, and opens the existing
Matter workspace. **Discard intake** asks for destructive confirmation, then removes
the entire proposal and its reference claim without a retained judgment or history.

All allowlisted practitioners share proposals and accepted Matters within this
synthetic deployment. Each submission requires confirmation that its material is
synthetic or fictional. Never submit real personal or client information.

In addition to Google/session and PostgreSQL settings, the combined service now
requires these proposal-analysis settings before analysis can execute:

| Variable | Required value |
| --- | --- |
| `PCG_PROPOSAL_ANALYSIS_LIMIT` | Positive 32-bit integer provider attempts per window, e.g. `10` |
| `PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS` | Positive 32-bit integer window duration, e.g. `86400` |
| `DEEPSEEK_API_KEY` | Non-empty provider credential |
| `DEEPSEEK_MODEL` | Optional non-empty model name; defaults to `deepseek-flash` |

Provider dispatch also requires `PCG_PROVIDER_TASK_ROOT` pointing to the existing
shared task artifact root and `PCG_PROVIDER_AUTHORIZATION` naming its explicitly
approved external invocation. Missing, inconsistent or exhausted authority blocks
dispatch; application requests never initialize a task or grant approval. The
application rate quota remains a separate gate. Every reserved dispatch, including
failed or interrupted attempts, remains charged in the same ledger as research.

Provider credentials/model availability are verified by the provider on invocation;
missing or locally invalid settings block analysis. There is no unlimited
fallback. Public reading remains available. The proposal allowance is persistent
and deployment-wide. Keep every replica on the same configuration and database.
Each attempt commits immediately before provider invocation; downstream failure never refunds
it. There are no automatic model retries. Existing reviews and discard remain
available when the allowance is exhausted.

Run the existing `alembic upgrade head` and explicit Evergreen initialization
during the coordinated cutover. Historical migrations introduced proposal JSONB
state, cross-resource canonical external-reference claims, and a separate proposal
allowance. Migration `0006` converts stored proposals and removes their legacy
graph/source columns; current proposal state uses only constrained relational facts. Original PDFs, filenames, PDF metadata, raw
extractions, submission confirmations, and review decisions are never persisted.

The single-PDF compatibility endpoint accepts exactly one text-layer PDF: at most 10 MiB, 50 pages, and
100,000 finalized Unicode characters, with at least one non-whitespace character.
Encrypted, malformed, scanned, or textless PDFs are rejected; OCR is unsupported.
Extension and MIME type are advisory. Page text retains its order, Unicode,
spacing, punctuation, and line breaks, with CRLF/CR converted to LF, invalid control
characters removed, and **two LF characters (`\n\n`) between every pair of pages**.
That finalized text goes unchanged to extraction, persistence, and exact Evidence
review. The acquisition file exists only within the active request.

The single-PDF compatibility form described here remains supported alongside the
ordered multi-Source intake form. The latter accepts a `sources` JSON array of
distinct Source IDs and titles, with matching `pdfs` fields in the same order.
Supply one to five Sources, with at most 10 MiB of PDFs and 100,000 extracted
characters combined. The per-PDF validation rules above still apply.

The proposal API provides collection and creation at `/api/matter-proposals` and
GET/DELETE at `/api/matter-proposals/{uuid}`. The compatibility POST requires multipart fields
`external_reference`, `matter_title`, `source_title`, `synthetic_confirmation=true`,
and one file field `pdf`, plus the existing trusted Origin and CSRF header. A
successful POST returns 201, the full proposal, and its API `Location`. Duplicate
409 responses identify the existing resource kind, UUID, and API location. Every
retry resolves the trimmed, case-folded external reference before another model
attempt, including recovery after an unknown commit/response outcome. No source,
raw extraction, or error details are retained for failed attempts.

`POST /api/matters` is the only runtime Matter-creation operation and accepts
exactly one JSON field, `matter_proposal_id`. It locks and revalidates the proposal,
generates a new Matter UUID, inserts the complete Matter, transfers the external-
reference claim, and consumes the proposal in one transaction. Success returns the
Matter with 201 and its API `Location`; the browser opens the corresponding Matter
workspace without rerunning extraction or graph construction. A known rollback
leaves the proposal reviewable. A missing proposal or lost commit response is not
treated as replay success: the outcome is reported as unknown and the practitioner
is directed to the Matter Ledger.

Deterministic tests substitute Google and the model boundary while keeping real
PDF acquisition, graph construction, PostgreSQL, and browser review, confirmation,
and discard. The
committed synthetic PDF fixture lives under `tests/fixtures/`; it is separate from
benchmark ground truth. Use the full test commands above with PostgreSQL enabled.
Start each browser-suite run with a freshly migrated and seeded disposable database.
Tests may create and consume synthetic proposals and Matters.


## Canonical persistence

PostgreSQL enforces the structural and referential invariants of canonical
facts wherever it can express those rules. Application validation complements
these guarantees. Accepted Matters and pending Matter Proposals use separate
relational facts with equivalent provenance integrity and isolation requirements.
See the [canonical persistence design](../design/canonical-persistence-slice.md)
and [ADR 0008](../adr/0008-enforce-canonical-provenance-and-aggregate-integrity.md).

The canonical domain boundary accepts a `CanonicalState` containing explicitly
identified Sources, Entities, Relationships, and source-attributed Evidence.
`single_source_state` adapts today's graph without interpreting document labels as
Source identity; `validate_canonical_state` checks references within that single
aggregate, and `reconstruct_graph` preserves the reviewed IDs, ordering and values.
The legacy graph projection does not carry Source IDs, so source-aware consumers
must retain the state for attribution. This boundary validates rather than repairs
facts: it never resolves aliases, merges names, or normalizes a reviewed graph.
Matter/proposal boundaries and Evergreen use it while retaining existing API
contracts. Both Matter and proposal reads reconstruct it from relational facts. Confirmation
copies the complete reviewed state unchanged, transfers the reference claim, and
consumes the proposal atomically.
