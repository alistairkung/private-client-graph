# Held-out annotation audit

This report records isolated annotation QA on 14 November 2026, based on
`7b3d55d39be2a435c76b3b3a25cd07af57e9e36d` (committed 11 November 2026,
19:24:12 +08:00). It intentionally contains only fixture identifiers, process,
digests and aggregate validation outcomes. Fixture-local READMEs contain the
semantic decisions. No model evaluation was performed or reported.

## Access and isolation

All six fixtures below had authored ideal contract-check dates of 11 November
2026 before this task. Authorship and those checks involved prior annotation
access. Earlier claims that the fixtures were frozen and never inspected during
development were not supported by an access log. This audit cannot reconstruct
all historical access or certify a pristine blind final-test set.

The task handoff also records an earlier independent audit that inspected all six
held fixtures. It found three incomplete answer keys and one unsupported gold
surname; all checked quotes occurred verbatim. Only aggregate findings were
shared outside that audit. No tuning or model runs were performed. Its exact date
and complete access log were not available in this correction task. This known
prior audit is distinct from original authorship and the current isolated repair;
the set must not be described as uninspected before the current work.

For this task, one isolated annotation owner inspected all six held packages and
the shared authoring/contracts documentation. The owner did not inspect the
benchmark development fixtures or tune extraction, resolution, construction,
evaluation, prompts or metrics. The repository-wide owner received aggregate semantic QA outcomes. A final
whitespace check also displayed a short held-out alias diff excerpt to that
owner. It did not trigger any annotation or pipeline change. No paid provider
calls were made.

## Fixtures and present QA

| Fixture identifier | Current annotation QA | Source text |
| --- | --- | --- |
| `benchmark_v1_aliases_held_out_1` | Deliberate truth/ideal repair; bidirectional semantic and deterministic checks passed | Original bytes preserved |
| `benchmark_v1_authority_held_out_1` | Deliberate truth/ideal repair; bidirectional semantic and deterministic checks passed | Original bytes preserved |
| `benchmark_v1_cross_source_held_out_1` | Deliberate truth/ideal repair; bidirectional semantic and deterministic checks passed | Original bytes preserved |
| `benchmark_v1_distractors_held_out_1` | Existing truth retained; bidirectional semantic and deterministic checks passed | Original bytes preserved |
| `benchmark_v1_hallucination_held_out_1` | Deliberate truth/ideal repair; bidirectional semantic and deterministic checks passed | Original bytes preserved |
| `benchmark_v1_temporal_held_out_1` | Existing truth retained; bidirectional semantic and deterministic checks passed | Original bytes preserved |

Every package now records ordered original Sources, a source-attributed authored
ideal and complete approved Source/quote pairs. Multi-document package files
reproduce the original combined text exactly with the documented original-CRLF
newline join; single-document manifests point directly to `source.txt`. Source identities were
retained from the pre-existing approval sidecars. Display names/descriptions were
preserved; explicit case, axis, split and conservative family metadata were added.

After truth stabilization, authored ideals and committed legacy contract results
were brought into agreement. Mechanical checks passed for schemas, unique
identities, references, ontology types, exact approved evidence, complete ideal
coverage, canonical-state construction, legacy quote evaluation and Source
attribution. These are fixture checks, not empirical model scores or proof of
semantic completeness. The owner separately re-read the sources in both audit
directions and inspected the complete held-package diff. Human review remains
necessary for the answer keys and evidence-sufficiency judgments.

## SHA-256 evidence

“Before” is the base revision above; “after” is the package submitted with this
audit. Unchanged rows deliberately show identical digests so absence of source
rewriting is verifiable. Only the four changed truth files have different truth
digests. All digests are over exact file bytes.

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `benchmark_v1/aliases/held_out/case_1/ground_truth.json` | `193f7ea254c99989fd1b63e35ad3ba02131947a013c12ef1428750eaa0bbccda` | `bb510bae10816ee4e802b927b1a478d04cd64af8a89ad0cef843d6e12b1a2da8` |
| `benchmark_v1/aliases/held_out/case_1/source.txt` | `00f40f750971f9057ccc778c82e4e81e7ea18ded1f0f2f41f9a3d2d6118e4838` | `00f40f750971f9057ccc778c82e4e81e7ea18ded1f0f2f41f9a3d2d6118e4838` |
| `benchmark_v1/authority/held_out/case_1/ground_truth.json` | `6270c6b8c601f09971e6c8ccbb2a21b2713d452f7a4c88b7b3edd375e0761796` | `572a82a461e2b7508f55e4033eaf9f8fab0c24a0b02ad215a37cdcd52aeec3cb` |
| `benchmark_v1/authority/held_out/case_1/source.txt` | `d5c2c417fc90610741292b6f1c244b5ccf54c03a0e3c9d301681ebebf756e26f` | `d5c2c417fc90610741292b6f1c244b5ccf54c03a0e3c9d301681ebebf756e26f` |
| `benchmark_v1/cross_source/held_out/case_1/ground_truth.json` | `bb0b1ccc406c056b0bd07716ce2b2086d5432b3aeee17ecd0b8561be82a7d9a0` | `8acb18fbde37f925b1dec2d0b3e2bb520a9e730e80d1526ea99a179d61ad5198` |
| `benchmark_v1/cross_source/held_out/case_1/source.txt` | `6bb0884f06d11eebb2ae177575c673446ebb352b27054a6c11e1159d90abf997` | `6bb0884f06d11eebb2ae177575c673446ebb352b27054a6c11e1159d90abf997` |
| `benchmark_v1/distractors/held_out/case_1/ground_truth.json` | `56a23f4a07702a90da628730a1327ddba09c7aec3edf3fcd3b0b301b60a20962` | `56a23f4a07702a90da628730a1327ddba09c7aec3edf3fcd3b0b301b60a20962` |
| `benchmark_v1/distractors/held_out/case_1/source.txt` | `9fd03d4ca127e04e7b6755eaefeb9f8753122c7ab2a5148ce8f43db3732e276e` | `9fd03d4ca127e04e7b6755eaefeb9f8753122c7ab2a5148ce8f43db3732e276e` |
| `benchmark_v1/hallucination/held_out/case_1/ground_truth.json` | `316e3d16d1ffb315e88c1e1db8f2770442f6c8e620eb0ec7035029277c54d450` | `7f914d734720ba96942ff76445a79c7de30cd2ddc309dc48f910a1618c228489` |
| `benchmark_v1/hallucination/held_out/case_1/source.txt` | `aa04c939076b523d7482c7af0b33daba9886cae5324571cc45f67963a80e89c3` | `aa04c939076b523d7482c7af0b33daba9886cae5324571cc45f67963a80e89c3` |
| `benchmark_v1/temporal/held_out/case_1/ground_truth.json` | `57fa4ebdf70cf6b08b5fcfe06983f06932b9f6f26053f32b9ad8da9ae3e7237e` | `57fa4ebdf70cf6b08b5fcfe06983f06932b9f6f26053f32b9ad8da9ae3e7237e` |
| `benchmark_v1/temporal/held_out/case_1/source.txt` | `41e3efab6e947ea3e240b0b9f18d87911d34fc520bb2e6b512efe96387702100` | `41e3efab6e947ea3e240b0b9f18d87911d34fc520bb2e6b512efe96387702100` |

## Limits on independence and use

Each `matter_family` is conservatively shared with the corresponding development
fixture: `benchmark_v1_<axis>_1`. The pairs repeat authoring patterns and are
related families, not independent observations merely because wording or labels
differ. The isolated owner did not inspect development content to verify finer
lineage. There is also overlapping fictional-world material between held temporal
and hallucination packages. The per-axis family keys do not establish
independence across axes or remove that limitation.

The six fixtures are a small diagnostic set. Current QA access and earlier
annotation access must accompany any future “held-out” description. Reusing these
fixtures for tuning or repeated interpretation further limits final-test claims.
No provider experiment, benchmark-driven rebuild or next evaluation iteration is
authorized or implied by this repair. Full-context source-aware authored ideals
exercise present contracts; they do not demonstrate sequential ingestion,
history selection, automatic authority adjudication or model generalization.
