# Private Client Graph — Resolver Comparison

The existing resolver improved relationship F1 from **94.87% to 100%** on these ten synthetic cases, with no observed regressions. All improvement came from two `Bea` → `Beatrice Ng` endpoint edits in one case. The incremental cost was ten resolver calls, 9,821 tokens and 9.060 seconds of summed provider-call duration; USD cost is unavailable.

## A. Experimental identity

- Experiment: `83b5778e74ba5e6e882d334fd4f87f09` — Final held-out benchmark — naive full-context baseline.
- Original A / Run 1: `97d26d8e5f9d5964826b144c9ca45ad7`; frozen chain `8ad73b00f44013f454ae166175d974f11f2e129d`.
- Exact replay A′ / Run 2: `d67a391bc95a5ad39e1b5786a04795c0`.
- Resolver B / Run 3: `841389cef51957ce8523ea41c03d2baa`.
- A′ and B used merged implementation `168d64a46acfd3468cb0293b2790e095c37fd3f6`. All required PR and merged-main CI checks passed before execution.
- Model requested and returned: `deepseek-flash`. Temperature: provider default (`null`); timeout: 90 seconds; thinking disabled; retries zero. B used one resolver repetition per case.
- Inputs: `heldout_01_fixture_fresh_01` through `heldout_10_fixture_fresh_01`, ten actual model-produced extraction snapshots, 14 ordered Sources and 39 expected relationships. A′ and B use the same saved inputs; their original fresh cohort is retained in lineage.
- Shared saved-input-set SHA-256: `581a0371831802847de542911fe64b82b4c41e488ca0b65fe706e5cc1096e95c`. Per-input Source, truth/approval, extraction and snapshot digests are retained in `frozen-B.json` and `results.json`.

Frozen plan digests:

- A: `6d1897fb89793649aca6064f253eb96106342a7c7c378b983bdb25fecb5f830e`
- A′: `71cbd2923cb0166d93382aff3b880fb75dc2a4319fbe4d462f2f8d3e5cd983e3`
- B: `2b5ab441e7efb0b5ad654c580113afa0ec61a7ec1e0809a206199953a7cbb85f`

A′ exactly matched A’s extracted candidates, Source attribution, canonical states/graphs, per-case evaluations, provenance diagnostics and scored coverage across all ten observations. It made **zero provider calls**. Original A’s artifact digest remains `edb95eacbff00ee63f0e27db1c7cf684d191b66c839b3c34f8e62e4e67ffc3fc`. This was a full retained-output equivalence check, beyond aggregate agreement.

B was frozen, then explicitly approved by the owner before browser authorization and start. There was one authorization, one start command, ten resolution attempts, zero extraction calls and zero retries. Execution ran from **2026-10-17T07:44:44.568794+00:00** to **2026-10-17T07:44:53.743709+00:00**. Existing Workbench pairing verified ten exact A′–B pairs, equal benchmark scope and no exclusions.

## B. Aggregate and per-case comparison

All deltas below compare B with A′. A and A′ have identical scores.

| Metric | A / A′ | B | Difference |
|---|---:|---:|---:|
| TP | 37 | 39 | +2 |
| FP | 2 | 0 | −2 |
| FN | 2 | 0 | −2 |
| Micro F1 | 94.87% | 100.00% | +5.13 pp |
| Macro F1 | 93.33% | 100.00% | +6.67 pp |
| Approved-quote provenance | 34/37 = 91.89% | 36/39 = 92.31% | +0.42 pp |
| Approved Source/quote pairs | 35/39 = 89.74% | 37/41 = 90.24% | +0.50 pp |
| Planned / scored | 10/10 | 10/10 | unchanged |
| Failed / uncertain / unscored | 0/0/0 | 0/0/0 | unchanged |
| Incremental provider attempts | A′: 0 | 10 | +10 |
| Incremental input / output tokens | A′: 0/0 | 9,432/389 | +9,821 total |
| Incremental provider duration | A′: 0 | 9.060 s | +9.060 s |
| Incremental USD cost | A′: zero calls | Unavailable | 10 unpriced attempts |

Original A consumed ten extraction calls. Total shared usage is now **20/30**, leaving ten unspent attempts; further execution is not authorised. B’s 3,456 cached input tokens are included within its 9,432 input tokens. Mean provider duration was 0.906 seconds per call; the sequential attempt window was 9.175 seconds. All token counts were available. Pricing was absent, so the zero known-cost subtotal must not be interpreted as zero spend.

Micro F1 is the existing pooled-observation metric. Macro F1 is the arithmetic mean of the ten retained per-case F1 values.

| Case | TP/FP/FN: A′ → B | A / A′ F1 | B F1 | Δ pp |
|---|---|---:|---:|---:|
| heldout_01 | 5/0/0 → 5/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_02 | 4/0/0 → 4/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_03 | 1/2/2 → 3/0/0 | 33.33% | 100.00% | +66.67 |
| heldout_04 | 3/0/0 → 3/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_05 | 4/0/0 → 4/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_06 | 3/0/0 → 3/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_07 | 6/0/0 → 6/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_08 | 5/0/0 → 5/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_09 | 3/0/0 → 3/0/0 | 100.00% | 100.00% | +0.00 |
| heldout_10 | 3/0/0 → 3/0/0 | 100.00% | 100.00% | +0.00 |

Nine cases were unchanged; heldout_03 improved from 1 TP / 2 FP / 2 FN to 3 TP / 0 FP / 0 FN. No relationships regressed. Temporal Cases 05/06 and duplicate-title Case 08 retained their correct results.

## C. Every resolver edit

Both edits occurred in `heldout_03`, Source `interview`. Indices are zero-based; the edited field was `source_name`.

| Candidate | Original → resolved | Relationship | Unchanged exact quotation | Effect |
|---:|---|---|---|---|
| 0 | Bea → Beatrice Ng | settlor_of Larch Family Trust | “Bea is the settlor of the Larch Family Trust.” | Replaced one FP with a TP and recovered one FN |
| 1 | Bea → Beatrice Ng | parent_of Isaac Ng | “Bea is the parent of Isaac Ng.” | Replaced one FP with a TP and recovered one FN |

The Source explicitly states: “Beatrice Ng attended the factual interview and asked to be called Bea. In this note, Bea means Beatrice Ng; no second person is being introduced.”

The other nine calls returned `edits: []`. Across every candidate, count/order, relationship type, Source ID and supporting quotation were preserved. The unchanged Isaac Ng beneficiary relationship remained correct.

## D. Scientific interpretation

This is a **post-hoc exploratory comparison** on ten short synthetic cases whose baseline outcomes had already been inspected. It is one treatment execution without resolver repetitions. The measured gain is preferred endpoint naming under exact-name scoring, consistent with the existing resolver’s full-name instruction. Baseline A already used `Bea` consistently; these results do not demonstrate that A split one person into separate identities, or establish general resolver superiority.

The resolver corrected two labels in one case. Nine additional calls returned no edits. The accuracy gain is demonstrated here; its economic value remains unresolved because USD pricing is unavailable and the benchmark is small.

The three approved-quote failures in heldout_02 and four Source/quote-pair failures across heldout_02/04 remain unchanged. They arise from the existing strict approved-span policy, including semantically supportive shorter or longer exact Source quotations. Provenance rates rose because the two corrected relationships entered the TP-based assessment denominators. No quotation or Source attribution was improved or rewritten. The Source-pair denominator counts evidence associations on true-positive relationships, so it increased from 39 to 41 while expected relationships remained 39.

No prompts, benchmark Sources, answer keys, metrics or architecture were changed during execution. Resolver candidates retain the accepted legacy projection without per-candidate Source IDs; deterministic attribution remains protected. This result does not establish behavior on more ambiguous cross-Source identities.

## E. Artifacts and genuine screenshots

Authoritative artifacts remain under `/Users/alistair/projects/private-client-graph/runs/final-day/`, in the three Run directories identified above, with the original Experiment records and shared task ledger. The original baseline results and screenshots were preserved.

The local Workbench is left **read-only**, with live execution disabled, at:

[Completed Experiment B](http://127.0.0.1:8080/#workspace=83b5778e74ba5e6e882d334fd4f87f09&run=841389cef51957ce8523ea41c03d2baa)

Report package: `/Users/alistair/projects/private-client-graph/research/final-day/resolver-comparison/`.

- `results.json`: identities, digests, settings, all metrics, usage, timing, per-case results, edits and pairing.
- `per-case-comparison.csv` and `endpoint-edits.json`: complete case comparison and every model edit.
- `control-equivalence.json`: exact ten-case reproduction proof.
- `B-workbench-run.json`, `B-aggregate.json`, `B-attempts.json`, `paired-comparison.json`: existing Workbench projections and retained provider records.
- `frozen-B.json` / `frozen-B-workbench-run.json`: pre-approval snapshots; `owner-approval.json` records the subsequent explicit approval. Their pre-execution statuses are intentional.
- `raw-artifacts.zip` with `RAW_SNAPSHOT_SHA256.json`: byte-preserving backup of all three Runs, original raw extractions, Experiment records and complete task ledgers. It is a backup, not a relocated executable environment.
- `RESULTS_SHA256.json`: report-package file hashes.

Key genuine browser captures under `screenshots/`:

- `03-control-completed-results.png`: exact replay control’s completed aggregate.
- `06-frozen-B-awaiting-approval.png` and `07-B-authorized-before-start.png`: separate freeze/approval/start gates.
- `08-B-completed-aggregate.png`: 39 TP, zero FP/FN, complete coverage.
- `09-exact-pairing-and-unpriced-cost.png`: existing comparison and unavailable pricing.
- `10-B-per-case-results.png`: per-case coverage.
- `13-Beatrice-settlor-original-Source.png` and `14-resolved-labels-with-original-quotes.png`: resolved names with original supporting Source material.
- `17-comparison-complete-Run-labels.png`: genuine F1 comparison across original A, control A′ and treatment B.

The Workbench presents an F1 comparison chart, exact pairing and individual aggregate panels; the table above supplies the full numeric side-by-side comparison. Its global scope warning reflects fresh A versus saved A′/B. The A′–B comparison itself has ten exact pairs and equal scope. Some observation display metadata inherits the original “Authored extraction” fixture label; the frozen manifests and verified lineage establish that actual retained live outputs were used.

No regressions or execution errors occurred, so there are no new failure screenshots. No new Runs, retries, merges, deployments or slide-deck updates were performed after B. All remaining work is interpretation.

## F. Questions for ChatGPT

1. How much weight should we give the perfect F1 when all improvement came from preferred-name labels in one already-inspected case?
2. Are two corrected labels worth ten calls, 9,821 tokens and roughly nine seconds when nine calls returned no edits and USD pricing is unavailable?
3. How should we present the unchanged strict quote-policy failures alongside provenance rates whose denominators grew after relationship corrections?
4. What further evidence would be needed before promoting this resolver beyond this synthetic exploratory experiment?
