# Case: Temporal Precedence (Development)

## Purpose
Test whether the pipeline resolves a completed trustee replacement within a
combined text, outputting only the *current* trustee and excluding the
historical trustee.

## Intended Variable
Temporal precedence. The combined source contains two dated file notes:
- Note 1 (1 September 2026): David Ng is the trustee.
- Note 2 (15 September 2026): David Ng has resigned; Rachel Lim is the
  replacement trustee.

The answer key reflects the current state as at 15 September 2026:
Rachel Lim is the trustee. David Ng is excluded.

All other facts are held stable across both notes.

## Supported Relationship Types
`settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`, `trustee_of`.

## Answer Key

### Entities
- Elaine Ho (person, settlor, spouse, parent)
- Martin Ho (person, spouse, parent)
- Sophie Ho (person, child, beneficiary)
- Rachel Lim (person, trustee)
- Willow Family Trust (trust)

### Relationships (6 edges)
1. Elaine Ho → settlor_of → Willow Family Trust
2. Elaine Ho → spouse_of → Martin Ho
3. Elaine Ho → parent_of → Sophie Ho
4. Martin Ho → parent_of → Sophie Ho
5. Sophie Ho → beneficiary_of → Willow Family Trust
6. Rachel Lim → trustee_of → Willow Family Trust

**Deliberately excluded:** David Ng → trustee_of → Willow Family Trust.
This is a historical edge, not the current state.

## Source Audit (Bidirectional)

**Answer key → source:** Every edge has explicit support in the combined
source text. Evidence spans are recorded in `ground_truth.json`.

**Source → answer key:** The source asserts David Ng as trustee in note 1,
but note 2 records his resignation. The final state excludes him. No other
supported relationships are asserted. No other family members or trusts
are mentioned.

## How to Test This Case

### Contract check (no model call)
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/temporal/dev/case_1 \
    benchmark_v1/temporal/dev/case_1/expected_extraction.json
    ## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 6, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (6/6 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. All 6 ground-truth edges are supported by exact source quotes.
The historical trustee edge (David Ng) is correctly excluded from the
answer key.

**Paid provider calls:** 0