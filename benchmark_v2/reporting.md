# Benchmark v2 reporting

Run the reporter from the repository root. It reads frozen Workbench plans,
saved results and retained attempt records, then writes JSON to stdout. Supply
original Run directories alongside their Experiment records and authoritative
task ledgers.

## Development baseline

Use the `preflight.json` retained at corpus freeze and repeat `--baseline-run` for
each Run in the approved baseline. The report always includes D1–D14 and all 18
planned slots, including the three individual Observations for each T3 order.

```sh
uv run python -m benchmark_v2.report development \
  --commitments /path/to/preflight.json \
  --baseline-run /path/to/workbench/first-run-id \
  --baseline-run /path/to/workbench/second-run-id > /path/to/development-report.json
```

The official report requires fresh live Runs. It checks the pinned baseline
settings, sourced prompt and captured code. Use the preflight results to review
ideal replays and the dependency lock. The saved Run supplies installed
dependency versions but lacks a lockfile snapshot. The baseline report lists
returned models and available fingerprints per attempt. The historical baseline
fingerprint was `bc19ba97cbe016479903222bb1578db6`.

## Final paired evaluation

The custodian prepares a private final manifest from the frozen condition
commitments and protocol. Supply four conditions with distinct `matter_family`
values and `observations` set to 1. Each row supplies `condition`, `matter_family`,
`case_id`, `input_id`, `observations`, `source_digest`, `truth_digest`,
`extraction_digest`, `annotation_digest` and `targets`. Use
`private_client_graph.research.retained_inputs.input_digests` on the frozen input
template for the three input digests. For `annotation_digest`, use `value_digest`
on `benchmark_v2.report.ConditionLabels(condition=..., input_id=...,
targets=...).model_dump(mode='json')`.

The manifest includes the frozen `evaluator_version`, `execution_mode` set to
`live`, and `baseline_plan_digests` and `final_plan_digests` from the planned
Workbench Runs' `execution.json` files. Preserve those digests before execution.
After unsealing and executing the separately approved evaluation, pass the
private manifest and all executed or frozen Runs to the reporter.

```sh
uv run python -m benchmark_v2.report final \
  --commitments /private/path/final-manifest.json \
  --baseline-run /path/to/workbench/baseline-run-id \
  --final-run /path/to/workbench/final-run-id > /private/path/final-report.json
```

Keep the final report with the private evaluation records. It can include
annotated edges and exact Evidence quotations. Each family row gives both
Observations and the reason for excluding an incomplete or mismatched pair.
Paired graph pooling includes only scored pairs with verified ordered Source
requests and identical captured evaluator code. Full arm pooling includes each
scored Observation once, and each coverage block gives the denominator.
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
