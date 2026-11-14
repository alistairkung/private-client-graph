# Case: Temporal Precedence — Material Correction (Development)

## Purpose
Test whether the pipeline applies a later material correction that retracts
an earlier sibling assertion, while preserving unaffected family and trust
edges.

## Intended Variable
Temporal precedence (material correction). The combined source contains two
dated notes:
- Note 1 (3 March 2025): Margaret is the settlor, Margaret and Thomas are
  spouses. Margaret and Thomas are each asserted as siblings of Caroline.
  Caroline is a beneficiary.
- Note 2 (18 July 2026): Margaret corrects the earlier note. Caroline is
  **not** a sibling of Margaret or Thomas. She is a cousin. The correct
  position is that Margaret and Thomas have no recorded siblings.

The answer key reflects the current state:
- The two sibling edges are **absent** (retracted by the correction).
- The settlor, spouse, and beneficiary edges are **present** (unaffected).
- The cousin relationship is **not represented** in the current schema
  (see "Ontology Decision" below).

## Ontology Decision
The correction introduces a "cousin" relationship, which is **not** one of
the supported relationship types (`parent_of`, `sibling_of`, `spouse_of`,
`settlor_of`, `trustee_of`, `beneficiary_of`). This case does **not**
attempt to represent the cousin relationship. It only tests whether the
model correctly retracts the sibling edges. If a future schema extension
adds `cousin_of`, this case can be revisited.

## Answer Key
### Required edges (3)
1. Margaret Nightingale → settlor_of → Nightingale Family Trust
2. Margaret Nightingale → spouse_of → Thomas Nightingale
3. Caroline Nightingale → beneficiary_of → Nightingale Family Trust

### Absent (superseded) edges (2)
1. Margaret Nightingale → sibling_of → Caroline Nightingale (retracted 18 July 2026)
2. Thomas Nightingale → sibling_of → Caroline Nightingale (retracted 18 July 2026)

## Source Audit (Bidirectional)
**Required edges → source:** Every required edge is explicitly supported
by Note 1. Evidence spans recorded in `ground_truth.json`.

**Absent edges → source:** Note 2 explicitly retracts both sibling edges.
The correction is written, not just implied.

**Source → answer key:** Note 2 explicitly states "Margaret Nightingale
and Thomas Nightingale have no siblings recorded in this matter." No
additional supported relationship is asserted. Caroline's beneficiary
status is preserved.

## How to Test This Case
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/temporal/dev/case_4 \
    benchmark_v1/temporal/dev/case_4/expected_extraction.json
```
## Contract Check Result (Ideal Extraction)
**Run:** 2026-11-14
**Result:** TP: 3, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0