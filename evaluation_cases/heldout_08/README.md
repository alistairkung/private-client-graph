# Distinct Sources carrying the same display title

Split: held-out. Synthetic material only. Not a continuation of development Cases 01–05.

Purpose / primary hypothesis: Can distinct input identities survive matching Source titles while complementary facts are combined?

New difficulty: Duplicate Source titles; full names, no temporal changes and disjoint factual support.

Supported relationship types: `beneficiary_of`, `parent_of`, `settlor_of`, `spouse_of`.

## Answer key fixed before source drafting

- Victor Lo → `spouse_of` → Wendy Lo
- Victor Lo → `parent_of` → Xavier Lo
- Wendy Lo → `parent_of` → Xavier Lo
- Victor Lo → `settlor_of` → Rowan Family Trust
- Xavier Lo → `beneficiary_of` → Rowan Family Trust

The 5 edges above are the complete intended current relationship answer key.
Only participants in those edges belong to the current graph. Unstated family or
trust links must not be inferred from surnames, attendance or document handling.

## Bidirectional semantic audit

Every listed edge has exact support in its identified Source. The two titles intentionally match, but family and trust are different explicit Source IDs. The first Source supports three family edges and the second supports two trust edges. A title-based merge or guessed document attribution is incorrect. Neither Source creates extra relationships beyond those five.
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
