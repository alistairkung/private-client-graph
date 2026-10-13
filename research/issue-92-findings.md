# Issue 92 paired alias-resolution pilot

Executed on 2026-10-11 against the reviewed Task A merge
`051e2b08166584c7372626dcd8b02c09fbd075af`.

Authorization was supplied in Codex task
`01a12a43-2a13-75b2-82d3-a0ccda6f5c02` by the user's `implement issue 92`
request. Before paid egress, the user explicitly replied `approved` for the first
six synthetic DeepSeek calls, then `yes approved` for the remaining fixed matrix
up to the 38-attempt ceiling. The archive contains a post-execution
`authorization.json` that preserves this approval chain without rewriting the
frozen pre-dispatch manifest. The experiment used the official `deepseek-flash`
alias, documented by DeepSeek as `DeepSeek-V4.1-Flash`, with thinking and retries
disabled and a 90-second timeout.

## Execution accounting

- Planned and attempted provider calls: 38 of 38 (5 extractions and 33 resolver
  calls).
- Valid calls: 38; provider failures: 0; uncertain calls: 0; replacements: 0.
- Tokens: 70,307 input, including 56,704 cached, and 3,449 output.
- Estimated actual spend: USD 0.004279962 at the documented Sunday off-peak rates.
  Fresh extraction calls account for USD 0.001356210; resolver calls account for
  USD 0.002923752.
- Mean provider latency: 0.919 seconds overall, 1.648 seconds for extraction and
  0.808 seconds for resolution. Resolver latency ranged from 0.519 to 1.428 seconds.
- Pricing source: <https://api-docs.deepseek.com/quick_start/pricing/>, retrieved
  2026-10-11. Rates per million tokens were USD 0.15 uncached input, USD 0.003
  cached input, and USD 0.60 output.

## Quality and variability

All 33 resolver repetitions were scored and paired with their deterministic
baseline. Every repetition retained precision, recall, F1 and conditional
provenance accuracy of 1.0 except where the baseline intentionally exposed an
alias split. Within-input resolver F1 standard deviation was 0.0 for every input.

- The authored Case 03 alias split improved from 6 TP / 1 FP / 1 FN (F1 0.8571)
  to 7 TP / 0 FP / 0 FN (F1 1.0) in all three repetitions. Its two missed-merge
  endpoint pairs fell to zero.
- The authored Beth/Elizabeth merge challenge improved from 1 TP / 1 FP / 1 FN
  (F1 0.5) to 2 TP / 0 FP / 0 FN (F1 1.0) in all three repetitions. Its one
  missed-merge endpoint pair fell to zero.
- The matched distinct-person challenge correctly abstained in all three
  repetitions: F1 remained 1.0 with zero incorrect merges.
- Case 01, Case 02 and the historical Case 03 extraction remained at F1 1.0 with
  no identity errors in all repetitions.
- All five fresh Case 03 extractions already scored F1 1.0. Resolver means and
  ranges remained 1.0, so between-extraction baseline variation and within-input
  resolver F1 variation were both zero. These inputs are unannotated, so identity
  metrics are unavailable rather than zero.
- The resolver returned no edits in 22 of 33 repetitions. Some fresh repetitions
  proposed mechanically valid canonical-name substitutions that did not change
  the canonical graph or score, showing output-level variability that F1 does not
  expose.

## Interpretation

The resolver reliably repaired both frozen alias challenges and preserved the
matched non-merge control, with no failures and modest measured cost and latency.
However, it produced no quality improvement on five fresh extractions because the
current extraction model already canonicalized those inputs. The pilot therefore
shows that the approach can repair the known failure mode, but does not establish
that it earns production complexity at the observed prevalence. The recommendation
is not to integrate it into production yet; retain the evidence and revisit only
with a separately authorized, broader sample containing naturally occurring alias
errors or a materially different controlled comparison. No generalization or
statistical reliability claim is supported by this small development pilot.

## Deliverables

- Standalone report: `research/results/issue-92/report.html`
  (`sha256:164f33313e12d3e133335fe4e8431d5df1386380ba45f05ec991675d1ee4c186`).
- Compact metrics summary: `research/results/issue-92/metrics-summary.json`
  (`sha256:1cadc45c04e2c289c2dcce8b339d4aebc10fa9c5b511b01513385c500aada601`).
  It retains configuration identity, operational accounting, cohort aggregates,
  per-input distributions and per-repetition metrics, identity counts, usage, cost
  and latency. Detailed graphs, Evidence, edits, predictions, raw responses and
  attempt records remain in the external archive rather than being duplicated in
  Git.
- Authorization record: `research/results/issue-92/authorization.json`.
- Portable archive: [GitHub Release asset](https://github.com/alistairkung/private-client-graph/releases/download/issue-92-research-artifacts-2026-10-11/issue-92-pilot-with-authorization.zip)
  in the [Issue 92 research-artifact prerelease](https://github.com/alistairkung/private-client-graph/releases/tag/issue-92-research-artifacts-2026-10-11)
  (`sha256:a87c2b9a7fa3585a2fc8860e4007f1e3132ef3833abad068ab7aaf124a78580d`).

The release asset was downloaded after upload, matched the original portable copy
byte-for-byte and passed its internal `CHECKSUMS.json` verification. It contains
the raw observations, attempt reservations, frozen inputs, provider metadata,
prompt/configuration/code snapshots, graphs, evaluations, derived full summary,
standalone report, sessions and authorization record. The original append-only
local bundle remains at `runs/research/issue-92-pilot/`, the authorization-complete
portable copy remains at `runs/research/issue-92-pilot-with-authorization.zip`, and
the task-wide ledger remains at `runs/research/task-ledgers/92/`; none is tracked by
Git and none was deleted.

To recover and verify the portable evidence with the GitHub CLI:

```bash
gh release download issue-92-research-artifacts-2026-10-11 \
  --pattern issue-92-pilot-with-authorization.zip
shasum -a 256 issue-92-pilot-with-authorization.zip
uv run python -c \
  'from pathlib import Path; from private_client_graph.research.export import verify_export; print(verify_export(Path("issue-92-pilot-with-authorization.zip")))'
```

The SHA-256 output must equal the archive checksum recorded above; `verify_export`
must print `True`. Extracting the verified ZIP restores the complete portable
experiment bundle without requiring provider credentials or network access.

## Code Quality Review

No production or research source code changed in Task B. The pilot used the public
CLI and reviewed Task A contracts unchanged. The pricing snapshot, findings and
generated artifacts are scoped to issue 92; no refactor or new abstraction is
warranted. The cleanup retains only the report and compact metrics in Git while the
verified release asset preserves the complete evidence bundle. Deterministic
research tests, typechecking, archive verification and the full repository suite
passed after execution.
