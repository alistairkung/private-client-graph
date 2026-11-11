# Case: Cross-Source Reconciliation (Development)

## Purpose
Test whether the pipeline combines facts from two separate documents into
a single accurate graph without duplicating, omitting, or misattributing
any relationship.

## Intended Variable
Cross-source reconciliation. The combined source contains two emails:
- Email 1 (12 April 2026): Alice Chen confirms that she and David Chen
  are spouses and both are settlors of the Oakwood Trust.
- Email 2 (14 April 2026): The solicitor confirms that Bob Chen is the
  sole beneficiary of the Oakwood Trust.

The answer key requires combining facts from both emails. Neither email
alone is sufficient.

## Supported Relationship Types
`settlor_of`, `spouse_of`, `beneficiary_of`.

## Answer Key

### Entities
- Alice Chen (person, settlor, spouse)
- David Chen (person, settlor, spouse)
- Bob Chen (person, beneficiary)
- Oakwood Trust (trust)

### Relationships (4 edges)
1. Alice Chen → settlor_of → Oakwood Trust
2. David Chen → settlor_of → Oakwood Trust
3. Alice Chen → spouse_of → David Chen
4. Bob Chen → beneficiary_of → Oakwood Trust

## Source Audit (Bidirectional)

**Answer key → source:** Email 1 supports edges 1–3. Email 2 supports
edge 4. Every edge has explicit support.

**Source → answer key:** Email 1 also says "my husband, David Chen" — this
supports the spouse edge, which is already in the answer key. No additional
supported relationships are asserted.

## How to Test This Case

```bash
uv run python benchmark_v1/evaluate_case.py \
    benchmark_v1/cross_source/dev/case_1 \
    benchmark_v1/cross_source/dev/case_1/expected_extraction.json

    ## Contract Check Result (Ideal Extraction)

**Run:** 2026-11-11
**Input:** `expected_extraction.json` (hand-crafted ideal extraction)
**Evaluator:** `benchmark_v1/evaluate_case.py`

**Result:**
- TP: 4, FP: 0, FN: 0
- Precision: 1.0, Recall: 1.0, F1: 1.0
- Provenance accuracy: 1.0 (4/4 passed)

**Interpretation:** The case's contracts are compatible with the existing
evaluator. All 4 ground-truth edges are supported by exact source quotes
from both emails. The case requires combining facts from both sources.

**Paid provider calls:** 0