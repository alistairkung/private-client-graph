# Practitioner Next

An independent practitioner frontend for Private Client Graph. **Working Atlas**
puts the relationship drawing and exact source Evidence alongside each other.
The original `web/` app and production deployment remain unchanged.

This frontend consumes the existing Matter and Matter Proposal APIs. It supports
only the existing synthetic prototype workflows; never enter real client or
personal information. No live model call is needed for the local setup below.

## Local launch

Prerequisites: Node.js 22+, the repository's `uv` environment, Docker (or a
separate disposable PostgreSQL server), and OpenSSL. Run from the repository
root. Use a new disposable database, separate from the existing application.

```sh
uv sync --locked
npm ci --prefix practitioner-next

docker run --rm -d --name pcg-next-db \
  -p 127.0.0.1:55440:5432 \
  -e POSTGRES_USER=pcg -e POSTGRES_PASSWORD=local-only \
  -e POSTGRES_DB=pcg_next postgres:16
```

After PostgreSQL is ready, migrate and seed that disposable database using the
unchanged repository migrations and synthetic seed:

```sh
export DATABASE_URL=postgresql://pcg:local-only@127.0.0.1:55440/pcg_next
uv run alembic upgrade head
uv run python -m private_client_graph.persistence.seeds.evergreen
npm --prefix practitioner-next run backend:synthetic
```

In another terminal:

```sh
npm --prefix practitioner-next run dev
```

Open **https://127.0.0.1:5443/app**. The local certificate is self-signed; accept it
in your development browser if prompted. The sign-in button follows the existing
OIDC/session flow using the repository's synthetic Google boundary. The backend
runs on loopback port 8001 and the new frontend on 5443; neither replaces the
original application on 8443. The synthetic launcher reuses
`local_development.server.create_local_app`, substituting only Google/model
boundaries, while leaving API, graph construction and persistence code intact.

The copied development identity/session settings are strictly local. This
launcher is not a deployment configuration. Stop the two servers with Ctrl-C;
`docker stop pcg-next-db` removes the disposable container/database.

## Existing backend integration

All API calls are same-origin and retain session cookies, trusted Origin and
`__Host-pcg-csrf` headers for mutations. Vite proxies `/api`, `/auth` and the
existing local synthetic Google route; it does not rewrite trusted origins or
weaken authentication. The backend's configured trusted origin and OAuth callback
must match `https://127.0.0.1:5443` for this local front door.

For another authorised local backend, set `PCG_BACKEND_URL` when starting Vite
(default `http://127.0.0.1:8001`). It must already accept the new frontend origin
and existing auth callback flow. Cross-origin cookie/CORS shortcuts are not
implemented. This PR does not reconfigure a running or deployed backend.

The Public Showcase link defaults to the existing local app at
`https://localhost:8443/`. Set `VITE_PCG_SHOWCASE_URL` to the actual existing
showcase URL when needed. The new app does not recreate the public site.

## Checks and evidence

```sh
npm --prefix practitioner-next run typecheck
npm --prefix practitioner-next test
npm --prefix practitioner-next run build
# With DATABASE_URL pointing to the migrated/seeded disposable database:
npm --prefix practitioner-next run test:e2e
# Required repository gate; TEST_DATABASE_URL needs CREATEDB on disposable PG:
uv run pytest
```

Playwright starts the two local servers if absent. Chromium must be installed
(`cd practitioner-next && npx playwright install chromium`). Its API integration
checks use the real unchanged backend, auth/CSRF, PDF acquisition, deterministic
construction and persistence. UI tests use that backend for complete journeys;
isolated failure/empty-state substitutions are explicitly labelled.

See [the parity checklist](../docs/agents/practitioner-next/parity.md),
[verification and usage](../docs/agents/practitioner-next/verification.md),
[the agent workflow](../docs/agents/practitioner-next/workflow.md), and
[the selected direction](../docs/agents/practitioner-next/design-direction.md).
Screenshots in `artifacts/` show actual rendered synthetic states. Local browser
traces and failure videos remain outside source control. The short
[walkthrough recording](artifacts/walkthrough.webm) is included for review.
Regenerate it against the disposable backend with
`PCG_RECORD_DEMO=1 npm --prefix practitioner-next run test:e2e -- walkthrough --project=desktop`
from the repository root.

## Scope and structure

- `src/app`: independent navigation, language/account shell and styling.
- `src/ledger`, `src/intake`, `src/review`: complete practitioner capabilities.
- `src/shared`: new-app contracts, request/auth helpers and shared UI language.
- `scripts/synthetic_backend.py`: local composition of existing substitutes/API.
- `e2e`: real-backend parity and browser interaction checks.
- `.codex/agents` at the repository root: reusable economical specialists.

The source reader and graph preserve canonical names, source attribution and
exact quotes. Frontend presentation does not reinterpret graph semantics,
create individual-edge acceptance, or expose benchmark evaluation. Motion uses
free `motion/react`, informed by authenticated premium Motion+ source research.
No private registry token or premium runtime dependency is needed.

Verified locally: 752 repository Python tests, 41 new-app unit tests, typecheck,
production build, formatting and 20 real-backend desktop/phone parity tests.
A separate opt-in walkthrough also passed. Graph coverage includes Evergreen
family placement, complete bounds, connector spacing, exact Evidence selection,
return focus, stable camera and language switching. Geometry regressions cover
reciprocal claims, multiple roles and graphs with no Trust or multiple Trusts.

The graph now restores the reference application's family structure within the
new visual system: spouses together, a prominent Trust, separate parent and
Trust-role connectors, and selectable labels. Caption routes and bounded name
previews prevent text from spilling into adjacent drawing space. Compare the
[original graph reference](artifacts/original-graph-reference.png) with the
[corrected Chrome view](artifacts/graph-corrected-chrome.png), or inspect the
[desktop](artifacts/desktop-corrected-graph.png) and
[phone](artifacts/phone-corrected-graph.png) interaction captures.

Known limits: finite graph routing can still overlap connectors in larger/dense
states; use pan/zoom and the complete searchable relationship list. The production
build reports a nonblocking main-bundle size warning (about 209 kB gzip). No
runtime MotionScore or production Google-provider check was performed. Local
OIDC and extraction use existing deterministic synthetic substitutes.
