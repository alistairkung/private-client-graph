# Practitioner product demo

An 84-second, captioned walkthrough of the authenticated practitioner application
in English and Simplified Chinese. Each video is 1920×1080 at 30 fps: 2,520 frames.
The two versions share the workflow and timing in [STORYBOARD.md](STORYBOARD.md)
and `src/story.ts`. This is a synthetic workflow demonstration; it does not
measure model accuracy or transaction speed.

## Production status

The authenticated workflow was captured in Chrome on 18 October 2026 using one
synthetic proposal and its accepted Matter. Both locale edits are 84 seconds,
1920×1080, 30 fps, with burned-in captions and no audio track.

Outputs (generated locally, ignored by Git):

- `output/private-client-graph-demo-en.mp4`
- `output/private-client-graph-demo-zh-CN.mp4`

Capture provenance, exact fixture hashes and the saved Matter identity are in
[PROVENANCE.md](PROVENANCE.md). The film uses authentic application captures,
continuous camera moves within review, a drawn cursor and a reveal of the actual
recorded input pixels. It makes no model-quality or analysis-speed claim.

Validation results and final media checks are recorded in `QA.md`. Rendering
rejects missing, changed or incorrectly sized capture assets. Direct Studio
exports also reject missing captures; the explanatory pending view is Studio-only.

## Local capture application

From the repository root, start or reuse the dedicated capture project:

```bash
docker compose -p pcg-product-demo -f compose.yaml -f presentation/product-demo/capture/compose.capture.yaml --profile practitioner up --build -d application
```

Open **https://localhost:8444/app**. The capture override uses a dedicated
`pcg-product-demo_pcg-postgres-data` volume and leaves the existing application at
port 8443 untouched. Startup applies the normal Alembic migrations and inserts
the Evergreen synthetic seed if absent. Do not reset or delete the database.

This environment uses the existing synthetic Google and model adapters. Session
authorization, PDF parsing, canonical graph construction, proposal confirmation
and local PostgreSQL persistence remain real. No production application changes,
external Google sign-in, provider credentials or paid provider calls are needed.
The temporary development certificate is self-signed. If the browser shows a
security warning, stop for the user's normal certificate handoff; do not disable
certificate verification or bypass the warning through automation.

When capture is finished, the dedicated project may be stopped without deleting
its data:

```bash
docker compose -p pcg-product-demo -f compose.yaml -f presentation/product-demo/capture/compose.capture.yaml --profile practitioner stop application database
```

## Capture both languages

Use the authenticated `/app` journey, already signed in when the story starts.
Set the browser viewport to **1440×900** and use its native language control to
select English or 简体中文. Capture the actual viewport after fonts, graph layout
and selection effects have settled. Scroll the real application as needed for
the requested state; do not stretch a full-page image into the viewport.

1. Capture the initial Matter register in both locales.
2. Choose **Create Matter**. Capture the empty form, a unique synthetic reference,
   and a plainly fictional Matter title. Record the same identity in both locales.
3. Select byte-identical copies of `tests/fixtures/synthetic-proposal.pdf` and
   `tests/fixtures/multiple-role-proposal.pdf`, named `01-family-note.pdf` and
   `02-trust-roles.pdf` to preserve Source order in the native picker. Give each
   Source a title and explicitly confirm that the material is synthetic. Capture
   the completed form before submission.
4. Choose **Upload and analyse**. Capture the actual saved proposal. The four-second
   video handoff is edited time, not a recorded analysis-duration claim.
5. Select **Morgan Example — Trustee of — Fictional Trust**. Capture the selected
   relationship with Source 2 attribution, then use **View in source** and capture
   the exact highlighted quotation.
6. Capture the whole-proposal decision in both locales before choosing
   **Confirm and create Matter**. Capture the actual created-Matter notice and
   **Accepted relationships** in both locales before leaving that route.
7. Return to Matters, capture the accepted row, reopen that saved Matter, and
   select **Alice Example — Parent of — Ben Example**. Capture its Source 1
   quotation in both locales.

Switch languages at each state to capture the same proposal and accepted Matter,
without repeating the transaction merely for localization. English source names,
entity names and exact quotations remain English in both versions. Captions and
application chrome use the selected locale.

The capture tool produced JPEGs. `scripts/prepare-captures.py` decodes them to PNG
without retouching any interface pixels. Run it with a staging directory containing
`capture-log.json` and `{locale}-{imageKey}.jpg` plus the available `-page.jpg`
variants. Python with Pillow is required for this packaging step only.

The packaged set contains 24 viewport captures (1440×900) and 22 full-page captures
(1440 pixels wide, original document height). `public/captures/manifest.json`
records hashes, routes, dimensions and capture origins. `src/captured-pages.ts`
selects the full pages for smooth pans without distorting their aspect ratio.
The empty rightmost 14 pixels are cropped in the video frame to exclude the
parked capture-tool pointer; the PNGs themselves remain unretouched.

## Remotion workflow

Use the Node.js version supported by `package.json`. From this directory:

```bash
npm ci
npx remotion browser ensure
npm run dev
npm test
npm run lint
npm run render:qa
npm run render:video
```

`dev` opens the local Remotion preview. `test` checks deterministic story and
presentation contracts; it is not a substitute for inspecting the actual captures.
`lint` runs ESLint and TypeScript. QA and video export are gated on the complete
capture set. Rendered output belongs in the ignored `qa/` and `output/` directories.
The scripts must report missing captures and stop rather than emit a misleading
video.

After captures are present, inspect both languages at every shot boundary and
caption change. Check exact quotations, Source attribution, cursor targets,
readable crop bounds, confirmation before accepted state, and reopening without
reanalysis. Verify the final two MP4 files have 2,520 frames at 30 fps and decode
successfully before recording final QA as complete.

## Code quality review

The full added project was reviewed against `AGENTS.md` and `docs/CODE_STYLE.md`.
The review identified a direct-Studio-export bypass of the missing-capture check,
which is now guarded and tested. Final review extracted a tested full-page hash/dimension
preflight and checked continuity through review cuts and visibility of every
cursor click. Capture metadata distinguishes viewport origins from full-page
origins. Scope is limited to this presentation project; no production application,
domain semantics, migrations or benchmark fixtures were modified. No material
readability problems remain.
