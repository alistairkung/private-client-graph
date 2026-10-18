# Agent ecosystem audit and migration

Snapshot: 2026-10-19, base `86161561` on `origin/main`. Inventory covers tracked
files on that base plus the pending team integration noted below; personal
installations and other worktree contents are outside the versioned inventory. The
[team index](teams.md) is the live source of registered teams.

## Existing integrations

- Root [AGENTS.md](../../AGENTS.md) links shared code style, domain documentation
  and GitHub issue workflow. ADRs 0001–0011 govern product/domain decisions; this
  change preserves them, including [shared pipeline boundaries](../adr/0009-share-one-fixed-configurable-analysis-pipeline.md)
  and [public synthetic reads](../adr/0011-make-synthetic-matter-reads-public.md).
- Eleven tracked portable skills live in `.agents/skills/`: `code-review`,
  `domain-modeling`, `frontend-design`, `grill-with-docs`, `grilling`, `implement`,
  `implement-spec`, `setup-matt-pocock-skills`, `tdd`, `to-spec`, `to-tickets`.
  Ten have `agents/openai.yaml`; `frontend-design` has only the skill body and
  license. UI metadata is optional, so this difference needs no migration.
- `code-review` requests two parallel review axes. `implement` invokes that
  review skill; `implement-spec` explicitly dispatches subagents. These are
  reusable task procedures rather than persistent teams. Existing workflows remain intact, subject to the active
  task's root-owned budget and two-child cap. A delegated specialist cannot
  invoke a recursively delegating workflow without explicit authorization.
- [GitHub tracker guidance](issue-tracker.md) selects `gh`.
  [CI](../../.github/workflows/tests.yml) runs Python, browser and Docker checks;
  its Python suite now includes offline governance validation. The
  [PR template](../../.github/pull_request_template.md) already requires Code
  Quality Review.
- No tracked native `.codex/` team config, repository MCP definition, or registered
  team existed at the base revision. A task-specific
  [public Matter handoff](public-matter-access.md) describes historical team
  sequencing; it is not a reusable team definition.
- The original active checkout had uncommitted product work, an untracked Motion
  skill and locally installed ignored integrations. Personal skills/plugins may
  also appear in this session's catalogue. They are outside this versioned
  inventory and have been left untouched. No account MCP settings were copied.
- Open [PR #157](https://github.com/alistairkung/private-client-graph/pull/157)
  (`codex/practitioner-agent-team`) adds a practitioner workflow under
  `docs/agents/practitioner-next/` and seven native roles: `pcg_lead`,
  `pcg_explorer`, `pcg_implementer`, `pcg_engineering`, `pcg_ux`, `pcg_motion`,
  `pcg_visual_qa`. Its config sets root Sol/High, the same Luna/Low child fallback,
  two-child concurrency, depth one and Motion MCP servers. The lead role pins
  Sol/High. These are pending branch contents, not merged repository defaults.

## Findings and decisions

Three options were considered: only document team prompts; add native role TOMLs
beside the existing portable skills; or migrate skills into a new team tree.
Native roles plus a compact documentation contract provide runtime discovery
without disrupting skill entry points. A new orchestration framework or skills
migration would add maintenance without a demonstrated requirement.

The setup skill's GitHub/domain reference files overlap the generated repository
docs. Their role as setup templates differs from the repository's authoritative
policy, and no conflicting tracker selection was found. Keep both and link the
repo documents from teams; a future setup refresh should preserve repository
customizations. Ticket-writing skills mention `ready-for-agent`, while the short
repo tracker doc does not define label policy; the setup skill supplies a triage
reference. Actual GitHub label availability was not audited, so no missing label
or changed tracker behavior is asserted.

The historical public Matter handoff includes temporary paths, branch sequencing
and old test counts. Use current AGENTS/ADRs/workflows for policy. Historical
claims were not revalidated against GitHub and are not copied into team contracts.

## Incremental migration and deferred work

This change adds one shared standard, one reusable contract template, one team,
four native roles and economical shared defaults. Existing skills, aliases, MCP
servers and product workflows keep their locations and entry points. No domain
policy or extraction behavior changes.

Future teams register incrementally using the same contract. Ownership conflicts
are reviewed before registration; shared files get one task editor. Retire a role
only after finding references in team docs, skills and user workflows. Defer
rewriting vendor/setup skills, reconciling personal/plugin duplicates, archiving
historical handoffs and migrating unrelated teams until their owners request it.
These changes could affect working integrations and are unnecessary for discovery.

Before combining PR #157 with this standard, its owner should register a
`practitioner-next` contract linking the existing workflow, reuse its current
role IDs, and remove per-role model/effort pins in favor of lead selection. Review
all seven role files and resolve the shared config's add/add conflict explicitly;
retain required Motion integrations and compatible safety controls. Review its
additional agents-table keys against the installed runtime and extend the narrow
validator deliberately before combining them. The validator checks the shared
agents table, leaving other runtime settings to Codex's strict
parser. Native role files in both teams need registration under this standard.
This migration is intentionally deferred to that PR's review so this task does not
rewrite an active product branch or silently change its agent behavior.
