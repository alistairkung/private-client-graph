# Case: Temporal Precedence (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Temporal Precedence.
- **Content:** Different family (Marlow), different trust (Marlow Family Trust),
  different trustee replacement (Andrew Bell → Fiona Grant). Same temporal pattern.
- **Difficulty:** Same as the development case.

## Answer Key
6 edges: Julia settlor, Julia+Peter spouses, both parents of Anna,
Anna beneficiary, Fiona Grant trustee. Deliberately excluded:
Andrew Bell as trustee (historical edge).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-11
**Result:** TP: 6, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## What This Case Does Not Test
Sequential multi-document processing. Pipeline reads one combined source.txt.
Full Case 05 multi-document structure deferred.

## Not Included
Aliases, Distractors, Hallucination, Authority, Cross-Source.