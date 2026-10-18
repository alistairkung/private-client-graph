# Setup coordination evidence

Base: `39fe75b6` on 2026-10-19. Setup uses the existing shared team contract and
configuration from merged PR 168. The root integrates the department as the
Agent Systems Architecture assignment; no second agent system is introduced.

## Allocation ledger

Choices below use this session's active `collaboration.spawn_agent` catalogue,
not a permanent list embedded in QA policy. It describes Luna as affordable for
simpler work and Sol as a coding workhorse; numeric relative prices are not
exposed. Both requested effort values are supported by their selected model.

| Task | Role | Complexity and judgment | Requested model / effort | Rationale |
| --- | --- | --- | --- | --- |
| Application E2E inventory and provisional layer classification | `qa_suite_analyst` | Bounded source inspection; moderate ambiguity in separating assertions from cross-boundary journeys | `gpt-6-luna` / Medium | Economical specialist for a fixed source set; root and independent reviewer assess critical-risk decisions |
| Research-suite inventory, CI history and setup metrics | `qa_performance_analyst` | Mechanical collection and bounded factual history; uncertainty must be marked | `gpt-6-luna` / Low | Primarily extraction/counting; no authority to infer coverage equivalence or flakiness |
| Resume bounded CI history collection with approved network access | `qa_performance_analyst` | Same factual extraction; the initial network restriction is resolved | Existing child, requested `gpt-6-luna` / Low retained | Reuse its context and ownership; no fresh agent or higher effort is warranted |
| Refine application classifications against actual browser-only assertions | `qa_suite_analyst` | Moderate coverage judgment within the same bounded source set | Existing child, requested `gpt-6-luna` / Medium retained | Correct broad preliminary recommendations before independent review; reuse source context |
| Independent consequential department/policy/coverage review | `qa_coverage_reviewer` | Security/provenance and replacement-equivalence judgment across the complete setup diff | `gpt-6.1-sol` / High | Catalogue workhorse capability and High effort justified for independent architectural review; no exceptional effort or repeated review invocation |

At most two children run concurrently; each receives the exact role instructions,
disjoint report ownership and a no-delegation limit. The root owns policy, native
roles, report integration and the final plan. Independent review is allocated
later against the actual consequential diff, after inventory integration.

## Runtime observations and budget

Native role selection is not exposed by this desktop tool. The supported fallback
supplies `developer_instructions` verbatim in each task, with `fork_turns: none`
and explicit model/effort arguments. An accepted spawn proves the request was
accepted, not the child's effective configuration. Effective model/effort and
coordination billing are unobservable on this surface; a child's self-report is
not verification. No separate paid CLI inference is needed to paper over that
limit. Official guidance: [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

Application-provider invocations attempted for setup: **0**. No live extraction
or evaluation experiment is authorised by this setup task. Hosting-runtime agent
coordination is separate and its internal request count/cost is not exposed.

## Observed outcomes

Both inventory children completed their assigned reports. Their source locations
were reconciled with collection; initial broad component recommendations were
refined to retain browser geometry, motion, focus and recovery guarantees. The
CI analyst resumed after approved read-only network access, collecting 20 runs
and one failed log. No third child ran concurrently with these two.

The independent reviewer completed one read-only invocation using the exact
`qa_coverage_reviewer` instructions. It found unsupported consolidation of a
Matter search/reload group, two mixed public-research classifications, a configured
case/skip denominator error and stale CI access wording. The root corrected all
five evidence issues. No test change or equivalence proof was claimed. Review of
local timing integration and the final complete diff is the root's gate.

The accepted prompt-fallback spawns and returned reports demonstrate usable
delegation with explicit task choices. Native TOML loading and effective child
model/effort remain unverified. CLI `0.162.1` and the existing offline validator
also accepted the current catalogue and unchanged fallback pair without inference.

Local validation: full `uv run pytest` with disposable PostgreSQL passed **760**
tests with zero skips, including 21 existing governance checks. Normal/research
Vitest passed **160/26** tests; both builds passed. Four unchanged Playwright
commands passed **153** cases with **12 existing skips**. The CSV/collection
reconciliation found no missing, extra or miscounted groups. See `baseline.json`
for timings, environment and initial-launch limitations. No tests, skips,
assertions, dependencies, workflow gates or application sources were edited.

The root inspected the complete final change set after validation. It clarified
truncated risk descriptions, normalised CSV line endings, checked numeric
denominators and local links, and verified that only the QA roles/reports and
team registration are included. No material readability concern remains; the
separate evidence files keep the reusable policy short. Replacement equivalence,
native role loading and long-term flakiness remain explicitly unproven.
