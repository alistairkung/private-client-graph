# Shared Analysis Pipeline

Status: agreed implementation handoff. This document authorizes architectural refactoring only; it does not authorize paid provider calls, a new experiment, non-synthetic Matter data, or changes to protected semantic contracts.

## Objective

Matter Intake, the Public Showcase, and the research harness must execute one fixed semantic workflow:

```text
PipelineInput
    → Extract Relationship Candidates
    → Resolve Aliases
    → Build CanonicalGraph
    → PipelineResult
```

The application uses an explicitly approved resolver configuration. Research may vary that same finite configuration and may replay a saved extraction, but it must not maintain a parallel implementation of resolution or graph construction.

The current system duplicates meaningful execution responsibilities:

- Matter Intake and the Public Showcase each compose extraction and `build_graph()` independently.
- Research separately composes provider invocation, deterministic resolver edits, and `build_graph()`.
- Research reconstructs the extraction prompt composition to obtain raw provider observations.

The shared design removes that semantic duplication while preserving consumer-specific operational responsibilities.

## Agreed contracts

The intended contract is conceptually:

```python
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class PipelineInput:
    source_text: str
    document: str


class PipelineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    resolver: Literal["none", "generative"] = "none"


@dataclass(frozen=True)
class PipelineResult:
    extracted: ExtractionResult
    resolved: ExtractionResult
    graph: CanonicalGraph
```

`document` is the Evidence document title passed to the existing graph builder. It must be explicit: Matter Intake uses the practitioner-supplied Source title, while the current showcase and research fixtures use `source.txt`. `PipelineInput` is an execution value, not a persisted aggregate `Source`, and carries no Matter or experiment identity.

`PipelineResult` is request-local. Matter Intake may discard both extraction representations after persisting the proposed graph. Returning them does not add them to Matter Proposal or Matter state. The frozen outer contract contains defensive snapshots; this refactor does not change the protected mutability contracts of the nested Pydantic domain models.

## Executor and replay

Use a small `Pipeline` object with concrete bound dependencies and no mutable workflow state:

```python
pipeline.run(input)
pipeline.run_from_extraction(input, extraction)
```

`run()` performs extraction and delegates to `run_from_extraction()`. The replay entry point bypasses extraction explicitly; `None` must not switch execution modes. Both entry points execute one downstream implementation for resolution and graph construction.

The executor binds narrow callables for extraction and resolution. Graph construction remains the fixed final semantic stage and must delegate to the existing `build_graph()` without changing its validation, canonicalisation, identity, evidence, or ordering behavior. A graph-builder callable may be bound as an implementation dependency so research can wrap and time the call, but it is not a `PipelineConfig` variation and any wrapper must delegate to `build_graph()`.

Inputs must not be mutated. The executor takes defensive copies at the replay boundary, and both supported resolvers return independent resolved values. The no-resolution implementation performs no provider call and returns equivalent copied content.

## Resolver composition

The shared generative resolver owns the complete semantic resolution operation:

1. construct the typed resolution request from the exact Source text and extracted Relationship Candidates;
2. invoke a narrow provider callable;
3. validate the returned `EndpointEdits` contract;
4. apply the edits deterministically to a copy; and
5. return the resolved `ExtractionResult`.

The shared resolution module owns the resolution prompt, typed edit/request contracts, canonical request content, and deterministic edit validation and application. It preserves candidate order and count, relationship types and directions, and supporting quotations. It must not silently retry, repair, drop candidates, or fall back to no resolution.

The provider callable returns the typed edit output expected by the shared resolver. A research adapter may wrap the underlying provider invocation, retain a safe raw response and usage, measure latency, record failures, and then return the parsed typed edits. Parse or provider failures are recorded before being re-raised. These wrappers observe execution; they do not construct a different prompt or apply edits themselves.

Extraction follows the same separation. The existing extraction prompt and structured `ExtractionResult` operation remain shared semantic code. Research observation may wrap its provider boundary, but research must not recompose a parallel extraction prompt merely to capture raw output.

## Failure contract

A failed stage raises a narrow `PipelineExecutionError`. It identifies the semantic stage, exposes defensive snapshots of domain outputs completed before the failure, and preserves the original exception through chaining.

| Failed stage | `extracted` | `resolved` |
| --- | --- | --- |
| extraction | absent | absent |
| resolution | present | absent |
| graph | present | present |

The error contains no HTTP status, retryability decision, run identifier, provider response, token usage, latency, persistence outcome, research status, or evaluation value. Consumers inspect the stage and chained cause and translate them into their existing error contracts.

The Public Showcase must preserve its current ordering: a successful live extraction is retained outside the pipeline before graph construction can fail. Its extraction adapter may persist the extraction before returning it to the executor; a graph-stage `PipelineExecutionError` also makes the completed extraction available to the application. No persistence behavior belongs in the shared pipeline.

## Composition roots

Define one explicit approved application constant:

```python
APPROVED_APPLICATION_PIPELINE_CONFIG = PipelineConfig(resolver="none")
```

It is selected in backend composition code, not from a practitioner request, browser control, or environment-provided strategy name. Matter Intake and the Public Showcase use this configuration while retaining separate authentication, quota, acquisition, error, artifact, and persistence behavior.

Research may construct `none` and `generative` pipelines. Frozen inputs call `run_from_extraction()` repeatedly with the identical saved extraction. Fresh inputs call `run()`. Experiment plans, repetitions, authorization gates, paid-call ledgers, raw observations, costs, diagnostics, ground truth, evaluation, artifacts, summaries, and reports remain in `private_client_graph/research/`.

Promoting `generative` into the approved application configuration requires a separate explicit product and engineering decision. Experimental availability never promotes it automatically.

## Responsibility boundary

The Shared Analysis Pipeline contains only:

- its explicit input, configuration, successful result, and stage-failure contracts;
- fixed Extract → Resolve → Construct Graph sequencing;
- selection between the known no-resolution and generative resolver capabilities; and
- the shared semantic extraction and resolution operations.

It does not contain:

- Matter IDs, Matter Proposal lifecycle, HTTP behavior, authentication, database transactions, or persistence;
- PDF acquisition, duplicate-reference checks, application quotas, retryability policy, or provider credential policy;
- research IDs, repetitions, scheduling, call budgets, authorization records, raw artifacts, pricing, or reports;
- ground truth, identity diagnostics, F1, provenance scoring, or Benchmark Evaluation; or
- a stage registry, plugin system, YAML graph, arbitrary ordering, planner, LangGraph workflow, or generic agent framework.

The repository remains synthetic-only. This architecture is production-shaped but does not satisfy the prerequisites for processing real client information.

## Implementation sequence

1. Add the pipeline contracts, explicit stage error, no-resolution resolver, and executor with focused deterministic tests.
2. Move the resolution request/edit semantics into shared code and adapt the research provider boundary to return typed edits while retaining observations externally.
3. Adapt research baseline, generative, frozen-replay, and fresh-extraction paths to the shared executor; keep evaluation and artifacts downstream.
4. Adapt Matter Intake to the approved configuration without changing acquisition, reference, allowance, error, or persistence ordering.
5. Adapt Public Showcase live and sample paths, preserving successful-extraction retention before graph failure.
6. Remove superseded semantic orchestration only after parity tests cover all three consumers.

## Required tests

Focused tests must prove:

- `run()` delegates to the same downstream implementation as `run_from_extraction()`;
- replay bypasses extraction and does not mutate the supplied extraction;
- no resolution performs no provider call and returns equivalent independent content;
- generative resolution constructs the shared request once, applies only valid typed edits, and has no fallback;
- both configurations call the existing graph builder with the exact document title and Source text;
- successful results contain defensive extracted, resolved, and graph snapshots;
- each failed stage exposes exactly the completed intermediate outputs and chains its cause;
- research records raw response, usage, latency, and failures without applying edits outside the shared resolver;
- repeated research resolver calls use identical saved inputs and retain existing resume and paid-call accounting behavior;
- Matter Intake preserves duplicate-reference, model-construction, allowance-consumption, provider-error, graph-error, and persistence ordering;
- the Public Showcase retains a successful live extraction when graph construction fails; and
- existing graph, evaluation, provenance, application, and research contracts remain unchanged.

Run focused suites during the refactor and finish with `uv run pytest` plus the mandatory final-diff review from `docs/CODE_STYLE.md`.

## Explicit non-goals

This handoff does not authorize provider calls, a follow-on experiment, automatic strategy promotion, new relationship or identity semantics, multi-source extraction, practitioner resolution controls, non-synthetic Matter data, changes to graph canonicalisation, changes to evaluation or provenance rules, or a generalized orchestration framework.
