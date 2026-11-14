# Cross-Source Reconciliation (Development)

`benchmark_v1_cross_source_dev_1` belongs to development family
`benchmark_v1_cross_source_1`. Combine complementary facts from two emails and preserve the Source identity for each selected quote.

## Complete current answer key

- Alice Chen → settlor_of → Oakwood Trust
- David Chen → settlor_of → Oakwood Trust
- Alice Chen → spouse_of → David Chen
- Bob Chen → beneficiary_of → Oakwood Trust
- Alice Chen → parent_of → Bob Chen

## Bidirectional audit

Email 1 explicitly supports the two settlor edges and spouse edge; its From header identifies Alice as the speaker. Email 2 is addressed to Alice and calls Bob “your son”, supporting Alice→Bob parent_of and Bob’s beneficiary edge. Registration is not a supported graph primitive. No David→Bob parent edge is inferred.

Two complementary emails, dated 12 and 14 April 2026 (note_01, note_02). The complete graph needs both documents. No update or historical-state operation is required.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 5 TP, zero FP/FN, 5/5 approved-quote passes
and 5/5 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
