# Case: Aliases (Development)

## Purpose
Test whether the pipeline resolves different surface forms of the same person
into one entity, rather than creating duplicate entities.

## Intended Variable
Aliases. The source document refers to the same people by multiple names:
- Margaret Wu / Margaret / Mrs. Wu (same person)
- Thomas Wu / her husband (same person)
- Daniel Wu / Daniel / "Danny" (same person)

All other dimensions are held stable: explicit family roles, single document,
cooperative language, one trust.

## Supported Relationship Types
`settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`.

## Answer Key

### Entities
- Margaret Wu (person, settlor, spouse, parent)
- Thomas Wu (person, spouse, parent)
- Daniel Wu (person, child, beneficiary)
- Ashford Family Trust (trust)

### Relationships (5 edges)
1. Margaret Wu → settlor_of → Ashford Family Trust
2. Margaret Wu → spouse_of → Thomas Wu
3. Margaret Wu → parent_of → Daniel Wu
4. Thomas Wu → parent_of → Daniel Wu
5. Daniel Wu → beneficiary_of → Ashford Family Trust

## Source Audit (Bidirectional)

**Answer key → source:** Every edge has explicit support in the source text.
(Evidence spans recorded in `ground_truth.json`.)

**Source → answer key:** No additional supported relationships asserted.
- "Her husband" implies Thomas is male. Not a graph edge.
- "One child" implies Daniel has no siblings. Not a graph edge.
- No mention of other family members, trustees, or additional trusts.

## How to Test This Case

### Run the extractor
The current CLI is hardcoded to Case 01. To run this case, the extractor must be
pointed at `benchmark_v1/aliases/dev/case_1/source.txt` and the result saved
to a run artifact in this folder.

*(Implementation: see `benchmark_v1/run_case.py` once available.)*

### Evaluate
Compare the extracted graph against `ground_truth.json` using the existing
`evaluate_graph` function. Report:
- TP / FP / FN
- Precision / Recall / F1
- Relationship Provenance Accuracy
- Axis Failure: did the model create duplicate entities for Margaret/Daniel?

### Expected result
- **Pass:** 5 TP, 0 FP, 0 FN, perfect provenance, no duplicate entities.
- **Fail (alias resolution):** Fewer than 5 TP because "Danny" was treated as a
  separate entity from Daniel Wu, or "Mrs. Wu" as a separate person from Margaret.
- **Fail (other):** Any missed or hallucinated edge not related to aliases should
  be recorded separately as an extraction failure, not an axis failure.

## How to Interpret the Result
- If the model passes: the pipeline handles simple alias resolution.
- If the model fails on alias edges only: the pipeline has an alias-resolution gap.
- If the model fails on non-alias edges: the failure is unrelated to this axis.
  Record it separately.

## Not Included
- Multiple documents (single document only)
- Distractors (no irrelevant named people)
- Temporal changes (no historical relationships)
- Prompt injection (no embedded instructions)

## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 5, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (5/5 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. All 5 ground-truth edges are supported by exact source quotes.
This does not measure model performance — it verifies schema compatibility
and internal consistency.

**Paid provider calls:** 0