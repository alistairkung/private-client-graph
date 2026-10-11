# Alias-resolution research

Issue [#91](https://github.com/alistairkung/private-client-graph/issues/91) implements
these tools. The separately authorized pilot is
[#92](https://github.com/alistairkung/private-client-graph/issues/92).
The [agreed design](../docs/design/entity-resolution-research-experiment.md) defines
the study; these commands do not extend its authority or alter production paths.

## Offline demonstration (no credentials or provider calls)

From the repository root:

```bash
uv run python -m private_client_graph.research plan runs/research/demo --kind demonstration --fresh 5
uv run python -m private_client_graph.research run runs/research/demo
uv run python -m private_client_graph.research render runs/research/demo
uv run python -m private_client_graph.research export runs/research/demo runs/research/demo.zip
```

Open `runs/research/demo/report.html`. It is a standalone document with no external
scripts, fonts or services. The bundle includes `summary.json` and every individual
observation; the ZIP adds `CHECKSUMS.json`. The demonstration uses authored/recorded
responses and is prominently labelled: none of its scores measure a live resolver.
Use a new directory for a new experiment; an existing manifest is never replaced.

`inspect BUNDLE` prints a complete summary without making calls. `render` recomputes
only derived HTML/summary files, never observations. All six frozen inputs, Source,
truth, annotations and hashes are embedded in the manifest. The manifest also
records prompts, source-code snapshots, code revision/dirty state and dependencies.

## Optional Task A development checks

Task A has a shared maximum of five attempted paid calls, including failures and
retries, for useful live diagnostics. No need to use it; CI/tests are fully offline.
For example, a targeted check can be planned with:

```bash
uv run python -m private_client_graph.research plan runs/research/diagnostic --kind task_a_diagnostic --samples alias_merge,alias_distinct --repetitions 1
uv run python -m private_client_graph.research run runs/research/diagnostic --live
```

`plan` freezes the explicit `--model` or configured `DEEPSEEK_MODEL` (fallback
`deepseek-flash`). `run --live` reads `DEEPSEEK_API_KEY`; credentials never enter the
manifest. Thinking and SDK retries are disabled; the default timeout is 90 seconds.
Environment tracing is disabled for these isolated observations. These checks do
not start the Task B matrix. Document any paid calls made outside this runner in
the same task accounting before using it; do not claim a new per-session allowance.

## Task B — only after review and explicit authorization

Do not run the paid pilot simply because Task A is complete. After the user
explicitly authorizes #92, plan a separate `task_b_pilot` bundle with the approval
reference and reviewed Task A commit:

```bash
uv run python -m private_client_graph.research plan runs/research/pilot --kind task_b_pilot --authorization-reference APPROVAL_REFERENCE --reviewed-commit REVIEWED_COMMIT
uv run python -m private_client_graph.research run runs/research/pilot --live
```

Defaults are six frozen inputs, five fresh Case 03 extraction attempts, and three
resolver repetitions per usable input: at most 38 new provider attempts. The first
run stops after six attempts on the matched challenge. Inspect those artifacts;
continue only if the implementation is working and further observations serve the
fixed study. `--checkpoint N` bounds new attempts in that invocation, never resets
the task budget. A poor result is data, not authorization to tune/rebuild or replace
failures. Record reasons for ending early. No automatic next experiment is started.

## Failure handling and recovery

An attempt is durably reserved before dispatch. A timeout or interruption counts,
even if billing is uncertain. Resume reuses results and never resubmits unfinished
attempts. Provider errors store the exception class, not messages that could expose
credentials. Parse failures retain raw responses. Invalid edits/graphs retain their
predictions and have null scores; they never masquerade as a successful no-op.

The task-wide ledger is `runs/research/task-ledgers/91/` or `92/`, shared across
bundles and sessions. Preserve it along with experiment bundles; copying an archive
is for analysis, not permission to reset a budget. Execution is locked against
concurrent runners. Interrupted in-flight reservations remain uncertain. Changes
to research/domain code invalidate execution resume; render/export still work from
saved observations. A revised experiment requires a new manifest and still shares
the existing task cap. Ask for approval before exceeding the task allowance.

Keep artifacts until the user elects deletion. `export` produces a portable archive
outside the bundle and refuses overwriting an existing archive. Verify it with:

```python
from pathlib import Path
from private_client_graph.research.export import verify_export
verify_export(Path('runs/research/pilot.zip'))
```

Archive checksums protect completeness and byte integrity, not source authenticity.
Keep an additional retained copy; Git ignores `runs/`. Attach actual report/archive
paths, hashes and attempt counts to #92 after execution; do not deliver only an
unavailable local path or only aggregates.

## Pricing and interpretation

Pricing is optional because unknown cost must not become zero. Supply `--pricing`
with JSON matching the configured model, for example (illustrative rates only):

```json
{"model":"deepseek-flash","currency":"USD","input_per_million":1.0,
 "cached_input_per_million":0.1,"output_per_million":2.0,
 "source_url":"https://PROVIDER_OFFICIAL_PRICING","retrieved_at":"YYYY-MM-DD"}
```

Use verified current rates for actual experiments. Cached tokens are a subset of
input tokens. Missing cache detail with different cache pricing makes cost unknown.
Actual experiment spend counts each attempt once. Single-pipeline estimates combine
one extraction with one resolver execution; authored extraction cost is unavailable,
and historical cost is unavailable without historical pricing. Reports retain these
limitations and separate authored, historical and fresh cohorts. Pairwise identity
errors measure annotated endpoints, not individuals or missing extractions.

Resolver latency includes provider and edit application time only. Pipeline latency
adds the shared extraction provider measurement and each configuration's graph and
evaluation times; artifact I/O and identity diagnostics are excluded. The historical
observation's original elapsed time includes local processing, so it is displayed
separately and comparable pipeline estimates remain unavailable. Resume rejects
changed code or dependency versions. Restore an incomplete task ledger before
attempting further paid calls; never reset it to recover an interrupted experiment.

## Deterministic verification

```bash
uv run pytest tests/research
uv run mypy private_client_graph/research --follow-imports=silent
uv run pytest
```

Research tests block live sockets and substitute only the provider boundary. They
cover endpoint edits, annotation truth, actual SDK HTTP shaping/parsing, pairing,
budget/resume, failures, metrics, escaping, report rendering and export restoration.
