# Benchmark v3 Evaluation Protocol v1

**Frozen for independent review on 24 November 2026.** Applies to the 19 admitted non-giant development families and all 34 admitted conditions. The protocol ID is `benchmark_v3_evaluation_v1`. The benchmark commitment is the SHA-256 of the exact private admission register, `c864f58786d21fd3f5b9735023c93df62256e537133f15fa602d3cf3d8d13b70`. The [public admission register](admissions/2026-11-24.json) commits to the private register and lists the exact family revisions and manifests. Family V is deferred.

## 1. Units and frozen commitments

- A **condition** is the smallest planned observation. It receives one prediction or an explicit unavailable outcome. Freeze the ordered Sources, exact key and condition membership before dispatch. The admitted key includes semantic truth, eligible ordinary quotations and their Source IDs, and approved sufficient-evidence alternatives.
- A **family** is one independent documentary history. Its natural and matched conditions stay in that family and contribute once each to its pooled counts. Families with multiple conditions receive the same macro weight as single-condition families. Preserve the natural/matched labels and predeclared deltas. Never count the matched siblings as independent evidence of generalization.
- A **run** commits to the protocol version, benchmark digest, ordered family and condition roster with Source and key commitments, split, scorer policies, and observation origin. Commit the exact code and dependency versions, prompt and schema digests, model and effective settings, paid-call authorization and immutable per-condition attempt and prediction artifacts. Log provider request and response provenance, token usage and latency separately from the score.
- Frozen components are cohort membership, Sources, keys, ontology, canonical construction and validation, scorers and denominator rules. Experimental components must be identified before execution. Their exact treatment and permitted differences are part of the pre-registration. Variants inside a family change only their already-admitted documentary contrast; an experimental extraction treatment runs against the same Sources for each condition.

## 2. Graph metrics and failure denominators

Use the protected semantic-edge scorer `semantic_edges_v1`. It compares exact endpoint names and predicate. The scorer normalizes only symmetric edge order, retains direction for directed edges, and counts each unique semantic edge once in its condition. Extra nodes without relationships do not affect edge equality. Report the following metrics with their integer counts.

| Metric | Definition |
| --- | --- |
| All-condition micro-F1 | Pool TP, FP and FN over the complete planned roster, then calculate 2TP/(2TP + FP + FN). |
| All-condition family-macro F1 | Pool counts within each family, compute its F1, and take the arithmetic mean across all 19 planned families. |
| Exact-graph accuracy | Validly delivered graphs with FP = FN = 0 divided by all 34 planned conditions. |
| Construction-success rate | Validly delivered graphs divided by all planned conditions. Graph correctness is reported separately. |
| Valid-graph-only metrics | Supplemental counts, micro-F1, family-macro F1 and exact-graph accuracy restricted to delivered valid graphs. List their exact denominators and the number of contributing families. |

Every condition with no valid graph contributes zero delivered edges. It contributes zero TP and FP and one FN for each expected semantic edge. It fails exact-graph accuracy and construction success, including when its expected graph is empty. A successfully constructed empty graph is a delivered graph. It is exact only if the expected graph has zero edges. The protected F1 zero-denominator convention is 0. An undefined valid-graph-only metric is reported as unavailable, including for a family that delivered no graph.

Maintain these distinct terminal condition outcomes:

- **Scored graph.** Report graph errors as scored extra and missed edges, regardless of the proof outcome.
- **Validation failure.** A parsed prediction was rejected by the canonical validator. Record the cause and preserve the complete prediction. Do not salvage, correct or process a subset for score.
- **Provider failure.** A provider attempt returned a transport/API error without a usable prediction. Any attempt still counts against budget.
- **Parse failure.** A provider response was received but could not be decoded into the agreed prediction contract.
- **Uncertain.** Dispatch was reserved but its outcome could not be verified. Count the reservation and preserve it without reissuing in the same run.
- **Not attempted.** No attempt was made for this planned condition. It remains in the denominator. Report an interrupted matrix as incomplete.

Artifact integrity failures, truth errors and unexpected scorer errors block publication. They cannot be converted into a model failure or dropped from scope. Preserve exact provider and parser failure counts as well as the all-condition FN contribution. Condition outcomes and evidence outcomes answer different questions.

## 3. Evidence metrics

Use `benchmark_v2_evidence_v1`, `source_attribution_v1` and `attached_sufficient_set_v1` on the retained CanonicalState. Each annotated target is one planned sufficient-evidence target. It receives one credit only when all exact `(Source ID, verbatim quotation)` members of **one approved alternative** are attached to the same correct semantic edge. Repeated candidate rows may supply different members. Pool the attachments on that edge through canonical construction. Quotes from different alternatives qualify only if the attachments contain an entire approved alternative. For joint-only targets, every approved alternative uses multiple Sources. A member found elsewhere or attached to another edge gives no credit.

Report overall completed targets / all planned targets and joint-only completed targets / all planned joint-only targets. Keep separate counts for complete proof, incomplete proof on a recovered edge, missed edge in a scored graph, and target in a condition without a valid graph. The last three categories receive zero completion credit. A failed condition contributes all its annotated targets to the denominator. If there are no planned targets in a reporting slice, the rate is unavailable.

Report approved quotation passes / eligible true-positive edges assessed and approved Source/quotation passes / eligible true-positive attachments assessed. Joint-only targets are exempt from ordinary quotation and attribution. Report an empty ordinary denominator as unavailable. The legacy single-Source provenance field from the graph scorer remains a diagnostic. Its denominator and meaning differ from the protected joint-proof metric. A semantically plausible unapproved span requires a separate review and does not change the official score.

## 4. Controlled comparisons and sealed evaluation

A paired comparison has the same frozen condition roster in both arms, including every condition with unavailable output. Declare the treatment, parameters, exact prompt/schema hashes, construction and scorer versions, arm schedule, retries, paid limit, hypotheses and selection criteria before dispatch. Compare condition by condition and report family-block summaries and matched-condition graph deltas. Aggregate differences over all planned conditions. Disclose any incomplete matrix, provider drift, or non-preregistered departure and qualify or stop the causal comparison.

Use the protocol scope guard before presenting scores as comparable. Agreement on protocol, cohort commitments and live observation origin is necessary. It does not verify causal isolation. Confirm the design’s backend versions, permitted arm differences and effective settings independently. The unit for uncertainty or resampling is the family, with matched siblings and both treatment arms kept together. One trial per condition supports a bounded development comparison with limited information on repeatability.

Sealed evaluation requires separate owner approval, a separate verified cohort and custody, and a fixed extractor configuration and scoring protocol approved before any sealed access. No tuning on sealed results, answer-key access by extraction, substitution of development cases, or mixing sealed and development metrics. Report a separate held-out result with its own commitment and denominators. The current protocol adapter covers the admitted development baseline only.

## 5. Audit and reproduced live baseline

The [existing Workbench aggregate](../private_client_graph/workbench/run_evaluation.py) includes only scored observations in graph F1. The protected graph scorer continues to score a valid graph against a key. Canonical construction continues to reject a condition with invalid evidence or inconsistent entity types as a unit. The [protected joint scorer](replay_evidence.py) evaluates a valid state and reports proof targets missed on that state. It has no valid state to score for failed conditions. Protocol v1 supplies the planned denominators and no-delivery accounting as a separate evaluation layer. It preserves the valid-graph-only results and does not modify either protected scorer, graph construction or the archived baseline.

The baseline used `deepseek-flash` with thinking disabled, the original full-context prompt and one call per condition, no resolver and no retries. The retained configuration SHA-256 is `5a53dd1f3e80da5c9cce3702498db40bd12b3ea731c0c7a1562c8b222b86e03d`. The immutable archive inventory SHA-256 is `b41242bd7bcfec25c09396b197f887441e11dccc0dff3aa920017fc6c18cdbab`. The [offline adapter](retained_evaluation.py) verifies the inventory, admitted key and ordered Sources, original request and normalized raw tool arguments, parsed prediction, retained graph score and scorer/construction code before rebuilding scores. The underlying predictions are from live receipts. No new model execution is involved.

| Result | Protocol v1 all conditions | Supplemental valid graphs |
| --- | --- | --- |
| Conditions contributing | 34 | 30 |
| TP / FP / FN | 91 / 10 / 22 | 91 / 10 / 5 |
| Micro-F1 | 182/214 = 0.8504672897196262 | 182/197 = 0.9238578680203046 |
| Family-macro F1 | 0.8307504873294347 across 19 | 0.9044634377967712 across 18 |
| Exact graphs | 20/34 | 20/30 |
| All sufficient evidence | 18/71 | 18/67 |
| Joint-only evidence | 0/30 | 0/28 |

Construction success is 30/34. All 34 attempts returned parsed responses. A0, B1 and AZ000 failed cross-candidate type validation. C2 failed verbatim quotation validation. The failed conditions account for 17 expected edges, four planned proofs and two planned joint-only proofs. Proof outcomes are 18 complete, 44 incomplete, five missed and four without a graph. Ordinary quotation is 23/66 and Source attribution is 23/74 on their eligible valid-graph denominators. The baseline had zero provider or parse failures, uncertain reservations or unattempted conditions. The retained receipts report 85,651 input tokens, including 35,968 cached tokens, and 10,248 output tokens. The original tariff-based cost estimate was US$0.027418308. Protocol v1 leaves that accounting separate from delivery and evidence scores.

The opt-in test reads the owner-only archive and runs real graph and evidence code. The normal tests use synthetic cases without private predictions or keys. To reproduce from a checkout:

~~~sh
PCG_V3_PRIVATE_BASELINE_CUSTODY=/absolute/path/to/private/benchmark-v3 \
  uv run python -m pytest tests/research/test_v3_evaluation_protocol.py
~~~

## 6. Separate experiment release

The [paired-experiment pre-registration](planning/experiments/PROOF-COMPLETENESS-v1.md) freezes the proof-only treatment and a 68-attempt matrix. It records methodology and a proposed cap. Execution, provider binding and budget authorization require a separate release.
