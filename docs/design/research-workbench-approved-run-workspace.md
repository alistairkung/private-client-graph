# Research Workbench: approved persistent Experiment workspace

Status: revised direction A approved by the user on 2026-10-12, including the final connector geometry and simplified Run copy. This records design approval; production implementation is a separate task.

## Approved interaction

An Experiment is a named persistent research workspace containing many independently configured, immutable Runs. The pipeline editor configures the next Run. Editing it preserves every previous Run and keeps the researcher in the same Experiment.

The primary **Run** button sits beside the pipeline editor. It is available for a valid executable draft, including a changed configuration or a repeated unchanged configuration. It opens review. Freeze, authorization where required, and start remain explicit controls in that flow. The permanent lifecycle caption and button ellipsis are removed; necessary guidance appears at the relevant step.

Completion adds a point to the same Experiment’s performance chart. Selecting a point opens that Run’s frozen configuration, input identities, provenance, cost, TP/FP/FN evaluation and exact Evidence below. Selection leaves the next-run draft intact. “Use as next draft” explicitly copies configuration without transferring execution authority.

Saved extraction and fresh extraction are input choices for a Run. They retain distinct comparison identities and cost coverage. The chart offers F1 by Run and F1 versus cost, with discrete points and honest exclusion of unavailable values.

## Visual source of truth

- [Approved interactive prototype](assets/research-workbench-approved-run-workspace.zip). Extract and serve the `performance-workbench` directory using a local static HTTP server; open `/workspace-runs/`. The archive’s earlier A/B/C exploration is historical; `/workspace-runs/` is the approved design.
- [Required future contract](research-workbench-experiment-run-contract.md), including lifecycle, immutable snapshots, migration and comparison limits.
- Review evidence and interaction checks are included in `workspace-runs/design-review.json` and `workspace-runs/review/` inside the archive.

![Approved desktop workspace](assets/research-workbench-run-workspace-desktop.png)

![Two Runs in the same Experiment](assets/research-workbench-run-workspace-comparison.png)

[Approved narrow layout](assets/research-workbench-run-workspace-mobile.png).

Retain the incumbent PCG typography, paper surfaces, ledger green and exact Evidence emphasis. Preserve the production pipeline’s supported nodes, inline settings, horizontal navigation and accessible insertion controls. The final prototype corrects the oversized connector: thin centered line, small arrowhead and centered insertion circle. Its simplified rendering is visual guidance, not a replacement component architecture.

Keep the default workspace concise. Do not reinstate explanatory model prose, redundant chart subtitles or the lifecycle caption alongside Run. Preserve actionable validation, authorization, coverage and error guidance. Prototype simulation labels distinguish illustrative data from real execution; they are not production interface copy.

## Implementation boundary

The current study-specific backend freezes an experiment plan and does not support adding independently configured Runs to a completed Experiment. Implementing this design requires the separately reviewed contract change above. Do not force users to create a new Experiment each time configuration changes, and do not imply the new model already exists in production.

Design approval does not authorize that backend change, production React work, paid executions or changes to extraction, identity, evaluation or provenance semantics. Preserve existing task-wide accounting and plan-bound authority. The approved separate lifecycle controls must be reconciled explicitly with the current atomic authorization/start API during future contract work.

The prototype demonstrates one input and one observation per Run. Multi-input aggregation remains undefined. Retained Issue #92 outcomes support the illustrations; simulated executions and chronology are not new measurements. Earlier approved workspace documents remain historical references where superseded here.

## Verification and review

The final prototype was checked at 1440px and 390px for changed and repeated configurations, separate authorization/start, immutable historical snapshots, draft preservation, keyboard Evidence inspection, cost exclusions and reload persistence. The finish review found no material issues. The final connector and copy refinements were included in the repeated workflow checks before approval.

Code Quality Review: this handoff changes documentation and isolated design assets only. Final review found no production changes or material readability concerns. Backend tests are not applicable to this approval record.
