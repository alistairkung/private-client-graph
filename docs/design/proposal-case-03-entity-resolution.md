# Proposal: Case 03 Entity Resolution Experiment

Status: proposal for design review. Implementation is not authorised by this document.

## Context

Private Client Graph currently follows a deliberately simple semantic path:

```text
Source
→ LLM relationship extraction
→ RelationshipCandidate[]
→ deterministic Entity derivation and graph construction
→ evaluation
```

Entity construction currently groups relationship endpoints using exact, case-sensitive names. This was sufficient for Case 01 and remains sufficient for Case 02.

Case 03 deliberately challenges that assumption:

> Can the system resolve the same person referred to by multiple surface forms without splitting or merging entities incorrectly?

## Current observed failure

Case 03's committed expected-extraction fixture currently produces:

- 6 true-positive relationships;
- 1 false positive;
- 1 false negative;
- precision = 85.7%;
- recall = 85.7%;
- F1 = 85.7%;
- provenance accuracy = 100% among correctly matched relationships.

The mismatch concerns the spouse relationship: expected extraction uses `Rebecca`, while ground truth identifies `Rebecca Tan`. Exact-name construction therefore treats them as distinct Entities.

This is a deterministic expected-extraction result, not a fresh live LLM run.

## Established persistence boundary

Entity identity is separate from Entity name.

Within one Matter:

- two distinct Entities may legitimately have identical names;
- multiple surface forms may eventually resolve to one Entity;
- Relationships refer to Entity identity rather than treating names as permanent identity;
- persistence must represent either outcome.

Exact-name grouping remains a Case 01 compatibility policy, not a permanent semantic identity rule. Entity resolution was explicitly deferred from the canonical-persistence redesign.

## Semantic requirement

Correct resolution must work in both directions.

Different surface forms may identify one real-world Entity:

```text
Rebecca Tan
Rebecca
Mrs Tan
→ potentially one Entity
```

Identical or similar names may identify different real-world Entities:

```text
John Smith
John Smith
→ potentially two Entities
```

Deterministic/fuzzy name normalisation is therefore not a general solution. Entity correspondence may require document context and semantic reasoning.

## Immediate experiment gate

Do not change architecture solely because the expected-extraction fixture fails. First run Case 03 through the current live extractor.

Possible outcomes:

1. The live extractor produces consistent identity and Case 03 passes: do not add a resolver merely because one was anticipated.
2. The live extractor emits multiple surface forms for one participant and identity splitting causes the failure: entity resolution is likely an earned semantic capability.
3. The live run fails for another reason: diagnose that failure rather than assuming entity resolution is the fix.

## Working hypothesis: semantic Entity Resolver

If the live failure confirms the hypothesis, one candidate is:

```text
Source
→ LLM relationship extraction
→ RelationshipCandidate[]
→ LLM Entity Resolver
→ resolved identities / candidates
→ deterministic validation and graph construction
```

The relationship extractor answers what relationships the Source asserts and what exact text supports them.

The Entity Resolver answers which extracted endpoint mentions refer to the same real-world Entities. It should see the relationship candidates plus relevant original Source context. It must not silently change relationship type, meaning, Evidence, or unrelated extraction decisions.

The deterministic layer continues to own structural validation, IDs, canonical graph construction, symmetric handling, deduplication, and persistence integrity.

## Competing designs

A separate resolver is a hypothesis, not an approved architecture. Compare at least:

- baseline: relationship extraction + exact-name deterministic Entity derivation;
- joint semantic extraction: Source → resolved Entities + Relationships;
- separate resolver: Source → relationships → semantic Entity Resolver.

A retrieval-backed resolver is an interesting later experiment, but short Case 03 does not itself justify RAG.

Where multiple approaches remain credible, consider implementing competing strategies and measuring them rather than choosing only by design argument.

## Evaluation implication

Entity resolution should eventually be independently evaluable. Relationship F1 exposes the current failure indirectly, but future ground truth should be capable of distinguishing:

- correct merge;
- incorrect merge / over-merge;
- missed merge / entity split.

Ground truth should represent real-world Entity correspondence rather than relying solely on canonical names.

## Benchmark vs practitioner behaviour

The benchmark asks whether the model inferred Entity correspondence correctly from available source material.

The practitioner product separately asks whether proposed Entity correspondence should become professionally accepted canonical Matter state without further confirmation.

Human-in-the-loop clarification may eventually be useful for genuinely ambiguous identity, but Case 03 does not authorise a merge UI or clarification workflow.

## Future provenance question

Entity resolution may eventually create semantic assertions with provenance of their own, e.g. evidence supporting `Rebecca == Rebecca Tan` rather than a family/trust Relationship. This could eventually motivate provenance for Entity correspondence or a more general Assertion/Evidence concept.

Do not introduce that abstraction merely because it is conceivable.

## Non-goals

This proposal does not authorise fuzzy-name identity, alias tables, practitioner merge UI, HITL clarification, RAG, vector databases, generalized Assertion models, multi-document entity resolution, canonical-persistence changes, or changes designed for later benchmark cases.

## Questions for design review

- Does the live Case 03 result actually earn entity resolution?
- Is entity resolution a separate semantic responsibility?
- Should it be joint with extraction or a second stochastic stage?
- What is the smallest useful resolver input/output contract?
- Should the resolver see the full Source?
- How do we prevent it from silently correcting unrelated extraction errors?
- What ground truth is needed to evaluate under- and over-merging?
- Does whole-proposal confirmation already provide sufficient HITL?
- What should remain deliberately deferred?
