# Benchmark v2 reporting

Run the reporter from the repository root. It reads frozen Workbench plans,
saved results and retained attempt records, then writes JSON to stdout. Supply
original Run directories alongside their Experiment records and authoritative
task ledgers.

## Development baseline

Use the `preflight.json` retained at corpus freeze. Record each approved Run's
`digest` from `execution.json` before execution. Supply all five digests in
committed batch order (D1–D7, D8–D9 three times, D10–D14). Repeat
`--baseline-run` for each available Run. Run paths can be supplied in any order.
The report includes all 18 planned slots even when a batch is missing.

```sh
uv run python -m benchmark_v2.report development \
  --commitments /path/to/preflight.json \
  --baseline-plan-digest "$FIRST_BATCH_DIGEST" \
  --baseline-plan-digest "$SECOND_BATCH_DIGEST" \
  --baseline-plan-digest "$THIRD_BATCH_DIGEST" \
  --baseline-plan-digest "$FOURTH_BATCH_DIGEST" \
  --baseline-plan-digest "$FIFTH_BATCH_DIGEST" \
  --baseline-run /path/to/workbench/first-run-id \
  --baseline-run /path/to/workbench/second-run-id > /path/to/development-report.json
```

The reporter checks the approved plan digest, ordered input group, one fresh
Observation per input, invocation and matrix caps, and the shared 18-attempt task
and ledger. It also checks the pinned settings, sourced prompt, installed
dependency versions, and captured code. Use preflight to verify the dependency
lock and review ideal replays.

The chronology compares retained extraction start times with the committed
schedule. Missing or tied timestamps leave chronology partially verified. A
known inversion excludes the affected scores while retaining attempt records
and failures. The baseline report lists returned models and available
fingerprints per attempt and compares them with the historical baseline
fingerprint, `bc19ba97cbe016479903222bb1578db6`. A change is disclosed alongside
scores.

## Final paired evaluation

The custodian prepares a private final manifest from the frozen condition
commitments and protocol. Supply four conditions with distinct `matter_family`
values and `observations` set to 1. List families in frozen order so the reporter
expects baseline first on families 1 and 3 and final first on 2 and 4. Each row supplies `condition`, `matter_family`,
`case_id`, `input_id`, `observations`, `source_digest`, `truth_digest`,
`extraction_digest`, `annotation_digest` and `targets`. Use
`private_client_graph.research.retained_inputs.input_digests` on the frozen input
template for the three input digests. For `annotation_digest`, use `value_digest`
on `benchmark_v2.report.ConditionLabels(condition=..., input_id=...,
targets=...).model_dump(mode='json')`.

The manifest includes the frozen `evaluator_version`, `execution_mode` set to
`live`, and `baseline_plan_digests` and `final_plan_digests` from the planned
Workbench Runs' `execution.json` files. Preserve those digests before execution.
Both arms use one private task ledger and shared cap. If the approved final
pipeline requires more calls, freeze both arms under the separately approved
revised cap. Pass the private manifest and all executed or frozen Runs to the
reporter after the separately approved evaluation.

```sh
uv run python -m benchmark_v2.report final \
  --commitments /private/path/final-manifest.json \
  --baseline-run /path/to/workbench/baseline-run-id \
  --final-run /path/to/workbench/final-run-id > /private/path/final-report.json
```

Keep the final report with the private evaluation records. It can include
annotated edges and exact Evidence quotations. Each family row gives both
Observations and the reason for excluding an incomplete or mismatched pair.
Paired graph pooling includes scored pairs with verified ordered Source
requests and matching captured graph and Source attribution scorers. Known
reversals of the expected arm order exclude the paired delta. Individual arm
scores remain visible, and each coverage block gives its denominator.
Differences are final minus baseline. FP and FN changes list the affected
edges. Quote and sufficient-set changes list edges gaining or losing support.
Source attribution changes give both the assessment count and the pass count.
The original scores beside each delta provide its Evidence denominators.

Resources include retained failures and uncertain reservations. Latency is
summed provider time in seconds. Tokens and latency give measured counts and
known subtotals when measurements are missing. Cost reports incurred attempts,
known subtotal, unpriced count and total. A missing total or delta is
`null`. Attempted totals describe the supplied Runs. Coverage shows planned
Observations without a Run. If an extraction is shared by multiple resolver
Observations, each lists that extraction, and the arm counts it once.
