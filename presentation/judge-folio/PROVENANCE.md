# Claims and visual provenance

Repository base: `d5130917b32ba03e41d6345a8c3d604f4c906432` (merged PR #160).
Discovery and deployed-page inspection: 18 October 2026, Asia/Hong_Kong.
No paid provider calls or production mutations were performed.

## Source hierarchy

The authoritative measured outcomes are in
`private_client_graph/published/research-results.v1.json`, snapshot
`final-heldout-a-aprime-b-v1`. The publication workflow describes verification
against the owner-retained experiment package. This task does not publish private
raw provider communications, operational records or personal decision logs.

| Claim | Source | Qualification |
| --- | --- | --- |
| Private-client solicitors/advisers review family and trust relationships | PRODUCT.md; GLOSSARY.md; issue #16 | Intended user and workflow hypothesis, not measured adoption |
| Private Wealth submission category | Author's explicit instruction, 18 October 2026 | Category framing; not a claim of customer adoption or advice quality |
| Source-specific exact Evidence; explicit whole-proposal acceptance | ADRs 0001, 0005, 0006; current README | Mechanical validity does not imply professional acceptance |
| Multi-PDF intake and application configuration | README; PRs #130 and #138 | Older PRODUCT prose is partially stale; current code/README govern multi-source support |
| Public synthetic reading, protected shared-state actions | ADR 0011; PR #159 | Authentication is not real-client readiness or Matter tenancy |
| Twenty progressively difficult scenario hypotheses | cases/README.md, Case progression | A research roadmap, not twenty executed treatments or validated capabilities; only development Cases 01-05 authored |
| Case-led development method | Author's explicit clarification in this task, 18 October 2026; cases/README; evaluation_cases/README; research/README | Case hypothesis, development sample and ground truth, separate held-out set, measure/plot in Workbench, surrounding application support |
| Hackathon establishes baseline plus constrained resolver | Author's scope clarification; research/README current configuration menu; published A/A-prime/B comparison | Does not imply the wider twenty-scenario programme is complete |
| 10 held-out cases, 14 Sources, 39 expected relationships | Published JSON benchmark; evaluation_cases/README.md | Small project-authored synthetic set |
| Ground truth checked separately from case authoring | research/final-day/validation/batch-01.md and batch-02.md | Separate AI validators; no external human/institutional validation claim |
| A and A-prime: TP37, FP2, FN2; micro-F1 94.87% | Published JSON runs A and A_prime | Macro-F1 is different: 93.33% |
| B: TP39, FP0, FN0; micro-F1 100% | Published JSON run B | Relationship metric only; not production accuracy |
| Two Bea-to-Beatrice Ng endpoint corrections in heldout_03 | Published JSON case edits and source | One person, two relationships; quotations unchanged |
| Resolver edits endpoints only and preserves relationship count, types, directions and quotations | `private_client_graph/resolution.py`; published edits | Replacement names must occur in Sources or existing endpoints; identity judgment remains model-driven |
| No relationship-score regressions in other nine cases | Published JSON case observations | All nine already scored 100% relationship F1 |
| Approved quotes 36/39; Source/quote pairs 37/41 under B | Published JSON B metrics | Separate populations; strict approved-span policy can reject supporting shorter quotes |
| B adds 10 resolver calls, 9,821 tokens | Published JSON B usage | 9,432 input plus 389 output; cached tokens are included; dollar cost unpriced |
| A-prime is exact zero-call replay; B reuses extraction | Published JSON pairing; publication workflow | A-prime and B share code identity; not independent replication |

The historical benchmark validation README predates execution and retains pending
approval language. Use it to describe authoring, not current execution status.
The publicly verified retained publication governs the final results.

## Visual assets in the finished folio

| Asset | Origin and handling |
| --- | --- |
| Cover relationship/quote diagram | Editorial vector rendering of the exact Case 01 parent relationship and quotation; not an application screenshot |
| Product relationship graph and highlighted Source detail | `docs/artifacts/ui-consolidation/practitioner-evidence-desktop.png`; current production build captured locally with synthetic fixtures, substituted Google/model boundaries and disposable database; see adjacent README and PR #160 |
| Historical intake and whole-proposal confirmation | `presentation/product-demo/public/captures/en-intake-files-page.png` and `en-confirmation-page.png`; authentic local authenticated workflow before PR #160 visual consolidation. Synthetic PDFs; substituted Google and model boundaries; real PDF parsing, graph, confirmation and persistence paths. See `presentation/product-demo/PROVENANCE.md` and merged PR #155 |
| Multi-source Hillcrest evidence | `docs/artifacts/ui-consolidation/curated-multiple-sources-desktop.png`; current UI local capture from authored Case 04, explicitly an ideal fixture rather than a model outcome or accepted Matter |
| `assets/production-research-chart.jpg` | Actual production research page captured through browser UI at `/research-results#comparison` on 18 October 2026; original screenshot bytes retained; PDF clips to the chart including its full 0-1 scale |
| Case-level chart, endpoint correction and quote-boundary figures | Vector editorial figures derived from the immutable publication JSON at build time; not product screenshots or new model executions |
| Public Sans and Newsreader Display | Existing project fonts in `web/src/styles/fonts/`; license records in `presentation/product-demo/public/fonts/`; converted for PDF embedding, not visually redesigned |
| Noto Sans SC and Noto Serif SC | Existing licensed Simplified Chinese WOFF2 fonts in `presentation/product-demo/public/fonts/`; converted and subset-embedded |

The shared Workbench chart is shown in the public retained-results experience.
It is not a new experiment or a manually redrawn metric graphic. Image clipping
removes surrounding interface chrome only; no chart values, marks, graph facts,
quotation words or highlights are changed.

## Editorial and translation review

Four independent agent reviewers simulated two technical and two Private Wealth
industry judges, calibrated to a university hackathon. Their suggestions and
implemented revisions are in `PANEL_REVIEW.md`; these are not actual judge
endorsements or an official competition rubric. The full Chinese edition uses
reviewed Simplified Chinese copy. Exact Source quotations, proper names and
authentic screenshot pixels retain the original English, with Chinese captions.
No experimental observations are generated by the translation process.

## Source links

- [Current product/repository](https://github.com/alistairkung/private-client-graph)
- [Verified production application](https://private-client-graph-production.up.railway.app/)
- [Verified retained research](https://private-client-graph-production.up.railway.app/research-results)
- [Prior twelve-slide proposal, closed PR #153](https://github.com/alistairkung/private-client-graph/pull/153)
- [Research publication, merged PR #152](https://github.com/alistairkung/private-client-graph/pull/152)
- [Current visual consolidation, merged PR #160](https://github.com/alistairkung/private-client-graph/pull/160)

The prior proposal and Evidence Folio comp are design references, not current
product screenshots. The historical product-demo lifecycle captures retain their
older-UI and deterministic-model-substitution qualifications in the PDF.
