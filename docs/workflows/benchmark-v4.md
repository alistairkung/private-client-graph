# PCG Benchmark v4

Benchmark v4 is the operational evaluation suite for PCG’s evidence-grounded
graph construction workflow. It has 20 synthetic Matters and 35 evaluation
inputs. The benchmark starts after a practitioner has approved the Sources.
Matter intake receives functional, integration and safety tests separately.

## Reference methodology

| Scope | Inputs | Reference |
| --- | ---: | --- |
| Originally qualified | 19 Matters, 34 Environment Conditions | Frozen Benchmark v3 admissions and documentary keys |
| Consensus adjudication | U revision 8, one input, 65 Sources | Ten blind AI reviews and separate Source-body evidence adjudication |
| Benchmark v4 | 20 Matters, 35 evaluation inputs | Mixed references |

The project adopted v4 to measure graph delivery across a practical range of
workloads using one pipeline. The 65-Source Matter gives upcoming full-context
and retrieval runs a larger workload while reusing the originally qualified
cohort. Its original qualification attempt ended with an unresolved
title-dependent proof issue. The later consensus reference has a different
basis and carries less assurance than the original qualification, which used
documentary keys, independent qualification and precommitted proof alternatives
and controls.

Ten independently elicited blind AI reviews voted on graph propositions. The
frozen aggregation admitted propositions with at least six affirmative votes.
Six relationships received all ten votes and passed a separate Source-body
evidence review. Four other propositions received zero affirmative votes.
Agreement measures consistency within this panel and can reflect shared model
biases. The four zero-vote propositions record the panel's dispositions and
supply no true-negative denominator. The frozen Source release, reference
projection and freeze record are tied to precise SHA-256 commitments. The
custodian can replay the aggregation from the retained reviewer outputs. The
original release and freeze records still carry their original v3 eligibility
flags. The v4 manifest supplies the product admission.

This is one large Matter. Its individual F1 describes performance against its
consensus reference. Its single observation cannot estimate performance across
large Matters or isolate a causal effect of Source count, case complexity or
retrieval.

## Scoring

Each Run uses the same ordered roster, common relationship ontology,
canonicalisation and semantic-edge scorer. Graph delivery reports use the
following pooled counts across planned inputs.

- Precision is TP / (TP + FP). Recall is TP / (TP + FN).
- Micro-F1 is 2 × TP / (2 × TP + FP + FN). A zero denominator yields zero.
- An unavailable graph contributes its expected edge count to FN, and zero TP
  and FP. Construction successes, failures, uncertain outcomes and inputs
  awaiting extraction remain visible. A valid empty graph counts as
  constructed. It is exact only when its reference is also empty.
- The combined score uses mixed references. The same counts and denominators
  are available for the qualified cohort, U8 and each Matter. Partial Runs are
  provisional. Unstarted Runs have no measured graph score.

Evaluation Protocol v1 continues to score Sufficient Evidence Alternatives,
including joint-only proofs, on the 34 original Environment Conditions. The
U8 diagnostic counts exact overlaps with frozen adjudicated citations for the
same relationship, Source ID and quotation. It is assessed when the graph is
constructed. Accepted citations support the reference and are a limited set
against which overlap can be reproduced. Other correct citations may exist.
U8 supplies no formal proof-sufficiency denominator.

## Historical transition

The versioned [Benchmark v4 manifest](../../private_client_graph/research/benchmark-v4.json)
refers to the original v3 admissions register and the separate frozen U8
release. Historical Sources, keys, proof alternatives, Evaluation Protocol v1
and baseline artifacts are reused from custody.

Benchmark v3 remains independently accessible through the
[historical import and replay workflow](benchmark-v3-workbench.md).
The frozen DeepSeek baseline retains TP 91, FP 10 and FN 22, graph micro-F1
0.850467, 20/34 exact graphs, 18/71 complete proofs and 0/30 complete
joint-only proofs. Those figures describe the original 34 Conditions. A new
full-context v4 Run will supply the first measured 35-input baseline.

## Open the private Workbench

Use the same private Benchmark v3 custody root and a dedicated local
Workbench artifact root and PostgreSQL database. Create the artifact directory
with owner-only permissions. Set these values in the owner-only environment
used to start the Workbench.

| Setting | Purpose |
| --- | --- |
| `PCG_RESEARCH_ARTIFACTS` | Existing absolute owner-only artifact directory outside Git |
| `DATABASE_URL` | Local dedicated Research Workbench database |
| `PCG_BENCHMARK_V4_CUSTODY` | Absolute owner-only v3 custody root containing the frozen admissions, U8 Source release and U8 consensus freeze |
| `PCG_BENCHMARK_V4_OWNER_TOKEN` | Private URL-safe token of at least 32 characters for the local `owner` sign-in |
| `PCG_BENCHMARK_V4_PRICING_FILE` | Optional local JSON conforming to the existing `Pricing` contract for the requested model |

Run the historical import steps against the same private artifact root to
keep the v3 Run visible alongside v4. Set `umask 077` for artifact writes.
Build the Research frontend, apply the existing migrations, then start
`private_client_graph.workbench.api:app` on `127.0.0.1` with
`--no-proxy-headers --no-access-log` for inspection. **Benchmark v4** opens by
default when custody is configured. Select a Matter and, where applicable,
an Environment Condition. Inspect the frozen reference graph and Sources
before running an experiment.

Use the [existing execution workflow](persistent-research-workspaces.md)
with `private_client_graph.workbench.execution_api:app` for an approved
experiment. New drafts in the owner Workbench default to the v4 roster. The
full-context configuration selects one Source-aware extraction per frozen
input and bypasses alias resolution. Review, freeze, authorize and start
through the existing Run controls. A frozen plan records all Source and
reference commitments, model settings, prompt hashes, scoring implementation
and authorization limits. Source bodies and titles reach the model through the
existing Source-only request. Evidence keys and consensus records remain
scorer-side. Benchmark v4 tracing stays local in the Run artifacts.

Open the selected Run for combined and cohort graph metrics, construction
outcomes, a separate U8 citation diagnostic and the qualified proof metrics.
Provider tokens, latency and estimated cost are displayed when retained
receipts and, for cost, frozen pricing support them. Run comparison aligns
the same frozen input and scorer commitments. Differences are descriptive.
Use `uv run python -m private_client_graph.research summarize RUN_DIRECTORY`
on a private Run bundle for a
reproducible summary without raw provider requests and responses. Full bundles
and their Sources stay in private custody.

To verify the exact references and historical numbers offline, set
`PCG_V3_PRIVATE_BASELINE_CUSTODY` to the existing custody root and run
`uv run pytest tests/research/test_benchmark_v4.py tests/research/test_v3_evaluation_protocol.py`.
CI uses synthetic fixtures and substituted provider responses.

## Next experiment

Freeze a 35-input full-context Run and a matched retrieval Run from the same
manifest. Keep the model, extraction contract and settings fixed and record
the context strategy, ordered Source selection and receipts for each request.
Reuse the same pipeline, graph scorer and evidence contracts. Register the
retrieval configuration and authorize the call allowance before execution.
Compare pooled counts, construction outcomes, both reference slices, formal
proofs, U8 citation overlap and observed provider usage. Keep the v3 baseline
as historical context and establish the v4 baseline from newly measured
results.
