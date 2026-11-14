# Case: Temporal Precedence (Held-Out)

Purpose: Recover the latest explicitly effective trusteeship while retaining unchanged family and trust facts from an earlier note.

Supported relationship types: `settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`, `trustee_of`.

## Status and access history

This is the `held_out` counterpart of its axis's development fixture. It was
committed with authored ideal checks dated 11 November 2026. Those checks and
case authoring already involved fixture access; the old “not inspected during
development” wording did not establish an access-controlled blind holdout.
An earlier independent audit also inspected all six held fixtures and shared only
aggregate findings, with no tuning or model runs; its exact date was not supplied
in this task's handoff. See the held-out audit for the known access sequence.
The current isolated annotation QA was performed on 14 November 2026 from
`7b3d55d39be2a435c76b3b3a25cd07af57e9e36d`. Its annotation owner inspected
only the six held packages, not development fixtures, and made no pipeline
changes. This access is benchmark QA, not evidence of untouched final-test data.

`matter_family` is `benchmark_v1_temporal_1`, deliberately sharing conservative
lineage with the corresponding development fixture. Different names or documents
do not prove independent case families. See the isolation-safe
[held-out audit](../../../held-out-audit.md) for suite limitations.

## Complete answer key and bidirectional audit

The reviewed final-current answer key remains six relationships: Julia Marlow
is settlor; Julia and Peter Marlow are spouses and each is a parent of Anna
Marlow; Anna is beneficiary of Marlow Family Trust; Fiona Grant is its current
trustee as at 20 March 2026. No truth or source repair was needed.

Both audit directions were checked. The second note records a completed,
effective resignation and replacement, so Andrew Bell's historical trustee role
is excluded from the final-current graph. Its statement that all other earlier
facts remain unchanged preserves the five unchanged relationships. Both approved
replacement-trustee quotes belong to the second note. The final ideal is not a
union of every historically asserted role or a sequential-state execution test.

The existing answer key was re-audited and retained before deriving the
source-attributed authored ideal. Source text was preserved. Evidence sufficiency was reviewed semantically;
substring checks alone do not establish support. Human review remains the final
boundary for semantic completeness and the intended difficulty.

## Source-aware package and deterministic checks

`sources.json` fixes `note_01` then `note_02`, using the original document
boundaries in `source.txt`. The separate files retain the original bytes; joining
them with one original CRLF newline reproduces `source.txt` exactly. This
full-context package presents both Sources together; it does not require sequential
processing.

`ground_truth.json` retains plain-string approved quotes. `source_evidence.json`
records exact Source/quote approvals without changing legacy scoring.
`expected_extraction.json` is the authored legacy ideal;
`expected_source_extraction.json` is the same final-current claims and selected
quotes with explicit Source identities. Neither is measured model output.

Current deterministic QA passed schema, identity/reference, complete-ideal,
exact-evidence, ordered-source reconstruction, canonical-state, legacy evaluation
and Source-attribution checks. `expected_extraction.evaluation.json` was
recomputed from the current authored ideal. The earlier 11 November contract
check is historical annotation validation, not model performance. No live
extraction or empirical capability claim is made. Paid provider calls: zero.

## Reproduce in the Workbench without provider calls

1. From the repository root, start `docker compose up --build -d` and open
   [the local Workbench](http://127.0.0.1:8080).
2. Create a named Experiment. In the next Run inputs, deliberately select only
   **Temporal Precedence (Held-Out)**, fixture
   `benchmark_v1_temporal_held_out_1_fixture`; held-out inputs are not default selections.
3. Choose the authored **saved extraction** input and **replay** execution mode,
   with **No resolution** (`resolver=none`) and one repetition. Do not select a
   recorded-provider demonstration or fresh extraction.
4. Preview the plan and verify that both extraction and resolution provider-call
   maxima are zero. Review/freeze the plan, then run the replay.
5. Inspect the resulting relationships and exact Evidence with its Source in
   the immutable Run. This validates the fixture and deterministic downstream
   path; it does not evaluate a model's ability to reconstruct the answer key.

For the legacy quote-only check, copy `expected_extraction.json` to a new local
run path, then run the following from the repository root (the output path must
not already exist):

```bash
cp benchmark_v1/temporal/held_out/case_1/expected_extraction.json /tmp/held-temporal-ideal.json
uv run python benchmark_v1/evaluate_case.py \
  benchmark_v1/temporal/held_out/case_1 /tmp/held-temporal-ideal.json
```

The evaluator writes `/tmp/held-temporal-ideal.evaluation.json`. This legacy command
uses combined `source.txt`; use Workbench replay to inspect explicit Sources.
