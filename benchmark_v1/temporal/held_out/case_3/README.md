# Case: Temporal Precedence — Death and Succession (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Temporal Precedence (death/succession).
- **Content:** Same family (Hartley), different dates.
- **Key difference:** The death note does not explicitly state "remains the father."
  The model must infer that death does not remove parenthood.
- **Why held out:** To test whether temporal-reasoning improvements generalize
  to implicit survival of family edges.

## Answer Key
6 required edges, 1 absent (James trustee_of).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 6, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Correlation
This case correlates to the **Death/Succession** scenario from issue #174.