# Case: Aliases (Held-Out)

## Held-Out Status
This case is held out. It is frozen before any development tuning begins.
It is not inspected during development. It is scored at final evaluation.

## Relationship to Development Case
- **Axis:** Aliases.
- **Content:** Different family (Beaumont), different trust (Beaumont Family Trust),
  different document. Same alias pattern: full name / first name / title /
  nickname.
- **Difficulty:** Same as the development case.
- **Why held out:** To test whether alias-resolution improvements generalize
  to unseen content.

## Answer Key
5 edges: Katherine settlor, Katherine+Richard spouses, both parents of Emily,
Emily beneficiary. Aliases: "Katherine Beaumont" / "Katherine" / "Mrs. Beaumont";
"Emily Beaumont" / "Emily" / "Em"; "Richard Beaumont" / "her husband".

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-11
**Result:** TP: 5, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## Not Included
Temporal, Authority, Cross-Source, Distractors, Hallucination, multiple documents.