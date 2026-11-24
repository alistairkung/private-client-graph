# Proof-completeness prompt comparison v1

**Pre-registered on 24 November 2026. Execution has not started.** The [machine-readable design](PROOF-COMPLETENESS-v1.json) freezes the exact string insertion, baseline and treatment prompt hashes, model settings and complete pair order. [Evaluation Protocol v1](../../EVALUATION-PROTOCOL-v1.md) governs results.

## Question and arms

**Hypothesis.** Explicitly asking for a complete proof in the existing flat candidate schema raises complete joint-only evidence across all planned targets. The first live baseline omitted at least one required Source from every approved alternative on all 25 recovered joint-only failures. In-memory controls established that the existing schema, constructor and scorer accept the complete required pairs.

- **Control.** The original full-context sourced extraction prompt, identified by its baseline digest. Rerun it in the same experiment as the treatment. The historical first live baseline is the reference and does not supply any of the 34 concurrent control observations.
- **Treatment.** Insert the exact committed joint-evidence instruction immediately before the existing Source and current-state rules heading. The wire schema is identical. The instruction requires separate rows carrying the same edge for necessary verbatim fragments and leaves Source identifiers and correct graph membership to the extractor.
- **Frozen in both arms.** All 34 exact admitted Source arrays, order within each condition, model and requested settings, code except the declared prompt selection, no resolver, structured-output schema, parser, construction, validation, protected scorers and attribution policy. Neither arm sees case identity labels, hints, keys, recommended Sources or the other prediction.

## Execution and accounting

One call per arm per condition, 34 pairs, **68 proposed paid attempts**, no retries. The seed ranks conditions by the ascending SHA-256 of the seed joined with colon and condition ID. Within each pair, alternate control-first and treatment-first in that order. Record chronological attempt/cost accounting and retain unavailable outcomes under v1. Do not substitute conditions or reuse earlier model responses. Reserve every attempt before dispatch.

Before dispatch, verify both effective prompt hashes and exact request schema locally, re-verify the admitted roster, confirm the effective served model or record the strength of its identity evidence, and obtain an explicit owner release for 68 attempts. Use one verified provider deployment and settings across arms. Pause for detectable model or configuration drift or compromised artifacts. A returned alias alone does not establish an immutable backend version. If pinning is unavailable, owner review of that limitation is an explicit condition of release. If provider state remains unknown after execution, qualify the comparison for that uncertainty.

## Endpoints and decision rule

Primary outcome is complete joint-only proofs divided by all planned joint-only targets in each arm, 30 per arm. Report treatment minus control in counts and percentage points. Secondary outcomes are overall proof completeness, per-target approved-Source coverage, approved quotation and attribution, all-condition micro and family-macro F1, exact-graph accuracy, construction success, failure breakdown, token cost and latency. Report paired target transitions and all mismatches within each family. Alternate approved proof routes count only under the frozen exact-pair policy. For the Source-coverage diagnostic, require that all Source IDs of any one approved alternative appear on the same correct edge. It is a diagnostic rather than an alternative score.

The full-suite progression screen requires **at least three additional completed joint-only proof targets**, with improvement in **at least three distinct families**, no net loss of construction successes, and no decline in all-condition micro-F1 greater than 0.02. A family improves when it has more complete joint-only targets in treatment than control. Report every newly invalid graph, newly unsupported edge and lost proof even when aggregate guardrails pass. Meeting the screen warrants human review and a separately approved decision on follow-up. One prediction per condition per arm does not establish stability. Treat repeated conditions within a family as dependent and report family-block effects. Any interval analysis is exploratory and must resample whole family blocks including both arms and all their conditions.

The baseline usage and tariff imply roughly US$0.055 for 68 calls at the same workload, before extra output from the treatment or pricing changes. Cost and effectiveness are unknown until measured. This pre-registration grants no paid authority and changes no extraction prompt or production path.
