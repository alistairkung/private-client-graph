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
