# Share one fixed configurable analysis pipeline

Matter Intake, the Public Showcase, and research use one Shared Analysis Pipeline with a fixed Extract → Resolve → Construct Graph topology, while a small typed configuration selects only explicitly supported resolver capabilities. The application uses an explicitly approved no-resolution configuration until a separate product and engineering decision promotes another strategy; research may select experimental configurations and replay saved extractions through the same resolution and graph-construction implementation.

## Consequences

The pipeline returns request-local extracted, resolved, and canonical graph values and reports stage failures with completed domain outputs. Provider observation, quotas and call budgets, application error policy, persistence, Matter Proposal lifecycle, experiment scheduling, ground truth, evaluation, and reporting remain owned by their consumers. This decision deliberately moves beyond the completed entity-resolution experiment's temporary restriction that production paths and production configuration remain unchanged; it does not enable non-synthetic Matter data or change protected extraction, graph, evaluation, or provenance semantics.
