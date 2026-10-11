# Persistent Research Experiments and Runs

The additive `/api/research/v2` API implements the approved Experiment → Run →
Observation contract. The existing `/api/research/v1` API and schema 1–3 study
readers retain their existing meaning. The practitioner API is unchanged.

## Storage and upgrade

Run `uv run alembic upgrade head` before starting the new backend. Migration 0008
adds `research_workspaces`, a disposable PostgreSQL projection. The existing
`research_experiments` table remains the legacy study index. No historical
manifest, summary, checksum or result is rewritten.

Retain the **whole** `PCG_RESEARCH_ARTIFACTS` directory, including:

- `experiments/<id>/workspace.json`: required name, optional hypothesis and
  description, stable identity and initial draft;
- `experiments/<id>/drafts/`: immutable numbered draft revisions;
- `experiments/<id>/runs/`: immutable Run membership records;
- `<run-id>/`: schema-4 frozen single-configuration plan, selected inputs and
  case/fixture labels, observation slots, execution binding, results and attempts;
- `live-task.json`, `task-ledgers/`, commands, authorizations and lifecycle records.

Workspace records carry content checksums; schema-4 manifests retain the existing
manifest checksum and execution binding. PostgreSQL does not authorize spending
or own non-derivable metadata. Rebuild both projections with the existing
`uv run python -m private_client_graph.workbench.bootstrap` command. It restores
packaged legacy history only when absent and does not re-execute anything.
Workspace history retains explicit missing/corrupt states; reads do not repair
artifacts. An interrupted publication after the complete plan but before
membership can be recovered by retrying the same freeze command. A partially
published plan fails explicitly and requires restoration from retained artifacts.

Executable artifacts remain bound to their original local path, task ledger,
code and dependencies. Copying/importing an artifact does not transfer execution
authority. Back up artifacts and task ledgers together; never reconstruct paid
accounting from PostgreSQL. Restart reconciles interrupted execution and requires
explicit continuation. Unknown attempts consume their reserved allowance and are
never automatically resubmitted.

## API sequence

Commands require a trusted local Host, matching Origin and JSON content type.
`create_app` provides read-only composition; `create_execution_app` explicitly
mounts commands. No browser credential or provider key is accepted.

1. `POST /v2/experiments` with `request_id`, non-blank `name`, optional `hypothesis`
   and `description`. Different request IDs permit duplicate display names.
2. `GET /v2/cases` exposes repository-owned Case and diagnostic fixture metadata.
   A new draft selects every authored Benchmark Case once. Alternate historical
   samples and diagnostic fixtures are explicit selections, not hidden defaults.
3. `PUT /v2/experiments/{id}/draft` with `request_id`, `expected_revision` and
   `configuration`. Optimistic revision checks prevent overwriting a newer draft.
   `POST .../draft/copy` copies a historical configuration only.
4. `POST /v2/preview` validates the configuration and reports bounded work.
   `POST .../runs` freezes the current draft using its `expected_revision` and
   a new `request_id`. Identical configurations can create independent Runs;
   repeating a command is idempotent.
5. For live work, `POST .../runs/{run}/authorize` accepts the existing
   `LiveApproval` contract. This durably authorizes **without starting**. Then
   `POST .../start` uses the same invocation `request_id` and plan digest.
   Changed task usage invalidates this prepared start. Offline replay needs no
   paid authorization. Continuation uses a new explicitly authorized invocation
   with `continuation=true` followed by `POST .../continue`. Existing v1 atomic
   authorize/start remains supported.
6. `GET /v2/status` exposes global active Run and task budget without creating
   locks, dispatching, reconciling or repairing records. A terminal lifecycle
   can briefly precede worker release; check `active_run_id` before another start.
7. `GET .../runs`, `GET .../runs/{run}`, `GET .../runs/{run}/aggregate`, and
   `GET .../runs/{run}/observations/{slot}` expose immutable plans, backend-owned
   scores/coverage/cost, frozen names and exact relationship Evidence.
   `GET .../comparison?left=...&right=...` separates benchmark scope from verified
   input pairing. Selecting a Run never changes the draft or authorization.

All paths above are under `/api/research`. Backend-generated client types live in
`web/research/shared/contracts.ts`; regenerate with
`uv run python -m private_client_graph.workbench.typescript`.

Schema-4 Runs exclude auxiliary baseline observations when the selected
configuration uses resolution. Saved/fresh inputs use the same Shared Analysis
Pipeline and evaluator. Fresh extraction failure preserves every planned slot.
Primary F1 is `observation_micro_f1_v1`, pooling per-observation TP/FP/FN.
Costs use unique incurred attempts; demonstration recordings never become live
spend. Unknown usage/pricing excludes only the cost point. Reconstructed
full-pipeline cost remains separate and is explicitly unavailable where no
verified reconstruction exists.

`/v2/legacy/experiments` and its detail route expose historical studies with
explicit unavailable name/description fields and unchanged v1 detail. They are
not automatically mapped into single-configuration Runs, and present-day case
labels never silently replace missing historical metadata.

## Deterministic validation

Use disposable PostgreSQL through `TEST_DATABASE_URL` and `DATABASE_URL`.
`tests/persistence/test_research_workspaces.py` exercises the real API, subprocess,
pipeline/evaluator, immutable historical Evidence, unchanged/changed Runs and
index rebuild. Workspace live tests substitute only provider/worker process
boundaries and preserve durable accounting. `tests/workbench/test_run_matrix.py`
and `test_run_evaluation.py` cover frozen membership, default selection and the
approved numerical, cost and comparison fixtures. No test requires React or
paid provider calls.
