# Semantic Evidence v1

**Semantic Evidence is AI-assessed and unverified.** It sits beside the
deterministic Benchmark v4 measures for Graph F1, Proof Completion, and
Multi-Source Evidence Coverage. Those measures retain their existing contracts.
The semantic assessment can surface plausible support or flaws in the attached
Evidence. DeepSeek and the extractor can share model-specific biases.

**Temporal limitation.** Benchmark v4 targets have no explicit assessment
cutoff. A Supported verdict or a timing finding of satisfied describes the
submitted quotations. If a claim depends on an unavailable cutoff, its status
at that cutoff remains unverified. Dates in a quotation can establish what the
Source says about timing. They cannot supply the assessment cutoff. The Run
and comparison reports carry this limitation alongside the results.

## Scope and rubric

The unit is one formal proof target in one qualified Benchmark v4 Condition.
The same 71 targets appear on every assessment and every compatible comparison.
The consensus U8 input has its own deterministic diagnostic. A missing
relationship or unavailable Canonical Graph stays visible and supplies no
judge request. A complete Run can have delivery failures.

A request includes the asserted relationship, versioned neutral documentary
requirements, and only its actual attached verbatim quotations. Each quotation
is checked against its attributed frozen Source body. Opaque Source labels
preserve grouping while the local artifact retains original attribution.
Approved evidence, Source titles, Source context, other relationships, and
deterministic outcomes stay out of the request. Timing and authority are required
for trust roles. The two authored sanity controls cover an appointment after
an explicit cutoff and conflicting authority. Control judgments sit outside the
71-target denominator.

| Verdict | Meaning |
| --- | --- |
| Supported | The submitted citations establish all applicable facts in one coherent route for the assertion as supplied. |
| Partially Supported | A material fact is established with an evidentiary gap remaining. |
| Unsupported | No material support or a decisive contradiction. |
| Uncertain | Ambiguity prevents a clear decision. |

Every required fact must appear once. Satisfied and contradicted facts cite
submitted quotation IDs. Only optional facts can be inapplicable. The validator
rejects malformed or inconsistent responses, preserving raw responses and
distinguishing invalid results from a valid Uncertain verdict. It verifies
citation membership. Semantic interpretation still comes from the model.

The retained Extractor v1 assessment used this same prompt, rubric, and
`deepseek-v4-pro` settings. It surfaced one potentially sufficient quotation
boundary miss, plus 22 partial signals at zero exact match. Seventeen responses
were invalid. The raw judgments and frozen report remain in their original
private directory. The Workbench links that assessment and does not rerun it.

## Prepare, authorize, and inspect a Run

Use the same private `PCG_RESEARCH_ARTIFACTS` and
`PCG_BENCHMARK_V4_CUSTODY` as the owner Workbench. The assessment reads a verified,
completed Run and writes to a separate directory under
`ARTIFACT_ROOT/semantic-evidence/RUN_ID`. This also applies to Extractor v2 and
RAG Runs once they deliver compatible, verifiable Benchmark v4 artifacts. This
workflow invokes neither extraction nor resolution.

In the following commands, substitute local paths and real Run IDs. Register the
existing baseline once, using its original location, to expose it in Workbench
and as an optional reuse donor. Initialize the shared Semantic Evidence task
ledger once per private artifact root. It starts with zero spending authority.

```sh
uv run python -m private_client_graph.research.semantic_evidence initialize-task ARTIFACT_ROOT

uv run python -m private_client_graph.research.semantic_evidence register-baseline \
  ARTIFACT_ROOT runs/semantic-evidence-v1-extractor

uv run python -m private_client_graph.research.semantic_evidence plan \
  ARTIFACT_ROOT TARGET_RUN_ID --reuse-from EXTRACTOR_V1_RUN_ID \
  --peak-rates 1.32 3.96 --usd-ceiling 2.50 --task-call-ceiling APPROVED_TASK_TOTAL
```

Check the rates on [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/).
The rates above are the earlier plan's USD per million input and output tokens.
The plan prints its digest, maximum new attempts, copied judgments, and upper
cost estimate. Up to one DeepSeek attempt is planned per uncovered recovered
target and sanity control. Payable requests have a 12,000-token input envelope
and a 4,000-token output limit. A fully reused plan is immediately readable.

After separate spending approval for that exact plan, load the existing
`DEEPSEEK_API_KEY` and dispatch with the verified rates:

```sh
uv run python -m private_client_graph.research.semantic_evidence run \
  ARTIFACT_ROOT/semantic-evidence/TARGET_RUN_ID \
  --approve-plan-sha256 APPROVED_DIGEST --approval-reference OWNER_APPROVAL \
  --verified-peak-rates 1.32 3.96
```

The semantic task ledger is shared across assessments in this artifact root
and independent of extraction and resolution. Each plan binds the absolute
task call ceiling and its own call and USD limits. A new plan starts from the
task's existing usage. Each attempt is reserved before dispatch. Failures and
interruptions consume that slot, including calls whose provider usage is unknown.
Continuation uses the original authorization and resumes only unused slots.
Provider access failures stop the invocation so the remaining slots can be
preserved. Completion records bind the receipts by checksum. An unsealed
retained receipt blocks continuation pending custody recovery. The retained v1
receipt inventory is verified separately. A response from a different or
unidentified judge remains invalid. The Workbench routes are read-only and
inherit owner-only access.
The Evaluation Protocol panel for a completed Run shows **Semantic Evidence**
with its **AI-assessed, unverified** label. Open **Inspect semantic assessment**
for cited evidence and execution details. Use **Refresh assessment** to read a
newly retained assessment.

## Reuse and compare

Optional reuse requires the same frozen benchmark and observation origin, the
same formal target identity (or control), the same model settings and exact
request digest, and the same original Source attribution. Only valid responses
from the configured judge are eligible. Reuse is frozen into the new plan with
the original Run, plan and request identities, and the original provider
receipt. The receiving Run incurs no call or cost for a reused judgment. Model
aliases may be updated by the provider, even when the returned model name
stays stable.

```sh
uv run python -m private_client_graph.research.semantic_evidence report ASSESSMENT_DIRECTORY
uv run python -m private_client_graph.research.semantic_evidence compare ARTIFACT_ROOT LEFT_RUN_ID RIGHT_RUN_ID
```

The comparison requires the same judge contract, frozen target population,
deterministic scorer, and report version. It works across Experiments in the
same private artifact root.
Within a Workbench Experiment, use **Compare with verified Run** and expand the
Semantic Evidence comparison under the deterministic results. Every formal
target retains both states. Coverage shows the fixed denominator and the
number with two valid judgments. Documentary fact changes are computed only
for those pairs. An unattempted, interrupted, invalid, or undelivered target
continues to count in each Run's denominator. A Supported result on an
exact-incomplete target is a candidate for interpretation. These comparisons
provide no certified documentary or legal sufficiency or causal attribution.
