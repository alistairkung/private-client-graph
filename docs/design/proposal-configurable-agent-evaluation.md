# Proposal: Configurable Agent Evaluation Architecture

Status: proposal for design review. Implementation is not authorised by this document.

## Motivation

The 20 visible development cases deliberately increase benchmark difficulty. Cases 01 and 02 show that difficulty does not automatically justify more agentic complexity; Case 03 may be the first point where another semantic capability is earned. Later cases may pressure reconciliation, temporal/conflict reasoning, retrieval and conditional orchestration.

Working principle:

```text
Pareto until failure
→ diagnose
→ minimal fix when obvious
→ compare competing strategies when several are credible
→ measure quality, cost, latency and reliability
→ retain the simplest strategy justified by evidence
```

Coding agents make competing implementations cheaper. Configuration should support empirical comparison without turning PCG into a generic agent framework.

## Configuration boundary

Prefer a small typed `AgentConfiguration` containing only variation points that benchmark evidence has earned, potentially:

- extraction strategy;
- entity-resolution strategy;
- context-selection strategy;
- later capabilities only when earned.

Configuration selects known, tested strategies. Do not create an arbitrary executable node/edge graph.

Keep orchestration stable while collaborators vary. Candidate Python styles to compare:

- callable/function composition;
- `Protocol` + Strategy implementations;
- LCEL-native composition.

A no-op/Null Object resolver may let baseline and experimental configurations share orchestration/instrumentation, but compare it with simpler Python composition rather than assuming it.

## EvaluationRun observability

Observed stochastic behaviour is useful before the unseen test set exists:

```text
Git                → what code existed?
Benchmark fixtures → what was expected?
EvaluationRun       → what did the stochastic system actually do?
```

Raw `/runs/` may remain Git-ignored, but retain structured telemetry before architectural experiments accelerate.

Capture at least:

- run ID, timestamp and git SHA;
- case/benchmark version and dev/test classification;
- complete AgentConfiguration;
- provider/model parameters;
- optional hypothesis/notes;
- TP, FP, FN, precision, recall, F1 and provenance accuracy;
- raw structured prediction.

For each stochastic stage capture where available:

- stage name;
- provider/model;
- input/output/cached tokens;
- latency;
- retries/errors;
- structured input/output.

Also capture end-to-end latency and deterministic/structured-output failures. Add capability-specific metrics only when the capability exists (e.g. entity merge/split metrics or retrieval recall/rank/context size).

## Cost

Raw usage is the durable measurement. Also record calculated cost plus enough model/pricing metadata to understand the historical calculation. Do not store only dollars because pricing changes.

When later strategies add retrieval/resolution/verification, measure the complete strategy cost.

## Storage question

Do not assume Git should store every run. A plausible separation is:

- local `/runs/`: ephemeral/debug output;
- retained EvaluationRuns: structured experimental observations;
- Git: code, benchmark definitions, decisions and selected reproducible summaries.

The grill should decide whether retained runs currently belong in PostgreSQL, structured files, or another lightweight store.

## Development vs unseen evaluation

The 20 visible development cases answer:

> What should we build?

The later unseen test set answers:

> Does the selected architecture generalise?

Development telemetry is architectural lineage and debugging evidence, not unseen generalisation performance.

## Future evaluation dashboard

After the hackathon, a dashboard may let users select known AgentConfigurations and compare quality, per-case failures, provenance/capability metrics, tokens, calls, latency and cost.

A key view would be a cost/quality Pareto frontier:

> How much marginal benchmark value does each increase in agentic complexity buy?

This UI is future scope; telemetry/configuration design should not depend on it.

## Retrieval as a future strategy

Long-context cases may eventually justify:

```text
full Source
→ lexical windows
→ BM25/full-text
→ vector retrieval
→ hybrid/reranking
→ iterative agent-controlled retrieval
```

Do not introduce retrieval merely because it is interesting. Retrieval indexes remain derived state; chunks should point to canonical Matter/Source identity and Source offsets where available. Canonical Evidence resolves back to canonical Source content, and Matter isolation applies to retrieval.

## Strategy lifecycle

Experimental configuration is scaffolding, not permanent complexity. When an experiment has a clear winner, record the result and remove losing implementations unless they retain a concrete experimental purpose.

## Immediate boundary

Do not build the dashboard now. The first useful configuration point may be the first genuine architecture comparison, potentially Case 03. Instrumentation should begin before important stochastic observations are lost, but remain proportional to current needs.

## Questions for design review

- Has configurable composition actually been earned?
- Should Case 03 be implemented once before introducing configuration?
- What is the smallest useful AgentConfiguration?
- Which dimensions belong in it now?
- Which Python composition style best fits this repository?
- Does a no-op strategy help or add ceremony?
- Where should common instrumentation wrap stochastic stages?
- What EvaluationRun fields should be retained immediately, and where?
- How should historical model pricing be represented?
- How should runs/configurations remain reproducible across git revisions?
- When should experimental strategies be deleted?
- What belongs in hackathon architecture versus post-hackathon research infrastructure?
