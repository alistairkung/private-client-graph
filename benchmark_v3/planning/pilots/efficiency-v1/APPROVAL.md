# Owner approval and staged dispatch

The owner accepted the scientific direction and budget at PR #198
revision `aed65c42ce02ea9af86705877cbd51b7f4caf39c`. Final dispatch
authorization is pending. The [approval drafts](owner-approval) pin
the owner, [portfolio](portfolio.json), three registered hypotheses
and [schema 2 manifest](manifest.json). The request is for 79 scientific
sessions, allocated H=20, I=25 and J=34, up to three workers, the manifest's
Medium/High allocations, and zero paid PCG extraction calls.

1. After the owner explicitly authorizes dispatch on the exact package,
   fill the actual `decided_on` and `decision_reference` in the batch
   draft, including its nested portfolio decision, and in the three
   hypothesis drafts. Cite the owner decision and reviewed PR revision.
   Place the three completed hypothesis decisions under
   `benchmark_v3/planning/decisions/<hypothesis-id>@1.json`. Keep the
   completed batch decision in private custody as `$APPROVAL`.
   The pending drafts have null attestation fields and fail validation.
2. Use one owner-only, canonical custody directory outside Git as
   `$CUSTODY`. From the approved checkout, commission and dispatch
   designs only. Capture the three commitments for the owner review.

   ```sh
   pilot=benchmark_v3/planning/pilots/efficiency-v1
   batch=efficiency-pilot-v1
   uv run --locked python -m benchmark_v3.batch commission "$CUSTODY" "$pilot/portfolio.json" "$pilot/manifest.json" "$APPROVAL" "$pilot/os-boundary.json"
   uv run --locked python -m benchmark_v3.batch run "$CUSTODY" "$batch"
   uv run --locked python -m benchmark_v3.batch designs "$CUSTODY" "$batch"
   ```

   If a design remains blocked, inspect `package` for the exception.
   Reopen the same custody for recovery to retain charges and completed
   designs. The authoring gate stays closed.
3. The owner reviews the three private design files at
   `$CUSTODY/batches/$batch/<family>/1/design.json`, including retainer,
   meeting purpose, participant knowledge, origins and custody. Record
   their disposition for each of the three digests in a private
   `$DESIGN_REVIEW` file. Use `schema design-review` for the fields and
   copy the manifest and design digests from `designs`. Give a reason for
   each return. Resume only the accepted families and package their
   dossiers for human admission.

   ```sh
   uv run --locked python -m benchmark_v3.batch review-designs "$CUSTODY" "$DESIGN_REVIEW"
   uv run --locked python -m benchmark_v3.batch run "$CUSTODY" "$batch"
   uv run --locked python -m benchmark_v3.batch package "$CUSTODY" "$batch"
   ```

## Evidence for the post-pilot recommendation

Record human review time, defects and reasons by design digest. Mark
which objections would have made the design scientifically unusable,
which required repair and which were resolved by deterministic checks.
Retain any downstream realism, blind-review or masking findings that
trace back to a design decision.

After the pilot, recommend whether an isolated independent reviewer
could assess future designs in shadow mode against those human findings.
Assess material misses, disagreements, cost, access boundaries and the
ability to escalate uncertainty. Three designs can identify useful
checks or reasons to retain human review. Replacing the gate would
require evidence across a broader and independently reviewed workload.
