# Case: Cross-Source Reconciliation (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Cross-Source Reconciliation.
- **Content:** Different family (Leung/Yeung), different trust (Ravenswood Trust).
  Same pattern: facts split across two emails.
- **Difficulty:** Same as the development case.

## Answer Key
4 edges: Susan and Michelle both settlors, they are spouses,
Amy Yeung is beneficiary. The settlor and spouse edges come from Email 1;
the beneficiary edge comes from Email 2. Neither email alone is sufficient.

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-11
**Result:** TP: 4, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## What This Case Does Not Test
Multi-document processing as separate sources with separate attribution.
Pipeline reads one combined source.txt.

## Not Included
Temporal, Authority, Aliases, Distractors, Hallucination.