# Product demo verification

Completed 18 October 2026, Asia/Hong_Kong.

## Delivered media

Both files are H.264 / yuv420p MP4, **1920×1080, 30 fps, 2,520 frames, exactly
84 seconds**, with burned-in captions and no audio track. Both decoded in full
without errors using the pinned Remotion FFmpeg and its rawvideo encoder.

| Locale | Bytes | SHA-256 |
| --- | ---: | --- |
| en | 10,581,496 | `d1f37dd6be61321fdb645a144ac285375b174e562f3884027dc9e8249a7ef891` |
| zh-CN | 9,189,136 | `0a8ae0460d41b4256111f5deae8d56ee779bd660e6bd7fadd0200133f1c5083f` |

Files are in `output/private-client-graph-demo-{en,zh-CN}.mp4`.
`output/render-video.json` records the complete input capture hashes and output
hashes. `qa/demo/media-verification.json` records independent ffprobe counts and
decode results. Generated media and QA intermediates are local ignored outputs.

## Visual inspection

Inspected 49 rendered frames per language across all fourteen shots, including
every caption cue and the graph/evidence/source camera positions. Rendered the
20-second connected-review segment in both languages. Inspected final encoded
frames at 17.8, 55, 63.8, 73.8 and 83.96 seconds to check intake actions, exact
quotation, whole-proposal confirmation, saved-row reopening and closing framing.
The final framing revision keeps the Matter reference and Source tabs visible.

- English and Chinese captions fit inside the 1080p canvas with local fonts.
- Exact Source 2 trustee and Source 1 parent quotations remain English, unaltered.
- The native source highlights and graph selections come from real app captures.
- Captured typing reveals actual before/after image pixels; no replacement UI text.
- Continuous camera endpoints carry review through graph, evidence and source.
- Action pointers align with visible controls. Intake and reopen positions were
  adjusted after visual inspection; every click also has a viewport-bounds test.
- Confirmation precedes the accepted state. The accepted row was reopened through
  the actual app and verified against persisted Source evidence.
- The synthetic-workflow badge remains visible throughout. The local-fixture and
  edited-timing label is visible during analysis and proposed-result shots.

The UI captures originated as browser JPEGs at 1440 CSS pixels wide, so magnified
interface text retains their original raster detail. Captions are rendered at
native output resolution. This is an edited, silent product walkthrough using
synthetic fixtures and the existing local model adapter; it is not live inference,
analysis-latency evidence or a real-client readiness claim.

## Validation

- `npm run lint`: passed (ESLint and TypeScript).
- `npm test`: **17 passed, 1 skipped**. The optional `pdftotext` check is skipped
  because that executable is unavailable. Exact quote contracts, real capture
  integrity, locale coverage, timing, camera continuity, click visibility and
  export rejection paths pass.
- `npm run build`: passed. Final exports also bundled the final scene code.
- `ruff check scripts/prepare-captures.py`: passed.
- `npx prettier --check src scripts/*.mjs`: passed.
- Repository `uv run pytest`: **537 passed, 204 skipped**. Persistence checks
  requiring `TEST_DATABASE_URL` are skipped when it is unset. The recorded browser
  transaction used the dedicated local PostgreSQL instance documented in provenance.
- Final `git diff --cached --check`: passed.
- Paid provider invocations: **0**.

## Code Quality Review

The complete added project was inspected against `AGENTS.md` and
`docs/CODE_STYLE.md`, including scripts, configuration, source, capture manifest,
font licensing and production documentation. The export guard prevents direct
Studio rendering from substituting missing captures. Final review extracted the
capture-integrity gate for explicit changed/missing-full-page tests, corrected
full-page capture-origin metadata, and removed duplicated scope-badge copy.
No material readability concerns remain. All changes are inside
`presentation/product-demo`; production application code, extraction semantics,
validation, evaluation, ground truth and migrations are unchanged.
