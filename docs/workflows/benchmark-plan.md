# Benchmark Plan: Complexity Axes & RAG Experiment

## Objective
Complement the existing `cases/` regression fixtures with a new diagnostic benchmark suite (`benchmark_v1/`). The existing cases have already informed development and remain as regression tests; they cannot serve as independent final evaluation.

The new suite evaluates the pipeline's baseline capabilities, defines capability gaps for future work, and tests whether Retrieval-Augmented Generation (RAG) improves graph reconstruction as document volume and complexity increase.

## 1. Benchmark Structure: 6 Axes, Dev and Held-Out

We propose 6 complexity axes. Following the collaborator's suggestion, we hold out a variety of axes by creating **6 held-out samples** (one per axis).

For each axis, we author two cases:
- **1 Development Case:** Visible, inspected, and used to tune the pipeline.
- **1 Held-Out Case:** Frozen before any development tuning begins. Scored at final evaluation.

### The 6 Axes
1. **Temporal Precedence:** A relationship changes over time (e.g., trustee replaced).
2. **Document Authority:** Informal intention vs. formal deed.
3. **Aliases:** Same person, different names.
4. **Distractors:** Irrelevant named people.
5. **Cross-Source Reconciliation:** Facts split across multiple documents.
6. **Incremental Hallucination:** Drafts mixing true facts with proposals.

### Capability Fixtures vs. Baseline Diagnostics
The graph currently represents relationships, not effective dates, authority rankings, or source-aware scoring. We distinguish measurable extraction failures from capabilities the system doesn't yet support.

- **Baseline Diagnostics:** Aliases, Distractors, Incremental Hallucination. The pipeline can attempt these today. Scored in both development and held-out.
- **Capability Fixtures:** Temporal Precedence, Document Authority, Cross-Source Reconciliation. These require capabilities the pipeline doesn't have yet. Their development cases are authored but not scored. Their held-out cases **are scored at final evaluation** — if the capability was built, the score reflects it; if not, the score reports "not attempted" as an honest finding.

## 2. RAG Experiment (Separate from Axes)
We test the hypothesis: *"As volume, complexity, and distribution of documents increase, RAG improves the ability to reconstruct an accurate graph."*

### The 3-Step Experiment
1. **Baseline:** Run the current pipeline (full context) on a small case. Record F1.
2. **RAG Added:** Run the same case with retrieval. Record F1. If identical, RAG is a no-op on small cases.
3. **Sweep:** Run both baseline and RAG across Small / Medium / Large versions of the same case.

### RAG Sweep Thresholds (Reasoning)
The interesting comparison is at the **context-window edge**: where the baseline can still process the file but starts losing accuracy. Below it, RAG is a no-op. Above it, baseline cannot run and the comparison becomes trivial.

| Tier | Approx. docs | What it tests | Trade-off |
|---|---|---|---|
| **Small** | ~5 | Control condition. Everything fits; RAG should be a no-op. | Cheap, low information, establishes the null. |
| **Medium** | ~15 | A realistic Matter file. Model still fits everything but starts losing accuracy. | Likely sweet spot. Moderate cost. |
| **Large** | ~30–50 (or context-window limit) | At the edge of context. Baseline drops; RAG recovers. | The meaningful finding. Capped at whichever is smaller: ~50 docs or the model's context-window limit. |

**Cap:** Above the context-window edge, baseline cannot run and the comparison is trivial. The finding is whether RAG's advantage appears at the edge, not past it.

### Design Constraints
- **Realistic, Not Noise:** The larger cases must look like real Matter files (deeds, letters, resolutions), not artificial stress tests.
- **Output is a Curve:** We plot F1 vs. document count. The gap between the baseline and RAG curves is RAG's value.
- **Conclusion:** If RAG never diverges from baseline, we report that RAG was not a good use case for this domain, showing the numbers.

## 3. Metrics (Aligned to Evaluator)
1. **TP / FP / FN:** Raw counts.
2. **Precision, Recall, F1:** Standard metrics.
3. **FP Count & 1 − Precision:** Because true negatives are not enumerated, we report raw FP count and false discovery proportion (1 − Precision).
4. **Relationship Provenance Accuracy:** TP edges where at least one predicted span matches an approved span.
5. **Source Attribution Accuracy:** Multi-source cases only. TP edges where the predicted `source_id` matches the approved `source_id`. Supported by the existing evaluator for `CanonicalState`.
6. **Retrieval Recall:** RAG runs only. Fraction of approved evidence present in retrieved chunks.
7. **Axis Failure:** Defined specifically. Only the intended variable counts.

## 4. Methodology (Per `synthetic-case-authoring.md`)
We strictly follow the canonical order: **Answer Key → Source → Audit → Evidence → Extraction.**

1. **Declare Case Purpose:** Record ID, purpose, intended variable, supported types.
2. **Define Answer Key:** Complete graph in JSON first. Challenge every edge.
3. **Draft Source:** Write realistic document from the answer key. No accidental edges.
4. **Bidirectional Audit:** GT → Source (is every edge supported?) and Source → GT (are there unintended edges?).
5. **Annotate Evidence:** Exact verbatim spans for every edge.
6. **Freeze Answer Key:** Re-verify after any source edit.
7. **Derive Expected Extraction:** Only after source is stable.
8. **Deterministic Checks:** Run schema, reference, and verbatim validations.
9. **Persist Run & Evaluate:** Run pipeline, save artifact, score.
10. **Record Failure:** Categorize (extraction, graph, annotation, etc.).

## 5. Multi-Document Schema (Existing Contracts)
Use existing files, no new schema:
- `sources.json`: Ordered source list.
- `ground_truth.json`: Entities/relationships with plain-string `approved_evidence`.
- `source_evidence.json`: Separate mapping of `source_id` to quotes.
- `expected_extraction.json`: Raw candidates.
- `expected_source_extraction.json`: Source-attributed ideal extraction.

*No `document_id` field in `ground_truth.json`.*

## 6. Document Count Policy
Initial non-RAG cases use the *minimum* documents needed for the axis. Document-count variation is reserved exclusively for the RAG experiment.
- **Aliases / Distractors / Hallucination:** 1 document.
- **Temporal / Authority / Cross-Source:** 1 combined `source.txt` containing two documents. The full multi-document structure (separate files per source) is deferred until the pipeline gains sequential processing.

## 7. Ownership and Approval
- **Stage 1 (This PR):** Agree on approach.
- **Stage 2 (Self-Review):** Author verifies ground truth completeness, evidence support, and automated checks. Includes summary and flagged uncertainties.
- **Stage 3 (Review):** Joint review only where needed. Author makes and defends routine decisions.

## 8. Out of Scope
Fraud detection, RCE, Agentic tool misuse, Real legal documents, artificial noise stress tests.

## 9. Reporting
Markdown summaries for metrics. Individual errors and Evidence inspectable via the existing Workbench.

## 10. Current Status
- **12 cases authored and contract-verified** (6 dev + 6 held-out, one per axis per phase).
- All 12 pass `evaluate_case.py` with F1=1.0 and provenance=1.0 on hand-crafted ideal extractions.
- **Held-out set is frozen** (not inspected during development).
- **RAG sweep is next.**
- Full details in each case's README under `benchmark_v1/<axis>/<dev|held_out>/case_1/`.