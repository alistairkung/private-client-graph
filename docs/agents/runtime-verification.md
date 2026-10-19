# Runtime compatibility and delegation smoke

Run this procedure when introducing a team or changing model controls. Offline
validation remains separate from optional inference. See the
[allocation policy](teams.md#orchestrator-owned-capability-allocation).

## Verified surfaces

On 2026-10-19, the installed executable reported **codex-cli 0.162.1**.
Its help exposes `--model`, `-c key=value`, `--strict-config`, `debug models`,
`debug prompt-input`, and app-server schema generation. The installed app-server's
strict `config/read` accepted the project's `[agents]` defaults and reported
`max_concurrent_threads_per_session = 2`, `default_subagent_model = gpt-6-luna`,
and `default_subagent_reasoning_effort = low` from the project layer.
No inference was needed for these checks. `--strict-config` is not supported by
`codex debug`; use a supported command such as app-server for strict parsing.

[Official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
defines standalone `.codex/agents/*.toml` files with `name`, `description`, and
`developer_instructions`. It documents explicit spawn settings, shared defaults,
and role-file precedence. Our roles omit model/effort so they cannot pin capability
above a task's selection. Parent permission/provider/MCP settings remain inherited.
Prompt-only read-only/no-recursion instructions are not sandbox enforcement.

The current desktop `collaboration.spawn_agent` exposes `model` and
`reasoning_effort`, and requires `fork_turns = "none"` for overrides. Full-history
forks inherit parent settings and reject overrides. It lacks a named-role selector;
read the role TOML and include its instructions explicitly. Its status listing
returns task names/status, not independently verified child model/effort. Its
session capacity is four total agents, so the lead must enforce the stricter
repository limit of two children. File config alone does not change this surface.

## Reproducible smoke procedure

1. Run `codex --version`; inspect the active spawn tool schema. On the CLI run
   `codex debug models > /tmp/pcg-models.json`, then
   `uv run python tools/validate_agent_teams.py --catalogue /tmp/pcg-models.json`.
   This checks the current fallback pair without paid inference. On another
   surface use its catalogue. Keep runtime controls and catalogue source together.
2. Give the orchestrator a bounded read-only task: “List tracked agent skills and
   distinguish repository config from personal installs.” It identifies
   `conventions_auditor`, reads that role, records low ambiguity/mechanical
   discovery, and selects the least expensive capable available model at Low.
   Record the choice before spawn and charge any live experiments to the shared
   task allowance.
3. Spawn once through the available tool, passing both selected values and the
   role instructions, worktree, output contract and no-delegation limit. For this
   desktop schema the fields are `task_name`, `fork_turns: "none"`, `model`,
   `reasoning_effort`, `message`. These are tool arguments, not TOML fields. Use
   the actual current schema; do not invent a named-role field.
4. Wait for completion and check the bounded output against files. If exposed,
   inspect child runtime metadata for model and effort, and compare with the
   request. Record mismatch/fallback explicitly. If only a task ID/status or a
   model self-report is available, mark effective settings **unobservable**.
5. Report role, selection rationale, requested settings, spawn result, observed
   settings and unsupported controls. Native-role execution needs a native
   selector smoke on a surface exposing one; do not claim that prompt inspection
   or a generic tool spawn proved native role loading.

## Establishment smoke evidence

The root orchestrator selected Repository Conventions Auditor for the inventory,
requested `gpt-6-luna` / `low`, and invoked `collaboration.spawn_agent` with
`fork_turns = "none"`. It returned `/root/conventions_audit`; the completed result
listed skills, policy pointers and instruction-overlap findings with paths.
A separate bounded systems design check selected the same model at `medium`,
showing task-based reasoning allocation. Both tasks finished read-only, with no
recursive delegation or overlap in edit ownership. At most two children ran.

These first two tasks preceded creation of the native role files and received
self-contained role prompts. They demonstrate delegation-time selection; they do
not establish native TOML loading. Child effective model/effort was not independently
observable from spawn/status results. Child acknowledgments were not treated as
verification. Native CLI role execution remains an explicitly unverified control
on this desktop surface; the documented supported prompt fallback is usable here.

Task ledger: three coordination agents were used: audit, systems design, and
independent engineering review. The review selected `gpt-6.1-sol` / `high` for
consequential runtime compatibility and enforcement claims, using the new
reviewer role instructions explicitly. Relative prices and the hosting runtime
request count were not observable; selection used catalogue capability/cost
descriptions rather than a claimed measured price minimum. No extraction or
other paid application-provider invocation was attempted. Coordination is billed
by the hosting runtime; its internal request count/cost is not exposed here and
must not be presented as a measured provider-call count. No extra paid CLI smoke
was launched merely to verify what this session could not observe.

## Final validation

The offline validator passed against both repository conventions and the current
CLI catalogue. The final full run (`uv run --no-sync pytest`, using the existing
locked development environment) passed **552 tests**, including **21 governance
checks**; **208 PostgreSQL-dependent tests skipped** because `TEST_DATABASE_URL`
was unset. The initial complete-diff independent engineering review found no
material correctness, readability or repository-boundary problems. Final review
clarified pending practitioner-team migration, kept unrelated MCP settings outside
the validator's scope, and wrapped dense validation/test expressions. The complete
final diff is reviewed again after those changes; final test counts and PR/CI
status are recorded in the PR handoff. Native role execution and child effective
configuration remain outside the evidence available in this session.
