# Two trusts with different role allocations

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can roles be assigned to the named trust without transferring a person’s role to the other trust?

New difficulty: Two Trust entities and role overlap; explicit names, one Source and no temporal update.

Supported relationship types: `beneficiary_of`, `settlor_of`, `trustee_of`.

## Answer key fixed before source drafting

- Sienna Mak → `settlor_of` → Birch Family Trust
- Tobias Mak → `beneficiary_of` → Birch Family Trust
- Uma Chan → `trustee_of` → Birch Family Trust
- Tobias Mak → `settlor_of` → Elm Family Trust
- Sienna Mak → `beneficiary_of` → Elm Family Trust
- Uma Chan → `beneficiary_of` → Elm Family Trust

The 6 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The first trust contributes three edges and the second contributes three. Uma has a trustee role in Birch and a beneficiary role in Elm; the text supplies no Elm trustee. Shared surnames do not create a family edge. The negative explanatory sentence does not add positive relationships.
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
