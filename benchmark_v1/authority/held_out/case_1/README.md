# Case: Document Authority (Held-Out)

## Held-Out Status
Frozen before any development tuning begins. Not inspected during development.
Scored at final evaluation.

## Relationship to Development Case
- **Axis:** Document Authority.
- **Content:** Different family (Foster), different trust (Ashworth Family Trust),
  different conflict. Same pattern: informal intention superseded by formal deed.
- **Difficulty:** Same as the development case.

## Answer Key
1 edge: Daniel Foster beneficiary_of Ashworth Family Trust.
Deliberately excluded: Charlotte Foster as beneficiary (informal intention,
never formalised; deed explicitly removes her).

## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-11
**Result:** TP: 1, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0

## What This Case Does Not Test
The graph has no authority-ranking field. Tests whether the model extracts
the correct current fact from conflicting sources, not graph storage.

## Not Included
Temporal, Cross-Source, Aliases, Distractors, Hallucination.