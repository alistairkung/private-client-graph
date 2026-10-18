# Proposed phased migration

This plan is for separate authorisation. Setup changes only team definitions and
audit documents; it does not migrate tests, alter assertions, skips/retries or CI.
Use [the inventory](inventory.md) and [layer policy](test-policy.md). Classifications
are proposals, not proof that an existing lower-layer test is equivalent.

## Phase 0 — establish a comparable baseline

Reconcile the CSVs with current Playwright collection before starting a slice.
The audit base is `39fe75b6`; unmerged branches (including PR 167's invitation
changes) are excluded. Refresh counts, commands, fixtures and the chosen failure
modes after those branches land. Record local and CI environments separately.
Use existing reporters and bounded Actions history, without rerunning live models.

Completion: every selected assertion has a failure description, original location,
current timing, intended replacement and retained boundary. Resolve gaps relevant
to that slice; a one-run timing is not a flakiness rate or a universal speed claim.

## Phase 1 — a small state-only component slice

Propose `web/research-e2e/history.spec.ts:161`, the outcome filter surviving
Overview → Investigate, as the first candidate. It protects shared selection state
rather than geometry or persistence. Add a mounted research history/route test
near the owning component (a proposed new test, not an assertion that existing
coverage is equivalent). Exercise the actual view controls, select `missing`,
change views, return, and observe the preserved selection and matching content.
Retain `history.spec.ts:3`'s real history/comparison/exact Source journey and the
narrow browser focus restoration at line 133.

Completion: demonstrate loss-of-filter state fails the replacement, restore the
code, pass both layers and obtain independent coverage review. Only then consider
retiring the precisely superseded group/viewport repetitions. Compare the actual
slice's costs, including new maintenance and fixture setup. If routing/hash state
cannot be faithfully exercised here, leave it class 6 and choose another slice.

## Phase 2 — split mixed UI groups without losing browser guarantees

Prioritise state/admission permutations in Intake, public disclosures and research
configuration only after checking the named existing component tests. Add missing
behaviour to the owning feature's tests, not a broad new harness. Move local error
or validation variants only where the same failure is observable below the browser.
Retain routing/session and uncertain-response recovery smokes. Motion, highlight
alignment, clipping, tab order and camera/scroll checks remain real-browser work.

Completion: an assertion-by-assertion mapping, failing-regression demonstration,
and independent review precede any removal. Class 6 groups stay intact until the
mixed responsibilities have an evidenced split. Avoid turning one concise journey
into many shallow component tests that reproduce its internal steps.

## Phase 3 — contract permutations and deliberate consolidation

Consider API-only Playwright request groups and artifact error matrices against
existing FastAPI/PostgreSQL/public-research integration tests. Exercise real
multipart parsing, admission, canonical construction and transaction outcomes.
Keep real browser ingestion → confirmation/discard and persisted review journeys.
Consolidate overlapping research comparison assertions only after mapping direct
bench entry, treatment repetition and exact expected quote selection; these are
not automatically duplicates of another comparison route.

Completion: equivalent public contract and failure assertions, retained boundary
smokes, and controlled fault evidence. No security/provenance assertion retires
because a neighbouring test's name sounds similar. Do not change final graph
fixtures to bypass construction or replace PostgreSQL constraints with mocks.

## Phase 4 — measure and stop at the authorised boundary

Run comparable before/after commands and report expanded cases, executed/skipped
counts, command wall time, summed test time and setup independently. Use repeated
timings only when variability needs investigation. Contrast local changes with
CI step timings cautiously: hardware, Node version and concurrency differ.
Keep suspected flakiness separate from deterministic failures and environment
failures. Review any loss of failure detection, diagnosis quality or critical
boundary coverage. Hand back the completed slice; the next phase needs new scope.

## Protected boundary map

These are anchors, not permission to remove other unique assertions. The CSVs
enumerate all definitions and proposed risks; the current source is authoritative.

| Protection | Existing boundary anchors | Lower-layer support / required proof |
| --- | --- | --- |
| Matter loading, deep links, refresh and navigation | `web/e2e/practitioner.spec.ts:40`, `public-access.spec.ts:7` | Navigation/workspace component tests plus persisted public reads; keep a real deep-link/reload journey |
| Ingest, confirm, discard and canonical accepted state | `practitioner.spec.ts:101,158`, `api-contract.spec.ts:59` | `tests/persistence/test_protected_local_integration.py`, `tests/test_proposal_api.py`; prove full-state transaction and no accidental confirmation |
| Authentication, authorization, origin/CSRF | `api-contract.spec.ts:26`, `public-access.spec.ts:31,53,83`, `practitioner.spec.ts:314` | `tests/persistence/test_public_access.py` and security/API tests; retain cookie/session-to-UI proof |
| Canonical graph selection and exact Evidence → Source | `graph.spec.ts:12`, `landing.spec.ts:116`, `source-navigation.spec.ts:30` | Graph/view transformations, `EvidenceList.test.tsx`, `SourceReader.test.tsx`; browser proves real highlight location/scroll/focus |
| Multi-source attribution and switching | `source-navigation.spec.ts:89`, `showcase-sources.spec.ts:4`, `practitioner.spec.ts:158` | Exact source/evidence identity and state tests plus actual tab visibility/repeated switching |
| Failure recovery and unknown mutation outcome | `interaction.spec.ts:167`, `public-access.spec.ts:83`, `landing.spec.ts:564` | Intake/decision async state and client/API tests; no duplicate submission or invented success after transport uncertainty |
| Research history/evaluation isolation | `web/research-e2e/history.spec.ts:3,81,175`, public research journeys | Artifact/comparison API and inspection components; preserve immutable exact quotes and absence of operational controls |
| Frozen plans, persisted execution and live admission | `web/research-execution-e2e/{execution,workspace,retained-inputs}.spec.ts`, `web/research-live-e2e/live.spec.ts` | Existing workbench lifecycle/integration tests; retain separate consent/start, continuation, zero-call replay and immutable results using substituted worker |

## Evidence limits and ownership

No replacement equivalence or fault detection has been demonstrated in setup.
No deletion count or timing reduction is promised. The preliminary inventory
does not include line/branch coverage, production telemetry, an assistive-tech
audit or a long-term same-revision flakiness study. CI includes Docker/recovery
checks outside Playwright; they remain protected. The QA architect coordinates
one named slice; feature owners implement their tests, and the independent
coverage reviewer challenges the mapping. Use [the launch prompt](launch-prompt.md)
only after human authorisation.
