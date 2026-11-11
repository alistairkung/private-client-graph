# Case: Distractors (Development)

## Purpose
Test whether the pipeline ignores irrelevant named people who have no role
in the family or trust, and extracts only the relationships that are
genuinely part of the answer key.

## Intended Variable
Distractors. The source mentions several people who are present in the
document but have no family or trust relationship:
- **Mr. Andrew Chan** — family solicitor, present at the meeting.
- **Rachel Lee** — personal assistant, present at the meeting.
- **Peter Park** — cousin, has asked about being added as a beneficiary,
  but is explicitly not currently a beneficiary.

None of these people should appear in the extracted graph.

All other dimensions are held stable: explicit family roles, single
document, cooperative language, one trust.

## Supported Relationship Types
`settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`.

## Answer Key

### Entities
- Helen Park (person, settlor, spouse, parent)
- Simon Park (person, spouse, parent)
- Chloe Park (person, child, beneficiary)
- Juniper Family Trust (trust)

### Relationships (5 edges)
1. Helen Park → settlor_of → Juniper Family Trust
2. Helen Park → spouse_of → Simon Park
3. Helen Park → parent_of → Chloe Park
4. Simon Park → parent_of → Chloe Park
5. Chloe Park → beneficiary_of → Juniper Family Trust

## Source Audit (Bidirectional)

**Answer key → source:** Every edge has explicit support in the source text.
Evidence spans are recorded in `ground_truth.json`.

**Source → answer key:** No additional supported relationships asserted.
- Mr. Chan and Ms. Lee are named but explicitly stated to have no
  beneficial interest. They are not family and not trust participants.
- Peter Park is named as a cousin who has asked about future beneficiary
  status, but the source explicitly states he is not currently a
  beneficiary. His future request is a proposal, not a current edge.
- No other family members or trusts are mentioned.

## How to Test This Case

### Contract check (no model call)
Run the hand-crafted ideal extraction against the existing evaluator:

```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/distractors/dev/case_1 \
    benchmark_v1/distractors/dev/case_1/expected_extraction.json

    ## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 5, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (5/5 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. All 5 ground-truth edges are supported by exact source quotes.
The distractor entities (solicitor, PA, cousin) are correctly excluded.

**Paid provider calls:** 0