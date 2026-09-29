# Synthetic Case Authoring Workflow

This document describes a repeatable process for creating synthetic benchmark cases for **Private Client Graph**.

The goal is not to generate lots of documents quickly. The goal is to create cases where:

- the correct graph answer is known in advance;
- the source document is realistic enough to be meaningful;
- the source does not accidentally change the answer key;
- expected extraction is derived from the evidence rather than written backwards from the desired output;
- provenance can be evaluated;
- each new case introduces difficulty deliberately.

## Core separation

Keep three artifacts conceptually separate:

```text
ground_truth.json
    = the graph answer key

source.txt
    = evidence presented to the extractor

expected_extraction.json
    = what a perfect extractor is justified in returning
      from that evidence
```

The ground truth is not intended to record every true statement in the fictional scenario.

It is the complete answer key for the graph task being evaluated.

For example, a source document may truthfully state that a meeting lasted approximately one hour or that the client requested a follow-up. Those facts do not belong in the graph answer key if the extractor is only being asked to reconstruct people, trusts, and supported relationship types.

## 1. Decide what the case is testing

Give every case one primary purpose.

Examples might include:

- explicit happy-path relationships;
- facts distributed across documents;
- indirect wording;
- aliases;
- irrelevant named people;
- conflicting evidence;
- uncertain/proposed relationships;
- historical relationships.

Do not combine several new difficulties merely to make a case feel realistic.

A case should make it possible to answer:

> What new behaviour or failure mode is this case intended to test?

If there is no clear answer, simplify the case.

## 2. Define the supported graph vocabulary

Before writing the fictional scenario, state which entity and relationship types count as valid graph output for the case.

Case 01 begins with:

### Entity types

```text
person
trust
```

### Family relationships

```text
parent_of
sibling_of
spouse_of
```

### Trust relationships

```text
settlor_of
trustee_of
beneficiary_of
```

Later cases may expand this vocabulary, but additions should be driven by domain requirements or observed benchmark failures rather than speculation.

## 3. Define the fictional graph in plain English first

Before writing JSON, describe a small fictional world in ordinary language.

For example:

- Alice Chen is the settlor of the Evergreen Family Trust.
- Alice Chen and David Chen are spouses.
- Alice Chen and David Chen are parents of Bob Chen.
- Bob Chen and Carol Wong are beneficiaries of the Evergreen Family Trust.

Challenge every proposed relationship:

- Is it necessary for this case?
- Is it within the relationship types currently being tested?
- Does it introduce legal/domain complexity we do not need?
- Can an ordinary source document state it clearly?
- Would evaluating it require another capability that is meant to be deferred?

Do not add relationships simply because they are common in real private-client structures.

## 4. Encode the graph answer key

Once the fictional graph is agreed, create `ground_truth.json`.

Ground-truth entities should contain only the information needed to identify them for the benchmark, currently:

- stable ID;
- type;
- canonical name.

Ground-truth relationships should contain:

- source entity ID;
- relationship type;
- target entity ID.

Do not put document evidence into ground truth.

A relationship is true in the fictional graph independently of which document later provides evidence for it.

## 5. Keep the answer key hidden from the extractor

The ground-truth fixture may be supplied to tools or agents involved in **authoring the benchmark source**, but it must not be supplied to the extraction pipeline being evaluated.

The intended separation is:

```text
BENCHMARK AUTHORING

ground_truth.json
       ↓
source authoring / domain review
       ↓
source.txt


EXTRACTION EXPERIMENT

source.txt
       ↓
extractor
       ↓
extracted result

ground_truth.json ──X──> extractor
```

Ground-truth IDs must also not be exposed to the extractor.

Extracted entities should have identities independent of the hidden answer key.

## 6. Choose a plausible document situation

Before asking an agent to generate prose, decide why the document exists.

The situation should naturally allow the target relationships to arise without requiring unrelated facts.

For Case 01, the useful framing was:

> An approximately one-hour initial fact-finding and review meeting concerning an existing family trust, where the client wants the professional to have an accurate understanding of the current family and beneficiary position before further review or substantive advice.

This framing creates room for realistic discussion without requiring new trustees, assets, tax facts, distributions, ownership structures, or family members.

Avoid meeting purposes that naturally demand facts outside the intended case.

For example, a tax-planning or trust-restructuring meeting may make silence about assets, office-holders and tax status feel artificial.

## 7. Use domain expertise to author realistic evidence

A domain-expert agent can be used as a **source author**, not as the benchmark designer.

Give the agent:

- the immutable graph answer key;
- the meeting/document framing;
- explicit constraints on facts it may not invent;
- the desired level of realism;
- the requirement that every target relationship has explicit textual support.

The source-authoring agent may know the hidden answer key because it is helping create the fixture.

The extraction agent later must not.

Do not ask the source-authoring agent to design the expected extraction.

## 8. Allow graph-neutral context

A realistic professional document can be substantially longer than the graph-bearing evidence inside it.

Useful graph-neutral material may include:

- purpose and scope of the meeting;
- the client's objectives;
- questions asked to establish the factual position;
- explanations of the review process;
- clarification;
- repetition;
- recap;
- limitations on what has been reviewed;
- questions about next steps;
- procedural next steps.

This context is valuable because the extractor must distinguish relevant graph evidence from ordinary professional prose.

However, do not use "outside today's schema" as permission to invent arbitrary facts.

Ask:

> Does this sentence assert another durable fact about the fictional world?

If yes, decide deliberately whether the fixture needs that fact.

## 9. Guard against accidental answer-key changes

Private-client documents can be relationship-dense.

Apparently harmless detail can introduce new graph facts.

Review generated source material for accidental mentions of:

- additional parents, children or siblings;
- additional spouses or partners;
- additional beneficiaries;
- trustees or protectors;
- other settlors;
- advisers or professionals;
- other trusts or organisations;
- historical or proposed relationships.

For the current benchmark, also be cautious about assets, ownership, distributions, powers, tax status and succession arrangements because they may create future graph-relevant facts or force additional domain assumptions.

The practical rule is:

> If the source introduces another true relationship of a type the benchmark is currently testing, update the answer key deliberately or remove the statement.

Never leave the source and ground truth inconsistent.

## 10. Audit the generated source before accepting it

Do not immediately save generated prose as `source.txt`.

Perform at least two manual checks.

### Answer-key integrity

For every supported relationship stated or implied by the source:

- Is it present in `ground_truth.json`?
- Has the source accidentally introduced an additional supported relationship?
- Has it contradicted an existing relationship?

### Evidence coverage

For every relationship in `ground_truth.json` that the source is intended to expose:

- Is there at least one clear passage that supports it?
- Is that passage sufficiently self-contained to serve as provenance?
- Does extracting the relationship require an assumption that the benchmark did not intend to test?

Only accept the source when both checks pass.

## 11. Prefer realistic language over artificial explicitness

Happy path does not need to mean unnatural prose.

Simple local pronouns are acceptable when their referent is obvious:

> Alice Chen confirmed that she is the settlor...

Avoiding every pronoun can make a source document unrealistic without meaningfully improving the benchmark.

The early cases should defer difficult alias/entity-resolution problems, not ordinary language itself.

## 12. Derive expected extraction from the accepted source

Only after `source.txt` is frozen should `expected_extraction.json` be created.

Read the source as though you were the extractor.

For each justified relationship:

1. identify the source entity;
2. identify the canonical relationship type;
3. identify the target entity;
4. select at least one exact supporting passage;
5. create/reference an evidence object.

Do not simply copy the relationships from `ground_truth.json` and attach convenient quotes.

The purpose of this step is to independently verify:

> What is the source actually sufficient to conclude?

For easy cases, expected extraction may contain the same relationship set as ground truth.

Later cases may intentionally differ.

## 13. Provenance rules

Every expected extracted relationship requires provenance.

Evidence should contain:

- stable evidence ID;
- source document;
- exact supporting text selected from that document.

Relationships reference evidence IDs.

Evidence does not need a duplicate back-reference to relationships; reverse views can be derived.

### Minimum sufficient evidence

A perfect extractor needs to provide **at least one sufficient supporting passage per relationship**.

It is not required to find every occurrence of the same fact.

For example, if a relationship is stated during fact-finding and repeated during the final recap, either sufficiently clear passage may justify the edge.

This keeps the benchmark focused on grounded graph reconstruction rather than exhaustive mention detection.

## 14. Validate the three artifacts together

Before considering a case complete, inspect:

```text
ground_truth.json
source.txt
expected_extraction.json
```

Check that:

- every ground-truth entity needed by the case is coherent;
- every expected relationship is supported by source evidence;
- every expected relationship maps to the intended graph truth;
- every evidence quote actually appears in the source;
- no supported source relationship is missing from the answer key;
- no expected edge depends on information hidden only in ground truth;
- no ground-truth IDs have leaked into the source or extraction fixture.

## 15. Keep case difficulty incremental

Do not make future cases "more realistic" by turning on every difficult feature at once.

A useful progression might be:

```text
Case 01
explicit happy path

Case 02
one additional controlled difficulty

Case 03
another controlled difficulty
...
```

The exact sequence should be chosen based on what the earlier extraction experiments reveal.

Complexity should be earned by observed failures.

## 16. Record domain feedback and design changes

If a lawyer, domain-expert agent, evaluator result or implementation failure reveals that a fixture is unrealistic or underspecified:

1. record what was learned;
2. decide whether it changes the graph answer key, source-authoring rules, extraction contract or evaluation;
3. update the relevant decision note;
4. regenerate/revise the fixture deliberately.

Do not silently patch the source document while leaving the benchmark assumptions undocumented.

## Case author checklist

Before implementation/testing:

- [ ] What single behaviour is this case testing?
- [ ] What entity types are in scope?
- [ ] What relationship types are in scope?
- [ ] Has the fictional graph been agreed in plain English?
- [ ] Is `ground_truth.json` complete for the graph task?
- [ ] Is the document situation plausible?
- [ ] Has domain realism been sanity-checked?
- [ ] Does the source avoid accidental extra graph relationships?
- [ ] Does every intended edge have at least one sufficient supporting passage?
- [ ] Has `expected_extraction.json` been derived from the source rather than copied from ground truth?
- [ ] Does every expected edge reference provenance?
- [ ] Do all evidence quotes occur verbatim in the source?
- [ ] Is the extractor kept blind to ground truth?
- [ ] Is this case adding only the intended new difficulty?

## Working principle

> Define the answer key first, generate realistic evidence from it, audit the evidence, and only then define what a perfect extractor should return.

The benchmark should become more difficult because we deliberately introduce a meaningful new challenge, not because fixture generation accidentally made the fictional world more complicated.
