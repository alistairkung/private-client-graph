# Case: Incremental Hallucination (Development)

## Purpose
Test whether the pipeline distinguishes current facts from proposals,
intentions, and draft language within a single document. The source
deliberately mixes "what is true now" with "what the client wants to
happen in future."

## Intended Variable
Incremental Hallucination. The source contains:
- **True current facts:** Gregory Ashby is settlor, he and Patricia are
  spouses, they have two children (Emma and James), and Emma is the
  current sole beneficiary.
- **Proposals not yet in effect:** James Ashby would become a beneficiary
  under a proposed variation; Emma's interest would be reduced; Margaret
  Ashby would become a trustee. None of these has legal effect.

The pipeline must extract only the current facts, not the proposals.

All other dimensions are held stable: explicit family roles, single
document, one trust.

## Supported Relationship Types
`settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`.

## Answer Key

### Entities
- Gregory Ashby (person, settlor, spouse, parent)
- Patricia Ashby (person, spouse, parent)
- Emma Ashby (person, child, beneficiary)
- James Ashby (person, child — NOT beneficiary)
- Ashby Family Trust (trust)

### Relationships (7 edges)
1. Gregory Ashby → settlor_of → Ashby Family Trust
2. Gregory Ashby → spouse_of → Patricia Ashby
3. Gregory Ashby → parent_of → Emma Ashby
4. Gregory Ashby → parent_of → James Ashby
5. Patricia Ashby → parent_of → Emma Ashby
6. Patricia Ashby → parent_of → James Ashby
7. Emma Ashby → beneficiary_of → Ashby Family Trust

**Deliberately excluded:** James Ashby → beneficiary_of → Ashby Family
Trust. The source says this is a *proposal*, not a current fact.

## Source Audit (Bidirectional)

**Answer key → source:** Every edge has explicit support in the current-position
section of the source text. Evidence spans are recorded in `ground_truth.json`.

**Source → answer key:** The proposal section mentions:
- James Ashby becoming a beneficiary (proposal, not current)
- Emma Ashby's interest being reduced (proposal, not current)
- Margaret Ashby as a proposed trustee (proposal, not current)

None of these are current facts. The source explicitly states: "No deed
of variation has been executed, and none of these proposals currently has
legal effect."

## How to Test This Case

### Contract check (no model call)
```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/hallucination/dev/case_1 \
    benchmark_v1/hallucination/dev/case_1/expected_extraction.json
    ## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 7, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (7/7 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. All 7 ground-truth edges are supported by exact source quotes.
The proposal section is correctly excluded from the answer key.

**Paid provider calls:** 0