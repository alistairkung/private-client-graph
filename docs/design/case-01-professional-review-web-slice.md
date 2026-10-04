# Case 01 professional-review web slice

> **Status:** Implemented and deployed. This document records the original
> showcase slice. The subsequent practitioner-application design preserves this
> experience as a public showcase while adding a separate persisted Matter
> journey; see
> [Practitioner Matter workspace slice](practitioner-matter-workspace-slice.md).

## Goal

Build the smallest complete professional-review experience that can form the first hackathon submission while preserving the existing extraction and graph semantics.

The product concept is a tool for a private-client professional to review AI-extracted relationship information and the exact source evidence supporting it. It is not a general case-summary tool, a client self-service application, or a benchmark dashboard.

## Scope

The first web slice covers:

```text
authoritative synthetic Case 01 source
    -> live or sample relationship extraction
    -> existing deterministic graph construction
    -> read-only relationship and evidence review
```

The slice uses only the preloaded synthetic Case 01 document. The backend owns the complete fixture and the browser cannot submit or alter source text. This is a benchmark-specific constraint, not a future product requirement that documents must always be backend-owned.

Arbitrary uploads, real client material, human correction, authentication, a database, analysis history, asynchronous jobs, and generalized case selection are excluded.

## Professional workflow

The application is a single progressive workspace. Before analysis, the source document is the primary content. After analysis, the workspace presents:

- a slightly larger relationship-graph surface;
- a substantial, persistent source-document surface;
- relationship selection that emphasizes the edge and scrolls to and highlights its exact evidence.

The graph is read-only and automatically laid out. Relationships, rather than nodes, drive evidence review. Directed relationships retain direction; symmetric relationships appear once. Product labels may be human-readable, but they must preserve the canonical relationship semantics and must not invent inverse edges.

When a relationship has multiple evidence items, selecting the relationship activates the first item and exposes the complete evidence list. Selecting another item moves the single active source highlight. The backend remains authoritative for the invariant that canonical evidence occurs verbatim in the source. The frontend locates the already-validated evidence through exact substring matching; inability to locate it is an unexpected client/data-contract error.

## Live and sample analysis

Live analysis is the primary action and invokes the real model extraction boundary. Sample analysis is a separately labelled, deliberate action. There is no silent fallback between them.

The sample path consumes `cases/case_01/expected_extraction.json` because its established meaning—one ideal raw extraction—also satisfies the deterministic sample boundary. The fixture remains a benchmark fixture and must not be reshaped for frontend needs. The action should be labelled **Load sample analysis**, not as replay of a prior live run.

Both paths converge immediately after extraction and use the current deterministic graph builder. Requests are synchronous. There are no automatic retries; after a retryable live error, the user may explicitly retry live analysis or load the sample analysis.

## Web application boundary

The implementation direction is a thin FastAPI backend and a React/TypeScript frontend in the existing repository:

```text
React professional-review workspace
    -> FastAPI application orchestration
    -> existing extraction and graph-construction boundaries
```

The backend is authoritative for the Case 01 source and sample fixture selection. A case-detail response supplies read-only display data. An analysis request supplies only the explicit execution mode. Ground truth remains part of the offline benchmark workflow and is not loaded for the professional web request.

The professional-facing analysis result is:

```text
CaseAnalysis
- execution metadata
- CanonicalGraph
```

Execution metadata distinguishes live from sample analysis. Successful live extraction returns a run identifier for technical traceability. `ExtractionResult` remains an internal pipeline artifact and is not returned to the browser. An explicit, stage-aware API error contract represents failures; `CaseAnalysis` is never partially populated and has no success flag.

## Run artifacts

Persist a successful live `ExtractionResult` under the existing `runs/case_01/` convention before deterministic graph construction. This preserves diagnostically useful model output if graph construction rejects it. These files are technical artifacts, not product state, and no run-history interface is included.

Sample analysis reads the committed ideal-extraction fixture and creates no duplicate run artifact. Live artifacts remain compatible with the existing offline evaluation command.

## Evaluation boundary

This decision supersedes the earlier proposal for a composite web response containing `ExtractionResult`, `CanonicalGraph`, and `EvaluationResult`, and it supersedes any first-slice UI plan containing evaluation summaries or diagnostics.

The first web slice does not invoke or expose evaluation. Precision, recall, F1, TP/FP/FN, provenance accuracy, evaluation diagnostics, and raw evaluation output do not appear in the application. The existing evaluator and evaluation CLI remain unchanged for offline benchmark and development work.

A benchmark/evaluation web surface is explicitly deferred to a separate future slice. It should not be anticipated in the professional workspace or its current API contracts.

## Failures and recovery

Live provider failures use the explicit API error contract and may be marked retryable. Deterministic graph-construction failures are non-transient pipeline failures and should not invite blind retries. A graph-construction error occurring after a live extraction should include enough technical traceability to locate the persisted run artifact.

The application never switches from live to sample analysis automatically.

## Testing boundary

Deterministic tests should cover web contracts and graph-to-UI/evidence-location transformations. The critical browser test uses the sample extraction boundary while keeping the frontend, API orchestration, real graph construction, relationship selection, and source highlighting in the path. Live model quality remains outside deterministic CI.

## Deployment

Deployment is **deferred and intended**.

The acceptance criterion for this slice is a reliably runnable local end-to-end application whose architecture remains deployable. Cloud infrastructure, authentication, public rate limiting, production secret management, CORS/origin policy, access and cost controls, and a public URL are not part of this slice.

After the professional-review slice is complete and tested, those concerns should be handled together as a coherent deployment slice. The model API key must remain backend-only throughout.
