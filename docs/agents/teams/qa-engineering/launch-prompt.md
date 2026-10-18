# Next-task launch prompt

This is a proposed implementation brief, not authorisation to start migration.
The human should approve one named slice from the plan before sending it.

> Act as the QA Architect under `docs/agents/teams/qa-engineering.md` and the shared
> team standard. Read the inventory, baseline, testing policy, migration plan and
> coordination evidence in its adjacent directory. Work only on this explicitly
> authorised slice: **[human names the slice and behaviour]**.
>
> Refresh main and create a feature branch under repository rules. Reconcile the
> selected inventory rows against the current suite, because this audit is pinned
> to `39fe75b6` and excludes unmerged branches. Re-establish a comparable baseline
> before editing tests. Resolve remaining evidence gaps for the chosen slice.
>
> Record workload, active model catalogue, cost evidence and the least costly
> likely reliable model/reasoning pair separately for each delegation. Follow
> shared effort approvals, concurrency and one-editor-per-path limits. Use the
> existing native roles or the documented verbatim-instruction prompt fallback;
> distinguish accepted settings from observable effective settings. Feature teams
> retain ownership of their tests; QA is not a new mandatory approval gate.
>
> Add meaningful replacement assertions while the existing browser assertions
> remain. Identify each failure mode and demonstrate that a temporary controlled
> regression makes its replacement fail; restore and verify the clean state.
> Preserve the real browser smoke for the selected integration boundary. Obtain
> independent coverage review, resolve evidence gaps, and only then remove the
> precisely superseded assertions within this approved slice. Retain anything
> whose equivalence is uncertain.
>
> Keep authentication/authorization, proposal confirmation/discard and uncertain
> mutation recovery, canonical identity, exact Evidence-to-Source provenance,
> multi-source review and research/evaluation boundaries protected. Preserve
> deterministic model substitution. Do not change domain contracts, benchmark
> truth, skips, retries or CI gates; do not introduce paid experiments or process
> non-synthetic Matter information. Broader changes require separate scope.
>
> Run focused checks plus `uv run pytest` and relevant web checks. Compare counts,
> wall time, summed test time, setup and retained failure detection on comparable
> before/after runs; do not target a numerical deletion count. Complete the full
> diff self-review, include `Code Quality Review`, and open a PR. Report local
> results, known CI failures and pending required checks without waiting solely
> for CI or merging automatically. Hand back the completed slice; do not launch
> another migration phase.
