# T1: Divorce

## Purpose
Spouse edge superseded by completed divorce. Tests whether the pipeline excludes it while preserving the other 5 edges.

## Documents
`note_01` + `note_02`.

## Answer Key
5 required edges. Absent: Alice spouse_of Benedict (divorced 15 March 2026).

## Contract Check Result
**Run:** 2026-11-15
**Result:** TP: 5, FP: 0, FN: 0, F1: 1.0, Provenance: 1.0
**Paid provider calls:** 0