# Reproduce the public research publication

The public Research Results interface and landing summary read the single packaged
`research-results.v1.json` artifact through `/api/research-results`. Its download
endpoint serves identical bytes. This read path imports no research, provider,
scoring, database or Workbench code. Missing or corrupt publication data returns
503; there is no live or private fallback.

The offline publisher is deliberately scoped to the retained final held-out
Experiment `83b5778e74ba5e6e882d334fd4f87f09`:

| Label | Source Run |
| --- | --- |
| A | `97d26d8e5f9d5964826b144c9ca45ad7` |
| A′ | `d67a391bc95a5ad39e1b5786a04795c0` |
| B | `841389cef51957ce8523ea41c03d2baa` |

From an owner-retained copy of `resolver-comparison-results.zip`, run:

```sh
uv run python -m private_client_graph.research.publication \
  /path/to/resolver-comparison-results.zip /tmp/research-results.v1.json
cmp /tmp/research-results.v1.json private_client_graph/published/research-results.v1.json
```

The destination must not exist. Publication performs no model invocation, pipeline
execution, graph reconstruction or scoring. It verifies the approved report's
pinned SHA-256, complete report and nested raw-file checksum inventories, manifest
checksums, exact Run/Experiment/commit/plan identities, ten scored Observations per
Run, retained aggregate counts, original versus replay equality, frozen-input
pairing, exact Source/Evidence text and retained relationship-inspection outcomes.
The trusted report-package SHA-256 is
`74167126e2b4af44ff9beedba0c4304520c47f89ea36d155d4c3ade12f980df8`.
Raw archives remain private and are not needed at application runtime or in CI.

Only explicit field projections enter the publication: identities/digests,
recorded metrics and coverage, synthetic Sources and expected relationships,
approved Evidence, retained canonical states and relationship outcomes, resolver
endpoint edits, and per-call model/status/usage/timing/recorded cost. Original
Sources, quotations, names and identities retain their exact text. Raw requests,
responses, prompts, credentials, authorization records, ledgers, paths and private
annotations are excluded, including unknown fields added to retained records.
The joined relationship outcomes come from the retained inspection report;
JavaScript does not reconstruct evaluator edge semantics.

The benchmark identity is the retained A′/B saved-input scope identity. A's
original fresh-input scope has a different identity because its input identities
and mode differ; the separately verified exact replay bridges these scopes.
Evaluator and aggregate version identifiers are frozen publication metadata.
Observation IDs are retained filenames verified against their planned slots.

The integrity envelope contains SHA-256 of the canonical UTF-8 JSON object with
its top-level `integrity` member excluded. Canonical JSON sorts object keys, uses
`,`/`:` separators, preserves Unicode, and forbids NaN. The served/downloaded
artifact is that canonical JSON plus a final newline. This defines digest
coverage without a self-reference. The snapshot ID and schema version are inside
the covered content.

A′ records zero calls and tokens. B's calls count only its ten resolver attempts;
reused A extractions are lineage, not newly executed provider calls. Cached tokens
are a subset of input tokens. Missing metadata stays null; unavailable pricing is
Unpriced. Provider duration is summed call duration, not elapsed experiment time.
These ten published project-authored synthetic cases were an internal development
benchmark; the post-hoc exploratory comparison establishes no production accuracy
or reliability, and publication prevents treating them as unseen future tests.
