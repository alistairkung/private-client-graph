# Submission deck checkpoint

This is a **draft for review**, not the final submission. Held-out benchmark approval, frozen-chain evaluation, actual result figures and approval of the updated deployment remain pending. No paid provider calls form part of deck preparation.

`build.mjs` creates ten editable slides with native architecture/provenance diagrams, actual application screenshots and a results slide driven only by supplied retained results. It writes a versioned PPTX and PDF, private slide previews and a validation receipt. The checked-in `draft/` contains the current checkpoint for inspection.

## Rebuild the draft

Use the bundled Node executable supplied by `load_workspace_dependencies`:

```bash
/Users/alistair/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node submission/build.mjs --draft
```

The source accepts `PCG_ARTIFACT_RUNTIME` and `PCG_PRESENTATIONS_SKILL` when installed runtime locations differ. The draft carries visible review labels on every slide.

## Supply actual results

After explicit user benchmark approval and chain freeze, save `submission/final-results.json` following `final-results.schema.json`, then run without `--draft`. `run_ids` is an array. Supply the frozen code commit, actual model, all planned case outcomes including failed/unscored cases, provider attempts, retained artifact paths and verified USD costs or `null`.

Relationship precision/recall/F1 use semantic edges. `quote_provenance_accuracy` measures approved quote support per true-positive edge. `source_attribution_accuracy` measures source correctness per assessed Evidence item and can be null when unavailable. Report scored/planned coverage independently. Neither metric can stand in for the other. Final generation refuses absent approval, lineage or inconsistent coverage. It does not execute experiments or contact a provider.

`deployment_verified` must reflect a fresh-session check of the new public showcase. When false, the deck explicitly describes the current earlier Case 01 deployment and the local preview. The URL alone is not evidence that the new showcase has shipped.

The final-results schema contains no example scores. Actual failure descriptions populate the findings slide. The source does not treat curated ideal fixtures or deterministic browser substitutions as model-quality measurements.

## Current checkpoint limitations

The source and editable diagrams are ready for continued work. Full-size slide review, screenshot composition and result-chart validation must be completed again after final data enters the deck. Draft screenshot crops may need improvement. A successful package/layout check does not establish final visual quality or factual completeness.

The PPTX finalizer checks package integrity, layout geometry and font policy, and successfully reimports the exported file. The bundled Artifact Tool PDF exporter currently lacks `#standard-fonts/Helvetica`; the script falls back to the bundled headless office renderer without changing runtime dependencies.
