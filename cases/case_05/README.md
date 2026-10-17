## Notes on Case 05

Purpose: distinguish an initially true trustee relationship from its completed
replacement, preserving unchanged family and trust facts in the current graph.

New difficulty: temporal state, as specified by the original case roadmap.
Explicit full names, one trust and a single completed trustee replacement keep
other dimensions stable. Supported relationship types: `settlor_of`, `spouse_of`,
`parent_of`, `beneficiary_of`, `trustee_of`.

### Fixed answer key and source audit

The answer key was defined before source drafting. Elaine Ho is the settlor of
Willow Family Trust. Elaine Ho and Martin Ho are spouses; each is a parent of
Sophie Ho. Sophie Ho is a beneficiary of the trust. The only changing relationship
is the trustee: David Ng initially, then Rachel Lim after a completed replacement.
No family connection is asserted for either trustee.

The initial attendance note records the position on 1 September 2026. The dated
follow-up records David Ng's resignation and Rachel Lim's effective appointment
on 10 September, confirming the current position as at 15 September 2026. These
are completed events, not proposed appointments or conflicting assertions.
Neither the vocabulary nor the stored relationship schema gains temporal fields.
Dates and the scope of the answer keys are explicit in the documents and notes.

The bidirectional source audit found support for every intended edge and no
additional supported family or trust relationship. The final answer key is the
current graph as at 15 September, not the union of all historically true edges.
David Ng's earlier trustee assertion remains valid for the initial snapshot,
but is not a current trustee edge after the completed replacement.

### Sequential expectations

| Stage | Expected graph | Source of support |
|-------|----------------|-------------------|
| After note_01, as at 1 September | Six edges: Elaine settlor; Elaine–Martin spouses; Elaine and Martin each parent of Sophie; Sophie beneficiary; David trustee | `note_01` only |
| After note_02, as at 15 September | Retain the five unchanged edges; remove David's trustee edge; add Rachel's trustee edge. Six edges total | Five unchanged edges retain `note_01` evidence; Rachel's trustee edge uses `note_02` evidence |

The final graph requires both documents. Processing note_02 alone yields only
Rachel's current trustee edge. Blindly accumulating both raw per-document
extractions yields seven edges and one false positive: David as a current
trustee. Processing note_01 alone misses Rachel and retains David incorrectly.
The final state uses the same IDs for surviving entities and evidence as the
initial state; it does not attach historical trustee evidence to Rachel.

### Artifacts

- `sources/note_01.txt`, `sources/note_02.txt`: chronological attendance notes.
- `ground_truth_after_note_01.json`, `expected_state_after_note_01.json`: initial
  `GroundTruth` and source-aware `CanonicalState` snapshot.
- `ground_truth.json`, `expected_state.json`: final current answer key and
  source-aware state, scoped to 15 September 2026.
- `expected_extraction_note_01.json`, `expected_extraction_note_02.json`: ideal
  independent raw extractions, including David only in the initial document.
- `expected_extraction.json`: ideal final-current extraction from both documents,
  with David's superseded edge omitted and Rachel's current edge included. It is
  deliberately not the concatenation of independent per-document extractions.
- `source.txt`: chronological concatenation of the notes with one blank line,
  for the existing single-text loader. It adds no answer-key annotations.
- `metadata.json`: catalog name and description.

Approved evidence and extraction candidates use exact source text. The final
state stores only evidence supporting current edges. The original dated sources
and initial snapshot retain the historical assertion separately. This expectation
does not prescribe a production history-storage model.

### Validation and implementation limit

Tests validate the initial and final schemas, references, endpoint types,
verbatim evidence, source attribution, snapshot consistency, and loader discovery.
Both authored snapshots score six true positives, zero false positives/negatives,
and perfect approved-quote provenance. A deterministic union control scores
six true positives and one false positive, exposing the temporal requirement.

The current loader can load the combined final-current fixture but cannot express
an ordered series of document updates or select snapshot dates. The extraction
schema has no time/status fields, the builder accepts one source and has no
supersession operation, and the evaluator compares edges and quote strings without
scoring temporal transitions or document attribution. The authored snapshots can
be validated with the existing canonical-state boundary, but this is not an
implemented sequential extraction run. A separate task must design temporal
interpretation and reconciliation before implementing the two-stage behaviour;
case authoring does not change these protected semantics.

No live extraction was run. No model performance or temporal capability is
claimed. Paid provider calls for this task: zero. Human PR review remains needed
for semantic completeness and evidence sufficiency.

### Final-day full-context annotations

`sources.json` explicitly fixes the Source identities and presentation order. `source_evidence.json` adds reviewed Source/quote approvals for the existing answer-key edges; it does not replace or change legacy quote scoring. `expected_source_extraction.json` is a source-attributed ideal final-current extraction. It is an authored fixture, not measured model output.

The full-context chain receives the ordered Sources together and extracts the latest explicitly effective state. The initial/final controls do not require sequential execution or a historical-state selector. Selected support need not exhaust every corroborating Source; every selected quote must be approved for its actual Source. When supplied, distinct Source evidence for one edge must be pooled rather than discarded.
