# Deterministic Evidence Quality v1

The Workbench and CLI use the reporting version `deterministic_evidence_quality_v1`.
The report derives quality metrics from a verified Run, its frozen reference and
the protected scorers. The independent methodology audit
rejected the [combined Evidence-Grounded F1 proposal](https://github.com/alistairkung/private-client-graph/pull/224) because 42 of the 113
qualified relationships could never earn grounded credit. Graph and proof
scores answer separate questions and have separate denominators.

| Measure | Scope and definition |
| --- | --- |
| Benchmark v4 Graph F1 | 35 inputs under mixed references, including U8. Pool semantic TP, FP and FN before calculating precision, recall and micro-F1. |
| Qualified Graph F1 | The same relationship scorer over the 34 original Conditions and their 113 expected relationship instances. |
| Complete Proof Rate | Complete formal targets divided by all 71 planned formal targets on the qualified cohort. |
| Joint-only Complete Proof Rate | Complete joint-only targets divided by the 30 planned joint-only targets. These targets already contribute to the overall proof rate. |
| Joint-only Best-Alternative Evidence Coverage | The mean fraction of exact required pairs matched on the most-covered single route for each of the 30 planned joint-only targets. Every target has equal weight. |

The protected formal evaluator credits one complete proof when every required
exact Source ID and verbatim quotation pair from any one approved alternative
is attached to the correct canonical edge. Alternative routes are evaluated
separately. A different Source, different quotation, or pair attached to
another edge earns no credit for that member. Repeated pairs count once after
canonical construction. Relationships with ordinary evidence but no formal
target are still graph-scored. U8 keeps its separate adjudicated citation
overlap diagnostic and supplies no formal targets.

For each joint-only target, the diagnostic divides the number of attached
required pairs by the number of pairs in each frozen route and keeps the
maximum fraction. For example, attaching two of three required pairs gives
two-thirds coverage even when the proof remains incomplete. Full coverage is
equivalent to completing an approved route. The best route can change across
Runs. The inspector shows exact matched and missing members so a reviewer can
check which pairs changed. Extra attachments do not reduce coverage. The
fraction describes recovery of reference members. Legal sufficiency is outside
the scope of this diagnostic. Documentary sufficiency is
established for scoring by completing a whole approved route.

## Run state and denominators

The historical planned-roster denominators apply to each reported value.
Missing relationships and unavailable graphs earn zero proof and coverage
credit. Terminal provider, parsing and graph-construction failures and
uncertain observations retain their original outcomes. A valid empty graph is
a successful construction and is graph-scored normally.

Provisional results keep the full planned denominator and display observed
input and target counts. Unexecuted slots contribute zero to provisional
numerators and remain distinguishable from terminal failures. A slice with
no observations shows an unavailable metric. Proof metrics are also unavailable
for a slice with no targets. Numeric comparison deltas require two complete Runs
with compatible frozen benchmark and scorer commitments, metric version and
observation origin. The cost plot requires verified pricing and usage and
complete Runs. A measured zero remains a valid plot value.

## Replay and export

Set `PCG_BENCHMARK_V4_CUSTODY` to the verified private custody root. For
Benchmark v4, both commands print the same report to stdout:

```sh
uv run python -m private_client_graph.research inspect RUN_DIRECTORY
uv run python -m private_client_graph.research summarize RUN_DIRECTORY
```

The `quality` object carries the metric version, benchmark and scorer
commitments, reference and observation origin, graph counts, rates, and
planned and observed denominators. `benchmark_v4` retains the U8 diagnostic
and `qualified_protocol` retains the historical proof outcome breakdown.
`inspect RUN_DIRECTORY --include-proof-members` adds per-target alternatives
and exact reference quotations to a **private** report. Keep that output in
private custody. The default summary omits those quotations.

For the frozen v3 baseline, use the inventory-verified historical adapter:

```sh
uv run python -m private_client_graph.research inspect-v3-baseline ARCHIVE_DIRECTORY ADMISSIONS.json
```

The same optional `--include-proof-members` flag applies. Retained v3 and v4
replays require no provider calls and print without writing to Run custody.

| Retained Run | Mixed Graph F1 | Qualified Graph F1 | Complete proofs | Joint-only complete | Mean joint-only coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Benchmark v3 first live baseline | — | 85.05% | 18/71 (25.35%) | 0/30 | 4.33% |
| Benchmark v4 Extractor v1 | 92.50% | 92.11% | 11/71 (15.49%) | 0/30 | 4.33% |
| Benchmark v4 Extractor v1 + Generative Resolver | 91.74% | 91.30% | 11/71 (15.49%) | 0/30 | 4.33% |

Both v4 Runs have five joint-only targets with nonzero coverage, one at
one-half and four at one-fifth. The two Runs have identical coverage on each
of the 30 targets. These diagnostic figures are derived from retained
attachments and frozen alternatives.
