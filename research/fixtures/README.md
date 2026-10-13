# Frozen alias-resolution inputs

These are research inputs, not new numbered benchmark cases or ideal-extraction
fixtures. The source/answer keys for Cases 01–03 remain under `cases/` and unchanged.
`load_inputs()` freezes their exact text, hashes, extractions and these reviewed
endpoint annotations into each experiment manifest.

## Agreed answer keys and semantic review

The matched challenge was approved in the issue #91 design interview (Q4).
Its sole new difficulty is alias correspondence; the ontology remains person/trust
with `settlor_of` and `beneficiary_of`.

- `alias_merge`: Elizabeth Tan is settlor and beneficiary of Harbour Trust. Beth
  is her nickname. The Source immediately establishes that identity before the
  beneficiary quote. Ground truth contains precisely those two roles and no others.
- `alias_distinct`: Elizabeth Tan is settlor and a distinct person named Beth is
  beneficiary of Harbour Trust. The immediate clarification requires preservation
  of the two people. Ground truth again contains precisely those two roles.

The two `extraction.json` files are byte-identical intentionally unresolved inputs.
Both exact supporting quotes occur in both Sources. Each approved quote supports
its answer-key edge when read with the immediately preceding clarification. The
procedural opening/closing sentences add no supported relationships. The answer
keys were written first; source drafting and candidate fixtures followed. No live
model was used to author, review or validate these fixtures. This implementation
preserves the two participant configurations explicitly reviewed by the user;
changes to their semantics require further review.

Annotations are keyed by candidate index and endpoint side, with participant IDs
from the corresponding truth. Cases 01/02 map the explicit named endpoints to their
participants; Case 03 maps both Rebecca and Rebecca Tan to `person_001`. The saved
historical Case 03 extraction has the same candidate order and uses Rebecca Tan
consistently. These are reviewed labels, never runtime inference from name matching
and never input to the resolver. Do not use them to claim coverage of homonyms.

## Historical observation

`case_03_historical/extraction.json` and `metadata.json` are exact copies of the
single recorded live observation supplied in issue #91. They retain its original
UTC timestamp, commit, model, prompt, usage and elapsed time; the loader checks
its Source and ground-truth hashes. This is one historical observation, not three
fresh samples and not evidence of longitudinal stability.

## Deterministic demonstration

`demonstration_responses.json` contains deliberately authored endpoint edits and
a replay of the historical extraction, selected by exact input hashes. They exist
only to exercise the runner and HTML report without network calls. Resolution
responses are substitutes, not measured model predictions. Demonstration manifests,
raw responses and reports are labelled accordingly. Model usage is unknown and
paid-call count is zero; measured Python execution time is not provider latency.
