# Three-family pilot readiness

## Factory and corpus

On 22 November 2026, PRs [#193](https://github.com/alistairkung/private-client-graph/pull/193)
through [#197](https://github.com/alistairkung/private-client-graph/pull/197)
were open. Remote main was `94cd87a0bcb78c5d4107d03c9c7f437b0a3ef7b1`.
The fetched #197 head `550b246b51bd93e2bb5d8dc96ceb773305ea0375` contains
the stack and all five human admissions. Its own Python, browser and Docker
checks passed. This planning PR targets that branch.

The factory independently verified the admitted register against the
admission records and condition manifests. Its canonical coverage digest is
`d02473460c7f169eafccd75882bec41eeccc26123739b68f435ce098be65d6bd`.
The twelve conditions belong to five independent histories. E0 and E1 are
returned diagnostics. There were zero paid v3 extraction observations at
the start of planning.

## Host isolation

The intended development host is macOS 26.2 (25C56), arm64, Codex CLI
0.166.0. On this host the outer managed tool sandbox disallowed installation
of a nested Seatbelt profile. The custodian ran the probe in the host shell
with the exact named `benchmark_packet` profile from the factory. The
workspace sentinel was readable. A synthetic sentinel in shared private
temporary storage and a synthetic sentinel in the repository both received
OS permission denials. The preflight was repeated before the authorized
retry and produced byte-identical evidence. The probes submitted zero
model turns. The
[probe results](os-boundary.json) are bound to the proposed manifest with
SHA-256 `ea1bc3f5d64b79f1596cd28cacf0d4ec8008040ee504ef98db93db759178ab01`.
The pinned packet implementation SHA-256 is
`63d2ba152800a4c4cdbbb329d43ac082463181c9d5fd0d2250b3233825159ab8`.

The permission profile denies the user tree and shared temporary trees.
Each worker receives its own revision directory in owner-only custody,
under one coordinator lock. Each packet launches a fresh app-server in
an empty workspace with the named read-only profile, no network, no
attached environment or runtime workspace roots, no inherited history,
no instruction sources and disabled tools/connectors. The runner checks
these declarations before submission and commits the handoff and output
separately. Role labels are mechanically checked. The custodian must also
inspect the text supplied under them for exposure. No sealed evaluation
mount or packet was used. This verifies the development host's packet
boundary. Future evaluation custody needs its own OS account or sealed
host and fresh boundary evidence.

The Architect input was reviewed before dispatch. It contained the
development scope and taxonomy, admitted technical findings with D/F
limitations, E's public return rationale, registered hypothesis lineage,
the ontology and [checked public practice references](practice-references.json).
The development planning allowlist rejected additional input labels in
the existing tests. The proposed manifest applies only on the verified
host with the pinned runtime and boundary evidence. Any change requires
fresh evidence before owner authorization.

## Deterministic dry run

| Check | Observed result |
| --- | --- |
| Commissioning | An exact test-owner approval commissioned the fixture batch. A changed portfolio digest, altered boundary evidence and missing hypothesis approval were rejected before dispatch. |
| Three independent workers | With three fixture families, the measured peak was three for a cap of three and two for a cap of two. Every invocation had a distinct verified fixture thread identity and a family/revision custody path. |
| Atomic budget and deduplication | Twelve simultaneous reservations awarded only ten authorized family slots. Exact duplicates acquired no new slot. A later fixture expansion could consume only the seven remaining task slots. The next reservation was rejected. |
| Dependencies | Malformed or changed Source or blind-output commitments blocked downstream adjudication and produced an integrity exception. The matched control fixtures exercised both exact literal edits and order-only controls. |
| Resume and uncertain dispatch | Reopening the completed test batch charged zero further sessions. An interruption after a verified receipt resumed from it. An uncertain attempt stayed charged and blocked the family until explicit recovery of its original matching receipt. |
| Scientific and shared failures | The documentary realism objection was retained in the exception queue while siblings completed. Failed dispatch could be quarantined. A shared isolation incident halted further submissions. |
| Dossiers and owner decisions | Twenty mock sessions yielded two technical dossiers and one returned family. The summary reverified the dossiers and their digests. A decision containing a wrong dossier digest left dispositions untouched. The exact fixture instruction recorded separate accept and return decisions. |
| Returned Family E | The development register excludes E, its admission remains returned and the exact human-admission validator rejects the family. The owner record also documents prior rejection of E0/E1 at the live planner gate. |
| Evaluation boundary | Development tests verify that a taxonomy-only projection and separate custody are required and the same OS account cannot open the evaluation ledger. |

The mock transport used saved synthetic fixtures and existing packet validation.
Run the focused deterministic checks with the following command.

```sh
uv run --locked pytest -q tests/test_benchmark_v3_batch.py tests/test_benchmark_v3_architect.py tests/test_benchmark_v3_packet.py tests/research/test_v3_family_admission_packages.py tests/research/test_v3_commissioned_replay.py tests/research/test_v3_matched_replay.py
```

The focused suite passed 95 tests on both planning passes. A temporary fixture-only concurrency
probe wrapped the existing family worker to record peak occupancy and
verified distinct receipts, no additional attempts on reopen and the
exception summary at both limits. The repository suite passed 1,026 tests
with disposable PostgreSQL 16. The full suite includes regression checks
that internally replay legacy checked-in held-out fixtures. Their contents
were outside the Architect packet and the pilot checks. No sealed v3
evaluation material was accessed. The CI-equivalent mypy command passed
across 126 files. Zero paid PCG extraction calls were made.

## D and F reconciliation

There is no saved formal reconciliation for either admitted family. The
current version of the reconciliation validator resolved each exact approved
hypothesis and bound each dated admission in a deterministic preflight.
The older deferral note predates those admissions. Their admitted technical
findings informed the planning packet. Formal verified findings in the
coverage register remain empty for D and F.

`verify_portfolio` and commissioning check exact current coverage,
admitted decisions and hypothesis lineage. They permit a portfolio while
D and F reconciliation is pending. The freeze gate requires reconciled
admitted coverage. The minimum follow-up is one separately authorized
reconciliation packet per family using its exact approved hypothesis,
admitted dossier and reviewed technical findings. Archive each verified
receipt and assessment and update the coverage register with supported
findings. If reconciliation changes the admitted snapshot before
commissioning, the final portfolio must bind that new snapshot. This
planning task records neither a reconciliation nor a new disposition.

## Architect receipts

The [initial attempt](architect-attempt.json) was rejected because each
proposal supplied `design.success_criteria` as a string. The runner
retained the rejection receipt and published no response or usage.
The owner authorized up to two preparation-only turns. The
[planning retry](architect-planning-retry.json) used schema-derived
array guidance and produced the [validated planning record](../../rounds/2026-11-22-efficiency-pilot.json).
The subsequent [portfolio receipt](architect-portfolio-receipt.json)
binds the exact output and handoff to the [portfolio](portfolio.json).
Both completed turns reported `gpt-6.2-sol` at High, fresh ephemeral
threads, empty workspaces, no inherited instructions or mounts, the
named network-disabled read-only profile, six disabled connectors and
zero observed tool actions.

The two completed turns reported 28,493 and 29,018 tokens, or 57,511
in total. The rejected first turn is charged as a session with unknown
usage. Pilot preparation used three scientific sessions across both
passes. Paid PCG extraction and live Matter construction remained at
zero.

## Human design checkpoint

The portfolio requires human acceptance of each design's retainer,
meeting purpose, participant knowledge, record origins and custody
before authoring. The schema 2 manifest makes that a batch-wide gate.
The first stock run commits each approved design under its existing
reservation and stops. Further runs without review can finish interrupted
designs from retained receipts and cannot reserve author sessions.

The owner must accept the exact manifest and all three design digests
in one dated review. The coordinator verifies that every accepted
design still matches the ledger transition and the committed file.
The session runner checks the review before reserving or submitting a
downstream packet. Human review stays private. Apply the existing
exception and uncertainty process if a design does not reach the
checkpoint. See the [dispatch instructions](APPROVAL.md).

Mock tests verify the initial pause and idempotent reopen, a direct
author request blocked before reservation, rejection of incomplete or
stale decisions, a tampered design blocking every author, and correct
reuse of interrupted and reviewed designs. The older schema remains
valid for its existing manifests.
