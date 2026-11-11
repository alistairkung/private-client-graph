# Case: Incremental Hallucination (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Incremental Hallucination.
- **Content:** Different family (Marlow), different trust (Marlow Family Trust).
  Same fact/proposal pattern: true baseline + proposals not yet in effect.
- **Difficulty:** Same as the development case.
- **Why held out:** To test generalization of fact/proposal distinction.

## Answer Key
7 edges: Julia settlor, Julia+Peter spouses, both parents of Anna and William,
Anna current beneficiary. Deliberately excluded: William as beneficiary
(proposal), Elizabeth as trustee (proposal), Anna's interest reduced (proposal).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-11
**Result:** TP: 7, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Not Included
Temporal, Authority, Cross-Source, Aliases, Distractors, multiple documents.