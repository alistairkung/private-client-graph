# A letter confirming the Juniper review facts

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Does a short client confirmation letter preserve explicit family and trust facts outside attendance-note prose?

New difficulty: Document genre: signed confirmation letter; explicit names and one trust remain stable.

Supported relationship types: `beneficiary_of`, `parent_of`, `settlor_of`, `spouse_of`.

## Answer key fixed before source drafting

- Nadia Lau → `settlor_of` → Juniper Family Trust
- Nadia Lau → `spouse_of` → Owen Lau
- Nadia Lau → `parent_of` → Maya Lau
- Owen Lau → `parent_of` → Maya Lau
- Maya Lau → `beneficiary_of` → Juniper Family Trust

The 5 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The letter asserts five edges; its signature and procedural request add no graph facts. The joint-parent sentence supports two directed edges. No sibling relationship is implied because there is only one named child.
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
