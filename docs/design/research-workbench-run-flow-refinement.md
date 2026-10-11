# Approved Run flow refinement

Follow-up to [Issue 117 implementation](research-workbench-117-implementation.md), approved after local review. Preserves the existing Experiment/Run contracts and visual system.

## Behavior

- Run opens a native modal with a compact server-provided summary and a persistent action footer. The body scrolls independently. Detailed input identities, limits and provenance remain available within review.
- Freeze, required authorization and start are distinct backend operations. A frozen Run can be reopened; dismissing review never starts or cancels it. Authorization retained in the current mounted controller remains tied to its existing invocation. Reloading or switching execution targets requires review again; no authority is copied.
- Execution and evaluation selection are separate. The execution strip and frozen/authorization/start dialogs name their stable Run number. Freezing another Run preserves the selected historical evaluation; the first Run becomes selected when no earlier result exists.
- Chart activation replaces the single evaluation panel, focuses it and scrolls smoothly into view. Reduced-motion preferences use instant scrolling. Hover and focus alone do not scroll. Re-activating the selected point also brings its evaluation into view.
- Remove case/input accordions from the chart. Keep compact scope/coverage disclosure, eligibility exclusions, and complete frozen metadata in Run details and observation inspection.
- Replace the insertion popup with one compact Add generative resolver option. Escape or outside click dismisses it. Expanded pipeline nodes, all existing settings, collapse and removal remain unchanged.

## Captured implementation

Deterministic synthetic replay; no paid provider calls. Missing sidebar records in the disposable test index are explicit recovery states.

- [Desktop review](assets/research-flow-review-desktop.png) / [mobile review](assets/research-flow-review-mobile.png)
- [Desktop frozen Run](assets/research-flow-start-desktop.png) / [mobile frozen Run](assets/research-flow-start-mobile.png)
- [Desktop insertion menu](assets/research-flow-insert-desktop.png) / [mobile insertion menu](assets/research-flow-insert-mobile.png)
- [Desktop workspace](assets/research-flow-workspace-desktop.png) / [mobile workspace](assets/research-flow-workspace-mobile.png)

Regression coverage includes modal focus containment/return, visible footer, frozen review dismissal/reopening, separate authorization/start, unchanged expanded resolver fields, repeated immutable Runs, different execution/evaluation targets, and chart activation into one evaluation panel.

Impeccable finish review cleared the explicit Run-label correction. System documentation review preserved the incumbent design records and identified an obsolete rail-height override, which was removed. The compact menu footprint and full narrow-screen visibility are covered by browser assertions.
