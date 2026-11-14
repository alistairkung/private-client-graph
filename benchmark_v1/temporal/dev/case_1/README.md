# Temporal Precedence (Development)

`benchmark_v1_temporal_dev_1` belongs to development family
`benchmark_v1_temporal_1`. Extract the final current graph after an explicitly completed trustee replacement.

## Complete current answer key

- Elaine Ho → settlor_of → Willow Family Trust
- Elaine Ho → spouse_of → Martin Ho
- Elaine Ho → parent_of → Sophie Ho
- Martin Ho → parent_of → Sophie Ho
- Sophie Ho → beneficiary_of → Willow Family Trust
- Rachel Lim → trustee_of → Willow Family Trust

## Bidirectional audit

The first note supports five unchanged family/trust edges. The second explicitly preserves those facts, records David’s resignation and supports Rachel’s completed appointment and current sole trusteeship. Both Rachel quotes are approved. No other named trustee or family relationship is asserted. The historical David edge is excluded only from this final-current scope.

Two dated file notes (note_01 then note_02). Full-context extraction interprets the explicitly effective final position; this fixture does not claim sequential mutation, temporal storage, or arbitrary historical snapshot selection.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 6 TP, zero FP/FN, 6/6 approved-quote passes
and 6/6 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
