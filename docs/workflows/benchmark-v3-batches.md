# Benchmark v3 development batches

A portfolio targets 20 independent Matter histories. Conditions attached to
one history count as one family. The starting register on PR #196 contains
A, B, C, D and F across twelve conditions. E is returned and remains diagnostic.
Formal Research Architect reconciliation is pending for D and F.

## Plan and commission

The Research Architect proposes individual versioned hypotheses using the
[packet planning profile](benchmark-v3-packets.md). Hypothesis schema v2
supports a natural-only family. Use the portfolio profile with
`portfolio_specification`, `development_findings` and `practice_references`
as its exact input labels. The runner supplies the current admitted snapshot
and registered hypothesis lineage. Archive the original receipt and print the
validated plan with `uv run python -m benchmark_v3.architect portfolio PACKET`.
It binds the Architect's session to the portfolio.

Use `uv run python -m benchmark_v3.batch schema portfolio` for the versioned
schema. The same command exposes `manifest`, `approval`, `pilot`, `admissions`
and `freeze` contracts. Use `coverage` to print verified existing coverage, and
`digest portfolio FILE` or `digest manifest FILE` to compute review commitments.
The owner explicitly approves the exact portfolio and batch digests and each
exact hypothesis revision through the existing hypothesis decision records.
Record the owner's identity, decision date and auditable references. The
custodian transcribes decisions into the schema after receiving them.

The manifest names the pilot or expansion batch, role allocations, maximum
concurrent family workers, each family's session allowance, the task ceiling,
repair limit, stopping criteria and isolation commitment. A pilot has exactly
three families. The base allowance covers one design, one author per Source,
one realism reviewer, two blind readers and one adjudicator per condition,
and one adversarial audit. Allow additional sessions for sections, masks and
repairs when planning cost. Treat the workload mix as research design.
Make matched controls conditional on a question that needs a contrast.

Before commissioning, stage OS boundary evidence from the intended runtime.
Record reads of an allowed neutral sentinel, a restricted temporary sentinel,
and a repository sentinel. Pin the exact evidence bytes and packet runner
bytes with SHA-256. Every new turn then verifies the named empty ephemeral
profile, disabled tools and connectors, requested model and effort. Repeat
runtime verification if the host, Codex CLI or profile changes. The custodian
validates that the staged policy and legal scope match the owner's approval.

Use one owner-only directory outside Git. Reuse it for every batch in the
approved task. These commands operate on the same task ledger.

```sh
uv run python -m benchmark_v3.batch commission CUSTODY PORTFOLIO MANIFEST APPROVAL BOUNDARY
uv run python -m benchmark_v3.batch run CUSTODY BATCH
uv run python -m benchmark_v3.batch package CUSTODY BATCH
```

`commission` only records authorisation. `run` can spend the approved
scientific sessions. `package` saves a digest-addressed summary with family
dossier links and the exception queue. The owner reviews the completed pilot
and records a `pilot-review CUSTODY DECISION` on the exact summary digest.
Expansion requires an explicit continuation. Revise and approve the plan when
the pilot changes hypotheses, resource assumptions or other scientific inputs.

## Worker stages and checkpoints

| Stage | Committed output or gate |
| --- | --- |
| Design | Approved workload, independent history, provenance, chronology, participant briefs and preblind conditions |
| Author | Completed natural inventory, with earlier received correspondence released in order |
| Realism and freeze | Condition-local documentary reviews followed by immutable ordered bundles and matched Source diffs |
| Blind readings | Two fresh full-file readings per condition and deterministic comparison of canonical edges and attached evidence |
| Adjudication | Every disagreement and Source accounted for. All provisional keys are committed before interventions are disclosed |
| Adversarial audit | Per-Source completeness, critical proof, negative controls, matched controls and shortcuts |
| Targeted masks | Independently observed responses against precommitted subsets, exact deletions and edge expectations |
| Technical replay | Schema v4 manifest, protected canonical graph and scorer, quote and Source attribution checks, exact sufficient sets and zero paid provider attempts |
| Admission package | Family dossier, retained replay and exact file commitments |

A schema 2 batch manifest requires a batch-wide human design review.
The initial `run` advances each eligible family through design only.
`designs CUSTODY BATCH` prints the exact manifest and design digests
when every design has committed. The commissioning owner reviews the
private designs and records a disposition on the complete digest set.
Design review schema 2 requires each entry to specify `accept` or `return`, with a reason required for
a return. A returned family stays at `pending_design_review` and cannot
reserve downstream packets. Record the dated decision with `review-designs CUSTODY DECISION`, using
`schema design-review` for the contract. Then resume with `run`. The
coordinator rechecks the design files and the session runner verifies
the decision before downstream reservations and submissions. A schema 1
manifest retains its original execution behavior.

If an initial design is blocked because its file cut-off predates a
required Source, the owner can authorize recovery against the exact
manifest and completed designer response hashes. First confirm that
the earlier relationship as-of date or delivery deadline is already
stated independently in the neutral brief and participant instructions.
`recover-source-cutoffs CUSTODY DECISION` sets the file cut-off to the
latest listed Source date and drops a redundant terminal full-file
snapshot if present. The full-file review and any proper prefixes are
preserved. It revalidates the full design and commits the result
without model dispatch. Use `schema source-cutoff-recovery` for the
decision contract. The ledger retains the original packets, charges and
exception alongside the recovery commitment. The recovered design still
requires the same human review before authoring.

The runner projects each role's packet from the approved plan and earlier
artifacts. An author receives only the participant brief and received
correspondence. Each blind reader receives one condition in isolation.
The adjudicator receives both readings of that condition. The audit sees
the contrasts only after the provisional keys have been locked. The role
allowlist checks visibility boundaries. Documentary realism and independent
review remain the checks for scientific cues inside natural-language content.

Audit intensity increases for joint proof, disagreement, ambiguous identities
or dates, contradictions, shortcuts, provenance uncertainty, controls that
may change multiple facts, and complex or large Matters. Code detects the
risks visible in structured claims and results. The independent auditor
identifies the remaining semantic risks and records why each mask is needed.
A joint alternative needs an independent sufficient subset and a proper
deletion for each contributing Source. The masks receive neutral prompts with
no expected answers. The existing v2 quotation, Source-attribution and
same-edge sufficient-set policies also apply during replay.

## Cost, interruption and exceptions

A SQLite transaction reserves one session before packet dispatch. Every
reservation uses one family slot and one task slot. Failed, interrupted,
uncertain and rejected sessions remain charged. Exact duplicate job
reservations reopen the same packet. Token usage and available monetary cost
stay with its receipt. An unknown price stays unpriced. Saved-ideal replay has
its own zero-paid-PCG Run and uses the Workbench's retained Run evaluator.

A coordinator lock limits the custody directory to one running coordinator.
Its bounded workers advance independent families in parallel. Each family
runs its own stages in dependency order. The ledger retains revisions,
transitions, receipt digests, evidence and exceptions. The packet runner
rechecks the shared halt and hypothesis authority before submission.
A shared isolation failure blocks new submissions across the task. Turns
already submitted can finish and retain their receipts.

Restart `run` with the same custody directory after interruption. A charged
reservation with a complete verified receipt resumes from that receipt.
A missing or uncertain receipt blocks that family. Use
`reconcile CUSTODY BATCH FAMILY REFERENCE` when the original exact terminal
receipt has been recovered. Use `quarantine CUSTODY BATCH FAMILY REFERENCE`
when a blocked job cannot be recovered. Leave failed and uncertain attempts
in custody. A shared isolation incident requires a custodian investigation
and fresh approval before further scientific work. The task's ledger remains
closed to submissions after a shared halt.

For a completed blind reading blocked on an exact quotation, use
`schema annotation-recovery` and `recover-annotation CUSTODY DECISION`.
The commissioning owner binds the original output, receipt, frozen bundle,
cited Source, candidate path and UTF-8 byte interval. The command accepts one
missing line feed at a unique Source span, preserves the original failed
reading and writes an immutable derivative with its validation record. A
verified resume reuses earlier sessions and sends the existing readings to
adjudication. Repeating the same decision verifies the recorded derivative.

Use `recover-adjudication-quote CUSTODY DECISION` only after an explicit
owner decision binds the exact output, receipt, frozen Sources, one token
interval and derivative digest. This path reuses the single exact quote
already selected in both blind readings and the retained adjudication. It
requires full adjudication validation before committing the derivative.
The original packet remains intact. The scoped run reopens the derivative
and can proceed to independent audit without another adjudication session.

Use `release-audit CUSTODY DECISION` for a separately authorised fresh
audit of a natural revision held by the frozen critical-edge map contract.
The release binds the earlier receipt, locked Sources, validated adjudication,
budget and exact proposed mask views. The new auditor supplies its own
expected findings and assesses the combined cut-off deletion. A return,
separate-deletion requirement or different plan holds mask dispatch.
The scoped `run --family FAMILY --stop-after audit` command stops after
the audit. Use `--stop-after masks` to inspect mask evidence before
deterministic replay. Re-entry reuses the charged jobs and receipts.

Use `schema deferred-exception-review` and
`record-deferred-review CUSTODY DECISION` to record approval of a documentary
repair scope or the merits of a proposed child design. Both decisions hold
the family at its existing gate. Repair execution, child activation and
budget amendments require separate authority and a tested release path.

Use `amend-budget CUSTODY DECISION` for an explicit pilot ceiling increase.
It binds the original owner approval, manifest, portfolio and completed
charges. A follow-up amendment uses schema 2 and also binds the latest
amendment in `previous_amendment_sha256` and the current effective ceilings.
All amendments, release commitments, original allocations and historical
charges stay in the ledger. The reservation transaction reads the latest
amendment before spending. Family allocations cannot decrease or transfer
under this operation. Scientific execution still requires owner authority.

Use `continue-family CUSTODY DECISION` to release an exact scientific
exception against the recorded budget amendment. A repair release binds the
held scope and participant-safe natural tickets. A child activation binds
the held merits decision and immutable child design. A fresh adjudication
binds the failed receipt and approved blind derivative, rederives the
disagreement IDs and publishes only those IDs in the output schema. Its
single distinct job preserves the charged original. A separately authorised
complete-evidence adjudication binds the retained fresh receipt and reproduces
its ordinary Source approval failure. The packet states the full-key
requirements for both ordinary and joint-only edges and retains the exact
dispute schema. Its own job preserves both earlier attempts. Use
`run CUSTODY BATCH --family FAMILY` for family-scoped dispatch. These releases
do not dispatch sessions by themselves. The normal run checks active revisions,
exact commitments and remaining capacity before reserving science packets.

The default allows one new scientific revision for participant-safe natural
documentary repairs. Reuse unaffected author results and regenerate the
affected recipients' records in chronology. Repeat all subsequent reviews.
A matched-sibling objection or a scientific objection that could disclose
the intervention requires separate human review. Further repair, a changed
hypothesis, or more sessions requires an explicit owner decision.

## Admission, Architect reconciliation and freeze

The dossier binds complete keys, independent comparisons, realism, imprecise
or disputed claims, control and mask results, limits, technical replay,
and resource consumption. Record decisions with `admit CUSTODY DECISIONS`.
One instruction can accept or return several families. Each decision binds
its own exact dossier digest. The command validates the full instruction
before recording separate decisions. A technical pass only produces an
admission recommendation.

Publish the approved development review files and exact `admission.json`
through the repository's reviewed artifact workflow. Use the existing
Architect reconciliation profile against that recorded admission. Update the
coverage register and use `benchmark_v3.architect coverage` to render it.
The private archive retains original design, author, and raw review packets.
The Technical Run and raw receipts stay available to the custodian.

Use `freeze-preview CUSTODY BATCH` after every selected family has a final
disposition, admitted records are published, and coverage reconciliation is
recorded. Give the owner the exact candidate digest. Record their freeze
decision and stopping rationale with `freeze CUSTODY DECISION`. The snapshot
counts admitted families and conditions independently. A defensible freeze
can stop below 20 families. Execution and evaluation remain separate
Workbench decisions.

## Giant Matters and future evaluation custody

A giant slot represents a single 100–200 Source Matter with a workload
hypothesis. The design records chronology, custody, inventory, section
assignments and optional ordered prefixes for scaling snapshots. Each reader
can incrementally finish sections, then independently reconcile identities,
cross-section claims and the complete inventory against the full file.
Reconciliation takes a full-file packet today. Model context, latency,
document composition and cost feasibility remain pilot questions.

Evaluation custody is a future deployment with its own OS account or isolated
host, private mount, role grants, lineage and ledger location. Development
commands accept only the development namespace. The evaluation commissioner
can receive only validated workload counts and registered difficulty-axis IDs.
Evaluation authors need a fresh sealed authoring environment with no mount
or credentials for development cases, keys, histories or model outputs. The
custody helpers validate that boundary's configuration and projection. This
workflow ships development commissioning only.

## Construction from approved designs

The construction phase uses its own ledger. Each family allocation binds
the owner's hypothesis decision, canonical design and revision lineage
digests, and the mask estimate used to check capacity. Stage the exact
design and lineage files under `approved-designs/<batch>/<family>/` in
private custody. Verify the original isolated packet receipts against the
referenced lineage before commissioning. The initial ledger has zero
reservations. The runner projects the approved design into the existing
authoring workflow and rejects designer reservations.

Construction disables automatic repairs. The shared preflight rechecks
the committed designs and lineage, then the runner rechecks them at each
dispatch. Fit the approved author, realism, blind, adjudication, audit
and estimated mask work within each family's allowance. When the
independent audit locks its actual mask plan, check the remaining family
capacity before starting that plan. The ledger retains each charged
attempt and its terminal evidence.

An owner can separately authorise one explicit construction repair for a
family quarantined at documentary realism before freeze. The custodian
records a `ConstructionRepairDecision` against the original manifest and
design, with the private repair-plan digest and the previous and effective
ceilings. `Ledger.record_construction_repair` appends the decision and opens
revision two in one transaction. The original manifest, quota rows and
reservations are retained. New construction reservations are restricted
to that family and revision.

Ordinary batch resume leaves this revision to the separately committed
custodian runner. Before dispatch, that runner verifies the plan bytes against
the decision, reuses only verified unaffected outputs and receipts, and checks
the complete repair and its dependencies. Review gates after authoring repeat
in the new revision. The same ledger charges every attempt and enforces
the effective family and shared ceilings.

## Milestone roadmap execution

A milestone commission binds one ordered list of exact hypothesis revisions,
an additional technical qualification target, a task ceiling and a ceiling
per family. Keep this approval and its development ledger in a separate
owner-only custody directory. The owner approves the budget and hypothesis
revisions once. The manifest authorises the coordinator to proceed after the
isolated design clears scope, chronology, inventory and capacity checks.
Existing human design reviews on schema 2 manifests keep their original
workflow.

The coordinator activates the next required slots in manifest order, up to
the approved worker limit. An activation stays in the ledger across restarts.
Only an activated family at its recorded stage can reserve a new milestone
packet. An independent family that returns, exhausts its allocation or blocks
can leave a place for the next approved reserve. An uncertain attempt keeps
its charge and requires the original verified receipt for reconciliation.
A shared isolation or integrity failure halts progression. Use the same
`run CUSTODY BATCH` after interruption. The milestone does not accept a
family selection override.

The design preflight counts the actual section topology and every remaining
mandatory first-pass packet before authoring. A permitted documentary repair
gets the same check against its affected authors and repeated reviews. Audit
determines the exact mask plan, and the ledger checks capacity for the full
plan before the first reservation. Adjudication supplies the exact disputed
keys and instructions for whole-graph Source attribution and joint proofs.
Ordinary follow-up questions stay with the Source audit. Any remaining
objection to the key blocks progression.

A family contributes to the target only after its dossier and zero-provider
replay are present and their recorded commitments verify. The package reports
the technical tally and unstarted reserve. Human admission remains a
separately recorded decision on the exact dossier. Prior ledgers remain with
their originally approved packet implementation and releases. If a former
manifest pins a different packet implementation digest, use its approved
revision and custody for separately authorised work on that history.

When the original designer lists the required full-file read again as a
terminal Source-count snapshot, the milestone removes that redundant count
from the proper-prefix list. It keeps every proper prefix, revalidates the
design, and records the original output and receipt alongside the corrected
design digest. This mechanical recovery can reopen the matching design
exception without another designer turn.
