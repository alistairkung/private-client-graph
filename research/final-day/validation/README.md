# Benchmark review request

Status: awaiting human benchmark approval. No held-out evaluation has run.

Start with the [case index](../../../evaluation_cases/README.md), then the
independent validation summaries: [batch 1](batch-01.md) and [batch 2](batch-02.md).
The held-out set has 10 cases, 39 current relationships and 14 Sources. Each
case directory includes its hypothesis, original Sources, complete answer key,
approved exact Source/quote pairs and authored ideal extraction/state.

## Personal review of development Cases 04 and 05

| Case | Source documents | Complete answer key | Expected current state |
| --- | --- | --- | --- |
| [04: multi-source](../../../cases/case_04/README.md) | [First note](../../../cases/case_04/sources/note_01.txt), [follow-up](../../../cases/case_04/sources/note_02.txt) | [Ground truth](../../../cases/case_04/ground_truth.json) | Seven edges. Andrew's beneficiary support can come from either Source; the ideal preserves both. Lucy and Marcus have no asserted family links. |
| [05: trustee replacement](../../../cases/case_05/README.md) | [Initial note](../../../cases/case_05/sources/note_01.txt), [replacement note](../../../cases/case_05/sources/note_02.txt) | [Final truth](../../../cases/case_05/ground_truth.json), [initial control](../../../cases/case_05/ground_truth_after_note_01.json) | Six current edges. Rachel replaces David as trustee, effective 10 September 2026. The other five relationships retain earlier support. |

## Held-out spot checks and approval

Choose any cases from the index for spot checks. Useful contrasting examples are
[explicit alias](../../../evaluation_cases/heldout_03/README.md),
[reverse-supplied chronology](../../../evaluation_cases/heldout_06/README.md), and
[duplicate Source titles](../../../evaluation_cases/heldout_08/README.md).

Confirm that the answer keys are complete, each approved quote supports its
relationship in the identified Source, historical relationships are excluded
appropriately, and the stated difficulty is suitable. Review any validator
uncertainties before approving the held-out benchmark.

The independent validator found no semantic blockers. These are short, explicit
synthetic checks with limited distribution coverage. Exact approved-quote
matching may reject a valid shorter quote, so distinguish that diagnostic from
relationship correctness. Authored ideals are not measured model results.

Approval freezes the reviewed dataset for the final run after the extraction
chain is frozen. It does not authorize tuning against held-out outcomes, changing
truth to improve scores, merging pull requests, or deploying. Requested changes
will be reviewed and revalidated before evaluation.
