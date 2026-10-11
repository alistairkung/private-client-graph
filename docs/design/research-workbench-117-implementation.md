# Research Workbench implementation — Issue 117

Implements the approved revised A in [the workspace handoff](research-workbench-approved-run-workspace.md), using the merged Issue 116 versioned API. The design and backend contracts remain authoritative.

## Verified workflow

Create a named Experiment, configure its next Run Draft, review and freeze, authorize where required, and start. Change or repeat configuration to append another immutable Run. Select its chart point to inspect frozen configuration, observation evaluation and exact Evidence. Explicitly copying a historical configuration creates the next draft without copying execution authority.

The shared input-mode filter filters whole Runs on both charts; React does not recompute metrics or cost. Stable Run numbers retain gaps when a historical Run cannot load. Provisional coverage, cost exclusions and comparison scope come from the backend.

The sidebar retains its wide-screen collapse preference and becomes a focus-trapped drawer below 760px. On narrow screens relationship selection moves focus into Evidence; Back returns to the selected relationship.

## Captured implementation

These deterministic browser captures show retained synthetic observations, not paid live evaluation. Desktop capture includes explicit missing-artifact sidebar records retained in the disposable test index; these are intentional recovery states.

- [Desktop, 1440px](assets/research-workbench-117-desktop.png)
- [Mobile, 390px](assets/research-workbench-117-mobile.png)

## Review and validation

The Impeccable finish reviewer scored all three material findings resolved: shared chart input-mode filter, mobile Evidence focus/return, and stable Run numbering under partial loading failure. Final disposition: ship at that review scope. The documenter checked the finished components, styles, captures, PRODUCT.md and DESIGN.md and preserved the incumbent visual system. Pre-existing sidecar omissions remain unchanged.

Deterministic validation includes research unit tests, real-backend execution/authorization browser tests at three widths, retained Issue 92 history/Evidence regressions, frontend type/build checks and the repository Python suite. Paid provider calls: zero.
