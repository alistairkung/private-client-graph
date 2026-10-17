# One dense sentence in a factual recap

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can one sentence be decomposed into distinct family and trust-role edges without conflating sibling and beneficiary status?

New difficulty: Relationship density in one sentence; one Source and explicit canonical names remain stable.

Supported relationship types: `beneficiary_of`, `settlor_of`, `sibling_of`.

## Answer key fixed before source drafting

- Felix Wong → `settlor_of` → Amber Family Trust
- Grace Wong → `sibling_of` → Hugo Wong
- Grace Wong → `beneficiary_of` → Amber Family Trust
- Hugo Wong → `beneficiary_of` → Amber Family Trust

The 4 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The single positive sentence asserts four edges. The explanation restates the same connections and supplies no new parent, spouse or trustee. Grace and Hugo are not assumed to be children of Felix.
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
