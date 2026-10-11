# Entity-resolution research experiment

Status: agreed design handoff. Task A is ready for implementation. Task B requires
Task A to be complete and reviewed **and separate explicit user authorization**.
The user's time-box limits their active deliberation and supervision; there is
no two-hour implementation deadline and no permission to reduce correctness.

Execution tickets:
[Task A — implementation](https://github.com/alistairkung/private-client-graph/issues/91)
and [Task B — separately authorized pilot](https://github.com/alistairkung/private-client-graph/issues/92).

## Paid-call policy and task boundaries

Each development task has a default allowance of up to five paid provider calls
for useful integration checks, smoke tests or small diagnostics, usable without
per-call approval. Count every attempted paid invocation, including failures and
retries, against one persistent task allowance shared across agents, sessions,
resumptions and test cases. Do not spend merely to exhaust it. Once exhausted,
obtain explicit user approval before another paid invocation.

Task A may use this five-call allowance for optional live development checks;
CI and automated tests remain deterministic and independent of live providers.
Task B retains its separately scoped 38-attempt ceiling and explicit execution
gate; the default five calls do not add to that budget. Keep Task A diagnostics
separate from the Task B pilot and label their artifacts accordingly.

`authorization_reference` and `reviewed_commit` are provenance records for this
operational workflow. Their presence lets the local CLI reject an incomplete
Task B manifest, but it does not authenticate the user, verify consent, or prove
that Task B was authorized. Explicit authorization must still be established in
the user-controlled workflow before execution; successful local validation is
not an authorization or security guarantee.

The user controls the build → evaluate → interpret → rebuild loop. Completion
of Task A does not start Task B, and experiment findings do not authorize a new
iteration or architectural change. No additional per-invocation approval is
required while executing an approved task within its allowance.

## Objective and evidence

Determine whether an explicit generative alias resolver earns its incremental
quality, consistency, token cost and latency compared with no resolution.
A negative result is valid. This is a development-set research experiment, not
a demonstrated repair or an unseen-test generalisation claim.

At `09ee8f5c6579ed2f22572b61c9977522598533f1`, Case 03's committed extraction scores
6 TP, 1 FP, 1 FN, F1 6/7 and provenance accuracy 1.0. A single live
`deepseek-flash` run on 2026-10-11 scores 7 TP, 0 FP, 0 FN and both accuracies 1.0.
It used Rebecca Tan consistently within that execution; repeatability is unknown.
Its local artifact stem is
`runs/case_03/2026-10-11T073006-076520a5dc0f4675a9c84f7ab80b9142`.
Usage: 1,879 input tokens (512 cached), 390 output tokens, approximately 2 seconds
including local processing. Retain its original metadata as historical evidence.

All 38 retained Case 01 extraction payloads also pass current relationship and
provenance evaluation and are identical ignoring candidate order. This describes
saved observations, not all attempted invocations or a controlled reliability study.
The Case 03 README overstates its fixture split: only Rebecca and Rebecca Tan
become endpoints; Mrs Tan appears in quotations. Correct that factual description
without modifying the existing source, expected extraction or answer key.

## Architecture and contracts

The research workflow is:

`saved extraction + Source -> selected resolver -> existing graph builder -> existing evaluator -> retained results -> offline report`

Implement only two configurations: `noop` and `generative_full_source`. Use small
Python callables and a narrow composition root selecting known implementations.
Keep model settings explicit in experimental configuration. No general
AgentConfiguration topology, plugin registry, dependency-injection framework,
Null Object class hierarchy or LangGraph. Existing LCEL extraction composition
may be reused where useful; it does not dictate research orchestration.

The resolver receives an immutable ExtractionResult and the exact Source.
No-op returns equivalent content, makes no provider call and does not mutate
inputs. The generative resolver may propose endpoint-name substitutions only.
Use a focused typed edit result keyed by candidate index and endpoint side;
apply it deterministically to a copy. Omitted edits preserve original endpoints.
Validate indices, sides, unique edit targets and nonblank names; reject malformed
responses. Replacement text must occur exactly in the Source or among original
endpoint names. This is a mechanical boundary, not proof of correct identity.
Do not invent participants or select new canonical names from the answer key.
The unaccepted Jev candidate-pool restriction is not imposed on this resolver.

Preserve candidate order/count, relationship types/directions and quotations
exactly. Instruct the resolver to leave uncertain identities unchanged. Preserve
its raw response and applied edits, without claiming that absent edits prove
certainty. Use the existing graph builder to detect invalid results, including
self-relationships and type conflicts. Do not silently repair, drop candidates,
retry, substitute a baseline result or turn a failed run into a successful no-op.
A merge may reduce canonical edge count through existing deduplication; record
that result without changing the builder's policy.

ExtractionResult, CanonicalGraph, extraction prompts, deterministic construction,
existing scoring, provenance policy and production application paths stay intact.
Endpoint names remain the builder's identity keys. Distinct same-name people are
out of scope. The experiment does not infer missing relationships. Keep semantic
resolution separate from deterministic validation and benchmark evaluation.

Research execution, artifacts and report rendering remain separate from PCG
application workflows and from each other. XJ10 may benefit from their design
lessons; do not extract shared packages or cross-project contracts now.

## Fixtures and annotation

Use six frozen inputs with explicit provenance:

1. Case 01 expected extraction: preservation control.
2. Case 02 expected extraction: preservation control.
3. Case 03 expected extraction: authored alias-split challenge.
4. The saved successful Case 03 live extraction: historical preservation control.
5. New authored merge challenge A.
6. New authored non-merge challenge B.

The new pair uses identical candidates and exact supporting quotations:

- Elizabeth Tan `settlor_of` Harbour Trust; quote: "Elizabeth Tan is the settlor of Harbour Trust."
- Beth `beneficiary_of` Harbour Trust; quote: "Beth is a beneficiary of Harbour Trust."

A establishes immediately before the beneficiary sentence that Beth is Elizabeth
Tan's nickname; its answer key has one person with both roles. B establishes that
Beth is a distinct person whose recorded name is Beth; its answer key preserves
two people. No other supported relationships are asserted. Follow the repository's
answer-key-first synthetic-authoring workflow, including semantic review of source,
complete truth and approved quotes. The agreed truth is explicit here; any semantic
change requires review. Keep these as named research fixtures, not a replacement
for numbered benchmark cases or their ground truth. Diagnostic inputs represent
intentionally unresolved candidates, not claims of ideal extraction or live errors.

For all frozen inputs, add research-only annotations mapping each candidate index
and endpoint side to its intended participant. Review annotations against the
Source. They never enter resolver requests and do not alter existing benchmark
models or evaluator. Fresh, unannotated outputs receive graph scores and edit logs;
identity metrics are unavailable rather than inferred from names or scored zero.
Preserve historical artifacts unchanged when importing; never synthesize historical
usage or fabricate a replacement live result if the recorded artifact is missing.

## Paired pilot protocol (Task B only)

Use the configured DeepSeek model, resolving and recording the effective model
before execution. Fixed prompt/model settings within each cohort; thinking disabled,
no automatic retries and explicit request timeout. Record actual provider metadata
and distinguish requested aliases from returned model/version information. A dated
or opaque model alias is not proof of immutable weights. Keep local run IDs outside
model inputs so repetitions send identical requests.

| Cohort | Maximum new extraction calls | Maximum resolver calls |
| --- | ---: | ---: |
| Six frozen inputs, three resolver repetitions each | 0 | 18 |
| Five fresh Case 03 extraction attempts, three resolver repetitions per usable extraction | 5 | 15 |
| Total ceiling | 5 | 33 |

Maximum **38 paid provider attempts**, including failures; this excludes the
previously authorized historical observation. It is a cap, not a spending target.
Task A's optional development checks use its separate five-call allowance. Task B
remains blocked until separately authorized, even after Task A passes review.
SDK/transport retries for the pilot must be disabled;
new attempts must not evade the budget after interruption or resume.

After authorization, preflight configuration, fixtures, disk persistence, pricing
metadata and the offline manifest. Start with three resolver calls on each matched
challenge (six attempts). Inspect contract handling and artifacts. Continue within
the ceiling only while the harness is valid and additional observations serve the
specified pilot. Poor quality alone is data, not a reason to discard observations
or tune prompts mid-cohort. If stopping early, report the incomplete planned matrix
and reason. Any prompt/setting revision starts a separately labelled experiment;
it does not reset authorization or the shared call cap.

Evaluate no-op once per saved extraction, reuse it as the deterministic paired
control, and apply three independent resolver repetitions to the identical input.
Three repetitions are a diagnostic sample, not a reliability guarantee. Keep the
fresh cohort separate from authored fixtures and the historical observation. Do
not pool repeated resolver calls as independent extraction samples.

Retain failed extraction attempts. Parsed candidates whose baseline graph fails
may still receive the scheduled resolver repetitions: record baseline failure and
report recovery separately, without inventing paired F1. Unparsed/missing extraction
outputs cannot be resolved; mark dependent runs unavailable and do not replace them
with additional extraction attempts. Every failure consumes its attempted-call
budget. Local failures before dispatch do not consume a provider attempt.

## Metrics and interpretation

Retain each existing EvaluationResult: TP/FP/FN, precision, recall, F1, provenance
passes/failures/accuracy and diagnostic edge sets. Provenance remains conditional
on matched relationships and approved exact quotes; it is not independent proof
of identity correctness.

For annotated inputs, compare all unordered pairs of type-compatible candidate
endpoints: truth equality comes from participant annotations; predicted equality
comes from final endpoint names. An incorrect merge joins different truth
participants; a missed merge separates the same truth participant. Record counts,
denominators and pair diagnostics; distinguish unavailable metrics and zero eligible
pairs from measured zero errors. These are endpoint-pair diagnostics, not counts of
real people harmed. Repeated mentions affect denominators, so report per input and
avoid misleading pooled rates. Correct grouping with the wrong canonical display
name can still fail existing name-based F1; retain both results for diagnosis.

Report resolver repetition mean, sample standard deviation (undefined for n<2),
minimum and range per input, plus paired F1 deltas where both graphs score. For
fresh extractions, separately summarize baseline variation and variation of resolver
per-input means; summarize within-input variation separately. Include precision,
recall and provenance with explicit aggregation labels and n values. Missing/failed
scores remain null with status, never become zero or vanish silently. Report failure
rates and paired-score coverage alongside successful-run aggregates; no best-of-three
selection, significance claim or assertion of generalisation from this pilot.

Record input/output/cached tokens, call count, provider latency and stage/end-to-end
latency. Distinguish experiment spend, hypothetical per-pipeline cost (one extraction
plus one resolver execution), and incremental resolver cost. Reuse the extraction
measurement for each paired configuration without charging it again as actual spend.
Authored fixtures have no measured extraction cost; historical runtime/usage retain
their original meaning. Unknown is not zero. Estimate costs only from documented
provider pricing, preserving currency, rates, cache treatment, source URL and retrieval
date. Unsupported pricing stays unknown. An interrupted or timed-out request may
have unknown billing; retain that uncertainty rather than assuming it was free.

### Research timing definitions

The runner measures durations with a monotonic clock. These are execution-stage
measurements, not total experiment wall time:

- `provider_seconds` measures one provider callable, including its transport and
  structured-output parsing, whether it returns or raises. Runner serialization,
  budget reservation, observation storage and observation reads are excluded.
- Summary `extraction_seconds` is the fresh extraction attempt's recorded
  `provider_seconds`, including failed attempts. It is not the entire ingestion
  workflow. Authored inputs and historical records without an isolated extraction
  measurement remain unknown.
- `resolution_seconds` measures local preparation, snapshots, typed edit validation
  and application through the graph boundary (or resolution failure), plus the
  recorded resolver provider duration. Observation I/O is excluded. On resume,
  local work is measured again and the original provider duration is reused;
  reading an artifact is never substituted for a model call's latency. Known
  provider/parse failures retain their elapsed resolution time. An uncertain
  attempt without a recorded provider duration remains unknown.
- `edit_seconds` is the local, non-provider portion of resolution when edit
  validation is reached, including preparation and copying; it is not an isolated
  edit-application benchmark. It remains unknown when provider/parse failure
  prevents edit validation. The no-resolution baseline records zero incremental
  provider, resolution and edit time by convention.
- `graph_seconds` and `evaluation_seconds` measure their respective domain calls,
  including calls that fail. Diagnostics, artifact writes and error classification
  are excluded. An unentered stage remains unknown, not zero.
- `downstream_seconds` sums the entered graph and evaluation stages. A graph
  failure retains graph time alone; an evaluation failure retains both durations.
  Summary single-pipeline latency is produced only for completed results with
  known extraction, resolution and downstream durations. Failed execution times
  remain visible in their stage fields and are never presented as successful
  pipeline latency.

## Artifact persistence and retention

Extend `runs/` conventions with one versioned, append-only experiment bundle:
manifest; frozen inputs/Source/ground truth/annotations; individual extraction and
resolver attempts; graph/evaluation results; derived summaries; standalone HTML.
Use unique IDs and links for experiment, extraction sample, resolver repetition,
configuration and provider attempt. Store UTC timestamps, code SHA/dirty state,
fixture/prompt hashes and snapshots, effective model settings, dependency versions,
provider response metadata, status/error stage, usage, duration and edits. Preserve
raw synthetic provider output even on parse/validation failures where available.
Never persist keys, authorization headers or credential-bearing errors.

Write the attempt record and budget reservation before dispatch, then atomically
persist completion. An interrupted in-flight attempt remains uncertain and counted;
resume skips recorded attempts and never silently reissues them. Preserve completed
results rather than overwriting. Store raw observations separately from regenerable
summaries; reject accidental fixture/config mismatches on resume or comparison.

Individual runs remain Git-ignored by default. Task B must deliver a self-contained
export/archive alongside the HTML, with a checksum manifest and sufficient snapshots
to analyse it on another machine. Keep it until the user explicitly elects deletion;
no automatic cleanup. Publish a concise result summary in Task B with artifact paths,
checksums and actual attempt counts; a local ignored path alone is not the portable
handoff. The historical input is supplied with Task A's ticket for independent use.
No PostgreSQL, hosted trace store or remote upload is required.

## HTML report

Render from saved bundles without credentials, network or model calls. Produce a
self-contained shareable HTML file with inline assets and escaped source/provider
content. Keep execution and rendering separate. The main chart uses paired extraction
sample index on the x-axis and F1 on the y-axis, with baseline and resolver mean
series, resolver range and accessible individual repetition data. Show failed runs
as missing scores with explicit status, never connected as successful values.

Use distinct panels/tables for fresh, authored and historical cohorts. Show planned,
attempted, valid, failed and scored counts; sample/repetition counts; model/config and
fixture/evaluator identity; quality and identity diagnostics; cost/latency; unavailable
measurements; and the limitations above. A labelled deterministic demonstration may
be generated in Task A but must not be presented as provider performance. No web app,
landing-page integration or analytics framework.

## Task A — Implement experimental infrastructure

Implement the research resolver boundary, known configuration selection, fixtures
and reviewed annotations, paired runner, durable artifact schema/budget ledger,
metrics and report renderer. Provider credentials alone must not enable execution:
require an explicit live-execution mode; offline planning, fixtures and rendering
must work without credentials. Keep production paths unchanged.

Test every deterministic rule with fixtures, mocked transports or recorded responses:
no-op parity/immutability; correct and harmful substitutions; malformed edits and
forbidden changes; ambiguity/no-edit behavior; exact Source forwarding and no truth
leakage; same-input pairing; schema/provenance/graph failures; null metrics; merge/split
diagnostics; repetition and cohort aggregation; usage/cost arithmetic; failures and
budget/resume behavior; complete portable export; safe, offline report rendering.
Mock the real provider boundary and fail automated tests on attempted live network
calls. Optional live smoke checks, integration checks and diagnostics outside CI
and automated tests may use Task A's shared five-call allowance. Record every
attempt, including failures and retries; seek approval before exceeding it.
No live check is required merely to use the allowance, and it must not launch the
Task B pilot or an unapproved architectural iteration.

Run `uv run pytest`, preserve required CI checks, and visually inspect a deterministic
HTML demonstration. Verify offline runner/export/render round-trip and label all
substitute data. Ensure code remains compositional and scoped. Task A is complete
when deterministic acceptance checks pass and implementation is reviewed; it must
not automatically start Task B. Follow repository fresh-main/feature-branch rules;
do not merge automatically.

## Task B — Execute and analyse the experiment

Depends on Task A being complete and reviewed plus **explicit user authorization to
execute this ticket**. Preflight the frozen protocol and run within the 38-attempt
ceiling, preserving all observations and stopping appropriately. Generate the portable
bundle and HTML from actual results. Summarize quality, resolver/extraction variability,
identity errors, failures, coverage, tokens, latency, estimated incremental and total
cost, and whether observed benefit justifies complexity. Separate authored challenges
from live findings and report negative or inconclusive results candidly. No silent
prompt tuning, selective reruns, replacement of failures or expansion into other models.

## Alternatives and deferred work

- Candidates-only resolver: useful next controlled context comparison, not initial scope.
- Jev identity resolution: deferred because candidate generation, reconciliation,
  conflict handling and canonical-name selection obscure a small model comparison.
- Jev relationship validation: strongest follow-on Jev fit, with a separate filtering
  contract and reviewed claim-support labels. It cannot repair missing relationships.
  Unapproved quotations and alias-related exact-name errors are not automatic negatives.
- Jev role classification: defer candidate coverage, direction, multi-role and
  no-supported-role semantics. Do not hide this behind a Resolver interface.
- LangSmith: official docs support ordinary-function tracing, usage/cost reporting,
  custom evaluators and experiment comparison without LangGraph. Defer integration:
  owned run bundles suffice here and remote retention/provider accounting add scope.
  PCG retains truth and metrics if integrated later.
- Defer homonyms, new ontology/graph identity/scoring semantics, practitioner confirmation
  or editing, retrieval, planners, production configuration, PostgreSQL analytics,
  generalized assertion provenance, unseen-test claims and a shared XJ10 framework.

Official research references:
[Jev API](https://docs.typesafe.ai/api),
[Jev batching](https://docs.typesafe.ai/cookbooks/parallel_questions),
[Jev confidence](https://docs.typesafe.ai/confidence),
[Jev limits](https://docs.typesafe.ai/model-jaggedness/jev-1.13),
[LangSmith instrumentation](https://docs.langchain.com/langsmith/annotate-code),
[LangSmith costs](https://docs.langchain.com/langsmith/cost-tracking),
[LangSmith comparison](https://docs.langchain.com/langsmith/compare-experiment-results).
