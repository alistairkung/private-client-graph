# Distractors (Development)

`benchmark_v1_distractors_dev_1` belongs to development family
`benchmark_v1_distractors_1`. Ignore irrelevant named people and future requests while extracting all asserted supported facts.

## Complete current answer key

- Helen Park → settlor_of → Juniper Family Trust
- Helen Park → spouse_of → Simon Park
- Helen Park → parent_of → Chloe Park
- Simon Park → parent_of → Chloe Park
- Chloe Park → beneficiary_of → Juniper Family Trust

## Bidirectional audit

The local Helen/she and they references establish the settlor, spouse and both directed parent edges. The final sentence establishes Chloe’s beneficiary edge. Andrew and Rachel have no asserted supported roles. Cousin is outside the relationship vocabulary; Peter’s requested beneficiary role is explicitly not current. No sibling or other family edge follows from the cousin label.

One documentary note. The beneficiary proposal adds factual-status interpretation to the named distractors; record failures separately rather than attributing every error to distractors.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 5 TP, zero FP/FN, 5/5 approved-quote passes
and 5/5 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
