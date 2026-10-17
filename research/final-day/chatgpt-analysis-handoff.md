# Private Client Graph — final held-out evaluation and analysis handoff

## A. Experiment identity

- **Experiment:** Final held-out benchmark — naive full-context baseline.
- **Experiment ID:** `83b5778e74ba5e6e882d334fd4f87f09`.
- **Run:** 1; **Run ID:** `97d26d8e5f9d5964826b144c9ca45ad7`.
- **Frozen Git commit:** `8ad73b00f44013f454ae166175d974f11f2e129d`; the recorded checkout was clean.
- **Model requested and returned:** `deepseek-flash`. Temperature unspecified/provider default; timeout 90 seconds; thinking disabled; automatic retries zero.
- **Pipeline:** one structured-output extraction invocation per case, all its Sources together in their original order; resolver `none`; one sample and one repetition; deterministic canonical construction and unchanged evaluation afterward. The prompt explicitly describes Source attribution, explicit identity links and current-state temporal rules. “Naive” means this single full-context invocation, not an instruction-free model.
- **Frozen dataset:** `heldout_01`–`heldout_10`, 14 Sources, 39 expected semantic relationships. All 132 reviewed artifact digests verified unchanged. Workbench scope identity: `a860c038af1edfcdb1070e9ede02b1ee2b4ecd29a125e328ca2a02dad173e74f`.
- **Frozen plan digest:** `6d1897fb89793649aca6064f253eb96106342a7c7c378b983bdb25fecb5f830e`.
- **Source-aware prompt SHA-256:** `d67afaeb19c26448a6779d9576800cc50ca399c634ad81a1a02b847be0a9dfae`.
- **Execution:** created, configured, frozen, authorized, started and inspected through the actual Research Workbench browser. No development cases, model substitutes, resolver calls, automatic retries or second Run were used. Retained provider requests contain Source text/identities and model settings, not ground truth or expected extraction.
- **Time:** 17 October 2026, 14:35:49.977–14:36:05.526 Hong Kong time; 15.548 seconds elapsed across attempts; summed provider latency 15.446 seconds.
- **Budget:** 10 attempted calls consumed out of the shared ceiling of 30; 20 slots remain numerically, but no further execution is authorized. This invocation has no remaining calls.
- **Authoritative artifacts:** `/Users/alistair/projects/private-client-graph/runs/final-day/97d26d8e5f9d5964826b144c9ca45ad7/`, retained with the shared ledger and Experiment records. A checksum-verified 73-file task snapshot also exists.

## B. Aggregate results

| Measure | Actual result |
|---|---:|
| Cases planned / attempted / completed / scored | 10 / 10 / 10 / 10 |
| Failed / uncertain / unscored cases | 0 / 0 / 0 |
| TP / FP / FN | 37 / 2 / 2 |
| Micro precision / recall / F1 | 0.948718 / 0.948718 / 0.948718 |
| Macro F1, equal weight per case | 0.933333 |
| Exact approved-quote provenance, TP-weighted | 34/37 = 91.89% |
| Approved Source/quote-pair diagnostic | 35/39 = 89.74% |
| Cases with perfect relationship F1 | 9/10 |
| Evaluation coverage | 100% |
| Input / output tokens | 10,501 / 2,642 |
| Input + output total | 13,143 |
| Cached input tokens, subset of input | 5,760 |
| Verified USD cost | Unavailable; all 10 attempts unpriced |

The TP/FP/FN and per-case scores are the retained evaluator results; Run micro-F1 is supplied by the existing Workbench aggregate. Micro precision/recall are arithmetic reductions of its recorded counts using the unchanged evaluator formulas. Macro F1 uses the existing descriptive-statistics helper over the ten recorded case F1 scores. TP-weighted provenance sums the recorded approved-quote pass/fail counts. These reductions do not rescore or change any observation.

**Important denominators:** quotation provenance passes a true-positive edge when at least one predicted quote exactly equals an approved alternative. Source attribution assesses each attached Evidence association on true-positive edges against an approved **(Source ID, exact quote)** pair. It therefore also penalizes quotation-boundary differences; it is not a pure wrong-document rate and does not assess the false-positive edges.

Token usage is retained for all ten attempts. Pricing was not frozen, so cost remains unknown. The UI's USD 0.0000 **known subtotal** is not evidence that the Run was free.

## C. Per-case results

“Source attribution” below means the existing strict Source/quote-pair diagnostic.

| Case | Hypothesis | TP | FP | FN | F1 | Provenance | Source attribution | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| heldout_01 | Recover family/trust facts from a confirmation letter | 5 | 0 | 0 | 1.000 | 5/5, 100% | 5/5, 100% | Completed/scored |
| heldout_02 | Decompose a dense sentence into distinct relationships | 4 | 0 | 0 | 1.000 | 1/4, 25% | 1/4, 25% | Completed/scored |
| heldout_03 | Link an explicitly introduced short form to its named person | 1 | 2 | 2 | 0.333 | 1/1, 100% | 1/1, 100% | Completed/scored |
| heldout_04 | Combine complementary notes and pool repeated support | 3 | 0 | 0 | 1.000 | 3/3, 100% | 3/4, 75% | Completed/scored |
| heldout_05 | Replace a trustee while retaining unchanged earlier facts | 4 | 0 | 0 | 1.000 | 4/4, 100% | 4/4, 100% | Completed/scored |
| heldout_06 | Respect effective chronology when the older document is last | 3 | 0 | 0 | 1.000 | 3/3, 100% | 4/4, 100% | Completed/scored |
| heldout_07 | Keep role allocations separate across two trusts | 6 | 0 | 0 | 1.000 | 6/6, 100% | 6/6, 100% | Completed/scored |
| heldout_08 | Preserve distinct Sources with identical display titles | 5 | 0 | 0 | 1.000 | 5/5, 100% | 5/5, 100% | Completed/scored |
| heldout_09 | Exclude administrative participants and unstated links | 3 | 0 | 0 | 1.000 | 3/3, 100% | 3/3, 100% | Completed/scored |
| heldout_10 | Resolve an unambiguous local pronoun across role statements | 3 | 0 | 0 | 1.000 | 3/3, 100% | 3/3, 100% | Completed/scored |

Case 03's 100% provenance concerns its **one matched edge only**; it does not mean its overall extraction was correct.

## D. Detailed failure analysis

### 1. Case 03 — explicit identity link not consolidated

The original `interview` Source states:

> Beatrice Ng attended the factual interview and asked to be called Bea. In this note, Bea means Beatrice Ng; no second person is being introduced.

| Expected relationship | Actual model relationship | Exact model-selected evidence | Source | Classification |
|---|---|---|---|---|
| Beatrice Ng → parent_of → Isaac Ng | Bea → parent_of → Isaac Ng | “Bea is the parent of Isaac Ng.” | `interview` | Entity identity; one FP plus one FN |
| Beatrice Ng → settlor_of → Larch Family Trust | Bea → settlor_of → Larch Family Trust | “Bea is the settlor of the Larch Family Trust.” | `interview` | Entity identity; one FP plus one FN |

Both quotes are exact documentary statements and support the intended roles. The error is the canonical endpoint name: the single-call baseline retained the short form despite the explicit equivalence. With no resolver and exact-name evaluation, these become two extra “Bea” edges and two missing “Beatrice Ng” edges. The Isaac Ng beneficiary edge matched. This is not evidence that the model invented two unsupported roles, nor a temporal or operational failure. The output consistently uses Bea; it does not create separate Bea and Beatrice people. Consequently this result establishes a canonical-label mismatch, not proof that the model misunderstood their equivalence. The sourced prompt permits explicit identity links but does not separately mandate full-name output, which is a possible task/scoring alignment confounder. Neither prompt nor answer key was changed.

### 2. Case 02 — three valid relationships fail strict quotation matching

The approved full documentary quotation in Source `recap` is:

> Felix Wong is the settlor of the Amber Family Trust, and Grace Wong and Hugo Wong are siblings and are both beneficiaries of the Amber Family Trust.

For the following three correctly extracted relationships, the model instead selected this exact shorter substring from the same Source:

> Grace Wong and Hugo Wong are siblings and are both beneficiaries of the Amber Family Trust.

| Expected relationship | Actual relationship | Model Source | Official failure |
|---|---|---|---|
| Grace Wong → sibling_of → Hugo Wong | Same relationship | `recap` | Approved-quote provenance and approved Source/quote pair |
| Grace Wong → beneficiary_of → Amber Family Trust | Same relationship | `recap` | Approved-quote provenance and approved Source/quote pair |
| Hugo Wong → beneficiary_of → Amber Family Trust | Same relationship | `recap` | Approved-quote provenance and approved Source/quote pair |

**Classification:** provenance / quotation-boundary mismatch. The selected substring supports all three relationships and occurs verbatim in the correct document, but is not an exact approved quotation. Thus relationship F1 is 1.000 while provenance and pair accuracy are 0.250. This interpretation does not revise the official failures. The model selected the approved full sentence for Felix Wong's settlor edge, which passed.

### 3. Case 04 — one correct Source, longer supporting quotation

Expected and actual relationship: **Keira Chan → beneficiary_of → Maple Family Trust**.

Approved evidence in Source `followup`:

> Keira Chan is a beneficiary of the Maple Family Trust.

Actual model-selected evidence from that same Source:

> The beneficiary position was checked again: Keira Chan is a beneficiary of the Maple Family Trust.

**Classification:** strict Source/quote-pair mismatch, not an observed wrong-Source assignment. The model used a longer exact documentary span containing the approved clause. It also retained the exact approved beneficiary quote from Source `initial`, so edge-level quotation provenance passed; one of four assessed Evidence associations failed the strict pair diagnostic. The two notes were correctly combined into one beneficiary relationship with two Source-distinct Evidence items.

These account for all two FP edges, two FN edges, three failed quotation-provenance edges and four failed Source/quote associations. No provider, parse, structural-validation or evaluation failure was recorded.

## E. Findings

### Observations

1. **Current-state interpretation worked in the two explicit temporal cases.** Case 05 retained Nora Tse as current trustee and omitted superseded Oscar Lee, while preserving earlier settlor/parent/beneficiary facts. Case 06 retained Rita Yuen and omitted Samuel Lok even though the older note was supplied last. Both had perfect relationship F1.
2. **Multi-document aggregation and explicit Source identity worked on these examples.** Case 04 combined complementary facts and pooled repeated beneficiary support. Case 08 preserved distinct `family`/`trust` Sources despite matching display titles and recovered all five expected relationships. All four multi-Source cases had perfect relationship F1.
3. **Several local semantic tasks succeeded.** Dense-sentence decomposition in Case 02, trust-role separation in Case 07, administrative-noise exclusion in Case 09 and local pronouns in Case 10 all achieved perfect relationship F1.

### Weaknesses and interpretations

1. **Canonical endpoint naming did not match the answer key in Case 03.** The roles were recovered consistently under Bea despite the direct identity statement. This may reflect output-name policy alignment rather than failure to understand the equivalence; the experiment does not distinguish those explanations.
2. **Quoted-span selection varied from the approved evidence granularity.** A shorter valid span in Case 02 and a longer valid span in Case 04 lowered strict evidence scores. These scores measure conformity to approved quotations as well as documentary support.
3. **Measurement and study coverage limit the conclusions.** The attribution diagnostic mixes Source identity and exact-quote conformity, and its denominator excludes FP/FN edges. This single-model, single-Run study contains ten short, explicit synthetic cases and no comparison arm or repetition. It does not establish a real-client error rate, stochastic reliability, superiority over another architecture, or the benefit of adding a resolver.

It is noteworthy that explicit temporal replacement and reversed document chronology succeeded while the explicit alias link failed. That is an observation, not evidence that temporal reasoning is generally solved or that a particular new component is warranted. No prompt, fixture, answer key, metric or architecture was changed after seeing results.

## F. References

- **Workbench Experiment/Run:** http://127.0.0.1:8080/#workspace=83b5778e74ba5e6e882d334fd4f87f09&run=97d26d8e5f9d5964826b144c9ca45ad7
- **Persistent task root:** `/Users/alistair/projects/private-client-graph/runs/final-day/`.
- **Immutable Run:** `97d26d8e5f9d5964826b144c9ca45ad7/` under that root; contains `manifest.json`, execution bindings, authorizations, ten started/finished attempt pairs, raw tool responses, parsed extractions, fresh input snapshots and ten canonical/evaluation results.
- **Complete task snapshot:** `analysis/final-task-artifacts.zip` under that root. Includes the Run, shared ledger, Experiment/draft/membership and approval/preflight records; all 73 files were checksum-verified. This is a filesystem snapshot, not a claim of compatibility with the older legacy-only export/import format.
- **Shared ledger:** `task-ledgers/live-2be8e54d4832420cbfbd05a55d966aef/` plus `live-task.json` under that root. Preserve it with the Run; PostgreSQL is only a rebuildable index.
- **Machine-readable results:** `research/final-day/final-heldout-results.json` and `per-case-results.csv` in branch `codex/final-heldout-evaluation`.
- **Workbench projection and full relationship diagnostics:** `research/final-day/workbench-run.json` and `relationship-diagnostics.json`.
- **Screenshots:** `research/final-day/screenshots/`: frozen configuration, aggregate results, upper/lower per-case table, Case 03 alias failure and exact Source, Case 02 strict provenance failure, Case 04 multi-Source evidence, execution identities and explicitly unpriced cost/attempt record. All depict the actual Run. Numeric Source-pair totals are in the JSON export; no new UI was fabricated to display them.
- **Representative raw extractions:** `attempts/heldout_02_fixture_fresh_01-extraction.finished.json`, `heldout_03_fixture_fresh_01-extraction.finished.json`, and `heldout_04_fixture_fresh_01-extraction.finished.json` inside the immutable Run.
- **Representative canonical/evaluation records:** the corresponding `results/heldout_XX_fixture_fresh_01-noop.json` files. They include exact Evidence, Sources, official errors and attribution diagnostics.

These local references supplement the report; the scores, original failure quotations, actual model behavior and relevant caveats are included above so discussion does not require opening each file. The final deck was not updated, no PR was merged and nothing was deployed.

## G. Questions for collaborative analysis

1. How should we present the distinction between exact approved-quote conformity and semantically sufficient documentary support, given Cases 02 and 04, without retrospectively changing this evaluation?
2. Does Case 03 justify a separate resolver, or indicate an underspecified full-name output convention, and what preregistered comparison on new cases would distinguish those explanations?
3. How much might the short, explicit synthetic prose and strong temporal instructions explain the successful replacement/chronology results compared with messier real documents?
4. How should we describe Source attribution when the current diagnostic assesses approved Source/quote pairs only on matched edges, rather than pure document correctness across all predictions?
5. What future evidence would be needed to distinguish stable baseline capability from model/sample variability before investing in additional architectural sophistication?
