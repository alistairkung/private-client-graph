# Case: Temporal Precedence — Death and Succession (Development)

## Purpose
Test whether the pipeline:
1. Correctly replaces the trustee edge after a death and succession document.
2. Does **not** infer that death automatically removes family edges
   (e.g., James remains Oliver's father).

## Intended Variable
Temporal precedence with death and succession. The combined source contains
two dated notes:
- Note 1 (5 June 2025): Eleanor and James Hartley are spouses and parents
  of Oliver Hartley. James is the sole trustee.
- Note 2 (12 September 2026): James Hartley passed away on 10 September 2026.
  A separate deed of appointment records Margaret Hartley as the new sole
  trustee with effect from 11 September 2026.

The answer key reflects the current state:
- The old trustee edge (James) is **absent**.
- The new trustee edge (Margaret) is **present**.
- James's parent edge is **present** — death does not remove parenthood.

## Answer Key
### Required edges (6)
1. Eleanor Hartley → settlor_of → Hartley Family Trust
2. Eleanor Hartley → spouse_of → James Hartley
3. Eleanor Hartley → parent_of → Oliver Hartley
4. James Hartley → parent_of → Oliver Hartley
5. Oliver Hartley → beneficiary_of → Hartley Family Trust
6. Margaret Hartley → trustee_of → Hartley Family Trust

### Absent (superseded) edges (1)
1. James Hartley → trustee_of → Hartley Family Trust (replaced 11 September 2026)

## Source Audit (Bidirectional)
**Required edges → source:** Every required edge is explicitly supported
by Note 1 and Note 2. Evidence spans recorded in `ground_truth.json`.

**Absent edge → source:** The succession document records James's
replacement by Margaret. The death notice alone does not supersede the
trustee edge — it is the succession document that does.

**Source → answer key:** Note 2 explicitly states "James Hartley remains
the father of Oliver Hartley." This confirms the parent edge is preserved.

## How to Test This Case
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/temporal/dev/case_3 \
    benchmark_v1/temporal/dev/case_3/expected_extraction.json
```
## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 6, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Provenance Note
The James Hartley → Oliver Hartley parent edge is asserted twice: once in
Note 1 ("are the parents of Oliver Hartley") and once in Note 2 ("remains
the father"). Both quotes are approved evidence. This prevents the ideal
extraction from failing provenance by quoting the "wrong" valid assertion.