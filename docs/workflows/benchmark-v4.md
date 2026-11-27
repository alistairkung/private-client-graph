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
including Multi-Source proofs, on the 34 original Environment Conditions. The
U8 diagnostic counts exact overlaps with frozen adjudicated citations for the
same relationship, Source ID and quotation. It is assessed when the graph is
constructed. Accepted citations support the reference and are a limited set
against which overlap can be reproduced. Other correct citations may exist.
U8 supplies no formal proof-sufficiency denominator. The Workbench and CLI
report [Deterministic Evidence Quality v1](deterministic-evidence-quality-v1.md),
including Graph F1 on both scopes, Proof Completion and Multi-Source Evidence
Coverage of exact Source–quotation pairs.

## Historical transition

The versioned [Benchmark v4 manifest](../../private_client_graph/research/benchmark-v4.json)
refers to the original v3 admissions register and the separate frozen U8
release. Historical Sources, keys, proof alternatives, Evaluation Protocol v1
and baseline artifacts are reused from custody.

Benchmark v3 remains independently accessible through the
[historical import and replay workflow](benchmark-v3-workbench.md).
The frozen DeepSeek baseline retains TP 91, FP 10 and FN 22, graph micro-F1
0.850467, 20/34 exact graphs, 18/71 complete proofs and 0/30 complete
Multi-Source proofs. Those figures describe the original 34 Conditions. A new
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
| `PCG_BENCHMARK_V4_PRICING_FILE` | Optional local JSON conforming to `Pricing`. New Runs freeze this rate. F1 vs Cost uses it as a uniform reference rate for completed Runs with full token usage. |

Run the historical import steps against the same private artifact root to
keep the v3 Run visible alongside v4. Set `umask 077` for artifact writes.
Build the Research frontend, apply the existing migrations, then start
`private_client_graph.workbench.api:app` on `127.0.0.1` with
`--no-proxy-headers --no-access-log` for inspection. **Benchmark v4** opens by
default when custody is configured. Select a Matter and, where applicable,
an Environment Condition. Inspect the frozen reference graph and Sources
before running an experiment.

## Run the paired resolver experiment

Start the private execution Workbench with
`private_client_graph.workbench.execution_api:app` and
`PCG_RESEARCH_LIVE_ENABLED=1`. Load `DEEPSEEK_API_KEY` into the worker's
environment. Keep the dedicated database at Alembic head and retain the
owner-only artifact directory and its task ledger together. Use the
[existing execution workflow](persistent-research-workspaces.md) to provision
the task registry and review authorization. Provisioning a registry starts with
zero paid allowance.

1. Create **Extractor v1 — Resolver Ablation**. Confirm **PCG Benchmark v4**
   and **Extractor only**. A fresh Run makes one `deepseek-flash` extraction per
   frozen input. In **Run settings and invocation limits**, set the invocation
   cap to 35 and enter the approved total task cap.
2. Choose **Run**, review and **Freeze Run**, then **Authorize invocation** and
   **Start Run**. Keep the completed, verified Run in the same Experiment.
3. In Run A, choose **Copy to next draft**. Select **Generative Resolver** and
   confirm Run A under **Verified extraction origin**. The model settings and
   committed Sources come from Run A. Preview shows 35 planned inputs, zero
   new extractions and up to 35 resolver attempts. A valid empty extraction is
   eligible. Provider, parse and uncertain extraction outcomes stay visible
   in their original slots.
4. Freeze and authorize Run B separately. From a zero-use dedicated task, the
   pair needs a maximum total task allowance of 70 calls. Stop or continue
   through the existing bounded invocation controls.
5. Open **Compare with verified Run**. The Workbench displays pooled graph
   scores, cohort delivery and evidence metrics, along with incremental and
   inherited usage. Full pipeline latency is reconstructed from extraction
   provider time, resolver provider time, and local edit and final graph
   construction timings. Provider costs remain unpriced without the frozen
   pricing and usage needed for the estimate.

The F1 vs Cost chart can show a reference-rate estimate from retained billable
tokens, including inherited extraction, even for Runs frozen without pricing.
The configured rate is a comparison basis. Historical Run accounting, the
task ledger and CLI summaries still use the original frozen commitments.

The Resolver receives the same ordered Sources and the existing candidate
projection. Its endpoint edits are applied to the retained attributed
candidates before construction. References and adjudication stay scorer-side.
Both Runs use the same v4 scorer and private roster. Freeze A and B on this
revision to share the same scorer commitment.

Use `uv run python -m private_client_graph.research summarize RUN_DIRECTORY`
to print the metrics to stdout without writing to Run custody or including
raw provider requests or responses. Keep the
parent Run, child Run and original task ledger in private custody so the
candidate lineage and receipts remain verifiable.

To verify the exact references and historical numbers offline, set
`PCG_V3_PRIVATE_BASELINE_CUSTODY` to the existing custody root, and set
`PCG_V4_RETAINED_EXTRACTOR` and `PCG_V4_RETAINED_RESOLVER` to the completed
paired Run directories. Run
`uv run pytest tests/research/test_benchmark_v4.py tests/research/test_v3_evaluation_protocol.py`.
CI uses synthetic fixtures and substituted provider responses.

## Optional Semantic Evidence assessment

The owner Workbench can show an AI-assisted, unverified evidence comparison
for completed Runs. The standalone stage reuses retained quotations and
requires separate approval for any new DeepSeek calls. See the
[Semantic Evidence workflow](semantic-evidence-diagnostic-v1.md).

## Later retrieval experiment

Freeze a 35-input full-context Run and a matched retrieval Run from the same
manifest. Keep the model, extraction contract and settings fixed and record
the context strategy, ordered Source selection and receipts for each request.
Reuse the same pipeline, graph scorer and evidence contracts. Register the
retrieval configuration and authorize the call allowance before execution.
Compare pooled counts, construction outcomes, both reference slices, formal
proofs, U8 citation overlap and observed provider usage. Keep the v3 baseline
as historical context and establish the v4 baseline from newly measured
results.
