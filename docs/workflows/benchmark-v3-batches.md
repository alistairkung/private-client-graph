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
private designs and explicitly accepts the complete digest set. Record
the dated decision with `review-designs CUSTODY DECISION`, using
`schema design-review` for the contract. Then resume with `run`. The
coordinator rechecks the design files and the session runner verifies
the decision before downstream reservations and submissions. A schema 1
manifest retains its original execution behavior.

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
