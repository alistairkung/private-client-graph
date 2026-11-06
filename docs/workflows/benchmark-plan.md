# Benchmark Plan: Complexity Axes

## Objective
Evaluate the baseline performance of the current pipeline (Extractor + Resolver) on synthetic documents that isolate distinct dimensions of legal complexity. We are measuring where the current architecture fails, not fixing it yet. We are moving away from the existing `cases/` scenarios to build a new, generic benchmark set.

## Optimization Goal
Trust and Exactness. We prioritize **Precision** (zero hallucinations) and **Provenance Accuracy** (exact quotes) over Recall. In a legal context, missing a relationship is annoying, but hallucinating one is dangerous.

## Metrics
We propose tracking four metrics:
1. **F1 Score:** The overall balance of Precision and Recall.
2. **False Positive Rate:** The count of hallucinated relationships (claims not in the ground truth).
3. **Provenance Accuracy:** The percentage of correct relationships backed by the exact, approved quote.
4. **Failure Rate by Axis:** A diagnostic breakdown showing which specific complexity axes the baseline fails.

## The 7 Complexity Axes
We propose creating 3 test cases per axis (amendable), spanning a variable document count (see Document Count Policy). Each isolated case tests **only one** difficulty so failures are attributable.

### 1. Temporal Precedence
- **Scenario:** A relationship changes over time (e.g., a trustee is replaced).
- **Challenge:** The AI must output only the *current* state, discarding the historical state.

### 2. Document Authority
- **Scenario:** An informal intention conflicts with a formal deed.
- **Challenge:** The AI must prioritize the formal deed and discard the informal note.

### 3. Aliases
- **Scenario:** The same person is referred to by multiple names.
- **Challenge:** The AI must resolve these as one entity, not three.

### 4. Distractors
- **Scenario:** A document mentions irrelevant people who have no role in the trust.
- **Challenge:** The AI must only extract the relevant family/trust relationships.

### 5. Cross-Source Reconciliation
- **Scenario:** A relationship is only visible when multiple documents are read together.
- **Challenge:** The AI must combine facts across documents into a single graph.

### 6. Incremental Hallucination (Draft vs. Fact)
- **Scenario:** A document mixes true facts with proposals or intentions.
- **Challenge:** The AI must distinguish between historical facts and proposals, extracting only the facts.

### 7. Prompt Injection (Weird Document Text)
- **Scenario:** A document contains text that looks like an instruction to the AI.
- **Challenge:** The AI must treat the document as data, not as instructions, and must not be hijacked.

## Document Count Policy (amendable)
We propose each axis gets 3 cases spanning a variable document count:
- **Case A:** Minimum documents needed to test the axis.
- **Case B:** Mid-range (axis + 1–2 surrounding documents).
- **Case C:** Maximum realistic file size (up to 7 documents).

| Axis | Min–Max docs (amendable) |
|---|---|
| Temporal Precedence | 2–5 |
| Document Authority | 2–5 |
| Aliases | 1–4 |
| Distractors | 1–5 |
| Cross-Source Reconciliation | 2–7 |
| Incremental Hallucination | 1–4 |
| Prompt Injection | 1–3 |

Each case declares its own document count in the ground-truth metadata, so we can report failure rate *per document count*, not just per axis.

## Methodology: How We Build and Verify a Case
Each benchmark case is built in the same sequence. The process is manual at the start (so we understand the case) and automated at the end (so the case is trustworthy).


### Step 1: Write the synthetic documents
For each case, we author one or more `source_NN.txt` files. The text is written to trigger exactly one axis and nothing else. If a source document accidentally contains a second difficulty, the case is rejected and rewritten.

### Synthetic Document Genres
To ensure the benchmark tests real-world complexity, we propose using a mix of legal document genres, not just meeting notes. This matches the `cases/README.md` guideline that "document genre shift" is a valid complexity axis.

1. **Formal Deeds / Trust Instruments:** Dense clauses where relationships are legally defined (e.g., "WHEREAS the Settlor...").
2. **Letters / Confirmation Notes:** Structured but narrative, like a client confirmation letter.
3. **Wills and Codicils:** First-person documents establishing historical relationships.
4. **Resolutions / Minutes:** Short, punchy documents recording appointments and removals (temporal changes).
5. **Meeting Notes / File Notes:** Narrative summaries of discussions.

### Step 2: Write the ground truth
We manually list every entity and relationship that *should* be extracted from the sources. The content and scenarios are entirely new and generic, moving away from the old `cases/` examples.

### Step 3: Write the approved evidence
For every relationship in the ground truth, we manually copy the exact quote from the source document that proves it, and save it to `source_evidence.json`. 

### Step 4: Manual verification
A human reads the source documents, the ground truth, and the approved evidence side-by-side. They must confirm:
1. Every relationship in the ground truth is genuinely supported by the source text.
2. Every quote in the approved evidence is an exact, verbatim substring of the source.
3. The source text contains no accidental difficulty from another axis.
If any check fails, we go back to Step 1.

### Step 5: Automated verification
A script (which we will write) checks the same files programmatically: all JSON parses, all entity IDs resolve, all quotes exist verbatim, and the document count matches.
If the script fails, we go back to Step 1.

### Step 6: Run the baseline
Once a case passes both verification steps, we run the current `extract` + `resolve` pipeline on it and record F1, False Positives, Provenance, and whether it failed the axis.

## Baseline Recording
- **Baseline definition:** The current `extract` + `resolve` configuration, unchanged.
- **Storage:** Results recorded in `benchmark_v1/results/baseline.md`.
- **Comparison:** Every future pipeline change is compared against this baseline. Baseline is frozen once approved.

## Approval Gate
Before running the baseline, the benchmark cases must be reviewed and approved by Alistair. This mirrors the existing rule for held-out cases: the benchmark is frozen and approved before results are produced.

## Out of Scope
The following were considered and deliberately excluded:
- **Fraud detection:** The app is a lawyer's assistant, not a fraud detector. Synthetic cases assume good-faith documents.
- **Server-level attacks (RCE, buffer overflow):** Out of scope; illegal; the project does not have pen-testing authorization.
- **Agentic tool misuse (DeepSeek Harness):** Not applicable until the pipeline exposes dynamic tool selection.
- **Real legal documents:** The project only accepts synthetic material.

## Why JSON for the Benchmark Files?
We are **explicitly discarding the old `cases/` scenarios** to build a new, generic benchmark (`benchmark_v1/`). However, we *must* use the existing JSON data format (the Pydantic schema). 

- **The pipeline requires it:** The Python code (`evaluate.py`, `graph.py`) uses Pydantic's `model_validate_json()`. Using YAML or another format would require rewriting the loading logic.
- **No content is reused:** The schemas are just empty containers. The entities, documents, and relationships are 100% new and generic.
- **Multi-document support:** Because a case can contain multiple documents, `ground_truth.json` includes a `document_id` so the evaluator knows which source proves each relationship.

```json
{
  "entities": [
    {"id": "person_001", "type": "person", "name": "Nadia Lau"}
  ],
  "relationships": [
    {
      "source": "person_001", 
      "type": "settlor_of", 
      "target": "trust_001",
      "document_id": "source_01.txt"
    }
  ]
}
'''
## Future Work: Composite Cases
After the baseline is established, we propose building composite cases that combine multiple axes (e.g., Temporal + Authority + Aliases in one file) to test whether isolated improvements transfer to realistic scenarios.

## Reporting
Baseline results will be recorded in `benchmark_v1/results/baseline.md`:

| Axis | Case | Docs | F1 | FP Rate | Provenance | Notes |
|---|---|---|---|---|---|---|

## Open Questions for Review
1. Is the proposed **3 cases per axis** structure the right granularity for a baseline?
2. Are the **document count ranges** per axis realistic for a typical private-client Matter file?
3. Is the **approval gate** correctly placed before baseline execution, or should it occur earlier?
4. Should the **composite cases** be built earlier, or deferred until the baseline is fully understood?