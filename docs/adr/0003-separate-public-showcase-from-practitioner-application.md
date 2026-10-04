# Separate the public showcase from the practitioner application

Private Client Graph retains the fixed Case 01 live/sample demonstration as a public showcase at `/`, while the practitioner application begins at `/app` and reads persisted Matter state. Their HTTP contracts and application orchestration remain separate—showcase endpoints live under `/api/showcase`, practitioner endpoints under `/api/matters`—and the two journeys share only the appropriate lower-level extraction and graph capabilities.

## Consequences

Case 01 terminology and transient analysis controls remain valid in the explicitly synthetic showcase but do not enter practitioner routes or Matter contracts. The practitioner journey opens a current graph directly and never calls through the showcase, while the showcase never reads or mutates persisted Matter state.
