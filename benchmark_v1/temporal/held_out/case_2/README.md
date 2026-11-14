# Case: Temporal Precedence — Divorce (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Temporal Precedence (divorce).
- **Content:** Same family (Pemberton), different dates.
- **Key difference:** The divorce note does not explicitly state "no longer spouses."
  The model must infer that divorce supersedes the marriage.
- **Why held out:** To test whether temporal-reasoning improvements generalize
  to subtler cues.

## Answer Key
4 required edges (spouse edge absent).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 4, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Correlation
This case correlates to the **Divorce** scenario from issue #174.