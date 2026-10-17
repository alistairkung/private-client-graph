# An older trustee note supplied after the effective update

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Does explicit effective chronology determine the current trustee even when the older document is supplied last?

New difficulty: Source order differs from temporal order; one trust and one completed replacement remain stable.

Supported relationship types: `beneficiary_of`, `settlor_of`, `trustee_of`.

## Answer key fixed before source drafting

- Petra Lam → `settlor_of` → Alder Family Trust
- Quinn Lam → `beneficiary_of` → Alder Family Trust
- Rita Yuen → `trustee_of` → Alder Family Trust

The 3 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The manifest intentionally orders update before archive. The supplied explicit dates and completed replacement establish Rita as current; Samuel is historical and absent from the current graph. Reordering the texts must not silently impose a last-document-wins policy. The historical note still supplies the unchanged settlor and beneficiary support.
The source-to-answer-key review found no further supported current relationship.
No conflicting assertions or new relationship/entity types are introduced.

## Evidence and execution

`sources.json` fixes Source identity and supplied order; titles are display values.
`source.txt` is a compatibility concatenation only. The live full-context request
must use the original individual Sources and their explicit identities.
`source_evidence.json` lists approved `(source_id, supporting_text)` pairs keyed
to answer-key endpoints. Legacy quote metrics remain unchanged. The ideal source
extraction and `expected_state.json` select all listed support in this fixture;
a correct model may select a sufficient subset, without exhaustive corroboration.
Every selected item must support its edge and name its actual Source.

These are authored ideals, not recorded model results. No provider was invoked.
Independent validator review and user benchmark approval are required before paid
held-out evaluation. Freeze text/truth after approval; do not tune against results.
