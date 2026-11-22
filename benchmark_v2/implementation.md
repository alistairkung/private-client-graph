# Offline admission and execution handoff

The design and the baseline configuration are frozen. The development roster has 14 conditions across ten declared family IDs. The six existing v1 IDs are historical development lineages; a count of IDs alone does not establish independence. The development content lock commits candidate bytes for review. All fourteen development conditions have completed admission. [Admission review and commitments](development-admission.md)

## Reproduce the offline check

From the repository root, use a new or empty local directory:

```sh
uv run --locked python -m benchmark_v2.preflight --artifacts runs/v2-dev-offline-review
```

The command verifies the pinned baseline files, lockfile, prompt and model settings, then checks the development package and annotation commitments. It freezes, executes and reopens all 14 saved ideals in one Workbench Run. D13 uses its existing package, case ID and Source order. The final JSON includes per-condition graph, Evidence and decision results, workload counts, digests, family lineage, the proposed fresh schedule and five Workbench draft configurations sharing a single 18-attempt cap. The artifact directory retains the Workbench Run, the targets and preflight.json. A nonempty destination is refused so an earlier review remains reproducible.

D7 and D8 use the original T0 and T3 packages from the pinned temporal revision. D9 supplies the same T3 bytes in reverse order. D12 and D13 share a three-Source file and the same complete semantic graph; the linked notice omits “of Seaforth Trust”. D14 contains 11 relationships across eight Sources. Seven Sources each supply unique facts. Its full-context estimate is **1,305 message tokens**, using 5,220 bytes at four UTF-8 bytes per token, rounded up. The estimate covers the sourced system and user message contents. Record actual tokens, including provider framing and schema, on a separately authorised run. [Composite evidence map](../benchmark_v1/composite/dev/case_1/README.md)

## Frozen joint-evidence policy

In D13, one Source establishes the appointment under a reference and another identifies the trust. The approved sufficient set requires both exact Source associations on the trustee edge. The ideal yields 3 TP, 0 FP, 0 FN and one complete jointly supported target. Under the frozen v2 reporting rule the trustee edge has N/A for ordinary quotation and Source attribution. The two settlor edges yield 2/2 ordinary quotations and 2/2 Source associations. The immutable raw scorer record retains its original 2/3 quotation result. D13 was admitted to the development corpus after independent human approval on 22 November 2026 and verification against revision `7d714ecd`. The Workbench loads the approved package as an opt-in development input and verifies the signed record and annotation commitments. [D13 signed disposition](reviews/D13.md). [Evidence policy, revision 1](evidence-policy-v1.md)

## Traced execution environment

The baseline pin in baseline.json records the historical lock. The traced execution lock from PR #192 has SHA-256 `b7f9674ec4252bb23651f56515b0e1f082083e6193df55a41b30c8543aee9795`. Comparing the two locks found twelve additional observability packages and identical records for every existing third-party package. The project package gained telemetry dependencies. Preflight checks the traced lock, all original scientific file pins, installed provider/scorer dependency versions, model settings and prompt. New Workbench bundles record the lock digest for the live baseline report.

A two-Source synthetic transport probe sent one request into an HTTP mock in each locked environment. Both request bodies, including ordered messages, the structured output schema, thinking and model parameters, had SHA-256 `20c4833ed423c7a8634872e3d0326f1722230866c34f9bae0f2aad5c31a3c6d7`. Both parsed the same response and used a 90-second timeout. Reproduce the combined-side comparison with the baseline transport test. The model provider was never contacted.

For the eventual synthetic research worker set `PCG_RESEARCH_LANGFUSE_ENABLED=1` and `PCG_RESEARCH_LANGFUSE_DETAILS=1` in the worker environment and supply the existing Langfuse credentials. The default is opt-in and metadata-only. The transport adapter disables LangSmith tracing around the model invocation. [Workbench tracing settings](../research/README.md#optional-langfuse-tracing)

Run preflight on the clean execution revision. Use its five exact proposed Workbench configurations for freezing. Compare the resulting ordered inputs, settings, Run plan digests, allocation and task-ledger identity before dispatch. A general-purpose Workbench draft can describe other experiments.

## Budget handoff

Workbench retains the original semantic-review marker and its hash on the five newly approved packages. Live planning verifies the recorded human disposition for each exact reviewed package and annotation. Historical snapshots carrying only a pending marker remain ineligible.

The proposed development ceiling is **18 attempted calls**. Use fresh, full context, the pinned model and settings, resolver none, one extraction per selected input, no retries and a single shared task allowance. The printed sequence gives the exact order: D1–D7, then three successive two-condition Runs of D8 and D9 in that order, then D10–D14. This keeps both temporal orders adjacent within each repetition. Count failures and retain their slots. Preflight is entirely offline. Historical output and ideal replays do not fill fresh slots.

Reserve eight attempted calls after final configuration freeze. The custodian releases four reviewed packages only at that gate. Capture provider fingerprint, usage, latency, and priced or unpriced cost per arm and Matter. A multi-call final arm requires a revised budget before access. The private custody path belongs to the project owner outside the Workbench catalog. See the [frozen protocols](README.md).

## Offline review outcome

Across the 14 development conditions the saved ideals recover all 68 expected edges with zero FP and FN. V2 ordinary quotations pass on all 67 eligible edges, and all 67 eligible Source associations pass. One joint-only target has N/A for both ordinary measures. The D12 and D13 target attachments each satisfy their predeclared sufficient set. Independent review confirmed the authority pair's date-only difference, the masked two-endpoint ambiguity and the composite evidence map. These are preparation checks. The fresh baseline has 18 planned slots and zero scored Observations.

The final cohort has its own semantic and custody review, including the joint-evidence review and separate ordinary versus supplemental evidence replays where a final case has both. The supplemental replay inspects the reviewability of an authored witness set. For a fresh Observation, score the single actual graph and its own attached Evidence once under each applicable diagnostic. [Retained-run reporting](reporting.md)

## Private final Run intake after release

1. Before opening any final package, commit the final architecture, exact settings, prompts, dependencies, scorer versions and costed stage counts. Record the architecture commitment beside the original baseline pin. The final **Run** digests come later because they include private inputs.
2. Once the four packages have human admission, the custodian checks the sealed package hashes in a private evaluation environment. Use isolated checkouts of the baseline and final revisions with each revision running its local Research Workbench against the same private artifact root and authorised task ledger. Keep the private working directories and artifacts outside shared development storage and remote branches.
3. In each private checkout, materialise the same approved Source packages using the existing opt-in catalog convention, e.g. evaluation_cases/heldout_v2_h1 through heldout_v2_h4. Supply the reviewed sources.json, original Source bytes, complete truth, ordinary Source approvals, compatibility text and both ideals. Give each wrapper a metadata.json whose id equals its directory name. Record wrapper identity, ordered-input, truth and ideal digests against the original private package commitment. The custodian must verify both checkouts produce identical input_digests before freezing either Run. The private joint-only case requires its own admission review and intake at release.
4. Freeze one fresh Workbench Run per family per arm. Bind the eight plan digests and custody-owned DecisionTargets to the final report manifest. Execute in the predeclared family/arm order under the approved task budget. The reporting command consumes the resulting private Runs. Actual private intake, live execution and the final report belong to the future release gate.

Only candidate digests and review status are committed publicly. The project owner retains the complete private files and review records in the ignored runs/benchmark-v2-custody directory of the original checkout. Preserve a custody-controlled backup before moving or removing that checkout. [Final candidate commitments](held-out-status.json)
