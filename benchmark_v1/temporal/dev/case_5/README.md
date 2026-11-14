# Case: Temporal Precedence — Proposal (Development)

## Purpose
Test whether the pipeline correctly rejects a proposed trustee replacement
that has not been formally executed, retaining the existing trustee edge.

## Intended Variable
Temporal precedence (proposal vs. effective). The combined source contains
two dated notes:
- Note 1 (4 April 2025): Rachel Moy is the settlor, Rachel and Simon are
  spouses and parents of Jasmine. Simon is the sole trustee.
- Note 2 (9 October 2026): Rachel is *considering* asking Simon to step
  down and appointing Jonathan. No formal steps taken. The current
  position remains that Simon is the sole trustee.

The answer key reflects the current state:
- The Simon trustee edge is **present** (still current).
- There is **no edge** for Jonathan (proposal never executed).

## Answer Key
### Required edges (6)
1. Rachel Moy → settlor_of → Larkfield Family Trust
2. Rachel Moy → spouse_of → Simon Moy
3. Rachel Moy → parent_of → Jasmine Moy
4. Simon Moy → parent_of → Jasmine Moy
5. Jasmine Moy → beneficiary_of → Larkfield Family Trust
6. Simon Moy → trustee_of → Larkfield Family Trust

### Absent (proposed) edges (1)
1. Jonathan Moy → trustee_of → Larkfield Family Trust (proposed, never effective)

## Source Audit (Bidirectional)
**Required edges → source:** Every required edge is explicitly supported
by Note 1 and Note 2. Evidence spans recorded in `ground_truth.json`.

**Absent edge → source:** Note 2 mentions Jonathan as a *proposed*
replacement. It explicitly states no formal steps have been taken, no deed
has been executed, and no resignation has been received. The proposal is
not effective.

**Source → answer key:** Note 2 explicitly states "The current position
remains that Simon Moy is the sole trustee." No additional supported
relationship is asserted.

## How to Test This Case
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/temporal/dev/case_5 \
    benchmark_v1/temporal/dev/case_5/expected_extraction.json
```

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 6, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0