# Preliminary suite inventory

Audit base: `39fe75b6ad9791725c601a48edd6ad40aa6970ff`, collected 2026-10-19.
Scope: tracked pytest, normal/research Vitest suites and all four Playwright
configurations run by `.github/workflows/tests.yml`. Unmerged feature branches,
including PR 167, are excluded. No tests or assertions change in this setup.

## Classification catalogue

[Application CSV](application-inventory.csv) enumerates 49 definition locations
and 114 configured cases across 15 files. [Research CSV](research-inventory.csv)
enumerates 17 locations and 51 configured cases: history 6/18, execution 9/27,
substituted-live 2/6. Total: **66 logical groups, 165 configured browser cases**.
Each row identifies the exact source definition line; loop titles/locale variants
and viewport projects are grouped explicitly, with their expanded case count.
Configured includes intentional run-time skips and opt-in recordings. Discovery
reporters label unexecuted cases skipped; those labels are not execution results.

| Class | Meaning | Groups | Configured cases |
| --- | --- | ---: | ---: |
| 1 | Retain as critical E2E; lower-layer assertions may supplement it | 49 | 122 |
| 2 | Proposed component replacement; preserve stated browser boundary | 4 | 9 |
| 3 | Proposed API/integration replacement; retain relevant user journey | 2 | 4 |
| 4 | Proposed focused unit replacement | 0 | 0 |
| 5 | Proposed consolidation, subject to unique-assertion mapping | 0 | 0 |
| 6 | Retain pending analysis, including mixed groups and recordings | 11 | 30 |

No class 4 or 5 retirement candidate is established: deterministic calculations
already have lower-layer tests, and apparent journey overlap has unique
assertions still needing analysis. These counts are not a deletion target.

CSV fields cover protected behaviour, current cost, proposed replacement, risk,
retained boundary and validation evidence. A path to a current lower-layer test
is supporting evidence, not proof of equivalence. Proposed new tests are labelled.
No test is retired or approved for retirement by its classification. Real layout,
scroll, motion and focus guarantees cannot be proved with jsdom alone.

## Baselines and interpretation

The [local baseline](baseline.json) records commands, runtime versions, workers,
counts, wall times and summed case times. The [lower-layer file inventory](lower-layer-inventory.csv)
enumerates all 58 pytest modules and 46 Vitest files with counts and observed
summed case durations. Vitest includes both pure functions and React behaviours;
pytest includes domain, API, persistence, research and workbench tests.

| Local suite | Collected | Passed | Existing skips | Command wall |
| --- | ---: | ---: | ---: | ---: |
| pytest, including PostgreSQL and 21 governance checks | 760 | 760 | 0 | 110.263s |
| Frontend unit/component | 160 | 160 | 0 | 3.727s |
| Research unit/component | 26 | 26 | 0 | 1.826s |
| Application browser | 114 | 104 | 10 | 97.577s |
| Research history browser | 18 | 16 | 2 | 7.663s |
| Research execution browser | 27 | 27 | 0 | 129.899s |
| Substituted-live research browser | 6 | 6 | 0 | 49.989s |

Both frontend builds passed (3.535s normal, 3.025s research), separately from
browser command time. Tests ran sequentially by suite on macOS ARM with warm
dependencies, Python 3.11.17 and Node 26.10.0; CI uses Ubuntu/Node 22. Do not treat
local and CI times as directly comparable. Browser CSV costs sum each group's
project/parameter case durations; concurrent workers make those sums different
from command wall time. Server startup is included in command time but not
separately isolated or attributed to a group. The baseline also retains pytest's
25 slowest call/setup/teardown phases. PostgreSQL fixtures create, migrate and
drop a database per test for isolation (`tests/persistence/conftest.py`); some
reported setup phases take roughly 0.4–0.7s. No safe fixture-sharing change is
established by that observation.

The 12 browser skips comprise four opt-in recording cases, six
application-project/viewport exclusions and two non-narrow history focus cases.
They are existing conditions; setup added none. Initial restricted launches and
an environment-mismatched application attempt are disclosed in `baseline.json`.
After resyncing and explicitly pinning the audited Python source path, the
unchanged application suite passed on a fresh server. That controlled final run
supplies the measurements; the earlier failures are not labelled flaky. No real
model provider was invoked, including the suite named “live”.

[CI observations](ci-observations.md) and
[raw bounded CI metadata](ci-history.json) distinguish workflow wall time,
concurrent job time and sequential step time. One successful main workflow took
9m24s; its browser job took 9m14s, including 5m21s across the three research steps.
This suggests investigating research execution/setup as well as UI repetitions;
it does not justify removing mission-critical research journeys.

The 20-run CI sample has 19 successes and one contrast assertion failure, all on
distinct revisions and attempt 1. No same-revision rerun evidence establishes
flakiness. Failed setup launches and intentional skips are reported separately
from assertion failures. Existing workflow installs/builds once per browser job,
but starts the research server/index separately for each invocation. Repeated
fixtures/navigation within tests may be intentional isolation; measure before
sharing mutable state or combining sessions.

This is a behavioural source audit and preliminary classification, not a measured
line/branch-coverage assessment or a promise of a smaller suite. Existing unit,
component and integration capabilities are assessed in [the policy](test-policy.md).
Critical protections and a bounded first candidate are in [the plan](migration-plan.md).
