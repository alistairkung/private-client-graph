# Case: Temporal Precedence — Divorce (Development)

## Purpose
Test whether the pipeline excludes a superseded spouse edge after a completed
divorce, while preserving all unaffected family and trust edges.

## Intended Variable
Temporal precedence (divorce). The combined source contains two dated notes:
- Note 1 (10 January 2025): Alice and Benedict Tan are spouses and parents
  of Chloe Tan. Chloe is a beneficiary of the Pemberton Family Trust.
- Note 2 (20 March 2026): Alice and Benedict finalised their divorce on
  15 March 2026. The marriage is legally dissolved.

The answer key reflects the current state as of the evaluation date.
The spouse edge is **absent** from the ground truth because the divorce
supersedes it. If the model extracts the spouse edge, it is counted as a
false positive — a failure of temporal reasoning.

## Answer Key
### Required edges (4)
1. Alice Tan → settlor_of → Pemberton Family Trust
2. Alice Tan → parent_of → Chloe Tan
3. Benedict Tan → parent_of → Chloe Tan
4. Chloe Tan → beneficiary_of → Pemberton Family Trust

### Absent (superseded) edges (1)
1. Alice Tan → spouse_of → Benedict Tan (divorced 15 March 2026)

## Source Audit (Bidirectional)
**Required edges → source:** Every required edge is explicitly supported
by Note 1. Evidence spans recorded in `ground_truth.json`.

**Absent edge → source:** The divorce is explicitly recorded in Note 2.
The marriage is legally dissolved.

**Source → answer key:** Note 1 asserts the marriage, which Note 2
supersedes. No other supported relationship is asserted. No new
relationships are introduced by the divorce.

## How to Test This Case
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/temporal/dev/case_2 \
    benchmark_v1/temporal/dev/case_2/expected_extraction.json
```
## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 4, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0
    