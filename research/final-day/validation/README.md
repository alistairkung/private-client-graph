# Benchmark review request

Status: awaiting human benchmark approval. No held-out evaluation has run.

Start with the [case index](../../../evaluation_cases/README.md), then the
independent validation summaries: [batch 1](batch-01.md) and [batch 2](batch-02.md).
The held-out set has 10 cases, 39 current relationships and 14 Sources. Each
case directory includes its hypothesis, original Sources, complete answer key,
approved exact Source/quote pairs and authored ideal extraction/state.

## Personal review of development Cases 04 and 05

| Case | Source documents | Complete answer key | Expected current state |
| --- | --- | --- | --- |
| [04: multi-source](../../../cases/case_04/README.md) | [First note](../../../cases/case_04/sources/note_01.txt), [follow-up](../../../cases/case_04/sources/note_02.txt) | [Ground truth](../../../cases/case_04/ground_truth.json) | Seven edges. Andrew's beneficiary support can come from either Source; the ideal preserves both. Lucy and Marcus have no asserted family links. |
| [05: trustee replacement](../../../cases/case_05/README.md) | [Initial note](../../../cases/case_05/sources/note_01.txt), [replacement note](../../../cases/case_05/sources/note_02.txt) | [Final truth](../../../cases/case_05/ground_truth.json), [initial control](../../../cases/case_05/ground_truth_after_note_01.json) | Six current edges. Rachel replaces David as trustee, effective 10 September 2026. The other five relationships retain earlier support. |

## Held-out spot checks and approval

Choose any cases from the index for spot checks. Useful contrasting examples are
[explicit alias](../../../evaluation_cases/heldout_03/README.md),
[reverse-supplied chronology](../../../evaluation_cases/heldout_06/README.md), and
[duplicate Source titles](../../../evaluation_cases/heldout_08/README.md).

Confirm that the answer keys are complete, each approved quote supports its
relationship in the identified Source, historical relationships are excluded
appropriately, and the stated difficulty is suitable. Review any validator
uncertainties before approving the held-out benchmark.

The independent validator found no semantic blockers. These are short, explicit
synthetic checks with limited distribution coverage. Exact approved-quote
matching may reject a valid shorter quote, so distinguish that diagnostic from
relationship correctness. Authored ideals are not measured model results.

Approval freezes the reviewed dataset for the final run after the extraction
chain is frozen. It does not authorize tuning against held-out outcomes, changing
truth to improve scores, merging pull requests, or deploying. Requested changes
will be reviewed and revalidated before evaluation.

## PR #80 overlap and benchmark readiness

Compared PR #80 head `394294969b6de3b5be5e892df8034eafcdb1e219` with the
benchmark package in PR #125: all 27 changed paths are present. Twenty-five are
byte-for-byte identical; the Case 04/05 READMEs retain the original contents and
append the agreed final-day scope. No source, truth, extraction, canonical-state,
metadata or test changes from #80 are missing. **PR #125 fully supersedes #80.**
Leave #80 open for the user to close; neither PR is merged automatically.

All 132 artifacts recorded by the independent validation digest files still
match. No fixture corrections were required. Cases 01–03 retain their existing
single-source schemas; the ordered manifests belong to Cases 04/05 and all ten
held-out cases. A source-aware adapter must bind the one known Source explicitly
for legacy inputs rather than require fixture rewrites.

Case 03 intentionally preserves a raw extraction with unresolved aliases. Its
legacy no-resolution control scores TP 6 / FP 1 / FN 1, with approved support
on all six true positives. This documented control is not a benchmark defect or
permission to repair its answer key. Other development ideal controls recover
all of their intended edges under the existing deterministic builder.

Relationship precision/recall/F1 and provenance accuracy remain distinct. The
existing evaluator checks provenance only on true-positive edges and requires
an exact approved quote match. A shorter, semantically sufficient quote can
therefore fail provenance while its relationship remains correct. That is an
annotation-granularity limitation, not evidence of an incorrect semantic edge.
The current scorer does not check originating Source identity. This PR retains
its policy unchanged and supplies Source/quote annotations for a separate
source-attribution diagnostic; it does not implement or redefine scoring.

## Held-out workbench integration handoff

On PR #125's base, repository discovery scans only `cases/`; `ResearchInput`,
`ModelRequest` and runner execution carry one combined source string. Merely
loading `source.txt` cannot establish multi-source attribution or prove temporal
interpretation. The missing dependency is a source-aware adapter in the existing
Research Workbench, reviewed separately from this benchmark PR.

| Need | Reuse and smallest required extension |
| --- | --- |
| Discover and select | Extend `workbench/case_catalog.py::repository_inputs`, `load_case_catalog` and metadata loading to discover `evaluation_cases/heldout_01`–`heldout_10` as explicit `heldout_XX_fixture` input IDs. Preserve `default_input_ids()` as development Cases 01–05 only. Expose the split in frozen case metadata; the existing `cohort` values describe extraction origin, not development versus held-out membership. |
| Configure a final Run | Reuse `GET /api/research/v2/cases`, `RunConfiguration.input_ids`, existing Experiment/Run Draft editing, preview and `freeze_run` in `workbench/run_planning.py`. Select exactly the ten held-out IDs in a separate Run: fresh extraction, one sample, no resolution, one repetition. Do not add a new execution surface. |
| Freeze inputs | Extend `research/inputs.py::ResearchInput` and catalogue loading to retain ordered Source IDs/titles/text from `sources.json`, the attributed ideal extraction and `source_evidence.json` approvals, plus all source/annotation digests. Preserve legacy single-source and historical replay contracts. Keep truth and ideal fixtures out of model requests. |
| Execute the evolved chain | Connect `research/provider.py::ModelRequest`/`invoke_deepseek` and `research/runner.py::_fresh_inputs`/`_pipeline_result` to the separately implemented source-aware pipeline (`Pipeline.run_sources` and attributed replay). One full-context call sees the ordered Sources; construction returns CanonicalState. Preserve source IDs in results, artifacts and Evidence inspection rather than inferring them from titles or quotes. |
| Record observations and usage | Reuse `research/artifacts.py::Bundle`, `live_accounting.py`, `results.py` and the existing Workbench Run inspection/aggregate evaluation. Retain planned/scored coverage, explicit failures, attempts, tokens, model/configuration/code identity and available costs. Preserve current relationship/quote metrics; report any separately implemented Source-attribution diagnostic under its own name. |

The separate implementation agent has prepared these capabilities on local
branch `codex/final-day-core`, checkpoint
`c31a7011bd7748063cdd465f39e623a4fe87cfee`, including its source-aware core
dependencies. That work is outside PR #125 and still requires its own review and
integration; it must not be reimplemented here. Relevant additional consumer
files are `workbench/run_inspection.py`, `workbench/evidence.py`,
`web/research/shared/contracts.ts` and the existing Evidence inspector.

Execution gates remain human benchmark approval, frozen chain/configuration,
reviewed adapter integration and the existing shared task budget/plan
authorization. This follow-up makes no provider calls and runs no held-out
evaluation. The benchmark is ready for human approval; those execution gates
and passing required CI remain separate from fixture correctness.


## Required CI blocker outside benchmark fixtures

At pre-follow-up head `95427e649785889281675dfb157d2bfd496c9c26`,
[CI run 39003461044](https://github.com/alistairkung/private-client-graph/actions/runs/39003461044)
passed Python and Docker smoke but failed the narrow-screen execution journey
in `web/research-execution-e2e/workspace.spec.ts`: the frozen-Run review dialog
never appeared. The aggregate `tests` check failed consequently.

The captured trace shows polling discovering the frozen Run before its freeze
POST response returns. `RunExecution` mounts with `initiallyOpen=false`, then
keeps that initial local state when the later freeze callback requests opening.
A temporary browser harness reproduced the missing dialog with a single click
and that response ordering. All 21 ordinary local execution journeys also pass,
so a passing rerun alone must not be described as a fix for this timing race.

`web/research/workspace/Workspace.tsx` and `RunExecution.tsx` are unchanged in
this PR. The separate workbench implementation owner must fix the modal-open
request lifecycle and cover the polling-before-response ordering. Do not weaken
the existing browser assertion or include a workbench behavior change in this
benchmark follow-up. No blocking fixture defect was identified, but the PR is
**not merge-ready** until this separate CI blocker is resolved and required
checks pass on the final head.
