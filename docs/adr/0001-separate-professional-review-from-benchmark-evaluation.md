# Separate professional review from benchmark evaluation

The first Case 01 web slice ends at deterministic canonical graph construction and read-only professional evidence review. Although benchmark evaluation remains an important existing capability, the web application neither invokes nor exposes it; a benchmark dashboard is deferred to a separate future slice so that evaluation concepts do not become part of the professional-facing contract or workflow.

## Consequences

The web analysis response contains execution metadata and a `CanonicalGraph`, but no `ExtractionResult` or `EvaluationResult`. Raw live extractions remain persisted as run artifacts and can be evaluated later through the existing offline workflow.
