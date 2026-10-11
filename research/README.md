# Research Workbench

Private Client Graph's primary research interface is the local, synthetic-only
**Research Workbench**. It uses the Shared Analysis Pipeline and existing
deterministic evaluators; it does not change the practitioner application.

## Start the workbench

From the repository root, with Docker installed:

```bash
docker compose up --build -d
```

Open **http://127.0.0.1:8080**. The `research` service builds the React
frontend, waits for its PostgreSQL service, applies Alembic migrations, indexes
retained artifacts and starts the research API. Inspect startup with:

```bash
docker compose ps
docker compose logs -f research
```

By default `PCG_RESEARCH_LIVE_ENABLED=0`: no paid model execution is enabled.
Use the deterministic demonstration path for an offline smoke test. Live execution
requires a separate deliberate configuration and explicit per-Run authorization;
setting a provider key alone does not enable it.

Compose persists the authoritative research artifacts under
`./runs/research` on the host and the rebuildable PostgreSQL index in a named
volume. Stop without deleting either:

```bash
docker compose down
```

Do not delete `./runs/research` or its task ledgers to reset an experiment
budget. Never treat a restored archive or rebuilt database as execution authority.

## Research workflow

1. Create a **named Experiment**, optionally recording its hypothesis.
2. Configure the **next Run** in the horizontal pipeline editor. Available
   capabilities currently include no resolution or generative alias resolution;
   the execution topology is not freely editable.
3. Select benchmark inputs (all authored cases by default), saved extraction
   or fresh extraction, and the supported execution settings.
4. Review and freeze the Run plan. For paid work, explicitly authorize the
   bounded invocation before starting; freezing alone does not authorize calls.
5. Execute the Run. Its configuration, inputs, results, provenance and available
   costs remain immutable. Interrupted Runs require explicit continuation.
6. Inspect F1, per-case coverage, provider cost and individual relationships
   with exact Evidence. Edit the next-Run draft and run again within the same
   Experiment; selecting historical Runs does not overwrite the draft.

A **Run** can contain several scored observations. The backend computes pooled
observation micro-F1 from TP/FP/FN. Partial results are provisional; unscored
observations do not become zeros. Cost means estimated provider spend incurred
by that Run, not historical extraction spending. Unpriced attempts make a
cost point unavailable. Runs with differing benchmark scopes remain visible but
must not be presented as directly matched comparisons.

For the authoritative v2 API sequence, idempotency, recovery, budget handling,
legacy history and migration requirements, see
[Persistent Research Experiments and Runs](../docs/workflows/persistent-research-workspaces.md).

## Historical alias-resolution pilot

The original [#91](https://github.com/alistairkung/private-client-graph/issues/91)
research runner and [#92](https://github.com/alistairkung/private-client-graph/issues/92)
pilot preceded the persistent Experiment/Run model. Their schema 1–3 bundles
remain available as **legacy studies**, not automatically converted into new
single-configuration Runs. Keep their original manifests, observations, checksums
and attempt ledgers intact.

The historical CLI is implemented in `private_client_graph.research`.
It can still inspect a retained bundle without making provider calls:

```bash
uv run python -m private_client_graph.research inspect runs/research/EXISTING_BUNDLE
```

The original study's planning, paid-call budget and report/export instructions
are historical, not the recommended way to start new experiments. In particular,
do not repeat the paid #92 pilot simply to populate the new UI. The legacy
standalone HTML report is being retired separately; until that cleanup is merged,
its CLI and export requirements may still be present in the checkout.

## Verification

```bash
uv run pytest tests/research tests/workbench
uv run pytest
```

The tests use deterministic provider substitutes; they must not invoke live
models. For the Research Workbench's end-to-end and frontend checks, follow
[Web application guidelines](../docs/WEB_APP_GUIDELINES.md).

Research and practitioner deployments are separate: the default Compose stack
starts the research workbench, while the practitioner demonstration uses the
explicit `practitioner` profile described in the
[repository README](../README.md).
