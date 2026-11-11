# Case: Document Authority (Development)

## Purpose
Test whether the pipeline prioritises a formal signed deed over an earlier
informal meeting note when the two conflict.

## Intended Variable
Document authority. The combined source contains two documents:
- Note 1 (15 March 2023): Alice Chen *intends* Bob Chen to be the primary
  beneficiary of the Evergreen Family Trust. No formal changes made.
- Note 2 (10 January 2024): A signed deed of variation changes the sole
  beneficiary to Carol Wong and removes Bob Chen.

The answer key reflects the formal deed: Carol Wong is the sole beneficiary.
Bob Chen is excluded because the intention was never formalised, and the
deed explicitly removes him.

## Supported Relationship Types
`beneficiary_of`.

## Answer Key

### Entities
- Carol Wong (person, beneficiary)
- Evergreen Family Trust (trust)

### Relationships (1 edge)
1. Carol Wong → beneficiary_of → Evergreen Family Trust

**Deliberately excluded:** Bob Chen → beneficiary_of → Evergreen Family
Trust. The 2023 note is an intention, not a current fact. The 2024 deed
supersedes it.

## Source Audit (Bidirectional)

**Answer key → source:** The deed explicitly states Carol Wong is the sole
beneficiary. Evidence span recorded in `ground_truth.json`.

**Source → answer key:** The 2023 note mentions Bob as intended
beneficiary. This is a proposal, not a current fact. The 2024 deed
explicitly removes him. No other supported relationships are asserted.

## How to Test This Case

```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/authority/dev/case_1 \
    benchmark_v1/authority/dev/case_1/expected_extraction.json

    ## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 1, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (1/1 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. The single ground-truth edge (Carol as beneficiary) is supported
by the exact deed quote. Bob Chen is correctly excluded — the informal note
is not a current fact.

**Paid provider calls:** 0