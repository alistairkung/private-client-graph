## Notes on Case 04

Case 04 introduces multiple source documents as its new difficulty: two
attendance notes about the same family and the same trust, one recording
an initial meeting and one recording a short follow-up meeting. The two
documents share one relationship assertion — Andrew Chan as a beneficiary
of the Hillcrest Family Trust — and the second document introduces two
further beneficiaries not mentioned in the first.

Case 04 is a deliberately **composite** case. It tests two things at once:

- whether the extractor finds the same semantic edge in more than one
  document, and
- whether the deterministic builder merges the duplicate candidates into a
  single edge.

The case is designed to expose the second of these. A correct extraction
produces eight candidates, two of which describe the same edge. If the
builder does not merge them, the predicted graph contains one extra edge
and the evaluation shows exactly one false positive, alongside a true
positive for the correctly merged edge. That failure mode is the point of
the case.

The two documents use different wording for the shared edge, which allows
the two candidates to be distinguished by `supporting_text` alone. No
`document` field is present in the extraction or ground-truth schema, so
cross-document provenance attribution is not tested here. Extending the
schema to carry a `document` field would enable that, and is a separate
change.

Case 04 deliberately does not exercise entity aliases (Case 03),
`sibling_of` or `trustee_of` (Case 02), or temporal revision. The follow-up
note explicitly states that nothing recorded at the first meeting had
changed, so that temporal change remains isolated to a later case.