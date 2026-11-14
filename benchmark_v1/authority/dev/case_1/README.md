# Document Authority (Development)

`benchmark_v1_authority_dev_1` belongs to development family
`benchmark_v1_authority_1`. Distinguish informal future intention from an executed deed while retaining unchanged family facts.

## Complete current answer key

- Carol Wong → beneficiary_of → Evergreen Family Trust
- Alice Chen → parent_of → Bob Chen

## Bidirectional audit

The note supports Alice→Bob parent_of, not a current Bob beneficiary edge. The deed supports Carol’s current beneficiary edge and explicitly removes Bob. No settlor, spouse or additional family relationship is asserted. Bob remains an entity because of his supported parent edge.

Two documents: the 15 March 2023 file note (note_01), then the 10 January 2024 executed deed (note_02). The documents also differ in date and effective status, so this is not an isolated causal test of document authority.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 2 TP, zero FP/FN, 2/2 approved-quote passes
and 2/2 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
