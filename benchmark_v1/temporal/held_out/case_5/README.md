# Case: Temporal Precedence — Proposal (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Temporal Precedence (proposal vs. effective).
- **Content:** Same family (Moy), different dates.
- **Key difference:** The proposal states only "would like to." It does not
  explicitly state "no formal steps taken."
- **Why held out:** To test whether proposal rejection improves with subtler cues.

## Answer Key
6 required edges, 1 absent (Jonathan trustee_of).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 6, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Correlation
This case correlates to the **Proposal vs. Effective** scenario from issue #174.

## Provenance Note
The Simon Moy → Larkfield Family Trust trustee edge is asserted twice: once
in Note 1 and once in Note 2. Both quotes are approved evidence. The initial
ground truth approved only Note 1, which caused the ideal extraction to fail
provenance by quoting Note 2. Fixed.