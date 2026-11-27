# Semantic Evidence

Semantic Evidence compares the quotations attached to a retained Benchmark v4
relationship with the approved evidence members for that relationship. It is an
**AI-assisted, unverified** diagnostic alongside the deterministic benchmark.

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
| Evidence Support | Targets with at least one matched required member divided by 71. |
| Proof Completion | Targets with a fully matched approved alternative divided by 71. |
| Multi-Source Evidence Coverage | For each Multi-Source target, take the highest matched-member fraction of its approved alternatives. Sum those fractions and divide by 30, giving equal weight to each target. |

Missing relationships and unavailable graphs contribute zero. Failed or absent
judgments retain all exact credit. Proof Completion and Multi-Source Evidence
Coverage therefore cannot fall below their deterministic counterparts. The
previous independent sufficiency percentages do not apply to these measures.

Workbench Run inspection and comparison show the exact baseline alongside
the additional matches. Inspect required quotations, attached quotations and
Source IDs, differences identified by the judge, and route completion.
Diagnostics retain execution coverage, invalid results, partial equivalence,
and estimated cost and latency.

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
uv run python -m private_client_graph.research.semantic_evidence report ASSESSMENT_DIRECTORY
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
