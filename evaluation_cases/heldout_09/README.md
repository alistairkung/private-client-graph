# Administrative detail around a small relationship record

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can supported relationships be recovered without treating administrative participants and process descriptions as graph facts?

New difficulty: Distractor density and unrelated named administrative contacts; explicit positive relationships and one Source.

Supported relationship types: `beneficiary_of`, `settlor_of`, `trustee_of`.

## Answer key fixed before source drafting

- Yasmin Fong → `settlor_of` → Hazel Family Trust
- Zachary Fong → `beneficiary_of` → Hazel Family Trust
- Adele Ip → `trustee_of` → Hazel Family Trust

The 3 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. Exactly three positive supported edges are supplied. Bruno and Clara are administrative contacts only and belong to no current edge. The shared Fong surname is expressly not evidence of family status. Process, document checking and unexamined assets do not introduce graph facts.
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
