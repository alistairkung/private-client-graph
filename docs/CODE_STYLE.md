# Code style

Read this guide before changing the Python pipeline. Keep conventions grounded in
existing code and requirements demonstrated by benchmark cases.

## Responsibilities and contracts

- `extract.py`: probabilistic semantic extraction; its CLI also handles extraction I/O.
- `graph.py`: deterministic candidate validation and graph construction.
- `evaluation.py`: deterministic semantic-edge and approved-provenance evaluation.
- CLI entry points: argument parsing, file I/O, and orchestration.

Preserve these domain boundaries rather than combining modules to reduce file
count. Pydantic models define explicit data contracts. Prefer plain functions for
deterministic transformations; introduce classes only when concrete state or
behaviour warrants them, not merely to organise functions. Service classes,
strategies, repositories, dependency injection, and inheritance need a real use.

## Public workflows and private helpers

Public entry points should read top-down at one useful abstraction level. A
reader should be able to understand the workflow without simultaneously tracing
index conventions, persistence mechanics, accumulator mutation, or serialization.
`build_graph()` validates candidates, builds entities and evidence, constructs
relationships, and assembles the graph. `evaluate_graph()` validates lookups,
resolves both graphs, compares edges, scores provenance, and builds the result.
Application workflows should tell the same kind of high-level story: load their
inputs, obtain the relevant domain result, perform deterministic construction,
and return the public contract.

Use underscore-prefixed module helpers for named conceptual responsibilities:
`_validate_candidates`, `_build_relationships`, and `_resolve_prediction` are
examples. A helper should hide a meaningful lower-level responsibility or
failure boundary; extraction is justified by that abstraction boundary, not by
function length. Avoid splitting every small operation. The three set operations
comparing edges remain inline because they already communicate the evaluation
policy clearly. Appropriately sized extraction functions and procedural CLI
orchestration need no extra fragmentation.

Prefer intention-revealing names and data representations. If several values
travel together across helpers or modules, give that contract a meaningful type
when it improves comprehension. Do not introduce a class merely to group
functions or replace a small, obvious local tuple.

### Examples from the alias-resolution research refactor

Before, `identity_diagnostics()` mixed annotation lookup, endpoint-position
translation, anonymous tuple construction, pair selection, comparison policy,
counter mutation, and error serialization:

```python
endpoints.append((
    label,
    getattr(candidate, label.endpoint),
    ENDPOINT_TYPES[candidate.relationship_type][side],
))

for (left, left_name, left_type), (right, right_name, right_type) in combinations(endpoints, 2):
    ...
```

After, the public function tells the diagnostic story and leaves mechanics in a
small number of conceptual helpers:

```python
endpoints = _annotated_endpoints(sample, output)
diagnostics = IdentityDiagnostics()
for left, right in _comparable_pairs(endpoints):
    _record_identity_comparison(diagnostics, left, right)
return diagnostics.model_dump()
```

The private `_AnnotatedEndpoint` representation also names `annotation`, `name`,
and `entity_type`, replacing positional knowledge that previously travelled into
the comparison loop. These helpers were earned because each hides a distinct
translation, selection, or recording responsibility. Helpers such as
`_increment_count()` or `_is_same_name()` would not be earned: they would only
rename self-explanatory operations and make the workflow harder to follow.

The same refactor replaced a cross-module result assembled through repeated
string-key updates:

```python
result.update(configuration="generative_full_source", repetition=repetition)
result["evaluation"] = evaluate_graph(graph, sample.truth).model_dump()
```

with a focused `ResearchResult` contract and named attributes:

```python
result.configuration = "generative_full_source"
result.repetition = repetition
result.evaluation = evaluate_graph(graph, sample.truth)
```

This type was earned because the record is persisted and interpreted by the
runner, summary, and report modules. It is not a precedent for introducing a
model for every short-lived dictionary.

## Determinism and validation

The LLM interprets natural-language semantics. Code handles IDs, deduplication,
reference resolution, type consistency, metrics, and canonical ordering.
Verbatim quote occurrence is mechanically checkable; semantic support is a
separate concern.

Validation rejects invalid input; normalization transforms valid input into a
canonical representation. They can share one flow without separate architectural
layers. Validate before constructing results, preserve documented error behaviour,
and do not mutate callers' inputs. In evaluation, check all duplicate IDs before
resolving relationships, and validate references even on false-positive edges.

Keep exact names and quotes intact under the current Case 01 contract. Preserve
sorted output, symmetric-edge normalization, directed-edge direction, pooled
evidence, and explicit zero-denominator metric behaviour.

## Earn abstractions through cases

Let benchmark failures drive new capabilities. Do not introduce pluggable
strategies without a concrete need for alternatives, a graph database simply
because the output is a graph, retry/verifier stages without observed failures,
or a generalized temporal model before cases require one.

## Tests and readability

Each deterministic behavioural rule should have focused unit coverage. Preserve
existing tests during refactors, run the full suite, and add coverage for actual
uncovered behaviour. Test public behaviour rather than private-helper structure;
helpers do not need direct tests when public tests already exercise them.

Use descriptive names, shallow nesting, early validation failures, explicit
intermediate values where useful, and straightforward Python data structures.
Prefer clarity over cleverness or fewer lines. Comments and docstrings should
explain boundaries, non-obvious invariants, or why a constraint exists, rather
than narrating self-explanatory code.

## Mandatory implementation completion gate

Do not declare implementation work complete after tests pass. Before completion,
perform this gate in order:

1. Implement the requested behaviour and run the appropriate focused and
   repository-required tests.
2. Independently inspect the complete changed diff against this guide and the
   repository boundaries in `AGENTS.md`; do not review only the files or hunks
   that were difficult to implement.
3. Identify and refactor material readability problems, including mixed
   abstraction levels, unclear names or representations, excessive nesting,
   duplicated mechanics, and unearned abstractions. Do not manufacture changes
   when the diff is already clear.
4. Rerun the relevant tests after any refactor and inspect the final complete
   diff for clarity, scope, accidental behaviour changes, and debugging residue.
5. Only then report the work complete.

Every implementation PR description must include a concise `Code Quality Review`
section stating:

- what the final-diff review found;
- what was improved as a result; and
- any material readability concern deliberately retained, with the reason.

When the review is clean, say that no material readability problems were found;
the gate does not require unnecessary helper extraction or churn.
