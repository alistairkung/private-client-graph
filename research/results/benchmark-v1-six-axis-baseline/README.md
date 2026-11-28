# Benchmark v1 — Six-Axis Baseline Evaluation

**14 November 2026.** A single full-context extraction per development matter recovered 30 of 31 expected relationships and added one unsupported relationship. Five of six complete graphs matched exactly. Three cases also passed every approved-quotation and Source-association check. All six planned observations were scored. [Recorded observations and input digests](observations.json)

## Objective and frozen configuration

Could PCG's existing extractor reconstruct the complete current graph across six diagnostic axes using only the ordered Sources? The working hypothesis was that explicit names, status changes and links between documents would often be sufficient for the existing prompt. Each axis was examined separately from whole-graph correctness.

PR #172 was open at preflight. Execution used its clean validated commit `3b579c96b8daa06285933a1efca17f2e41c23407` and locked environment. The Workbench v2 API created the named Experiment, selected the six development fixtures explicitly, previewed six extraction slots and zero resolution slots, froze the Run, and authorised one invocation capped at six attempted calls. The normal Workbench worker executed it. There were no protocol deviations in dataset, model settings or call allocation. [Reviewed fixtures and implementation](https://github.com/alistairkung/private-client-graph/pull/172)

| Parameter | Frozen or observed value |
| --- | --- |
| Input | Nine Sources across six synthetic matters, original text including line endings, manifest order, IDs and titles. Only the sourced system prompt and the serialized Source array went to the model. |
| Extraction | Fresh, one structured call per case in the order below, full context, resolution disabled, no retrieval. Each recorded prediction came from that case's provider response. |
| Requested model and settings | `deepseek-flash`, temperature unset and omitted from the request, thinking disabled, timeout 90 seconds, application and SDK retries zero. The authenticated model-list endpoint returned the requested ID before execution. |
| Returned model | All six responses reported `deepseek-flash` and system fingerprint `bc19ba97cbe016479903222bb1578db6`. The provider listed this alias as DeepSeek-V4.1-Flash-1017 on the execution date. The responses did not expose a separate build name. |
| Fingerprints | Sourced system prompt SHA-256 `d67afaeb19c26448a6779d9576800cc50ca399c634ad81a1a02b847be0a9dfae`. Model settings SHA-256 `a388906e2964889173a636ec633f7106f91926ab8cedf1b237b31caa7c010edd`. The observations file includes each complete message-pair digest and dependency versions. |
| Construction and scoring | Existing sourced pipeline, deterministic canonical-state builder, `semantic_edges_v1`, `source_attribution_v1` and `observation_micro_f1_v1`. |

The provider's model mapping and execution-date rates are documented in its [model and pricing table](https://api-docs.deepseek.com/quick_start/pricing/).

## Results

Quotation accuracy counts matched edges with at least one exact approved quote. Source attribution counts approved (Source ID, exact quote) associations among attached evidence on matched edges. The two measures have different units. Here each matched edge had one association. FP and FN edges contribute to graph scoring and do not enter either evidence denominator.

| Axis | TP | FP | FN | Precision | Recall | F1 | Quote accuracy | Source attribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Aliases | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 5/5 | 5/5 |
| Authority | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1/2 | 1/2 |
| Cross-source | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 5/5 | 5/5 |
| Distractors | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 5/5 | 5/5 |
| Proposals | 7 | 1 | 1 | 0.8750 | 0.8750 | 0.8750 | 7/7 | 7/7 |
| Temporal | 6 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 5/6 | 5/6 |
| **Micro / pooled** | **30** | **1** | **1** | **0.9677** | **0.9677** | **0.9677** | **28/30 (93.33%)** | **28/30 (93.33%)** |

Coverage was **6 scored / 6 planned**, with zero failed, uncertain, pending or unavailable observations. Workbench recorded six paid attempts, six completed provider responses and zero replacement, retry, or resolver calls. All calls returned token usage. Of 6,354 input tokens, 3,200 were cache hits and 3,154 were uncached. The model generated 2,022 output tokens. Summed provider latency was 10.456 s (mean 1.743 s, range 1.036–2.232 s). Elapsed time between the Workbench running and complete events was 10.865 s.

Workbench marked all six calls **unpriced** because the plan contained no price schedule. The invoice amount is unknown. A separate estimate from the reported usage and Saturday off-peak USD rates is **$0.0016959**, calculated as (3,154 × 0.15 + 3,200 × 0.003 + 2,022 × 0.60) / 1,000,000. The retained Run's cost was left as recorded. [DeepSeek pricing, checked 14 November 2026](https://api-docs.deepseek.com/quick_start/pricing/)

## Per-axis observations

| Axis | What the recorded candidates, current graph and Evidence show |
| --- | --- |
| Aliases | Margaret / Mrs. Wu and Daniel / Danny appeared under their source-supported full names. Both parents and Danny's beneficiary role matched. This fixture tests linked names. It has no competing similar-name person. |
| Authority | Carol was the sole current beneficiary under the executed deed. Bob's intended beneficiary role was excluded and Alice's parent relationship to Bob survived. Its evidence span differed from the approved span. Document authority, recency and explicit removal all point to the same outcome here. |
| Cross-source | The extractor combined both emails, attributed the two settlors and spouse to the first, and used the second email's addressee and “your son” for Alice's parent edge and Bob's beneficiary edge. All five edges had approved evidence. This shows success on complementary emails with local context. |
| Distractors | The five asserted edges survived. The solicitor and assistant acquired no trust role and Peter's future request produced no current beneficiary edge. |
| Proposals | The extractor excluded both the proposed trustee appointment for Margaret and the proposed beneficiary role for James. It nevertheless missed an asserted family fact embedded in the trustee proposal and generated an extra family edge from the list of children. Handling the proposed roles succeeded. Handling the whole passage was mixed. |
| Temporal | Rachel replaced David as current trustee, the former trustee was excluded, and all five unaffected earlier edges survived with their first-Source evidence. The trustee edge cited the correct second Source. Its exact quote failed approval. This fixture presents the effective change in chronological order. |

### All graph errors

Both errors were present in the raw **proposals** extraction. The provider returned eight candidates and the graph retained eight relationships. The raw sibling candidate named both children. No candidate mentioned Margaret, under her full name or an alias. The builder and scorer reproduced the output from those candidates with no resolver.

- **FN, one omitted assertion.** Expected `Gregory Ashby sibling_of Margaret Ashby`. No candidate asserted this edge. In `note_01` the approved evidence is “Mr. Ashby has also suggested that his sister, Margaret Ashby, should be appointed as a trustee in place of the current trustee.” The appointment is proposed, while “his sister” asserts the family relationship. Proposal wording is a plausible source of the omission. This single observation cannot isolate its cause.
- **FP, one unsupported inference.** The model emitted `Emma Ashby sibling_of James Ashby` with the exact `note_01` evidence “They have two children, Emma Ashby and James Ashby.” The sentence supplies shared-parent evidence. The fixture's asserted-edge policy does not derive sibling edges from common parents. This extra edge came from the current-position paragraph. It was independent of accepting a proposed appointment. [Fixture's bidirectional audit](https://github.com/alistairkung/private-client-graph/blob/3b579c96b8daa06285933a1efca17f2e41c23407/benchmark_v1/hallucination/dev/case_1/README.md)

### Both evidence failures

Workbench inspection located both predicted quotes verbatim in the original Sources (zero-based character offsets, end exclusive). Each cited the correct Source ID and supported the correct graph edge. Each failed the existing exact approved-quotation and Source/quote comparisons.

| Case and edge | Actual evidence | Approved evidence |
| --- | --- | --- |
| Authority, `Alice Chen parent_of Bob Chen` | `note_01[108:181]`: “Alice mentioned that she intends to leave everything to her son, Bob Chen” | `note_01[108:258]`: the full sentence, which continues “, and that Bob will be the primary beneficiary of the Evergreen Family Trust.” |
| Temporal, `Rachel Lim trustee_of Willow Family Trust` | `note_02[194:389]`: “Rachel Lim was appointed as replacement trustee with effect from 10 September 2026. The current position as at 15 September 2026 is that Rachel Lim is the sole trustee of the Willow Family Trust.” | Each of those two sentences is separately approved, at `[194:277]` and `[278:389]`. The model attached them together as one quote. |

These observations locate the discrepancies at evidence-span selection during extraction. We observed no wrong-document citation, fabricated quotation, endpoint naming error, or deterministic construction failure. They give no reason to add a Source router or enable a resolver. For evidence quality, an independent annotation review can assess whether these spans are sufficient before using this specific metric gap to motivate a prompt change. This baseline retains its original scores.

## Next experiment and limits

The smallest next experiment is a **matched proposal-scope control**. Keep the two children, the proposed appointment, the explicitly stated sister relationship and the graph fixed. Compare the original proposal sentence with a version that states the existing sister relationship in its own sentence before proposing appointment. Freeze the two versions with reviewed evidence, hold model, prompt, order and resolver settings fixed, and compare fresh paired runs. The primary decision is recovery of Gregory–Margaret. Track the forbidden trustee/beneficiary roles, the extra Emma–James edge, complete-graph scores and evidence separately. Improvement only when the family assertion is moved would support a proposal-scope explanation. A persistent extra sibling edge would point to a separate tendency to infer family relationships. This is a proposed development control for separate authorisation. [Diagnostic controls issue #174](https://github.com/alistairkung/private-client-graph/issues/174)

One execution per matter cannot measure stochastic reliability. Six short development fixtures cannot establish generalisation, and passing one fixture cannot establish robust handling of its axis. The related split and overlap with older cases further constrain interpretation. The Run supplies no evidence about whether RAG helps and contains no held-out final-evaluation results.

## Reproducibility and retained outputs

| Identity | Value |
| --- | --- |
| Named Experiment | `benchmark-v1-six-axis-baseline`, ID `c7eae3fb42735f97a80851d282109956` |
| Workbench Run | `724873665d0f5e7f839e1507fa3badfd` (first and only Run) |
| Plan SHA-256 | `9df8e798f18c833bb1cc980739707c199b2867bee14b7a45561a2b1598e34b16` |
| Workbench artifact digest | `40470f27ef74899d09ad4af20bd4a7e352b809ebd2cde47df1c2ddde667feb3c` |
| Owner-retained artifact root | `runs/benchmark-v1-six-axis-baseline/` in the original workspace, including the Experiment membership, immutable Run, task ledger and authorisation. The Run directory holds the manifest, requests/responses, fresh input snapshots, canonical states, Evidence, results, lifecycle and session records. |

The frozen case IDs below are the fixture lineages. Their Workbench input IDs append `_fixture`. The displayed Source and truth digests are prefixes of Workbench's SHA-256 of the source bundle plus compatibility text, and of the truth plus Source-specific approvals, respectively. Every ordered Source file, manifest, approval and ground-truth file was independently checked against its exact bytes at the execution commit before dispatch. Full digests, Source IDs, actual candidates, per-attempt usage and observation IDs are in [observations.json](observations.json).

| Case ID | Ordered Sources | Source digest | Truth digest |
| --- | --- | --- | --- |
| `benchmark_v1_aliases_dev_1` | note_01 | `bd8b93edce12` | `82338cc4c622` |
| `benchmark_v1_authority_dev_1` | note_01, note_02 | `150acc5ae8d8` | `d2f452d9998c` |
| `benchmark_v1_cross_source_dev_1` | note_01, note_02 | `0bfb5b25a768` | `00c22ca1ef7e` |
| `benchmark_v1_distractors_dev_1` | note_01 | `a0e687053af4` | `759bebb6758c` |
| `benchmark_v1_hallucination_dev_1` | note_01 | `ba7bdf096ee1` | `2e85f58deebd` |
| `benchmark_v1_temporal_dev_1` | note_01, note_02 | `c056f436468b` | `28bdb67fe53e` |

For offline inspection at the execution revision, point the Workbench at the retained artifact root and read `/api/research/v2/experiments/<experiment-id>/runs/<run-id>` and its `/observations/<observation-id>` children. The report was checked by reopening the bundle, matching each fresh candidate list to its original provider payload, and rebuilding each canonical state, graph and evaluation from that recorded payload using the frozen Sources. All six matched. This verification consumed zero further calls. [Workbench storage and inspection contract](https://github.com/alistairkung/private-client-graph/blob/3b579c96b8daa06285933a1efca17f2e41c23407/docs/workflows/persistent-research-workspaces.md)

To reproduce the six graph and evidence scores from the portable observations, run this from a checkout of the **execution commit**, setting `PCG_BASELINE_OBSERVATIONS` to an absolute path to the accompanying JSON file. This uses the actual retained candidates and makes zero model calls.

```sh
uv run --locked python - <<'PY'
import json
import os
from pathlib import Path
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.pipeline import Pipeline, PipelineConfig
from private_client_graph.research.retained_inputs import input_digests
from private_client_graph.research.source_attribution import diagnose_source_attribution
from private_client_graph.workbench.case_catalog import repository_inputs

records = json.loads(Path(os.environ["PCG_BASELINE_OBSERVATIONS"]).read_text())
fixtures = {sample.sample_id: sample for sample in repository_inputs()}
for row in records["observations"]:
    sample = fixtures[row["fixture_id"]]
    assert sample.case_id.endswith("_dev_1")
    for field in ("source_digest", "truth_digest"):
        assert input_digests(sample)[field] == row[field]
    actual = SourcedExtractionResult.model_validate(row["candidates"])
    output = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, actual)
    score = evaluate_graph(output.graph, sample.truth)
    attribution = diagnose_source_attribution(output.state, sample.truth, sample.source_evidence)
    assert score.model_dump(mode="json") == row["evaluation"]
    assert attribution.model_dump(mode="json") == row["source_attribution"]
    print(row["case_id"], score.tp, score.fp, score.fn, attribution.passed, attribution.assessed)
PY
```
