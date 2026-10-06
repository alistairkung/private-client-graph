# Private Client Graph

**Integration branch notice (#84):** accepted Matter persistence is relational in
this branch, while Matter Proposals still use JSONB. Do not deploy this intermediate
slice independently; #85 must complete the combined cutover. See the
[maintenance and verification procedure](docs/workflows/canonical-matter-cutover.md).

Private Client Graph is an FTEC5660 MSc AI technical spike exploring whether an LLM can reconstruct **family and trust relationship graphs** from synthetic private-client-style documents while preserving **source provenance** and producing measurable evaluation results.

The project is deliberately benchmark-driven: start with a known answer key, generate realistic source material, extract relationships, build a canonical graph deterministically, and evaluate the result.

## Architecture

```mermaid
flowchart LR
    A["Synthetic source document"] --> B["LLM semantic extraction"]
    B --> C["RelationshipCandidate list"]
    C --> D["Deterministic validation + graph construction"]
    D --> E["CanonicalGraph"]
    E --> F["Deterministic evaluation"]
    G["Ground truth + approved evidence"] --> F
    F --> H["Precision, recall, F1 + provenance diagnostics"]
```

The LLM is responsible for semantic interpretation. Mechanically checkable work such as validation, entity construction, IDs, deduplication, canonicalisation, reference resolution, and scoring remains deterministic.

## Example generated graph

A canonical graph contains entities, relationships, and first-class evidence supporting those relationships:

```json
{
  "entities": [
    {"id": "entity_001", "type": "person", "name": "Alice Example"},
    {"id": "entity_002", "type": "person", "name": "Bob Example"},
    {"id": "entity_003", "type": "trust", "name": "Example Family Trust"}
  ],
  "relationships": [
    {"source": "entity_001", "type": "parent_of", "target": "entity_002", "evidence_ids": ["evidence_001"]},
    {"source": "entity_002", "type": "beneficiary_of", "target": "entity_003", "evidence_ids": ["evidence_002"]}
  ],
  "evidence": [
    {"id": "evidence_001", "document": "source.txt", "supporting_text": "Alice Example confirmed that she is Bob Example's parent."},
    {"id": "evidence_002", "document": "source.txt", "supporting_text": "Bob Example is a beneficiary of the Example Family Trust."}
  ]
}
```

## Current scope

Current entity types:

- `person`
- `trust`

Current relationship types:

- `parent_of`
- `sibling_of`
- `spouse_of`
- `settlor_of`
- `trustee_of`
- `beneficiary_of`

Current constraints:

- synthetic documents only;
- provenance is required for every extracted relationship;
- entity aliases, temporal state, contradictions, and richer graph semantics are deferred until benchmark cases require them.

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run pytest
```

For a live extraction, add `DEEPSEEK_API_KEY` to a local `.env` file:

```bash
uv run python -m private_client_graph.extract
```

Successful runs are saved under the Git-ignored `runs/` directory.

## Run unit tests

```bash
uv run pytest
```

The test suite covers deterministic graph construction, evaluation behaviour, reference integrity, extraction integration boundaries, and Case 01 end-to-end fixtures. CI runs the same suite on pull requests to `main`.

## Evaluation

```bash
uv run python -m private_client_graph.evaluate runs/case_01/<run>.json
```

The benchmark evaluates two dimensions: **relationship quality** and **provenance quality**.

```mermaid
flowchart LR
    P["Predicted graph"] --> E["Evaluation"]
    G["Ground truth"] --> E
    E --> R["Relationship quality"]
    E --> V["Provenance quality"]
    R --> M["Precision / Recall / F1"]
    V --> A["Provenance accuracy"]
```

| Metric | Meaning |
|---|---|
| **TP** | Correct relationship recovered |
| **FP** | Unsupported relationship predicted |
| **FN** | Ground-truth relationship missed |
| **Precision** | Of predicted relationships, how many were correct |
| **Recall** | Of expected relationships, how many were recovered |
| **F1** | Balance of precision and recall |
| **Provenance accuracy** | Of correct relationships, how many included at least one approved evidence span |

Relationship scoring compares semantic graph edges rather than generated graph IDs. Symmetric relationships such as `spouse_of` and `sibling_of` are treated equivalently in either direction. True negatives are not enumerated because the possible universe of non-existent relationships is open-ended.

Provenance is evaluated separately on true-positive relationships. Each ground-truth edge contains one or more human-approved exact evidence spans, and an edge passes provenance when at least one attached predicted evidence span matches one approved span.

## Repository layout

```text
private_client_graph/   Core extraction, graph construction, and evaluation code
cases/                  Synthetic benchmark cases and fixtures
tests/                  Unit and integration tests
docs/                   Project conventions and authoring workflows
runs/                   Local extraction/evaluation outputs (Git ignored)
```

## Design principles

- **LLM for semantics; deterministic code for mechanics.**
- **Answer key first.** Benchmark cases are designed from ground truth before source documents are written.
- **One new difficulty at a time.** New cases should make failures interpretable.
- **Architecture is earned by failures.** Add retries, verification, temporal state, entity resolution, or other complexity only when benchmark results justify it.
- **Canonical facts live in PostgreSQL; representations are derived.** Persist enough canonical Matter state and relationships to reconstruct the current state deterministically from the database. Derived forms such as `CanonicalGraph` are representations of that state and must not contain authoritative facts that exist nowhere else in canonical persistence. A derived representation should gain independent persisted identity only when the domain gives it an independent lifecycle, history, or other semantics that cannot be reconstructed from the underlying state. This principle does not require every domain concept to have its own table; persistence structure remains earned by concrete requirements and invariants.
- **Refactors preserve behaviour.** Deterministic rules are protected by focused tests and required CI checks.

Canonical persistence must also protect the structural and referential invariants that make its facts trustworthy wherever PostgreSQL can naturally enforce them; application validation complements rather than replaces those guarantees. Provenance integrity and Matter isolation are explicit domain requirements. The [agreed canonical-persistence slice](docs/design/canonical-persistence-slice.md) and [ADR 0008](docs/adr/0008-enforce-canonical-provenance-and-aggregate-integrity.md) define the design; accepted Matter facts are relational on this integration branch, with proposal conversion still pending.

The preparatory domain boundary accepts a `CanonicalState` containing explicitly
identified Sources, Entities, Relationships, and source-attributed Evidence.
`single_source_state` adapts today's graph without interpreting document labels as
Source identity; `validate_canonical_state` checks references within that single
aggregate, and `reconstruct_graph` preserves the reviewed IDs, ordering and values.
The legacy graph projection does not carry Source IDs, so source-aware consumers
must retain the state for attribution. This boundary validates rather than repairs
facts: it never resolves aliases, merges names, or normalizes a reviewed graph.
Matter/proposal boundaries and Evergreen use it while retaining existing API
contracts. Accepted Matter reads reconstruct it from relational facts; pending
proposals retain their JSONB storage until #85.

## Documentation

- [Agent instructions](AGENTS.md)
- [Project glossary](GLOSSARY.md)
- [Code style](docs/CODE_STYLE.md)
- [Web application guidelines](docs/WEB_APP_GUIDELINES.md)
- [Case 01 professional-review web-slice decisions](docs/design/case-01-professional-review-web-slice.md)
- [Practitioner Matter workspace slice](docs/design/practitioner-matter-workspace-slice.md)
- [Synthetic case authoring workflow](docs/workflows/synthetic-case-authoring.md)

## Status

Experimental MSc/hackathon research prototype. The current baseline covers a complete source → extraction → canonical graph → evaluation loop for Case 01, with additional cases intended to grow the benchmark and expose the next required capabilities.

## Protected local development

Docker is the only prerequisite for the normal protected-development workflow.
From a clean checkout, run:

```bash
docker compose up --build
```

Open [https://localhost:8443/app](https://localhost:8443/app) and accept the
expected warning for the temporary self-signed development certificate. Follow
the normal sign-in journey; the local environment substitutes a synthetic
allowlisted Google identity while retaining the real callback, secure session,
authorization, application, and PostgreSQL paths. Proposal analysis also uses a
deterministic local model substitute, so Google, DeepSeek, Railway, and external
PostgreSQL credentials are not required.

PostgreSQL 16 is health-checked before the application starts. Startup applies
the Alembic migrations and runs the idempotent Evergreen seed before serving the
built frontend. Database state is stored in the named Compose volume and survives
ordinary stops and restarts. Stop the environment without deleting its data with:

```bash
docker compose down
```

Reset to a clean database by removing the volume:

```bash
docker compose down -v
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

Open http://127.0.0.1:5173. Vite proxies `/api` to the local backend. The fixed
synthetic Case 01 source is available immediately. **Run live analysis** invokes
the model; **Load sample analysis** explicitly loads the ideal-extraction fixture.
Both use the existing graph builder. Select a relationship (by click or keyboard)
to highlight its exact evidence in the persistent source panel.

The practitioner application at `/app` requires an allowlisted Google identity and
opens persisted synthetic Matters from PostgreSQL. Configure authentication and
initialize PostgreSQL as described below before using the practitioner application.
The plain HTTP Vite server above is for the Public Showcase; practitioner use
requires the combined build behind HTTPS at the configured trusted origin.
Both journeys link to each other; direct entry and refresh at `/app` are supported
by the combined deployment. The previous `/api/case-01` routes are removed.

Live showcase analysis is disabled by default, even with `DEEPSEEK_API_KEY`.
Enable it explicitly with the configuration below, in the backend environment or
root `.env`.
The optional backend-only `DEEPSEEK_MODEL` defaults to `deepseek-flash`.
No key is needed for sample analysis. No automatic retries or fallback occur.
Disabled live analysis needs no key and leaves sample analysis available.
An enabled deployment with a missing key fails startup. Non-transient live errors
leave the explicit sample action available; transient provider failures offer
**Retry live analysis** while the global allowance remains available.

Successful live extractions are saved before graph construction to
`runs/case_01/<timestamp>-<unique-id>.json`. The API's execution metadata (or graph
error) identifies that file, including when graph validation fails. For isolated
test environments, `PCG_RUN_DIR` overrides the output directory. Sample analysis
creates no artifact. Evaluate live artifacts offline using the existing command:

```bash
uv run python -m private_client_graph.evaluate runs/case_01/<run>.json
```

The web API exposes `GET /api/showcase/case-01` and `POST /api/showcase/case-01/analysis` with body
`{"mode":"live"}` or `{"mode":"sample"}` only. Analysis returns `execution` and
`graph`; failures return an `error` with stage, safe message, retryability, and
optional run-artifact identifier. Source text and fixture selection remain
backend-authoritative. Raw extraction and benchmark evaluation are never returned
to the professional workspace.

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

Browser tests build the production frontend and serve it through FastAPI,
exercising the real sample path and practitioner navigation/refresh at desktop
and phone widths. The test servers use ports 4173 (disabled production app) and 4174 (enabled
quota journey with only the model boundary substituted). Start each E2E run with
a freshly migrated and seeded disposable database: the quota journey deliberately
consumes its one persisted slot. API tests substitute the provider boundary for deterministic live
coverage; CI never requires model credentials. `npm run build` creates the static
frontend in `web/dist`.

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
failing stops pre-deploy, so the new application is not started.

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
   reference `PC/2026/0142`, and `/` still loads sample analysis. A redeploy must
   leave persisted Matter values unchanged.

The web service writes no Matter data to its filesystem. `/health` runs `SELECT 1`
against PostgreSQL and returns 503 on missing configuration or a failed database
operation; it does not require Evergreen or any Matter row. Schema compatibility
is established by the pre-deploy migration step.

See Railway's [pre-deploy documentation](https://docs.railway.com/deployments/pre-deploy-command)
and [configuration reference](https://docs.railway.com/config-as-code/reference).
No Railway account provisioning is performed by repository code.

### Deliberately enabling public live analysis (#24)

No new Railway variables are needed for the safe default: live analysis is disabled,
while sample analysis and the practitioner application remain available. Migration
`0002` adds the separate `showcase_live_quota` table through the existing
`alembic upgrade head` pre-deploy step; the Matter migration and seed are unchanged.

To enable live analysis, set these variables on the Railway application service
and redeploy:

| Variable | Default | Enabled configuration |
|---|---|---|
| `PCG_SHOWCASE_LIVE_ENABLED` | `false` | Set explicitly to `true` (`true`/`false` only, case insensitive). |
| `PCG_SHOWCASE_LIVE_LIMIT` | Unset | Positive integer provider-attempt allowance, e.g. `10`. |
| `PCG_SHOWCASE_LIVE_WINDOW_SECONDS` | Unset | Positive integer window in seconds, e.g. `86400` for UTC days. |
| `DEEPSEEK_API_KEY` | Unset | Required provider credential. A key alone never enables live analysis. |
| `DEEPSEEK_MODEL` | `deepseek-flash` | Optional backend-only model selection. |
| `DATABASE_URL` | Existing PostgreSQL connection | Use the existing private-network reference. |

Limit and duration must fit positive 32-bit integers. Enabled deployments fail
configuration at startup for missing/invalid quota values, missing credentials,
or missing/non-PostgreSQL database configuration. Disabled deployments do not
require any live settings. Keep all replicas on the same configuration and database.
To turn live analysis off, set `PCG_SHOWCASE_LIVE_ENABLED=false` and redeploy.

Buckets are aligned to Unix epoch UTC using PostgreSQL's clock. Each row contains
only window duration, bucket start, and consumed attempts; it is operational state,
not Matter state. A single `INSERT … ON CONFLICT DO UPDATE … WHERE attempts < limit`
claims a slot under PostgreSQL's row lock and commits before invoking the provider.
Provider, extraction, graph, or artifact failures never refund it. Invalid requests,
unreadable source, and provider setup failures occur before consumption. Database
failures prevent provider invocation while sample analysis remains usable.

The allowance bounds attempts per fixed window, not tokens or currency; two
adjacent windows each have their own allowance. Restarts and additional replicas
share the persisted count. Changing the duration selects a different bucket series;
treat quota changes as an operator budget change, avoid mixed configurations during
rollout, and do not delete quota rows to restart an allowance. Old buckets are
retained; this slice introduces no cleanup job or usage-history endpoint.

`GET /api/showcase/case-01` adds `live_analysis` with `state` (`disabled`,
`available`, `exhausted`, or `unavailable`) and nullable ISO timestamp `resets_at`.
Only exhausted responses include a reset time. The extra `unavailable` state
covers a quota database outage. This response is uncached and advisory: the POST
atomically claims its own slot. POST rejects disabled/unavailable live requests
with 503 and exhausted requests with 429, with safe `error.live_analysis` metadata.
No counters or visitor identifiers are exposed. The UI refreshes availability after
live attempts and invites a reload after the reset time.

After deployment, check sample analysis and `/app` with live disabled. When you
choose to enable it, verify the live action, exhaustion messaging, and continued
sample/Matter access against your chosen allowance. No Railway-specific logic is
part of quota enforcement.

Live run artifacts use the container filesystem and are therefore ephemeral by
default. To retain them, attach a Railway volume at `/app/runs`; the existing
default path will then persist `runs/case_01/*.json` without additional
configuration.

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
exact reconstruction, then removes the legacy graph/source columns. Existing-data
upgrades require the coordinated maintenance procedure above. Alembic alone owns
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
route, and check the Public Showcase sample journey. Do not seed through request
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


## Google authentication for the synthetic prototype (#47)

One deployment is one synthetic Prototype Tenant: every allowlisted Google subject
can read every Matter. Google OIDC is the only identity provider. No user or
session records are persisted, and no schema migration is needed for this feature.
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
fallback. The service validates configuration before reporting ready: missing or
invalid values return `/health` 503 and cannot open private paths. Google validates
the actual client credentials during the authorization-code exchange; configure
and verify a real allowlisted sign-in before release. The combined deployment's
readiness check also requires PostgreSQL connectivity. Public routes remain public,
but a misconfigured combined service must not be released as healthy.

Use the combined frontend build behind HTTPS for practitioner development and
production. `/app` and its entire subtree redirect unauthenticated navigation to
Google; all `/api/matters*` and `/api/matter-proposals*` routes enforce authentication
independently. API clients receive 401 for missing/expired sessions and 403 for a
subject removed from the allowlist. The current environment allowlist is checked on
every private request; applying deployment environment changes may require the
platform to restart the process. Email never grants access.

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
The Public Showcase and sample/live showcase POST behavior remain public and
unchanged. Google login/callback use the OIDC state/nonce mechanisms.

Deterministic tests use synthetic settings and replace only Google's HTTP boundary
with generated signed identities; they do not introduce a production bypass.
Browser servers generate temporary self-signed HTTPS certificates so secure cookies
are exercised on desktop and phone widths. Browser tests keep the real callback,
session, PostgreSQL, graph, and review flows. Their Google authorization endpoint is
mounted only by test code, which is not copied into the deployment image.

## Synthetic Matter Intake (#48, #49)

The authenticated `/app` entry offers **Create Matter** and a separate **Awaiting
confirmation** collection. Upload and analyse produces a durable machine-proposed
graph for review; it does not create a Matter. **Confirm whole graph and create
Matter** copies the reviewed identity, Authoritative Source, and proposed graph
unchanged into a complete Matter, consumes the proposal, and opens the existing
Matter workspace. **Discard intake** asks for destructive confirmation, then removes
the entire proposal and its reference claim without a retained judgment or history.

All allowlisted practitioners share proposals and accepted Matters within this
synthetic deployment. Each submission requires confirmation that its material is
synthetic or fictional. Never submit real personal or client information.

In addition to Google/session and PostgreSQL settings, the combined service now
requires these proposal-analysis settings before `/health` reports ready:

| Variable | Required value |
| --- | --- |
| `PCG_PROPOSAL_ANALYSIS_LIMIT` | Positive 32-bit integer provider attempts per window, e.g. `10` |
| `PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS` | Positive 32-bit integer window duration, e.g. `86400` |
| `DEEPSEEK_API_KEY` | Non-empty provider credential |
| `DEEPSEEK_MODEL` | Optional non-empty model name; defaults to `deepseek-flash` |

Provider credentials/model availability are verified by the provider on invocation;
missing or locally invalid settings fail readiness. There is no unlimited fallback.
These settings are required even when Public Showcase live analysis is disabled.
The proposal allowance is persistent, deployment-wide, and independent of Showcase
quota. Keep every replica on the same configuration and database. Each attempt
commits immediately before provider invocation; downstream failure never refunds
it. There are no automatic model retries. Existing reviews and discard remain
available when the allowance is exhausted.

Run the existing `alembic upgrade head` and explicit Evergreen initialization
before deployment. New immutable migrations add minimal proposal JSONB state,
cross-resource canonical external-reference claims (including existing Matters),
and a separate proposal allowance. Original PDFs, filenames, PDF metadata, raw
extractions, submission confirmations, and review decisions are never persisted.

Acquisition accepts exactly one text-layer PDF: at most 10 MiB, 50 pages, and
100,000 finalized Unicode characters, with at least one non-whitespace character.
Encrypted, malformed, scanned, or textless PDFs are rejected; OCR is unsupported.
Extension and MIME type are advisory. Page text retains its order, Unicode,
spacing, punctuation, and line breaks, with CRLF/CR converted to LF, invalid control
characters removed, and **two LF characters (`\n\n`) between every pair of pages**.
That finalized text goes unchanged to extraction, persistence, and exact Evidence
review. The acquisition file exists only within the active request.

The proposal API provides collection and creation at `/api/matter-proposals` and
GET/DELETE at `/api/matter-proposals/{uuid}`. POST requires multipart fields
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
Start each browser-suite run with a freshly migrated and seeded disposable database;
the quota journey deliberately leaves its persistent allowance exhausted.
