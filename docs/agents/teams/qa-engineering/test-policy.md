# Test-layer selection policy

Apply the [web testing guide](../../../WEB_APP_GUIDELINES.md) and root repository
rules. Feature teams choose coverage with their change; QA advises on shared
strategy and targeted improvements. No standing QA sign-off is required.

## Choose by failure boundary

| Layer | Use when the failure can be observed here | Keep real | Avoid |
| --- | --- | --- | --- |
| Focused unit | Deterministic graph/view transformations, identity mapping, evaluation arithmetic, formatting or finite state rules | Public function inputs/outputs, domain validation | Private-helper tests, rendering supplied text, snapshot counts as behaviour |
| React component | Meaningful selection, filter, dialog, loading/error, keyboard or async state transitions | Mounted feature, user events, accessible roles and observable output | Mocking the component's own state, implementation selectors, trivial render tests |
| API/integration | Authentication/authorization, origin/CSRF, request contracts, transaction outcomes, persistence, subprocess/service boundaries | FastAPI application and relevant services; PostgreSQL for database integrity | SQLite substitutes, fake final graphs, mocking the transaction being tested |
| Browser E2E | Routing, actual DOM geometry/scroll/focus, browser cookies/session, network-to-UI wiring or a mission-critical multi-boundary journey | Browser → frontend → API → deterministic construction/persistence → review | Repeating all local input permutations or component branches in each viewport |
| Live evaluation | Stochastic extraction quality against benchmark truth | Authorised provider invocation and recorded configuration/results | Ordinary CI dependence on a model returning the same answer |

Use the lowest layer that can expose the actual failure. A component test of an
error message cannot replace a server test of authorization. An API test of
stored evidence cannot prove a user reaches the exact visible Source passage.
Deliberate overlap is appropriate when the tests protect distinct boundaries;
name those boundaries instead of removing coverage because titles look similar.

## Existing capabilities

The repository already has pytest, FastAPI clients, PostgreSQL integration
fixtures, Vitest, React Testing Library, user-event and Playwright. Vitest uses
jsdom for normal and research React suites; this supports user/state assertions
but does not provide a browser layout engine. Playwright already supports real
viewport, touch, reduced-motion, keyboard, request interception, trace and
screenshot checks. Use its existing projects/reporters. Existing pytest fixtures
exercise relational integrity, transactions, API admission and research workers.
No additional runner, coverage threshold tool, accessibility library or scheduler
is required by this setup. Propose another dependency only for an evidenced gap.

## Safe movement and meaningful regressions

Before moving coverage, identify each assertion and its intended failure, fixture
and observation boundary. Add the lower-layer replacement while the browser test
still exists. Show that a representative regression or controlled temporary fault
fails the new test, then restore the fault and show it passes. Do not commit a
broken production path or mutate protected semantics to manufacture proof.

Preserve the smallest real cross-boundary smoke covering the lost integration
risks. An independent coverage reviewer checks the mapping for an authorised
migration slice; uncertain equivalence means retain the existing assertions.
Only then remove specifically superseded assertions. Compare before/after on the
same environment, commands, worker settings and dataset. Report suite wall time,
summed test time, setup, pass/skip/failure counts and retained guarantees
separately. Improvement is confidence and maintenance cost, not a deletion quota.

Add regression tests at the layer where the observed defect would be detected.
Describe the broken outcome, not the current helper structure. A passing test
that never fails for that defect is not evidence of equivalent coverage.

## Browser growth and UI-specific coverage

Every new E2E should state the browser or cross-service failure it protects and
why existing smokes plus lower-layer tests do not catch it. Expand parameters at
lower layers unless locale, viewport or browser behaviour changes that boundary.
QA may challenge duplication in review without becoming an approval queue.

- Accessibility: component tests cover names, semantics, keyboard activation,
  dialog focus lifecycle and state announcements; retain browser checks where
  real focus, tab order, offscreen content or browser semantics matter. Existing
  role assertions alone are not a full accessibility audit; use focused manual
  assistive-technology review for changed critical workflows when warranted.
- Motion: unit/component tests cover state, cancellation and reduced-motion
  decisions. Browser tests cover actual scroll timelines, geometry, pinning and
  reduced-motion outcomes. Prefer observable settled states or sampled geometry
  to fixed sleeps. Do not replace a visual/timing guarantee with a class check.
- Responsive behaviour: components cover conditional controls; browser projects
  cover meaningful narrow/touch/wide layout transitions, scroll ownership and
  unobscured targets. jsdom cannot prove clipping or highlight alignment.
- Regressions: preserve exact Evidence → Source identity/range and visible
  highlighting, multi-source switching, canonical edge selection, recovery after
  uncertain mutations, authenticated writes and public read isolation. Keep the
  curated Case 01 browser journey required by the web guide.

## Determinism and operating limits

Substitute only stochastic/external provider boundaries with the established
fixtures. Keep deterministic graph construction, provenance checks, admission
and persistence real at their integration layers. Retain research execution's
substituted worker and its frozen-plan/admission/evaluation isolation checks.
Do not mock a final graph to speed up a test that is meant to exercise its
construction. Offline evaluation rules remain deterministic unit/integration
tests; live quality experiments need separate human scope and provider budget.

Do not weaken assertions, add skips/retries, accept real Matter data or change
protected semantics to improve timings. Track suspected flakiness with revision,
attempt, failing assertion, logs/trace and denominator. A changed-commit success
does not prove a previous failure was flaky. One local pass is a baseline, not a
stability estimate. Follow the [migration plan](migration-plan.md) for staged work.
