# Private Client Graph

Private Client Graph reconstructs reviewable family and trust relationships from source documents while preserving the evidence for each relationship.

## Language

**Benchmark Case**:
A synthetic source document, complete relationship answer key, and associated fixtures used to exercise and evaluate the pipeline under controlled conditions.
_Avoid_: Client case, production case

**Relationship Candidate**:
A raw semantic claim extracted from source evidence, consisting of two named endpoints, a supported relationship type, and exact supporting text. It has not yet passed deterministic graph construction.
_Avoid_: Edge, canonical relationship

**Canonical Graph**:
The deterministic, validated representation of entities, relationships, and first-class evidence produced from relationship candidates.
_Avoid_: Raw extraction, model output

**Evidence**:
Exact text from a source document that supports an extracted relationship. Evidence is provenance for a relationship, not a graph entity or a generated explanation.
_Avoid_: Justification, rationale

**Professional Review**:
Inspection by a private-client professional of AI-extracted relationships and the source evidence supporting them. In the first web slice it is read-only and does not include benchmark evaluation or human correction.
_Avoid_: Case summary, benchmark review

**Live Analysis**:
An analysis that obtains relationship candidates from a new model invocation before deterministic graph construction.
_Avoid_: Replay, sample analysis

**Sample Analysis**:
A deterministic demonstration path that loads the Case 01 ideal-extraction fixture and passes it through current graph construction. It is explicitly selected and is never a fallback from live analysis.
_Avoid_: Live analysis, prior-run replay

**Run Artifact**:
A persisted raw extraction created for reproducibility and diagnosis. It is technical traceability data, not application state or a professional case history.
_Avoid_: Saved case, analysis history

**Benchmark Evaluation**:
Offline comparison of a canonical graph with a benchmark case's known answer key, including relationship and provenance metrics. It is separate from professional review.
_Avoid_: Professional review score, confidence score
