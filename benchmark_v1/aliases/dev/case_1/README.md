# Aliases (Development)

`benchmark_v1_aliases_dev_1` belongs to development family
`benchmark_v1_aliases_1`. Resolve Margaret Wu / Margaret / Mrs. Wu and Daniel Wu / Daniel / Danny as the same respective people.

## Complete current answer key

- Margaret Wu → settlor_of → Ashford Family Trust
- Margaret Wu → spouse_of → Thomas Wu
- Margaret Wu → parent_of → Daniel Wu
- Thomas Wu → parent_of → Daniel Wu
- Daniel Wu → beneficiary_of → Ashford Family Trust

## Bidirectional audit

The settlor sentence refers locally to Margaret Wu and Ashford Family Trust. The spouse and child sentences support the spouse edge and both directed parent edges. The Danny sentence supports Daniel’s beneficiary edge. No trustee, additional child or other supported relationship is asserted.

One documentary note. Alias interpretation remains probabilistic; this authored ideal uses canonical full names and does not measure whether a model or resolver will recover them.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 5 TP, zero FP/FN, 5/5 approved-quote passes
and 5/5 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
