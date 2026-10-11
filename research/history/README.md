# Retained history for the read-only Workbench

These are existing, unmodified portable exports, not newly executed experiments.
`issue-92-pilot.zip` is the Issue #92 release asset
`issue-92-pilot-with-authorization.zip` (SHA-256
`a87c2b9a7fa3585a2fc8860e4007f1e3132ef3833abad068ab7aaf124a78580d`).
`issue-91-demonstration.zip` is the retained reviewed recorded-provider demonstration.
Each archive includes its original manifest, frozen inputs, observations, results,
report and internal checksum inventory. Demonstration results are not live quality
measurements. Frozen absolute ledger paths are preserved and convey no execution
authority. Local task ledgers remain in the persistent `runs/research` mount;
these historical exports are sufficient for read-only inspection, not execution.

The workbench bootstrap restores these verified archives into new directories only.
It never replaces an existing bundle. Additional bundles placed below the artifact
root appear after an explicit index rebuild. Never put real client data here.
