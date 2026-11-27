# Inspect Benchmark v3 in the read-only Research Workbench

Use a checkout containing the Benchmark v3 Evaluation Protocol v1 implementation, Python dependencies, the web dependencies, and a dedicated PostgreSQL database for this Workbench instance. Keep the private archive, admitted registry and their referenced files on the same host. The importer checks the original records in place and does not relocate the archive.

## Import and open the baseline

From the repository root, set the following values for your machine. Run these commands under the account that already has access to the private Benchmark v3 custody.

```bash
umask 077
export PCG_RESEARCH_ARTIFACTS=/absolute/path/to/private/workbench-artifacts
export DATABASE_URL=postgresql+psycopg://USER@127.0.0.1:5432/PRIVATE_RESEARCH_DB
benchmark_custody=/absolute/path/to/private/benchmark-v3

mkdir -p "$PCG_RESEARCH_ARTIFACTS"
uv run alembic upgrade head
uv run python -m private_client_graph.workbench.benchmark_v3_import \
  --artifacts "$PCG_RESEARCH_ARTIFACTS" \
  --archive "$benchmark_custody/live-baseline-2026-11-24" \
  --admissions "$benchmark_custody/admissions-2026-11-24/ADMISSIONS.json"
uv run python -m private_client_graph.workbench.bootstrap
npm ci --prefix web
npm run build:research --prefix web
uv run uvicorn private_client_graph.workbench.api:app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080` and choose **Benchmark v3 Research** in the sidebar. The service should report `read_only: true` at `/health`. Use the dedicated artifact root and database only with the read-only app. The generic Research Docker entry point defaults to the execution app, so an equivalent container deployment must explicitly select the read-only app and make the original custody and its referenced paths available.

Run the same import again to verify that it is unchanged. After recreating the dedicated database, apply the existing migrations and rerun bootstrap to rebuild the indexes. Keep the private Workbench artifact root alongside the separately retained original archive and admissions.

Open the Run and expand **Observations & Evidence**. Choose a Benchmark Family and Condition to inspect graph and proof delivery. Use **Compare with Run** when the workspace contains another verified Run. Comparisons are descriptive and include unavailable Conditions when the scope matches. The first release imports the retained baseline format. Future live formats require a verifier for their actual retained records.

## Export local figures

Install Chromium with `cd web && npx playwright install chromium`. Run the exporter from the repository root while the read-only Workbench is running.

```bash
node web/research/export/benchmark.mjs \
  --origin http://127.0.0.1:8080 \
  --experiment EXPERIMENT_ID --run RUN_ID --condition CONDITION_ID \
  --output /absolute/path/to/new/private/figure-directory
```

Find the Experiment and Run identifiers in the Workbench. Omit `--condition` for cohort and family output without a condition graph. The output directory must be new. The command reads the same verified Run as Workbench and writes metric CSV, provenance JSON and SVG/PDF figures. A selected `--condition` must have a valid predicted graph and at least one incomplete joint proof; the exporter checks both before writing any files. Keep the generated materials private until the specific figures and example are approved for disclosure.

## Reproduce verification

- Run the standard Python and Research Workbench test suites using a separate disposable PostgreSQL database.
- To opt in to the exact private regression, set `PCG_V3_PRIVATE_BASELINE_CUSTODY` to the existing Benchmark v3 custody root and run the Benchmark v3 evaluation and Workbench import tests locally.
- Run browser tests and capture examples with synthetic fixture data for shared or public evidence. Keep screenshots, browser traces and exports from the live baseline private.

## Inspect the separately released 65-Source rehearsal

The exploratory scale workload appears in its own sidebar section. It is
read-only, unqualified and unscored. It has no Benchmark Family, condition,
run, admission or score and stays outside official reporting and run selection.

Start the read-only Workbench with the custodian's owner-only environment
file and the usual private artifact root and database. The environment file
supplies `PCG_EXPLORATORY_WORKLOAD_DIR`, `PCG_EXPLORATORY_MANIFEST_SHA256` and
`PCG_EXPLORATORY_ACCESS_TOKEN`. The workload directory contains only the
approved `manifest.json` and exact ordered `sources.json`. Keep the directory
and both files owner-only. Keep the access token, review records, and all
Source content outside Git.

~~~sh
set -a
. /absolute/path/to/owner-only/workbench.env
set +a
uv run uvicorn private_client_graph.workbench.api:app --host 127.0.0.1 --port 8080 --no-proxy-headers --no-access-log
~~~

Open `http://127.0.0.1:8080/#exploratory=1` and sign in as `owner` with the
access token from the private environment file. Use the owner instance
directly on loopback. The Workbench verifies the release manifest and the
ordered Source file on every read. The separate execution application
continues to offer only its existing workloads. The private display grants
no authority to execute a retrieval or extraction experiment.

### Inspect a separately frozen exploratory reference

The same owner instance can show a consensus reference when both
`PCG_EXPLORATORY_REFERENCE_FILE` and `PCG_EXPLORATORY_REFERENCE_SHA256` identify
an exact private projection for the installed workload. Keep the projection
outside the two-file Source release and bind its workload ID and Source
commitment to that release. The endpoint verifies the references and all
displayed body quotations before returning the projection.

The view separates the ten-reader majority reference, the independent
evidence-adjudicated subset and below-threshold propositions. The majority
rule requires six affirmative votes. Explicit rejections, uncertainty and
omissions have separate counts. The full vote matrix and original reviewer
packets remain in private evidence custody. Treat the two reference sets as
exploratory artifacts. Any future graph metrics against them must remain
separate from Evaluation Protocol v1.
