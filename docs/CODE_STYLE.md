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

Public entry points should read top-down at a useful abstraction level.
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
