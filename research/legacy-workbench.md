# Legacy Research Workbench operations

These instructions describe the retained v1 study workflow and schema 1–3
artifacts. For new Experiments and Runs, start with the [Research Workbench guide](README.md)
and the [persistent workspace contract](../docs/workflows/persistent-research-workspaces.md).
The v2 workflow supersedes the experiment-creation steps below; the legacy API
and study readers remain supported.

Commands run from the repository root. Importing history or rebuilding an index
never grants provider execution authority.

## Local services and historical artifacts

```bash
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). This separate React/TypeScript
application and `/api/research/v1` API require no provider credentials. The default
Compose services restore the retained Issue #91 recorded demonstration and Issue #92
pilot exports, migrate a separate PostgreSQL database and rebuild its research index.
No experiment starts automatically. Offline replay and recorded demonstrations require
an explicit frozen-plan command. Practitioner services remain available through the explicit
`practitioner` profile command in the [application setup guide](../docs/workflows/application-setup.md#protected-local-development).

In history, search `issue-`, select the two experiments and compare them. Inspect
Issue #92's `case_03_fixture` baseline, select **Missing**, open the Jonathan Tan /
Rebecca Tan relationship and choose **View expected in Source**. The expected
quotation is highlighted in the frozen Source; **No predicted relationship** remains
explicit. Choose a treatment repetition to inspect the repaired result.

Artifacts and task ledgers persist together in `runs/research`, mounted at
`/artifacts`. PostgreSQL persists in `pcg-research-postgres-data`; it is only a
rebuildable projection. Never delete the artifact directory to reset an index.
Historical absolute ledger paths remain unchanged and imports confer no execution
authority. See [historical archive provenance](history/README.md) for the portable archives.

To restore an additional supported schema-1 export into a **new** directory:

```bash
uv run python -m private_client_graph.workbench.restore archive.zip runs/research/new-history
```

The offline service refreshes its rebuildable index on reads. To explicitly rebuild it
through its CLI:

```bash
docker compose exec research python -m private_client_graph.workbench /artifacts
```

The index records artifact identity, full-file digest and index time. Reads detect
changes since indexing and withhold stale result detail. Missing, corrupt and
unsupported artifacts remain discoverable with an explicit reason. A legacy bundle
without an export checksum inventory validates its frozen manifest and parses its
recorded contracts; its content digest detects subsequent changes, but cannot prove
that an original result was never altered before import. Exported bundles additionally
validate every file against `CHECKSUMS.json`. No evaluator is rerun while importing.

History supports `q`, `kind`, `lifecycle`, `integrity`, `offset`, and `limit` (1–100).
Detail and comparison use opaque index IDs. API schemas are available at
`/openapi.json`; checked TypeScript contracts are generated with
`uv run python -m private_client_graph.workbench.typescript` and verified by tests.
Unknown costs/diagnostics remain unavailable. Comparisons require identical case,
cohort, Source, truth and extraction digests and disclose configuration/code changes;
ambiguous or unmatched inputs are excluded explicitly, not silently pooled.

For local development without Docker, migrate an isolated PostgreSQL database,
set `DATABASE_URL` and `PCG_RESEARCH_ARTIFACTS`, then run:

```bash
uv run alembic upgrade head
uv run python -m private_client_graph.workbench runs/research
uv run uvicorn private_client_graph.workbench.execution_api:app --host 127.0.0.1 --port 8080
# In a second terminal:
npm run dev:research --prefix web
```

Validation uses real stored historical results and PostgreSQL, with no provider calls:

```bash
TEST_DATABASE_URL=postgresql://... uv run pytest
npm run test:research --prefix web
npm run build:research --prefix web
DATABASE_URL=postgresql://... npm run test:e2e:research --prefix web
DATABASE_URL=postgresql://... npm run test:e2e:execution --prefix web
python tests/research_compose_smoke.py
```

Use a migrated disposable database for browser tests. The Compose smoke test requires
Docker and verifies container restart, retained artifact digests, empty-index rebuild
and idempotence. `docker compose down` retains data; `down -v` removes the disposable
PostgreSQL volume but retains the bind-mounted artifacts. All ports publish only to
loopback. No public deployment is included; optional local live execution is described below.


### Legacy offline experiment configuration

Choose **New experiment**, select repository-owned saved snapshots and choose
**Saved replay** (no resolver or provider calls) or **Recorded demonstration**.
The recorded mode supports `none` or `generative` resolution and 1–3 resolver
repetitions. Fresh recorded extraction supports the existing Case 03 Source with
1–5 samples. This is the finite recording coverage, not arbitrary source ingestion.
Each extraction is held fixed across its baseline and resolver repetitions.

The server previews extraction calls, resolution calls, matrix maximum, invocation
cap and observation count. Paid task allowance, usage and remaining authority are
all zero: these are offline tasks. Recorded attempts have a separate invocation cap
and do not represent live quality, latency or cost. Model settings are retained for
provenance; the response model is explicitly a deterministic substitute.
**Review frozen plan** writes a schema-2 manifest, code/dependency provenance,
recorded responses and zero-paid-authority ledger. Then choose **Run replay** or
**Run recorded demonstration**. Schema-1 study manifests and authorizations remain
unchanged. `POST /api/research/v1/preview`, `/plans`, and
`/plans/{id}/{start,stop,continue}` accept only local same-origin JSON requests.

One experiment subprocess runs at a time, independent of the browser connection.
**Stop after current attempt** prevents the next dispatch and retains the current
observation. A checkpoint or interrupted worker requires **Review continuation**
and an explicit continuation command. Repeated command IDs cannot dispatch twice;
uncertain reservations remain counted and are never resubmitted. There are no
provider retries, automatic resume or queue. Offline modes never dispatch live calls. Results use the same
pipeline/evaluator and history/Evidence inspector as retained experiments.

Executable artifacts and accounting use stable `/artifacts` container paths.
Do not move bundles or ledgers, change recorded responses, or mix code/dependencies
on continuation: execution rejects these mismatches. Inspect old results read-only
or create a new plan after code changes; never edit an old manifest to bypass a
rejection. Historical imports cannot start or continue execution.

The strictly read-only composition remains
`private_client_graph.workbench.api:app`; it mounts no commands and imports no
runner. For a read-only Docker service, set `PCG_RESEARCH_APP` in the research
service's Compose environment to that entry point. Both compositions serve the same
frontend; creation/controls appear only when the execution capabilities endpoint is
present. Live approval is a separately enabled capability described below.

### Legacy live research authorization

Live execution is disabled by default. The read-only composition still has no
command endpoints. Issue #103 is demonstrated with substituted providers; starting
an actual paid experiment requires separate user authorization.

Provision one persistent task inside the same stable artifact root used by the
service (for Compose, the container path is `/artifacts`):

```bash
docker compose run --rm research python -m private_client_graph.workbench.approval /artifacts --label 'Approved research task'
```

Provisioning creates a task identity with **zero paid allowance**. It is a one-time
operator step, not a way to reset budgets. Keep `live-task.json` and the complete
`task-ledgers/` directory with the experiment artifacts. Missing accounting must
be restored from backup; copying/importing a bundle or rebuilding PostgreSQL does
not create execution authority. A root represents one task across experiments,
processes and sessions. Do not create another root to evade a task allowance.

For an explicitly authorized experiment, set `PCG_RESEARCH_LIVE_ENABLED=1` and
supply `DEEPSEEK_API_KEY` to the research service environment, then recreate the
service. Credentials stay server-side; never put them in a plan, task label or
approval reference. Host/Origin checks and loopback-only Compose publishing remain
in force. Disable the flag again to prevent further live invocations.

In **New experiment**, choose **Live provider**, configure the finite matrix and
propose a total task call cap. Review the server's extraction/resolution maxima,
existing task usage and invocation cap, then freeze. On the frozen page, review the
current task budget and explicitly check the approval box before **Authorize and
start**. Freezing cannot increase the allowance. Every continuation requires a new
explicit approval; editing creates a new frozen plan. A stale task-budget review
is rejected: refresh the budget and review it again. Increasing the cap requires
freezing and explicitly approving a plan with that larger cap.

Schema-3 authorizations bind the plan digest, task identity/cap, invocation ID and
bound, approval time and validated local Origin. Durable task reservations precede
bundle reservations and provider dispatch. Interrupted/uncertain calls keep their
slots and are never retried. Stop means stop after the current attempt; restarting
the service never resumes work automatically. Full authorization records remain
inspectable under **Execution & artifacts**.

The requested model is frozen and returned model names, latency and token usage
are retained when supplied. This slice does not fetch or invent pricing: USD cost
estimates remain unavailable without verified pricing metadata. Unknown usage is
not zero, and a call cap is not a guaranteed dollar cap. Fresh extraction retains
the finite Case 03 Source coverage from Slice 2.

Run the live-control browser journey without paid calls:

```bash
DATABASE_URL=postgresql://... npm run test:e2e:live --prefix web
```

Its server launches a test-only worker that substitutes the DeepSeek boundary;
the real approval, supervisor, reservation, pipeline, evaluator and index remain
in use. Production has no provider-substitution environment switch.
