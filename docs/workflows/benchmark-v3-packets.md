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

Run `python -m benchmark_v3.packet PACKET_DIR` from the repository root with
Codex CLI available and signed in. The runner sends only the prompt and the
named text inputs. Record the custodian's model and effort decision in
`rationale` and the prior revision identifier in `parent` when applicable.
Use a fresh directory and session for each handoff.

## Role boundaries

| Role | Allowed input labels | Handoff |
| --- | --- | --- |
| `designer` | `capability_question`, `meeting_setting`, `genre_references` | One context per family. Deliver a private dated history, custody, role-specific fact briefs and a separately logged intervention. Exclude graph answers, other families, model outputs and sealed material. |
| `author` | `author_brief`, `genre_references`, `received_correspondence`, `revision_ticket` | One dated perspective at a time. Release recurring-author packets chronologically. Provide only facts the participant could know and exact earlier correspondence they received. Exclude target labels, answers, other perspectives and extraction outputs. |
| `realism` | `sources`, `neutral_brief`, `cutoff`, `possession_ledger`, `genre_references` | Review candidate Sources for purpose, possession, chronology, form, density and cues. Limit the ledger to transmission. Return per-Source revision tickets. Exclude hidden history, semantic targets, keys and extraction outputs. |
| `annotation` | `sources`, `neutral_brief`, `ontology`, `annotation_rules` | Review exactly one locked, ordered bundle. Return the complete graph, exact evidence and minimum sufficient alternatives, contradictions, open questions and dangerous guesses. Exclude variant names, siblings, intended answers, peer labels and extraction outputs. |
| `adjudication` | `sources`, `annotation_a`, `annotation_b`, `neutral_brief`, `ontology`, `annotation_rules` | Reconstruct disagreements against the locked Sources and commit a provisional key. Exclude hidden history, paired conditions and interventions until this key is committed. |
| `audit` | `paired_bundles`, `intended_intervention`, `provisional_keys`, `neutral_brief`, `ontology`, `audit_rules` | After provisional adjudication, compare the actual matched bundles and key differences. Audit evidence sufficiency, masking and shortcuts. |
| `masked` | `sources`, `neutral_brief`, `ontology`, `annotation_rules` | Give a fresh reader only the masked or subset bundle and the neutral annotation instructions. Exclude unmasked facts, target labels and the intended effect. |
| `probe` | `probe` | Use harmless synthetic test text to verify the runtime. |

The runner checks labels. The custodian supplies the appropriate fields for
each role and verifies that the text stays within its allowed scope.

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
   checks. Keep their responses with the audited revision.
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

Use the opt-in replay from the repository root once a family has all three frozen
Source arrays, a committed declaration, complete adjudicated keys and saved
ideals. Run `uv run python -m benchmark_v3.replay --manifest PATH/manifest.json --artifacts EMPTY_DIRECTORY`.
The preview sets the maximum provider attempts to zero. Reopen the saved Run
and inspect its coverage, complete graph scores, eligible Source associations,
same-edge proof, and the exact paired decisions in `preflight.json`. The replay
raises an error if any ideal fails. Test inputs are defined in
[the replay tests](../../tests/research/test_v3_replay.py).

The owner reviews the complete file and dossier and records accept, return or
quarantine against a dated package and annotation digest and evidence policy.
A pending dossier stays outside execution. A failed or incomplete comparison
keeps its planned and scored coverage visible. This workflow ends at admission.
