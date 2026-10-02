# Private Client Graph

A FTEC5660 hackathon technical spike exploring whether GenAI can reliably reconstruct **family and trust relationship graphs** from synthetic documents while preserving **provenance, ambiguity, and uncertainty**.

> **Iteration 1 scope guardrail:** The purpose of this iteration is to test the core **extraction → structured relationships → provenance → visual graph** capability.

## Hackathon problem

Family and trust relationships can be represented as a graph of people, trusts, organisations, and typed relationships. In realistic documents, however, those relationships are expressed in natural language rather than supplied as structured graph data.

This project tests whether a GenAI extraction pipeline can reconstruct those relationships from **synthetic source material**, retain evidence for each extracted edge, and be evaluated against a hidden ground-truth graph.

The emphasis is on a measurable technical experiment rather than a polished application.

## Iteration 1 hypothesis

> Can GenAI reconstruct a complex but synthetic family/trust relationship graph from a small set of documents with enough precision, provenance, and appropriate abstention to produce a useful evaluated prototype?

The extractor will operate on synthetic material only.

## Run the Case 01 extraction slice

From the repository root, with Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
# Add DEEPSEEK_API_KEY to the local .env file before running.
python -m private_client_graph.extract
python -m pytest
```

The command reads only `cases/case_01/source.txt` and prints an
`ExtractionResult` JSON object containing relationship candidates to stdout.
It also saves each successful result to `runs/case_01/YYYY-MM-DDTHHMMSS.json`,
using the UTC completion time. Files contain only the existing `ExtractionResult`
JSON. The `runs/` folder is local-only and ignored by Git.
Existing files are never overwritten; a same-second filename collision
raises an error. Neither answer-key fixture is read by the extractor.

The default model is `deepseek-flash`; override with `--model MODEL_NAME`.
The CLI loads `.env` using `python-dotenv` (existing environment values take
precedence). `.env` is ignored by Git. Like the receipt-agent coursework,
extraction uses a `ChatPromptTemplate` and an LCEL chain:
`prompt | llm.with_structured_output(ExtractionResult)`.

`ChatDeepSeek` uses function calling to request the existing Pydantic schema;
LangChain parses the returned tool arguments into `ExtractionResult` and raises
on schema failures. This is not a server-side strict JSON-schema guarantee.
No manual JSON parser or deterministic evidence checks are added. A missing
structured result or API error fails the run, and `max_retries=0` disables client
retries. Thinking is disabled, following receipt-agent's configuration.

Names are assumed unambiguous for Case 01. Supporting quotes may rely on local
pronoun context; the open evidence-span decision remains deferred. Tests use a
stubbed HTTP response to check the integration, not to measure model extraction
quality. A live run requires a DeepSeek API key and network access.

## Deterministic graph construction

`private_client_graph.graph.build_graph` accepts structured candidates independently
of the extraction chain:

```python
from private_client_graph.graph import build_graph

graph = build_graph(
    result.relationships,
    document="cases/case_01/source.txt",
    source_text=source_text,
)
```

The caller supplies a sequence of `RelationshipCandidate` objects (such as
`result.relationships`), the document identity as `document`, and its content as
`source_text`. The builder performs no file I/O or model calls. It first rejects
empty or whitespace-only names/evidence, non-verbatim evidence,
self-relationships, unsupported types, and conflicting
endpoint types with `ValueError`; it never returns a partial graph.

It then constructs `CanonicalGraph` with lean entities, relationships, and evidence.
Names are exact, case-sensitive identity keys for Case 01. Sorted names and quotes
receive graph-local sequential IDs. Symmetric endpoints use alphabetical name
order; directed edges retain their direction. Duplicate edges retain all distinct
evidence references, and identical quotes share one evidence object within the
supplied document. Output ordering is independent of candidate ordering.

Verbatim matching only checks that a quote occurs in the source; it does not
establish semantic support. The extraction CLI and its output contract remain
independent of graph construction.

## Deterministic Case 01 evaluation

To evaluate a saved extraction and save its metrics and diagnostics alongside it:

```bash
python -m private_client_graph.evaluate runs/case_01/2026-10-02T075056.json
```

This creates `runs/case_01/2026-10-02T075056.evaluation.json` and prints the same
`EvaluationResult` JSON. It uses the current Case 01 source and ground-truth
fixtures, makes no model calls, and leaves the extraction file unchanged.
Existing evaluation files are never overwritten. Both files remain local-only
under the Git-ignored `runs/` directory.

`private_client_graph.evaluation.evaluate_graph(graph, ground_truth)` accepts an
already constructed `CanonicalGraph` and a `GroundTruth` model. It performs no
model calls or file I/O and does not depend on the extraction or graph builder.

```python
from pathlib import Path
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.models import GroundTruth

ground_truth = GroundTruth.model_validate_json(
    Path("cases/case_01/ground_truth.json").read_text(encoding="utf-8")
)
evaluation = evaluate_graph(graph, ground_truth)
```

Both inputs resolve their own entity IDs to exact names. The evaluator compares
sets of `(source_name, relationship_type, target_name)` tuples, sorting endpoints
only for `spouse_of` and `sibling_of`. TP is the intersection; FP and FN are the
respective set differences. Precision is `TP / (TP + FP)`, recall is
`TP / (TP + FN)`, and F1 is `2 * TP / (2 * TP + FP + FN)`.

Ground-truth relationships retain their entity ID references and now include
`approved_evidence`: the benchmark's explicit list of acceptable exact spans.
These annotations extend the earlier truth-only fixture for provenance evaluation.
They include alternatives from the source's summaries and recap, including spans
that resolve pronouns through local context. `expected_extraction.json` remains
one ideal extraction, not the exhaustive list of approved evidence. Arbitrary
longer quotes or paraphrases are not automatically approved.

Provenance passes for a true-positive edge when at least one attached quote
exactly matches one approved span. Extra unapproved quotes do not fail that edge.
Provenance accuracy divides passes by TP; FP and FN do not enter this metric.
All zero denominators return `0.0`, including an empty-vs-empty comparison and
provenance accuracy with no TP. Counts and sorted semantic-edge diagnostic lists
in `EvaluationResult` distinguish these cases from measured successes.

Duplicate semantic edges count once and pool their evidence. Missing entity or
evidence references and duplicate IDs raise `ValueError` before scoring, including
broken evidence references on FP edges. Empty attached evidence lists produce a
provenance failure for TP edges. Source-text occurrence validation remains solely
the graph builder's responsibility; evaluation checks approved support by exact
text, not document IDs or semantic similarity.

## Proposed first vertical slice

The smallest credible end-to-end slice is:

```text
synthetic ground-truth graph
        ↓
2–3 synthetic source documents
        ↓
LLM relationship extraction
        ↓
structured JSON
        ↓
deterministic validation / normalisation
        ↓
merge into relationship graph
        ↓
basic visualisation
        ↓
compare extracted graph with hidden ground truth
```

The first case should use **unambiguous names** so that Iteration 1 tests relationship extraction rather than immediately becoming an entity-resolution project.

## Evaluation philosophy

The demo should not rely on “the graph looks right.”

We will create the hidden ground-truth graph first, derive synthetic documents from it, and evaluate the extractor against that truth.

Candidate metrics:

- relationship precision;
- relationship recall;
- unsupported / hallucinated relationship rate;
- provenance accuracy;
- ambiguity / abstention behaviour;
- contradiction handling, if introduced later.

The initial development set should contain several deliberately different scenarios rather than many random examples.

Suggested scenario categories:

1. explicit happy-path relationships;
2. facts distributed across multiple documents;
3. indirect natural-language relationships;
4. aliases / alternate references;
5. statements that should **not** become graph edges;
6. conflicting sources;
7. ambiguous or incomplete evidence where abstention is correct.

The exact scenarios and their difficulty should be agreed jointly before implementation.

---

# Shared design worksheet

The sections below are intentionally incomplete. They are the decisions we should make together before building too far.

## 1. Iteration 1 problem statement

**We need to agree:**

- What exact question is Iteration 1 trying to answer?
- What evidence would make us say the spike is promising?
- What would count as a failed experiment?
- Are we evaluating relationship extraction only, or also entity resolution?
- What should the system explicitly refuse to infer?

### Agreed statement

> TODO — write together.

## 2. Scope

### In scope

Things we currently expect Iteration 1 to include:

- synthetic private-client-style source material;
- people and trusts;
- typed family/trust relationships;
- source provenance for each extracted relationship;
- structured extraction;
- deterministic validation / normalisation;
- relationship merging;
- basic visual graph;
- ground-truth evaluation.

### Explicitly out of scope

Candidates to defer unless the experiment itself requires them:

- real or confidential client data;
- production authentication or permissions;
- external enterprise integrations;
- production graph infrastructure;
- full RAG architecture;
- complex multi-agent orchestration;
- polished frontend.

### Team decision

> TODO — cut anything else we can postpone.

## 3. Synthetic evaluation set

The synthetic cases are effectively the specification for the experiment, so they should be designed together.

### Ground-truth process

Questions to agree:

- Do we define the graph first and then write documents from it?
- How many cases do we need for Weekend 1?
- Which cases are “development” cases versus later challenge cases?
- Do we include explicit negative expectations / relationships that must not be extracted?
- How do we represent conflicts or ambiguous facts in the truth data?

### Proposed case list

| Case | Goal | Status |
|---|---|---|
| 01 | Explicit happy path | TODO |
| 02 | Cross-document facts | TODO |
| 03 | Indirect language | TODO |
| 04 | Alias / alternate reference | TODO |
| 05 | Non-relationship / distractor | TODO |
| 06 | Conflicting sources | TODO |
| 07 | Ambiguous evidence / abstention | TODO |

> TODO — decide whether all seven belong in the first build or whether 1–3 are enough for the first vertical slice.

## 4. Data model / extraction contract

We should agree the **meaning** of the contract before arguing about exact Python classes.

### Entities

Questions:

- Which entity types exist in Iteration 1?
- Person?
- Trust?
- Organisation / corporate trustee?
- Do entities need stable IDs, or can the merge layer assign them?

### Relationships

Candidate examples:

```text
spouse_of
parent_of / father_of / mother_of
child_of
settlor_of
trustee_of
beneficiary_of
```

Questions:

- Which relationship types are actually required?
- Should inverse relationships be stored explicitly or derived deterministically?
- Are relationship directions canonical?
- Do we model family relationships separately from trust roles?

### Provenance

Every extracted relationship should ideally retain:

- source document;
- page / section / note reference where available;
- supporting source text;
- extraction status.

Questions:

- What is the minimum provenance required for Iteration 1?
- Do we store exact quoted evidence or a source span/reference?
- Can one relationship have evidence from multiple documents?

### Uncertainty / status

Candidate statuses:

```text
confirmed
reported
inferred
conflicting
ambiguous
```

Questions:

- Do we need all of these in Iteration 1?
- Should “inferred” relationships be allowed at all?
- What should happen when the source says something like “Sophie may be added as a beneficiary”?

### Agreed contract

> TODO — write the smallest JSON shape together after answering the above.

## 5. Architecture / chain design

Current starting hypothesis:

```text
document
  ↓
extract candidate entities + relationships
  ↓
structured JSON
  ↓
deterministic validation / normalisation
  ↓
merge into graph
  ↓
render
```

Questions to decide:

- One extraction stage or multiple prompt-chained stages?
- Extract entities and relationships together or separately?
- What should be deterministic rather than LLM-driven?
- What failures should trigger retry?
- Do we need routing for different document types in Iteration 1?
- Do we need a verification/reflection step, or should that wait until evaluation gives us a reason?
- What exactly is the merge layer responsible for?

### Guiding principle

Do not add an agentic pattern merely because it exists in the course.

Add another stage only if it creates a clear contract, isolates a real failure mode, or improves evaluation.

### Agreed architecture

> TODO — draw / describe together.

## 6. Validation rules

Receipts had arithmetic invariants; relationship extraction will need different deterministic checks.

Questions:

- Which fields are always required?
- Can an edge exist without provenance?
- Can the source and target be the same entity?
- Which relationship/entity type combinations are valid?
- Should unknown relationship types fail validation?
- How are duplicate edges handled?
- How do we distinguish malformed output from uncertain-but-valid output?

### Agreed validation rules

> TODO.

## 7. Graph merge semantics

This is deliberately separate from extraction.

Questions:

- What defines “the same” entity in Iteration 1?
- Do we avoid alias resolution in the first case?
- What counts as a duplicate relationship?
- How do multiple evidence records attach to one edge?
- How do we represent contradictory relationships?
- Which operations are deterministic?

### Agreed merge policy

> TODO.

## 8. Evaluation metrics

Candidate core metrics:

```text
relationship precision
relationship recall
unsupported relationship rate
provenance accuracy
```

Questions:

- What constitutes an exact relationship match?
- Does entity ID need to match, or only canonical names/types?
- How is provenance scored?
- How do we score a correct abstention?
- How do conflicts affect precision/recall?
- Which metric matters most for the demo?

### Agreed evaluator contract

> TODO.

## 9. Visualisation

Iteration 1 only needs enough visualisation to inspect the reconstructed result.

Questions:

- What graph library should we use?
- Static image, HTML, or small interactive view?
- How should people, trusts, and organisations look different?
- Should provenance be visible on click/hover, or is a side table enough?
- What is the minimum demo-worthy output?

### Agreed visualisation

> TODO.

## 10. Collaboration and ownership

The goal is to parallelise around stable interfaces rather than split the project into unrelated halves.

### Shared decisions

We should decide together:

- Iteration 1 hypothesis;
- synthetic case definitions;
- semantic data model;
- evaluation meaning;
- definition of done.

### Possible work split

**Extraction / pipeline track**

Possible ownership:

- prompt / chain;
- structured extraction;
- deterministic validation;
- graph merge integration.

Owner: TODO

**Synthetic data / evaluation track**

Possible ownership:

- ground-truth fixtures;
- synthetic source documents;
- precision/recall evaluator;
- challenge cases;
- basic graph visualisation if useful.

Owner: TODO

### Integration boundary

Ideal Weekend-1 interface:

```text
source documents
    ↓
extraction pipeline
    ↓
extracted_graph.json
    ↓
evaluation harness + renderer
```

Each side should be able to work against a hand-written fixture before the other side is implemented.

### Git workflow

Proposal:

```text
main
 ├── feature/extraction-pipeline
 └── feature/evaluation-harness
```

Questions:

- PR review expectations?
- Who owns shared fixtures?
- How small should PRs be?
- How do we prevent both people editing the same core files?

> TODO — agree before Build Weekend 1.

## 11. Build Weekend 1

**Goal:** one ugly but complete evaluated vertical slice.

Proposed target:

- one small ground-truth family/trust graph;
- 2–3 source documents;
- working extraction;
- structured relationship output;
- basic validation;
- deterministic merge;
- evaluator;
- basic graph rendering;
- one end-to-end command.

### Tasks

> TODO — split together.

### Weekend-1 exit criterion

A successful first weekend should be able to answer:

> Can the extractor reconstruct the agreed relationships from unseen-to-the-extractor synthetic documents, preserve usable provenance, and produce measurable precision/recall?

Not:

> Is this already a useful production system?

## 12. Build Weekend 2

**Goal:** use Weekend-1 failures to earn exactly one or two additional capabilities.

Possible additions — only if justified:

- alias/entity resolution;
- contradiction handling;
- stronger provenance validation;
- selective retry / verification;
- document-type routing;
- better graph visualisation;
- more adversarial evaluation cases.

### Tasks

> TODO only after Weekend-1 results exist.

## 13. Definition of done

Candidate hackathon submission bar:

- [ ] complete end-to-end pipeline runs from synthetic documents to graph;
- [ ] structured relationships include provenance;
- [ ] hidden ground truth exists independently of extractor output;
- [ ] evaluator reports precision/recall and unsupported edges;
- [ ] at least several deliberately different synthetic cases exist;
- [ ] graph can be visually inspected;
- [ ] one or more observed failure modes and improvements are documented;
- [ ] architecture remains understandable enough to explain in a short demo;
- [ ] no real/private client data is required.

### Team definition

> TODO — agree what can be dropped if time runs short.

## 14. Deferred technical ideas / parking lot

Not for Iteration 1 unless the evaluation exposes a concrete need:

- sophisticated entity resolution;
- human review workflow;
- confidence calibration;
- document-type routing;
- persistent graph storage;
- richer retrieval;
- more complex agent orchestration;
- production security / permissions;
- polished UI.

Add technical ideas here rather than silently expanding the hackathon scope.

## 15. Open decisions

Use this as the live checklist before coding:

- [ ] exact Iteration-1 hypothesis;
- [ ] relationship extraction vs entity-resolution boundary;
- [ ] first synthetic ground-truth case;
- [ ] development/challenge case set;
- [ ] minimum entity types;
- [ ] minimum relationship types;
- [ ] provenance schema;
- [ ] uncertainty/status vocabulary;
- [ ] extraction contract;
- [ ] validation rules;
- [ ] merge semantics;
- [ ] evaluator matching rules;
- [ ] graph visualisation choice;
- [ ] teammate work split;
- [ ] Weekend-1 time budget;
- [ ] hackathon definition of done.

---

## Working principle

**Build the smallest system that can prove or disprove the Iteration-1 hypothesis.**

If something does not help answer that question yet, defer it.
