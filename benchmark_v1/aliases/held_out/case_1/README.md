# Case: Aliases (Held-Out)

Purpose: Resolve full name, first name, title and nickname references within one factual file note.

Supported relationship types: `settlor_of`, `spouse_of`, `parent_of`, `beneficiary_of`.

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

`matter_family` is `benchmark_v1_aliases_1`, deliberately sharing conservative
lineage with the corresponding development fixture. Different names or documents
do not prove independent case families. See the isolation-safe
[held-out audit](../../../held-out-audit.md) for suite limitations.

## Complete answer key and bidirectional audit

The reviewed answer key has five relationships: Katherine Beaumont is settlor;
Katherine and Richard Beaumont are spouses and each is a parent of Emily; Emily
is beneficiary. The source introduces the child only as “Emily” and later “Em”.
The earlier answer key invented the surname “Beaumont” for that child. The repair
uses the most complete supported name, “Emily”, in truth and both authored ideals;
the source itself is unchanged. Katherine's title and first-name references and
the child's nickname have unambiguous local antecedents.

Both audit directions were checked: each answer-key relationship has exact,
sufficient support and no other supported relationship is asserted. Establishing
the trust and the explicit settlor statement support the same role, rather than
separate graph facts.

The answer key was repaired and frozen before deriving the updated authored
ideal. Source text was preserved. Evidence sufficiency was reviewed semantically;
substring checks alone do not establish support. Human review remains the final
boundary for semantic completeness and the intended difficulty.

## Source-aware package and deterministic checks

`sources.json` fixes one Source, `note_01`, pointing directly to `source.txt`.
There is no duplicate copy of the source document.

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
   **Aliases (Held-Out)**, fixture
   `benchmark_v1_aliases_held_out_1_fixture`; held-out inputs are not default selections.
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
cp benchmark_v1/aliases/held_out/case_1/expected_extraction.json /tmp/held-aliases-ideal.json
uv run python benchmark_v1/evaluate_case.py \
  benchmark_v1/aliases/held_out/case_1 /tmp/held-aliases-ideal.json
```

The evaluator writes `/tmp/held-aliases-ideal.evaluation.json`. This legacy command
uses combined `source.txt`; use Workbench replay to inspect explicit Sources.
