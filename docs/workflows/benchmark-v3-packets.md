# Benchmark v3 packet workflow

The custodian stages each handoff in a fresh private directory containing one
UTF-8 `request.json`. Keep restricted histories, keys, intervention declarations
and packet directories under custodian control. Use a neutral directory name
and paste the authorized text into the request. Review every text value, including
the prompt, for unintended context or paths before dispatch.

Keep raw runs, prompts, designer histories, author briefs and draft keys in the
private archive. Public review can cite approved Source and packet digests,
aggregate session evidence and the approved portions of the disposition dossier.

```json
{
  "role": "probe",
  "model": "gpt-6.2-sol",
  "effort": "low",
  "rationale": "Check the isolated packet runtime",
  "parent": null,
  "inputs": {"probe": "This is harmless test text."},
  "prompt": "Return the supplied sentence exactly."
}
```

Run `uv run python -m benchmark_v3.packet PACKET_DIR` from the repository root with
Codex CLI available and signed in. The runner sends only the prompt and the
named text inputs. Record the custodian's model and effort decision in
`rationale` and the prior revision identifier in `parent` when applicable.
Use a fresh directory and session for each handoff.

## Role boundaries

| Role | Allowed input labels | Handoff |
| --- | --- | --- |
| `research_architect` | Planning: `research_specification`, `development_findings`, `practice_references`. Reconciliation: `hypothesis_revision`, `admission_dossier`, `technical_findings`. | Work across admitted development families. Return ranked proposed hypotheses or an achieved-versus-intended assessment. See the exact profiles below. |
| `designer` | `hypothesis_revision` | The runner resolves the revision and sends only the approved capability brief. Use one context per family. Deliver a private dated history, custody, role-specific fact briefs and a separately logged intervention. |
| `author` | `author_brief`, `genre_references`, `received_correspondence`, `revision_ticket` | One dated perspective at a time. Release recurring-author packets chronologically. Provide only facts the participant could know and exact earlier correspondence they received. Exclude target labels, answers, other perspectives and extraction outputs. |
| `realism` | `sources`, `neutral_brief`, `cutoff`, `possession_ledger`, `genre_references` | Review candidate Sources for purpose, possession, chronology, form, density and cues. Limit the ledger to transmission. Review every sibling as a separate file in its own documentary situation. Return per-Source revision tickets. Exclude hidden history, semantic targets, keys and extraction outputs. |
| `annotation` | `sources`, `neutral_brief`, `ontology`, `annotation_rules` | Review exactly one locked, ordered bundle. Return the complete graph, exact evidence and minimum sufficient alternatives, contradictions, open questions and dangerous guesses. Exclude variant names, siblings, intended answers, peer labels and extraction outputs. |
| `adjudication` | `sources`, `annotation_a`, `annotation_b`, `neutral_brief`, `ontology`, `annotation_rules` | Reconstruct disagreements against the locked Sources and commit a provisional key. Exclude hidden history, paired conditions and interventions until this key is committed. |
| `audit` | `paired_bundles`, `intended_intervention`, `provisional_keys`, `neutral_brief`, `ontology`, `audit_rules` | After provisional adjudication, compare the actual matched bundles and key differences. Audit evidence sufficiency, masking and shortcuts. |
| `masked` | `sources`, `neutral_brief`, `ontology`, `annotation_rules` | Give a fresh reader only the masked or subset bundle and the neutral annotation instructions. Exclude unmasked facts, target labels and the intended effect. |
| `probe` | `probe` | Use harmless synthetic test text to verify the runtime. |

The runner checks labels. The custodian verifies the scope of the text supplied
under each label. Stage inline text only. The runner never opens paths mentioned
in input text. Keep raw packets and unapproved evidence in the private archive.

## Research Architect commissioning

The Research Architect owns portfolio hypotheses and coverage assessment. The
Matter Designer owns independent construction. The owner makes two separate
decisions, first on the proposed hypothesis and later on admission.

```text
Research Architect → owner hypothesis approval → Matter Designer
→ Document Authors → Realism Reviewer → Blind Annotators
→ Adjudicator → Adversarial Auditor → owner admission → Research Architect
```

### Plan a development round

Use `role: research_architect` and `prompt: research-architect-v1` in the
same request envelope as other roles. The inputs must be exactly these three
text fields.

| Input | Custodian preparation |
| --- | --- |
| `research_specification` | Provide the current [portfolio research scope](../../benchmark_v3/planning/RESEARCH-SCOPE.md) and any approved development planning constraints. |
| `development_findings` | Provide reviewed excerpts from owner-admitted development dossiers and independent technical audits. Exclude raw model runs, sealed material, in-progress or unreleased blind work and private histories. |
| `practice_references` | Paste a JSON array of publicly checked references with `title`, `url` and `relevance`. Use an empty array if public grounding is unavailable. |

The runner adds the development register and its taxonomy, ontology and
previous proposals and decisions. It selects the versioned
[architect prompt](../../benchmark_v3/instructions/research-architect-v1.md)
and appends the output schema. Research is offline within the isolated turn.
The custodian verifies public sources and stages them before dispatch. This
profile excludes v3 extractor outputs. Any later post-baseline diagnostic use
requires a separately authorised profile.

```bash
uv run python -m benchmark_v3.packet PACKET_DIR
uv run python -m benchmark_v3.architect proposals PACKET_DIR
```

The second command prints a validated record from the completed packet and
receipt. The custodian archives the original request, handoff, response and
receipt, then commits the reviewed printed record to
`benchmark_v3/planning/rounds/<round>.json`. An empty ranked array is valid.
The [v1 contracts](../../benchmark_v3/research_contracts.py) specify required
grounding, contrasts, controls, feasibility and version lineage. The
[initial round](../../benchmark_v3/planning/INITIAL-ROUND.md) links complete
proposal examples and runtime evidence. Assessments are qualitative and
compare one independent Matter history at a time.

### Record the owner's decision and commission one Matter

The archived proposal always retains its original `proposed` status and
session provenance. The owner reviews the full proposal against its revision
digest in the coverage register and provides their explicit disposition. The custodian records it at
`benchmark_v3/planning/decisions/<hypothesis_id>@<revision>.json` for the
exact revision.

```json
{
  "schema_version": 1,
  "hypothesis_id": "example-hypothesis",
  "revision": 1,
  "hypothesis_sha256": "<64 lowercase hex characters from the register>",
  "status": "approved",
  "owner": "<human benchmark owner>",
  "decided_on": "2026-11-22",
  "decision_reference": "<auditable reference to the owner's explicit decision>"
}
```

The other owner dispositions are `returned` and `rejected`. Preserve the
original record when revising. Submit a child revision with the same IDs,
incremented revision and the exact previous revision digest. The revision
digest is SHA-256 of compact UTF-8 JSON with sorted keys, containing the
validated hypothesis and the architect session provenance. The owner record
is a custodial attestation. Keep writes to the trusted repository records
under human review. The packet runner consumes those records and has no
command to create approval.

To run a designer, set the prompt selector to `commissioned-designer-v1` and
supply only `"inputs": {"hypothesis_revision": "example-hypothesis@1"}`.
The runner resolves the revision under its trusted factory directory, checks
the owner disposition and digest before opening a session, then constructs
the approved capability brief. A request containing its own approval,
unapproved brief or arbitrary designer prompt is rejected. Families A–C retain
their historical admissions and original digests. Their family IDs are reserved.

Give each author only the participant knowledge and legitimate received
correspondence. Give each blind reader only the locked file and uniform
annotation contract. Release the intended experimental objective to the
adversarial auditor after both blind readings and the provisionally adjudicated
key are committed. The architect transcript and portfolio stay with the custodian.

### Reconcile after owner admission

For a commissioned development family, record the approved hypothesis
reference (`hypothesis_id`, `revision`, `hypothesis_sha256`) in the existing
admission record under `hypothesis`, along with `split: development`. The
runner requires a dated human acceptance and the existing manifest digest.
Set the same architect role and prompt selector. Supply exactly
`hypothesis_revision`, `admission_dossier` and `technical_findings`.
Stage the reviewed dossier excerpt, matching and mask outcomes, shortcut
findings and limitations. The runner adds the approved revision, current
development coverage and a receipt commitment to the exact admission.

```bash
uv run python -m benchmark_v3.packet PACKET_DIR
uv run python -m benchmark_v3.architect reconcile PACKET_DIR
```

Commit the reviewed printed assessment separately under
`benchmark_v3/planning/reconciliations/<FAMILY>.json`. The output measures
how the original hypothesis was operationalised. It records evidence for
verified axes, redundancy, remaining gaps and the recommendation. The
commands leave protected keys, approval records and scores untouched.

Update the admitted family row and any residual gaps in the canonical
[coverage data](../../benchmark_v3/coverage.json). Verified findings for
commissioned families come from their separate reconciliation. Pending and
rejected hypotheses remain visible through the archived proposals and owner
decisions. Regenerate the [Markdown register](../../benchmark_v3/COVERAGE.md)
with the read-only renderer and review the diff.

```bash
uv run python -m benchmark_v3.architect coverage > benchmark_v3/COVERAGE.md
```

## Lock, annotate and revise

1. Freeze each Source's UTF-8 bytes, IDs, titles, and serialized bundle order.
   Record the bundle digest and declare each pair's allowed change and expected
   semantic delta before annotation.
2. For each condition, including order-only siblings, prepare two fresh
   annotation directories with byte-identical prompts and inputs. Verify that
   the two handoff receipts have the same packet digest and different sessions.
   Wait for both completed receipts with output digests before opening either
   answer. Keep both commits and record shared and disputed claims, passages
   and proof sets before adjudication.
3. Give adjudication the locked bundle and the two committed answers. Record
   rulings and residual doubts against exact Source passages. Commit the
   provisional key before releasing paired bundles and the intervention for
   audit. Commission fresh masked readers for necessity and surviving-proof
   checks. Keep their responses with the audited revision. When two planned
   masks produce identical Source arrays and neutral briefs, verify and record
   the byte equality before reusing a fresh masked result. For exact proof
   sets, a surviving one-member deletion can be checked by literal containment
   in a whole-file masked packet that already failed to prove the edge.
   Verify that the enclosing packet withheld the edge because a needed fact
   was missing. The full set and each semantically distinct masked packet
   still need an independent reading.
4. If a Source changes, retain the prior revision and link the child to it.
   Send the responsible author only the relevant revision ticket and their
   perspective packet. Repeat affected realism review, both blind passes,
   adjudication, paired audits and deterministic preflight against the new
   lock. Keep prior receipts. Freeze the final key, approvals and policy
   digests before recording the owner's disposition against those digests.

## Receipts and isolation

`handoff.json` records a session ID, the SHA-256 of the exact submitted text,
and UTF-8 byte counts and SHA-256 for each input and prompt. It is written
before the model turn starts. The runner writes read-only, no-clobber files.
A completed `receipt.json` ties the handoff to the exact `output.txt` bytes,
Codex runtime isolation findings, requested and observed model settings,
timestamps and any reported token usage. Use only outputs whose completed
receipt matches the bytes. Archive the receipts as an append-only lineage.

The verified runtime is macOS with Codex CLI 0.166.0. The app-server launches
in a neutral empty directory and uses temporary runtime state and logs. Each
ephemeral thread has empty environment and workspace-root lists, no loaded
instruction files, no connector capabilities, no network and a named
read-only profile. The profile denies shared temporary and user paths and
allows the empty working directory. Check rejected receipts for the
failure reason, record any observed exposure, quarantine the affected pass
and replace it with a fresh reader. A directory left without a completed
receipt has no usable output.

## Offline replay and human disposition

Use the opt-in replay from the repository root once a family has all its frozen
Source arrays, a committed declaration, complete adjudicated keys and saved
ideals. Family A uses a version 1 manifest. Families B and C use version 2,
with the preblind freeze declaring each literal edit, both candidate edges,
and the required edge set for each condition. Families D, E and F use version 3.
Each freeze declares one literal edit, the candidate edges and the required
edge sets for both conditions. The replay checks the scoped switch, unresolved
parentage and identity invariance respectively, including their joint proofs.

Run `uv run python -m benchmark_v3.replay --manifest PATH/manifest.json --artifacts EMPTY_DIRECTORY`.
The preview sets the maximum provider attempts to zero. Reopen the saved Run
and inspect its coverage, complete graph scores, eligible Source associations,
same-edge proof, and the exact paired decisions in `preflight.json`. The replay
raises an error if any ideal fails. Test inputs are defined in
[the replay tests](../../tests/research/test_v3_replay.py).

The owner reviews the complete file and dossier and records accept, return or
quarantine against a dated package and annotation digest and evidence policy.
A pending dossier stays outside execution. A failed or incomplete comparison
keeps its planned and scored coverage visible. A commissioned development
family then returns to the Research Architect for coverage reconciliation.

## Batch commissioning

For new Matter families, use the [development batch workflow](benchmark-v3-batches.md).
The custodian records exact portfolio, hypothesis, budget and isolation approval
before dispatch. The batch coordinator assembles packets for the same isolated
runner and retains their receipts across interruptions.
