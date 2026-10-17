# Named short form within one interview

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can an explicitly introduced short form be linked to its named person while preserving the supplied evidence text?

New difficulty: One explicit alias; no same-name people, temporal change or multiple Sources.

Supported relationship types: `beneficiary_of`, `parent_of`, `settlor_of`.

## Answer key fixed before source drafting

- Beatrice Ng → `settlor_of` → Larch Family Trust
- Beatrice Ng → `parent_of` → Isaac Ng
- Isaac Ng → `beneficiary_of` → Larch Family Trust

The 3 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The explicit Bea/Beatrice mapping makes each local short-form assertion unambiguous. Canonical expected endpoints use Beatrice Ng; the quotes retain Bea exactly. There is no basis to add a spouse or another parent.
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
