---
status: accepted
---

# Keep research artifacts authoritative behind an isolated workbench

The local Research Workbench uses immutable filesystem artifacts and task ledgers as its authority, retaining all non-derivable state, including authorizations; PostgreSQL is a disposable, rebuildable index. This preserves the existing research runner's paid-call durability and reproducibility guarantees rather than migrating spending authority into the database. A separate local research API and React + TypeScript application consume the Shared Analysis Pipeline and existing evaluators through explicit, versioned contracts, without exposing research execution through the practitioner application.

## Consequences

- Historical imports are read-only and never confer execution authority. Retain artifacts and ledgers together; a database backup alone is insufficient.
- One locally supervised experiment runs at a time and survives browser closure. Service restarts require explicit continuation; uncertain attempts remain counted and are never automatically reissued.
- Live approval binds a frozen plan digest and bounded call allowance to a task-wide budget shared across experiments. Plan changes invalidate approval; a new bundle never resets accounting.
- Baseline and treatment share each extraction across resolver repetitions. Extraction variability is separate, and historical comparisons disclose different configurations, code versions and unmatched inputs.
- Read-only research composition must exclude execution endpoints and provider access, enabling a future separately approved public Research Lab without exposing paid controls.
- React consumes research contracts rather than implementing evaluation, metric calculation or provider-call accounting. Real cases drive deliberate contract evolution and regression tests; no speculative registry is introduced.
- Backend work can be authorized independently. React implementation requires a separately approved Impeccable design and must follow it. Architecture acceptance does not authorize implementation or paid experiments.

This extends the research surface while preserving ADRs 0001, 0003 and 0009 and all protected semantic contracts. See the [design handoff](../design/research-workbench.md) for the three delivery slices and acceptance criteria.
