## Notes on Case 04

Purpose: reconcile a relationship asserted in two source documents while keeping
its evidence attached to the correct document.

New difficulty: cross-document extraction and provenance. Explicit names, one
trust, cooperative language and unchanged facts keep the case focused. Supported
relationship types: `settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`.

### Scenario and answer key

Raphael's two Hillcrest attendance notes are preserved. Victoria Chan is the
settlor of Hillcrest Family Trust, Victoria Chan and Peter Chan are spouses and
parents of Andrew Chan, and Andrew Chan is a beneficiary. The follow-up confirms
Andrew Chan's beneficiary role and records Lucy Chan and Marcus Yip as additional
beneficiaries. It asserts no family connection for either additional beneficiary.
The complete answer key has six entities and seven relationships.

The notes are complementary sources for one unchanged factual picture. Their
meeting order supplies context; Case 04 does not test a state transition. Eight
raw candidates represent seven semantic edges. Andrew Chan's beneficiary edge
must retain evidence from both documents. The existing builder and evaluator
already deduplicate semantic edges; duplicate candidates do not inherently
produce a false positive.

### Artifacts and attribution

- `sources/note_01.txt` and `sources/note_02.txt`: original documentary evidence.
- `ground_truth.json`: complete answer key and approved exact quotes, preserved.
- `expected_extraction_note_01.json` and `expected_extraction_note_02.json`:
  separate `ExtractionResult` fixtures containing five and three candidates.
- `expected_extraction.json`: the preserved eight-candidate combined extraction.
- `expected_state.json`: an authored `CanonicalState` expectation with explicit
  Source identities, document labels, evidence references and one shared edge.
- `source.txt`: note_01 followed by note_02, separated by a blank line, for the
  existing single-text case loader. It contains only documentary text.
- `metadata.json`: repository catalog name and description.

The expected state attaches the first five candidates to `note_01`; the last
three belong to `note_02`. Every approved quote can be located in these sources.
The Source identity in the state, rather than string matching between documents,
defines the selected evidence's attribution. Raw extraction and ground truth keep
the existing schemas without added document fields.

### Validation and limits

The source-to-answer-key audit found no additional supported relationships.
Every intended edge has explicit support; ordinary local pronouns resolve to
Victoria Chan. Tests validate schemas, references, endpoint types, exact quotes,
per-document candidates, the source-aware state, seven-edge perfect deterministic
scoring, and case-loader compatibility.

The loader presents `source.txt` as one document and the standard pipeline builds
one document at a time. A perfect combined fixture score does not demonstrate
cross-document extraction or attribution. `validate_canonical_state` checks the
separate source-aware expectation; the evaluator scores approved quote text but
ignores document identity. Multi-source extraction, merging and document-aware
scoring require a separate implementation task. No live extraction was run and
no model success or failure is claimed. Paid provider calls for this task: zero.

Semantic completeness and evidence support remain subject to human PR review;
mechanical checks do not establish those judgments.
