# Synthetic held-out evaluation inputs

These ten independently selected Benchmark Cases are separate from development
Cases 01–05 under `cases/`. They exercise supported Person/Trust relationships
with narrow, documented variations. They are a small controlled synthetic set,
not evidence of performance on real practitioner documents.

| Input | Primary variation | Current edges | Sources |
| --- | --- | ---: | ---: |
| heldout_01 | Confirmation-letter genre | 5 | 1 |
| heldout_02 | Four relationships in one sentence | 4 | 1 |
| heldout_03 | Explicit personal short form | 3 | 1 |
| heldout_04 | Cross-source corroboration and repeated quote | 3 | 2 |
| heldout_05 | Completed trustee replacement | 4 | 2 |
| heldout_06 | Temporal order differs from supplied order | 3 | 2 |
| heldout_07 | Two trusts with different role allocations | 6 | 1 |
| heldout_08 | Distinct Sources with matching display titles | 5 | 2 |
| heldout_09 | Administrative distractors and extra named contacts | 3 | 1 |
| heldout_10 | Unambiguous local pronoun | 3 | 1 |

Total: 39 current semantic edges over 14 Sources. Each directory contains a
complete legacy answer key/ideal extraction plus ordered Source manifest,
source-aware evidence approvals, source-attributed ideal extraction and explicit
CanonicalState expectation. Answer-key entity IDs are annotations, never model
input. `source.txt` is a compatibility view, not Source identity authority.

`source_evidence.json` version 1 contains `relationships`, each keyed by the
answer key's `source`, `type`, `target`, with `approved_evidence` objects containing
`source_id` and exact `supporting_text`. This adds attribution approval without
changing legacy approved-quote scoring. The ideal may select several approved
supports; model success does not require exhaustive corroboration. Supplied
support from separate Sources must retain those distinct identities.

These files contain authored expectations, not recorded model results. All
paid provider calls during authoring: zero. Independent validators must inspect
both answer-key-to-source support and source-to-answer-key completeness, record
uncertainties, and recheck fixes. The user must approve the benchmark before
held-out execution. Current authoring checks do not constitute that approval.

After user approval, freeze the dataset digests and final chain before running
the held-out set once under the common task budget. Do not tune the chain or
quietly revise truth in response to held-out results. Flag a genuine benchmark
defect for explicit review. Keep development results, held-out results and
authored ideal scores clearly distinguished.
