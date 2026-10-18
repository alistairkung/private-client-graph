# CI baseline observations

## Evidence boundary

This report is pinned to revision `39fe75b6ad9791725c601a48edd6ad40aa6970ff` on branch `codex/qa-engineering-department`, collected 2026-10-19. The requested sample is the 20 most recent completed `Tests` runs from GitHub Actions (`gh run list --workflow Tests --limit 20`): 19 success and 1 failure, all attempt 1, with 20 distinct head SHAs. The window is short (2026-10-18 14:48–17:30 UTC, about 2h43m), so it is a small, activity-biased sample rather than a long-term reliability rate. Each run's ID, branch, SHA, event, timestamps, URL, attempt and conclusion is recorded in `ci-history.json`.

The latest complete successful `main` run is 39149906958, SHA `39fe75b6ad9791725c601a48edd6ad40aa6970ff`, attempt 1, created 2026-10-18 17:30:34 UTC and completed 17:39:58 UTC. It passed all required jobs. Its workflow wall interval was 564 seconds. Jobs ran concurrently: browser-e2e 554s, python 244s, docker-smoke 94s, and required-check aggregator 4s. Their sum (896s) is aggregate runner-job time, not workflow elapsed time. Per-job steps and timestamps are recorded in the JSON report; step times are derived from GitHub Actions timestamps rounded to seconds.

One bounded failed-run log was inspected: run 39149927229, branch `codex/tactile-relationship-invitation`, SHA `ad8f1afa98209f063aaa7f076c5d8da0d598e138`, attempt 1. Its browser-e2e job failed at `Test professional-review journey`; the phone project failed `web/e2e/theme.spec.ts:86` because the submit action contrast ratio was 3.43336132935938 against a 4.5 minimum. The same command reported 108 passed, 11 skipped, 1 failed. Python and docker-smoke passed. Research history, offline execution and substituted-live steps were skipped after this failure. The preceding same-branch run 39149538104 succeeded on a different SHA (`741323d3...`). This is a changed-commit comparison, not a retry at the same revision. No same-SHA attempt repeats occur in the 20-run sample, so no flakiness is inferred. One failure is too small a sample for a rate estimate. No large artifacts were downloaded.

The bounded sample has no per-test timing report for Playwright definitions. The successful main Python job runs pytest with `--durations=25`, but its per-test duration tail is not summarized here; summed test duration remains distinct from the pytest command's 3m17s wall time. No retries appear in the sampled attempts. The complete run list and inspected failure log are source evidence; individual browser test durations remain unavailable.

## Workflow and setup costs

The authoritative workflow definition is `.github/workflows/tests.yml`. Its `python` job runs locked environment setup, `uv run pytest --durations=25`, and mypy. Its `browser_e2e` job runs Python setup, Node install, web test/build, research test/build, Chromium installation, database migration/seed, then four Playwright invocations: the default practitioner suite and the research history, offline execution, and substituted-provider live suites. A separate Docker job performs the Compose restart/index smoke and image build/deployment smoke.

Workflow YAML establishes command order and configured limits; the successful main run below supplies elapsed job and step times. Summed individual test duration and isolated test-server startup remain unavailable from this CI sample. The Playwright research suites share one browser job setup but each invocation starts its own configured Python `webServer` on port 4175. The server restores retained history into a temporary directory and rebuilds the index; execution and live configurations each incur that server/index setup independently. The three configs use three viewport projects; the history narrow-focus test intentionally skips its two non-narrow executions at run time. This is structural fan-out/setup evidence, not measured overhead. The browser job also installs a separate Chromium browser and initializes the PostgreSQL database before tests.

## Latest successful main timing detail

Run [39149906958](https://github.com/alistairkung/private-client-graph/actions/runs/39149906958), attempt 1, revision `39fe75b6ad9791725c601a48edd6ad40aa6970ff`, succeeded across Python, browser-e2e, Docker smoke and the required-check aggregator.

| Job | Duration | Relevant step durations |
| --- | ---: | --- |
| browser-e2e | 9m14s | pre-browser steps through DB initialization 1m53s (includes component tests and both builds); professional-review browser suite 1m57s; research history 23s; offline research execution 3m37s; substituted-provider live research 1m21s; remaining post/cleanup steps about 11s |
| python | 4m04s | setup through PostgreSQL tools 26s; `uv run pytest --durations=25` 3m17s; mypy 18s; remaining cleanup about 1s |
| docker-smoke | 1m34s | Compose restart/index smoke 52s; image build and deployment smoke 16s; setup/check-out 24s |
| required-check aggregator | 4s | setup and required-job verification |

The browser job's three research steps total **5m21s** (23s + 217s + 81s). This is step wall time in one sequential job, including browser test execution and each Playwright invocation's server startup/teardown. The research step times do not expose per-test summed durations or isolate server setup. The full browser job is 9m14s and full workflow wall interval is 9m24s; jobs overlap. Setup is measured at named workflow-step granularity: web dependency installation 5s, Chromium installation 28s, and database migration/seed 2s. The combined component-test/build step is 50s; its internal commands and each browser server's startup are not separately timed by this CI record.

## Local discovery, not an execution baseline

At the pinned revision, the following `--list --reporter=json` commands were run from `web/` with `DATABASE_URL=postgresql://pcg_tactile@127.0.0.1:55489/pcg_tactile_e2e`. The URL satisfies config collection validation; Playwright list mode did not start the configured servers or connect to the database. Environment: macOS workspace, Node v26.10.0, Playwright 1.63.0. No app/model provider calls were attempted.

| Suite | Unique definitions | Configured project cases | List status | Collection reporter duration |
| --- | ---: | ---: | --- | ---: |
| research-history | 6 | 18 | 18 skipped by discovery-only reporter | 12.723 ms |
| research-execution | 9 | 27 | 27 skipped by discovery-only reporter | 16.678 ms |
| research-live | 2 | 6 | 6 skipped by discovery-only reporter | 11.294 ms |
| Total | 17 | 51 | 51 skipped by discovery-only reporter | 40.696 ms summed |

The durations above are Playwright's JSON `stats.duration` for each list/collection command. Their sum is not suite wall time, summed test duration, CI time or setup time. `--list` executes no tests; the reported skipped count is not a runtime skip rate. At execution, `history.spec.ts:133` intentionally skips only desktop and compact, leaving the narrow project case. That conditional is not determined by the skipped status emitted during list collection.

## Deterministic provider substitution

Source inspection confirms that `tests/research_browser_server.py` only enables its substituted live path under `PCG_BROWSER_LIVE=1`: it initializes a named substituted-provider task, enables the feature flag, and replaces the supervisor subprocess worker with `tests/research_live_worker.py`. The research live config sets that environment flag. The three list commands did not launch this server or make any dispatch. No live external provider was invoked.
