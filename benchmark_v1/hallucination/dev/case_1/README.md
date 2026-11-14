# Incremental Hallucination (Development)

`benchmark_v1_hallucination_dev_1` belongs to development family
`benchmark_v1_hallucination_1`. Separate current relationships from proposed trust appointments within a draft note.

## Complete current answer key

- Gregory Ashby → settlor_of → Ashby Family Trust
- Gregory Ashby → spouse_of → Patricia Ashby
- Gregory Ashby → parent_of → Emma Ashby
- Patricia Ashby → parent_of → Emma Ashby
- Gregory Ashby → parent_of → James Ashby
- Patricia Ashby → parent_of → James Ashby
- Emma Ashby → beneficiary_of → Ashby Family Trust
- Gregory Ashby → sibling_of → Margaret Ashby

## Bidirectional audit

The current-position paragraph supports seven edges. The “his sister, Margaret Ashby” clause supports the eighth edge despite appearing in the proposals paragraph. That paragraph does not establish Margaret as trustee. The current trustee is unnamed and has no recoverable named endpoint. We retain asserted relationships, without deriving Emma–James sibling closure from the shared-parent facts. No other supported edge is asserted.

One documentary note. Draft status does not negate the explicitly stated current facts or the existing sister relationship embedded in proposed appointment language.

## Offline reproduction

Select this case in the Workbench and follow the saved replay instructions.
The authored ideal yields 8 TP, zero FP/FN, 8/8 approved-quote passes
and 8/8 approved Source/quote associations. This checks the fixture and
deterministic pipeline. [Benchmark plan](../../../../docs/workflows/benchmark-plan.md)
