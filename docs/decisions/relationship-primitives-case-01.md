# Relationship primitives — Case 01

## Context

Private Client Graph is testing whether GenAI can reconstruct a synthetic family/trust relationship graph from source documents while preserving provenance and uncertainty.

Before defining the extraction contract, we explored what kinds of relationships should exist in the smallest happy-path case, and how to avoid forcing natural-language family descriptions into graph structure that the evidence does not actually support.

The guiding principle is:

> Store the smallest set of structural relationships that can be stated directly or derived deterministically, and do not invent intermediate entities or edges merely to explain a natural-language kinship label.

This note captures the current Case 01 decision. It is deliberately provisional: the vocabulary should expand only when later benchmark cases demonstrate that another primitive is necessary.

## Decisions

### 1. Represent relationships as typed edges between entities

The conceptual model is:

```text
entity -- relationship_type --> entity
```

The data model should not be designed around six bespoke fields. Relationship types should be extensible so that later domain discoveries can add new primitives without changing what an entity or relationship fundamentally is.

### 2. Canonicalise inverse relationships instead of extracting redundant edges

Example:

```text
Alice parent_of Bob
```

is sufficient.

We should not separately require:

```text
Bob child_of Alice
```

because that inverse can be derived deterministically.

This applies the same principle used in the receipt-extraction project: do not ask a probabilistic component to produce redundant information that deterministic code can derive.

### 3. Symmetric relationships should be represented once

For example:

```text
Alice spouse_of David
```

and

```text
David spouse_of Alice
```

represent the same fact.

The extraction/evaluation layer should understand that `spouse_of` is symmetric rather than requiring the LLM to emit two edges or follow an arbitrary source/target ordering convention.

The same reasoning applies to `sibling_of`.

### 4. Case 01 family relationship primitives

For Case 01, the agreed family primitives are:

```text
parent_of
sibling_of
spouse_of
```

Semantics:

- `parent_of` is directed.
- `sibling_of` is symmetric.
- `spouse_of` is symmetric.

These are sufficient for the first benchmark case, but they are not intended to be a complete ontology of family relationships.

### 5. Case 01 trust relationship primitives

For Case 01, the agreed trust-role primitives are:

```text
settlor_of
trustee_of
beneficiary_of
```

All three are modelled as directed person-to-trust relationships.

For example:

```text
Alice -- settlor_of -----> Evergreen Family Trust
David -- trustee_of -----> Evergreen Family Trust
Bob   -- beneficiary_of -> Evergreen Family Trust
```

The trustee role was discussed but is not required to appear in the first synthetic world merely because it exists in the domain.

### 6. Do not create a primitive for every kinship word

Terms such as:

```text
aunt
uncle
niece
nephew
cousin
grandparent
```

can often be derived from simpler structural relationships when enough evidence exists.

Example:

```text
Alice sibling_of Emma
Emma parent_of Sophie
```

allows the system to derive that Alice is Sophie's aunt and Sophie is Alice's niece.

Therefore, `aunt_of`, `niece_of`, `cousin_of`, etc. are not Case 01 graph primitives.

### 7. Do not invent hidden graph structure to explain an observed kinship label

If a source document says only:

> Sophie is Alice's niece.

the system must not manufacture something like:

```text
Alice sibling_of UnknownPerson
UnknownPerson parent_of Sophie
```

The missing person and relationships are plausible explanations, but they are not evidence.

Similarly, if a document says:

> George is Alice's grandfather.

we should not invent an unnamed intermediate parent solely to force the statement into `parent_of` edges.

### 8. Preserve unsupported kinship descriptions as evidence/context, not fabricated graph edges

If a source says:

> Sophie, Alice's niece, is a beneficiary of the Evergreen Family Trust.

and the source does not reveal the structural path that makes Sophie Alice's niece, the graph can safely contain:

```text
Sophie beneficiary_of Evergreen Family Trust
```

The phrase "Alice's niece" should still be preserved in provenance/context so that later documents can provide enough information to reconstruct the primitive family relationships.

Example of later evidence:

```text
Emma is Alice's sister.
Sophie is Emma's daughter.
```

This would then justify:

```text
Alice sibling_of Emma
Emma parent_of Sophie
```

and the niece relationship becomes deterministically derivable.

This distinction supports the project goal of preserving what the evidence actually supports rather than filling gaps with plausible assumptions.

## Why `sibling_of` remains a primitive

A sibling relationship can sometimes be derived from shared parents:

```text
Grace parent_of Alice
Grace parent_of Emma
```

However, documents may directly say:

> Emma is Alice's sister.

without identifying either parent.

If `sibling_of` were not a primitive, we would either lose an explicitly stated fact or invent unknown parents. Therefore `sibling_of` is justified as a primitive even though some sibling relationships are derivable from parent edges.

## Relationships considered but deferred

We tested the primitive set against several plausible future statements.

### Divorce / former spouse

A statement such as:

> Alice and David divorced in 2022.

cannot be truthfully represented as a present-tense `spouse_of` edge.

This suggests that relationship status/time may eventually need to be modelled orthogonally to relationship type.

Historical relationships are explicitly deferred from Case 01.

### Adoption

For the current abstraction, an adopted parent can still be represented by:

```text
Alice parent_of Bob
```

The fact that the relationship arose through adoption is additional context/provenance rather than a separate primitive for Case 01.

### Half-sibling

```text
Alice sibling_of Emma
```

still captures the existence of the sibling relationship.

If the relevant parent structure later becomes known, the graph can represent the information that makes the relationship specifically half-sibling.

### Partner

`partner_of` is not equivalent to `spouse_of` and cannot currently be represented without loss.

It is deferred until a benchmark case requires it.

### Legal guardian

`guardian_of` is not a kinship relationship and cannot currently be represented by the family primitives.

It is deferred because Case 01 is scoped to family structure plus trust roles.

## Scope boundary

For the first happy-path benchmark:

> Model family structure plus roles connecting people to a trust.

Do not attempt to model every possible private-client relationship yet.

Possible future domains may include:

- guardianship;
- corporate ownership/directorship;
- powers of attorney;
- advisers;
- trust roles not yet encountered;
- historical relationship state.

Those should only be introduced when observed benchmark/domain requirements justify them.

## Case 01 primitive vocabulary

Current agreed vocabulary:

```text
FAMILY
parent_of
sibling_of
spouse_of

TRUST
settlor_of
trustee_of
beneficiary_of
```

This means:

> These six relationships are sufficient for Case 01.

It does **not** mean:

> These six relationships are a complete model of the private-client domain.

## Next design question

The next unresolved question is:

> What counts as an entity in Case 01?

The current candidate entity types are `Person` and `Trust`, but the rationale and minimum required fields have not yet been agreed.
