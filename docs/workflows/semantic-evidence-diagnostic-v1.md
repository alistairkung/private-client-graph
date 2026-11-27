# Ground-Truth-Aligned Evidence Evaluation

PCG Evaluation uses one frozen Benchmark v4 population to assess whether PCG
found the expected relationships and recovered their approved supporting evidence.
Graph F1 uses the existing scorer and all 34 qualified Conditions. The mixed
35-input score remains available as a diagnostic. Evidence uses 71 formal proof
targets, including 30 Multi-Source targets.

## Matching contract

- Read the 71 formal targets and their approved Sufficient Evidence Alternatives
  from the frozen qualified cohort. Use the existing deterministic matcher for
  exact Source–quotation pairs, including its 30 Multi-Source targets.
- For each unmatched required member, consider the verbatim quotations attached
  to the same relationship from that member's original Source. Check each
  attachment against the frozen Source text. Group eligible pairs into one
  request per target. An unmatched member from an absent Source gets no request
  or credit. Exact members need no judgment.
- The approved quotation defines the comparison target. The actual quotation
  must convey its material content on its own. Preserve identity, relationship
  direction, negation, dates, operative timing, authority, and conditions when
  material to that member. No facts may be imported from the reference, other
  pairs, or background knowledge. Any date or cutoff expressed by the reference
  is material. An unspecified benchmark cutoff is never inferred.
- Require one structured decision per requested pair. The four outcomes are
  Equivalent, Partially Equivalent, Not Equivalent, and Uncertain. Equivalent
  earns member credit. Preserve the reason and material differences for
  inspection. Partial, uncertain, invalid, and absent results earn no semantic
  credit. Validate pair identifiers, completeness and uniqueness mechanically.
- Union the exact and accepted member IDs, then score each approved route
  separately. Credit a member once within a route, even when several actual
  quotations match it. One quotation can match several members only if it
  independently contains the material content of each. Never pool members
  from distinct alternatives to create a new route.

## Metrics and inspection

| Metric | Calculation |
| --- | --- |
| Graph F1 | Existing qualified Graph F1, computed from TP, FP and FN, including delivery failures. |
| Evidence-Adjusted F1 | Custom weighted score using the qualified graph counts and the additional penalty for recovered formal targets without complete proof. |
| Evidence Support | Targets with at least one matched required member divided by 71. |
| Proof Completion | Targets with a fully matched approved alternative divided by 71. |
| Multi-Source Evidence Coverage | For each Multi-Source target, take the highest matched-member fraction of its approved alternatives. Sum those fractions and divide by 30, giving equal weight to each target. |

Evidence-Adjusted F1 is a custom weighted F1-style metric alongside
conventional Graph F1. Its formula is `2TP / (2TP + FP + FN + αU)`. All four
counts use the same 34 qualified Conditions. `U` counts recovered formal proof
targets with no complete approved alternative under the displayed evaluation
state. The 42 expected relationships outside the formal proof targets carry
no additional evidence penalty. Missing formal targets count through graph FN,
and incorrect relationships count through graph FP.

The fixed weight `α = 71/113` reflects formal annotation coverage. It is a
design choice without statistical calibration. A zero denominator yields
zero, following Graph F1. With `U = 0` the scores coincide. Each completed
proof can remove one penalty, with no partial-proof weight. For a fixed
expected graph, recovering a missed relationship changes TP by +1 and FN by
−1. Even when it adds one evidence penalty, the numerator rises by 2 and
the denominator by only `1 + α`.

For the retained Extractor v1 exact-only baseline, TP = 105, FP = 10,
FN = 8 and `U = 56` (67 recovered formal targets less 11 complete routes).
Graph F1 is **92.11%** and Evidence-Adjusted F1 is **79.79%**. Model-assessed
proof completions only enter the headline once the evaluation finishes.

Missing relationships and unavailable graphs contribute zero. Exact credit
survives all review outcomes. Before a plan exists the report shows an exact-only
baseline. A pending assessment also shows that baseline, even if some pairs
already have decisions. Interrupted or unsealed attempts keep the assessment
pending. After all eligible targets have retained outcomes, the report combines
exact and Equivalent matches. Invalid responses and provider failures add no
credit and are identified separately.

Only completed evaluations free of invalid responses and provider failures
are eligible for evidence change comparisons. Comparisons also require the
same frozen populations, approved routes, scoring scope, model settings and
prompt. Exact-only and pending evidence values remain visible with their
state and evidence changes are withheld. Qualified Graph F1 changes remain
available across compatible Runs. A committed plan with no eligible pairs
completes without provider access.

The Workbench shows both F1 scores above the three supporting evidence metrics,
a confusion matrix and expandable evidence diagnostics. The F1 details expose
`U`, `α` and the number of proofs completed through equivalence. Inspect approved
and actual Source-attributed quotations, exact and model-assessed matches, material differences, proof routes,
judgment coverage, invalid responses, costs and latency. The configured judge is
DeepSeek V4 Pro (`deepseek-v4-pro`). Reports retain its settings and prompt
commitment and record the returned model and token usage. Model-assessed
equivalence has no independent verification.

## Plan, approve, and inspect

Use the existing private Workbench artifact root and set
`PCG_BENCHMARK_V4_CUSTODY` to the verified frozen workload. This stage reads
completed Runs and runs no extraction or resolution. It freezes the expected
proof routes, original Source attribution, exact packets, model, prompt, and
request digests. Old independent sufficiency judgments are ineligible. If an
old plan occupies the assessment path, move it aside before creating a fresh
plan. There is no registration step for an old baseline.

```sh
uv run python -m private_client_graph.research.semantic_evidence initialize-task ARTIFACT_ROOT
uv run python -m private_client_graph.research.semantic_evidence plan \
  ARTIFACT_ROOT RUN_ID --peak-rates INPUT OUTPUT \
  --usd-ceiling APPROVAL_CEILING --task-call-ceiling APPROVAL_ATTEMPTS
uv run python -m private_client_graph.research.semantic_evidence report ARTIFACT_ROOT --run-id RUN_ID
uv run python -m private_client_graph.research.semantic_evidence compare ARTIFACT_ROOT LEFT_RUN_ID RIGHT_RUN_ID
```

The plan prints its digest, maximum attempts and conservative peak estimate.
Verify the [DeepSeek peak rates](https://api-docs.deepseek.com/quick_start/pricing/)
before approving the exact plan. The shared ledger starts with zero authority.
Execute only with explicit approval and the verified rates.

```sh
uv run python -m private_client_graph.research.semantic_evidence run ASSESSMENT_DIRECTORY \
  --approve-plan-sha256 APPROVED_DIGEST --approval-reference OWNER_APPROVAL \
  --verified-peak-rates INPUT OUTPUT
```

The shared task ceiling, per-plan USD ceiling, no-retry policy, sealed
receipts and provider token accounting apply. Explicit `--reuse-from RUN_ID`
can reuse valid decisions with the same target, request digest and original
Source attribution under the same frozen benchmark and judge contract.
Reporting and comparison use retained data without calling the provider.

## Provider-free verification

Exercise the frozen plan, mocked DeepSeek transport, report and comparison
output, and Workbench display. Cover exact-only, paraphrase, missing facts,
wrong Source, relationship direction, date and authority changes, multiple
routes, malformed results, fixed denominators, and retained execution controls.
