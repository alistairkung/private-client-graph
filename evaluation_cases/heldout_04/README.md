# Two notes corroborating one beneficiary

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can complementary Sources be combined while repeated beneficiary support remains attributed to each originating Source?

New difficulty: Multi-source corroboration and deduplication; full names, one trust and no temporal changes.

Supported relationship types: `beneficiary_of`, `settlor_of`, `trustee_of`.

## Answer key fixed before source drafting

- Jonas Chan → `settlor_of` → Maple Family Trust
- Keira Chan → `beneficiary_of` → Maple Family Trust
- Lina Ho → `trustee_of` → Maple Family Trust

The 3 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The shared beneficiary sentence occurs identically in both Sources and represents one edge with two eligible Evidence items. Jonas and Keira share a surname but no family relationship is asserted. The office-holder appears only in the follow-up.
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
