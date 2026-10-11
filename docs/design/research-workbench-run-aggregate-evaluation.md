# Research Workbench: Run → Observations → Aggregate Evaluation

Status: user-resolved contract, 2026-10-12, for design PR #114. This specifies future implementation; it changes no evaluator, runner, artifact or UI code. The [persistent Experiment/Run contract](research-workbench-experiment-run-contract.md) and existing authorization decisions remain in force.

## Frozen scope and observations

A Run executes one frozen pipeline configuration against selected benchmark inputs. An Observation is an individual case/sample/repetition evaluation within that Run. Preserve its Case/fixture identity, parent extraction sample, repetition, selected configuration, status, input/provenance references, evaluator output, relationships and Evidence. Resolver repetitions sharing an extraction are not independent fresh extractions; do not infer independent-sample confidence intervals.

Select all available Benchmark Cases by default, with uniform sample/repetition allocation across selected cases. Case selection is distinct from input/diagnostic-fixture selection: the current input loader includes multiple Case03 inputs and standalone diagnostic scenarios. Do not silently select duplicate Case03 samples or diagnostic fixtures merely because they are in that list. Freeze the resolved input selection and observation matrix explicitly. Any unequal allocation is disclosed as intentional weighting. Adding a repository case later does not expand an already frozen Run.

Each planned observation slot has a stable identity within the Run and is counted once. Frozen slots remain in the denominator of coverage even if extraction fails before downstream evaluation can occur. Continuation fills existing slots; it does not duplicate them. No baseline/treatment mixture is permitted in a Run aggregate: include only observations belonging to the Run's selected configuration. Retain any separate diagnostic/comparator results for inspection without counting them in that aggregate.

## Primary metric: observation-weighted micro-F1

Let P be the non-empty set of frozen planned observation slots. Let S be the subset with successful completion and a valid, available evaluator result. A completed status alone does not imply an available evaluation. Failed, missing, uncertain or unavailable observations are not in S.

For the existing semantic relationship counts of each observation i in S:

```text
TP = Σ TP_i
FP = Σ FP_i
FN = Σ FN_i
D  = 2 × TP + FP + FN

Run F1 = null             when |S| = 0
       = 0                when |S| > 0 and D = 0
       = 2 × TP / D       otherwise
```

Pool integer counts, never averaged or rounded F1 values. Never union relationship sets across observations or cases: repeated labels/edges in two observations contribute independently. Larger cases and additional scored repetitions carry more weight by definition. Version this new aggregate as `observation_micro_f1_v1`; it does not rename or alter any existing evaluator metric or historical summary.

Retain per-case pooled counts/F1 using the same rule, all individual results and per-case coverage. Preserve existing relationship and provenance evaluation semantics and outputs; provenance accuracy is not blended into relationship F1. Case-balanced/macro aggregation is deferred until separately defined and versioned. Do not claim that micro-F1 exposes case-specific failures without the accompanying detail.

## Coverage and one-point chart eligibility

The backend returns planned and scored counts, total and per-case coverage, and explicit non-scored counts/reasons. Use a disjoint coverage partition: scored, pending/not attempted (including currently running), failed, uncertain, and unavailable/missing result. Retain detailed underlying execution statuses separately. An upstream failure leaves each affected planned slot non-scored with a reason; it does not silently reduce P. Coverage counts must sum to the frozen planned count without counting a slot twice.

- `complete`: all planned slots are scored, regardless of whether scores are high or zero.
- `provisional`: at least one slot is scored but some planned slots are not.
- `unavailable`: no slot is scored; F1 is null.

Evaluation completeness is separate from execution lifecycle: a terminal Run can have incomplete evaluation coverage. Provisional aggregates describe only scored survivors and must disclose that selection bias. Retain Runs with no score in history and show why they have no numeric point.

Each eligible Run contributes exactly one point on F1 by Run, based on its aggregate, and at most one on F1 versus Cost. Visually distinguish provisional points from complete points and expose overall/per-case scored/planned coverage and failure/uncertainty counts. As results arrive, update that Run's provisional point rather than appending observation points. Observation, relationship and exact Evidence drill-down remains available; unavailable outputs have explicit reasons, never fabricated Evidence or zero scores.

Filters selecting Runs do not recompute their score over an undisclosed subset of observations. Any observation-level inspection remains separate from the primary frozen-scope Run aggregate. Both charts use the same Run F1 and selection.

## Comparable benchmark scope versus exactly matched inputs

The backend returns comparable-scope identity plus explicit differences. Scope includes stable Case/fixture selection, frozen Source and ground-truth versions/digests, evaluator and aggregation versions, input mode/cohort, and per-case sample/repetition allocation. Human-readable labels are display metadata, not scientific matching keys. Preserve configuration, model, code/dependency/prompt and evaluator differences in provenance.

Keep differing scopes visible with their differences disclosed. Do not present an unqualified improvement claim across scope mismatches or unequal/provisional coverage. Matching planned scope alone does not establish matching scored coverage. Runs evaluated with different configurations can share benchmark scope, but their configuration/provenance differences must remain inspectable.

Exactly matched inputs additionally require independently verified, unambiguous frozen Source, truth, cohort and extraction identities, with an explicit observation pairing. Do not pair by display name, Run order or repetition number alone. Identical saved extractions can support stronger paired comparisons; fresh extractions remain unpaired unless exact matching is independently established. Retain unmatched observations and exclusion reasons. Neither scope equality nor matching authorizes combining unrelated historical records into one Run.

## Primary cost: estimated provider spend incurred by the Run

Let A be the unique incurred provider attempts attributable to this Run across its lifecycle/continuations. Use authoritative attempt identities to prevent duplicate charging. For each attempt a, C_a is its estimated provider cost derived from retained usage and applicable model/pricing/currency provenance.

```text
Known subtotal = Σ C_a over attempts with known costs
Unpriced count = number of incurred attempts with unavailable costs

Run cost = null             when Unpriced count > 0
         = Known subtotal   otherwise
```

Count all incurred attempts, including known-cost failures and non-scored work. Count each fresh extraction attempt once even when its output feeds multiple resolver repetitions. Exclude spending on historical saved extractions; a saved deterministic replay with no provider attempts has a known zero provider cost. This is provider spend, not local compute cost or a guaranteed invoice amount. Do not label recorded/simulated usage as incurred live provider spend.

Unknown usage or pricing, including an uncertain incurred attempt whose cost cannot be established, leaves Run cost unavailable. Preserve the known subtotal, unpriced count and exclusion reasons; never plot the subtotal as if it were the complete total. Do not silently sum incompatible currencies or reprice historical usage using today's rates.

F1-versus-Cost eligibility requires both an available Run F1 and a complete known Run cost. Provisional F1 can be plotted with its provisional treatment when cost is known. Missing cost excludes only the cost-chart point, not the Run from history, F1 by Run or inspection. Show workload, input mode and coverage when interpreting cost differences.

Retain reconstructed full-pipeline cost as a separately labelled secondary measure with its own scope, pricing provenance and availability. Existing single-pipeline estimates may add a shared extraction to each resolver repetition for illustration; never sum those estimates as Run spend. Do not invent a new Run-wide reconstructed-cost formula in this change.

## Backend, artifacts and compatibility

Backend aggregation owns slot membership, eligibility, integer pooling, completeness, scope comparison and cost accounting. The existing versioned Research Workbench API exposes the aggregate version, counts, F1, coverage/state, scope and provenance references, cost/subtotal/unpriced count, chart eligibility and reasons, plus observation drill-down. React displays these values; it does not aggregate, evaluate, pair observations or calculate spending.

Freeze the observation plan, selected inputs, relevant case metadata and required evaluation/pricing provenance in authoritative artifacts under an explicitly versioned future contract. Immutable observations and append-only lifecycle/attempt records remain authoritative. Aggregate projections are reproducible from those records; PostgreSQL is rebuildable. Retain aggregate version and source artifact identities/digests so a projection cannot silently mix changed inputs or policies. Corrupt or insufficient evidence yields an unavailable aggregate with reasons, not inferred counts from rounded F1.

Issue #92 manifests, results, checksums, summaries, identities and existing cohort means remain byte-for-byte unchanged. Existing study bundles can mix baseline/treatment configurations and therefore must not be silently presented as a new single-configuration Run. Do not rename resolver repetitions into Runs or fabricate a planned matrix. Preserve their existing read-only inspection and summary views.

Any later compatibility adapter must explicitly establish a trustworthy single-configuration Run mapping, planned membership, evaluator count provenance and attempt attribution before exposing this aggregate. If those facts cannot be established, report aggregate/comparability/cost unavailable as appropriate. Keep derived adapter output separate, versioned and traceable to the original artifacts; never rewrite old manifests. Missing display metadata uses the already-agreed fallback labels.

Evolve artifact/API schemas deliberately and retain supported legacy readers. Index schema changes require a new Alembic migration; rebuilding the index must reproduce new aggregates and legacy exclusions. This documents migration requirements without implementing migration or altering Run identity.

## Deterministic acceptance criteria for implementation

1. Two scored observations `(TP, FP, FN) = (8, 2, 2)` and `(1, 0, 3)` produce totals `(9, 2, 5)` and F1 `18/25 = 0.72`, not their mean F1 `0.60`. Identical relationship labels in the two observations do not deduplicate across observations.
2. Repeating the second observation once produces `(10, 2, 8)` and F1 `20/30`; the extra weight is disclosed. Per-case counts/results and sample/repetition identities remain inspectable. Input/observation order does not alter totals; duplicate slot identities must not double-count.
3. A scored all-zero count observation yields valid F1 `0`. No scored observations yields null F1 and no numeric point. Failed/missing observations never enter pooling as zeros; completed-without-evaluation remains non-scored.
4. The two scored observations from criterion 1 plus one failed planned slot retain F1 `0.72`, coverage `2/3` and provisional status. Per-case coverage reveals the failed case. Fully attempted execution with failures is not evaluation-complete. Upstream extraction failure preserves all affected planned slots; coverage partitions sum to planned counts.
5. Completion of a remaining slot updates the same Run point and completeness; continuation/reindexing creates neither extra points nor duplicate counts. Distinct Runs remain distinct even with equal configurations/scores. All observations and existing relationship/Evidence drill-down remain accessible.
6. Default selection contains every available Benchmark Case, with uniform allocation, without selecting every alternate historical/diagnostic input automatically. Frozen membership remains unchanged after a new repository case or label appears; unequal explicit allocation is reported.
7. Changing Case/fixture set, Source/truth version, evaluator/aggregate version, cohort/input mode or allocation reports scope differences. Label-only changes do not change matching identity. Fresh samples are unpaired absent verified exact matching; ambiguous saved-input matches are excluded. Provisional/mismatched coverage never produces an unqualified improvement claim.
8. One fresh extraction costing `0.10`, two resolver attempts costing `0.02` each, and one known-cost failed attempt costing `0.01` produce Run cost `0.15`, regardless of shared-extraction repetitions. Reused historical extraction spending is excluded. A provider-free replay costs `0`.
9. Adding one unpriced incurred attempt to criterion 8 leaves subtotal `0.15` but null Run cost, an explicit exclusion reason and no cost-chart point; F1 by Run remains eligible if scored. Duplicate attempt records cannot charge twice. Pricing/currency incompatibility cannot produce a misleading numeric total.
10. Rebuilding projections from authoritative artifacts reproduces values, coverage, names and provenance. Supported Issue #92 artifacts retain byte-identical manifests/results/checksums and unchanged legacy summaries. Missing mapping/count/attempt evidence produces explicit compatibility exclusions, never silent backfill or baseline/treatment pooling.
11. API and frontend tests verify one point per eligible Run, provisional styling, exact backend-provided values and coverage/reasons, with per-observation Evidence drill-down. Deterministic tests substitute provider boundaries; no experiment or paid call is needed.

## Evidence and review

The existing [evaluator](../../private_client_graph/evaluation.py) provides per-observation semantic counts and zero-denominator behavior. [Research results](../../private_client_graph/research/results.py) allow unavailable evaluations. Existing [summary aggregation](../../private_client_graph/research/summary.py) produces repetition distributions and cohort/input means, and separates attempt spend from single-pipeline estimates. [Comparison](../../private_client_graph/workbench/comparison.py) verifies frozen inputs. This contract adds an explicitly versioned projection rather than changing those semantics.

Code Quality Review: documentation-only contract; no production changes, evaluator changes, migrations or experiments. Acceptance examples are arithmetic specifications for future deterministic tests. Review covers complete changed documentation, consistent references and removal of obsolete undefined-aggregation language.
