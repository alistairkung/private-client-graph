# Practitioner-next agent workflow

Use this workflow for the independent practitioner frontend in `practitioner-next/`.
The existing `web/` frontend, backend, domain, database, existing tests and
deployment are read-only references. Both frontends use the existing API.

## Launch and configuration

Start a fresh trusted Codex session in the repository. Project settings in
`.codex/config.toml` select GPT-6.1 Sol/high for the root and cap open child
threads at two. Standalone `.codex/agents/*.toml` files define named specialists.
Use `pcg_lead` instructions for the root, not a delegated second lead. Explicit
UI or invocation overrides can supersede project defaults: check the selected
root model and effort before starting. Keep the user's permission policy.

| Specialist | Model / effort | Deliverable |
| --- | --- | --- |
| `pcg_lead` | GPT-6.1 Sol / high | Sequence, decisions, integration, draft PR |
| `pcg_explorer` | GPT-6 Luna / low | Bounded functional/API inventory |
| `pcg_ux` | GPT-6.1 Sol / medium | Selected UX direction and tokens |
| `pcg_motion` | GPT-6.1 Sol / medium | Source-backed motion specification |
| `pcg_implementer` | GPT-6.1 Sol / medium | Working vertical slice and tests |
| `pcg_visual_qa` | GPT-6 Luna / low | Up to three evidenced defects |
| `pcg_engineering` | GPT-6.1 Sol / high, on demand | Final full-diff review |

These are model choices from the installed account catalog, not price promises.
Luna is described there as fast and affordable; Sol is the workhorse. If a model
is unavailable, inspect `model/list` and select a supported economical model;
record the substitution rather than silently inheriting the root model.

Clients exposing custom agent types should spawn by the exact role name. A
client exposing only generic delegation must use a fresh context, explicitly
pass the role's model/effort, and instruct the child to read its TOML file. Record
that fallback; a task name alone does not load a custom agent. Never infer actual
model execution from a child's self-report. Prefer effective runtime metadata.

## Sequence and handoffs

Every assignment supplies: goal, bounded file/route inputs, output contract,
owned write paths (or read-only), model/effort, stop condition and shared budget.
Return: result, exact references, decisions, validation/evidence, unresolved
risks and usage. Keep ordinary handoffs under 500 words; link larger artifacts.

1. **Explore.** Trace practitioner entry points, all supported workflows and
   public API/auth/error contracts. Return a parity matrix and relevant test
   references. Reuse this inventory across the team; do not repeat a repo scan.
2. **Direct.** UX consumes the matrix and product/brief context. Use the local
   frontend-design skill and Impeccable's context workflow. Choose one experience
   and record flows, tokens, responsive structure and state/accessibility needs.
   Existing styling is evidence, not a template. Preserve product truth.
3. **Choreograph.** Motion consumes that direction, searches at most three
   targeted concepts and reads at most two actual premium source resources.
   Return implementation references, trigger/property/timing and reduced-motion
   behaviour. Authentication is via the parent Motion+ MCP connection; no token
   belongs in the repository. Follow the Motion skill if source is unavailable.
4. **Implement.** One writer builds complete slices in `practitioner-next/`,
   including state/error handling and meaningful parity tests. The lead may own
   a disjoint integration slice. No competing implementations. Use new component
   structure and design choices; preserve the backend's workflow/semantics.
5. **Inspect.** Visual QA uses the running app at desktop and phone widths,
   keyboard navigation and reduced-motion settings. Return the three defects
   with the greatest task/legibility/accessibility impact, with evidence.
6. **Refine.** The same implementer fixes that batch, reruns focused checks and
   returns to the reviewer. Default to one inspection and one confirmation;
   three cycles per surface is an absolute user-authorised ceiling. Count
   screenshots, micro-edits and rebuilds within the same cycle, not fresh loops.
7. **Verify.** Engineering reviews the complete diff and parity evidence once.
   The lead resolves material findings, runs repository-required validation and
   performs CODE_STYLE.md's final-diff self-review gate.
8. **Hand back.** Open a draft PR with Code Quality Review, local results,
   parity/evidence links, limitations and CI status. Do not merge, deploy or wait
   solely for CI. Investigate any known failure before calling the work ready.

## Budget and escalation

- At most two child threads open; one active writer. Reuse a specialist's context
  for adjacent follow-ups, and release/close finished threads when supported.
- Only the root delegates. Installed CLI configuration also sets `max_depth = 1`
  to stop child delegation; confirm it through effective configuration after
  upgrades. Children also prohibit nested Codex processes in their instructions.
- Bound reads to the supplied files and necessary direct dependencies. Stop
  research when the deliverable is implementable; avoid duplicate inventories.
- Start mechanical inventory and QA on Luna/low; design/motion/implementation
  on Sol/medium. Escalate once only after recording a concrete failed cheaper
  attempt, the missing capability and a bounded next task. Use Sol/high for a
  difficult consequential decision or final review. Subagent xhigh/max/ultra
  requires explicit user authorisation; do not request it for routine work.
- Maintain one shared task ledger in the verification report: delegation
  attempts, escalations, visual cycles, Motion lookups and paid pipeline calls.
  Count failures and retries. Follow AGENTS.md's five-call default for paid
  application-provider checks; no live calls are required for UI parity tests.
  Codex delegation uses account usage separately; this is not a credit meter.
- The two-thread cap is enforced by Codex configuration where loaded. Tool
  allowlists, read-only reviewer roles, reasoning ceilings and refinement limits
  are instructions, not claimed per-agent security controls. Child agents inherit
  parent permissions/MCP connections. No invented credit/token budget feature.

## Tools and reproducibility

- Read `.agents/skills/frontend-design/SKILL.md` for design reasoning.
- Existing local Impeccable: `.agents/skills/impeccable/SKILL.md`,
  `.impeccable/config.json`, PRODUCT.md and DESIGN.md. Follow its context loader;
  do not repair tool/context drift or rewrite existing design files incidentally.
  Record the new app's design within `practitioner-next/` instead.
- Motion skill: `.agents/skills/motion/SKILL.md` when installed; Motion+ MCP
  source search and resource reads are available after account sign-in. This
  locally installed skill is not bundled by this setup. If absent, use the
  official Motion AI Kit installer separately. No premium runtime dependency is
  needed just to research source; install one only when a selected pattern needs it.
- Browser: use available CUA/browser tooling for real state/screenshots. The
  standalone app's Playwright tests provide reproducible desktop/mobile,
  keyboard and reduced-motion checks and evidence capture. Do not claim a runtime
  MotionScore audit without access to its methodology and profiling tools.
- Deterministic tests substitute the stochastic model boundary, keeping real
  API orchestration and graph construction wherever practical. Label any isolated
  UI fixtures and supplement them with unchanged-backend integration checks.

## Capability sources

Verified against installed Codex CLI 0.162.1, its generated app-server schema,
`config/read`, `model/list` and a strict app-server startup on 2026-10-18.
Current [custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes standalone TOML role files and inherited permissions. The
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents the concurrency cap; the
[app-server protocol](https://learn.chatgpt.com/docs/app-server) exposes effective
configuration and model discovery. Revalidate after an incompatible CLI upgrade.

See [verification.md](verification.md) for actual smoke results and limitations,
and [launch-prompt.md](launch-prompt.md) for the next session's starting prompt.
