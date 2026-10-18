# Product demo provenance

## Status and source pin

This is the production record for an **84-second / 30 fps / 2,520-frame** bilingual
workflow video. Authentic captures were completed in Chrome on 18 October 2026
(Asia/Hong_Kong). The user handled the localhost certificate warning manually.
Final rendering and verification results are recorded in `QA.md`.

Application source: `alistairkung/private-client-graph`, commit
`a83b0e4af14fa79a899cadea7cf833c5ad7a96c8` (the fresh main checkout used for this
production task). Presentation code is isolated under `presentation/product-demo`.
No production application file has been changed to stage this demonstration.

The actual UI follows `DESIGN.md`,
`docs/design/matter-ledger-visual-spec.md` and
`docs/design/matter-workflow-implementation.md`. Current source and
`web/e2e/proposals.spec.ts` govern the implemented multi-PDF behavior; older
single-PDF design prose does not override the current one-to-five-PDF interface.

## Local environment verified

| Item | Recorded value |
| --- | --- |
| Browser entry | `https://localhost:8444/app` |
| Compose project | `pcg-product-demo` |
| Application container | `pcg-product-demo-application-1` |
| Database container | `pcg-product-demo-database-1` |
| Dedicated database volume | `pcg-product-demo_pcg-postgres-data` |
| Database image | `postgres:16` |
| Build definition | Unchanged `Dockerfile.dev` at the pinned commit |
| Capture override | `capture/compose.capture.yaml` |
| Startup observed | Alembic completed; Evergreen seed inserted; application started |
| Infrastructure verification | Database healthy; HTTPS `/health` returned 200 with its generated certificate explicitly trusted for that local check |

The existing port-8443 stack was inspected and left untouched. It packaged an older
provider adapter without the current multi-source dispatch substitution, so it was
not reused for this capture task. No existing volume was reset or removed.

The following packaged files were hashed inside the new application container and
matched the fresh source checkout:

| File | SHA-256 |
| --- | --- |
| `local_development/server.py` | `6fc0c945dd9bd253dadfff145cbb7521065cc9d251340f37b4796b0dc12e878a` |
| `local_development/model.py` | `48fdcdf77826af7b8b8fbbf17c0d91590987627054b1cc852d6923436b30142d` |
| `private_client_graph/api/app.py` | `f9e6e9b615b9dffc7f3a6337e4f17bc5869692e140c4cfda707751e942a64053` |

`local_development/google.py` substitutes external Google HTTP responses using a
synthetic allowlisted identity. The real application callback, secure session,
allowlist and request-authorization paths remain in use. This is not a recording
of Google's sign-in interface or a claim about a real practitioner's identity.

`local_development/server.py` replaces both `_extract_proposal` and
`_extract_proposal_sources` before external model dispatch. The deterministic
candidates come from `local_development/model.py`; no paid model invocation or
provider authority is required. PDF parsing, validation, canonical graph
construction, proposal storage, whole-proposal confirmation and PostgreSQL
persistence remain the application's real paths.

`local_development/https.py` generates a temporary self-signed development
certificate. Infrastructure health verification did not alter browser trust.
Any browser interstitial requires the normal user handoff; automated warning
bypasses are outside this capture procedure.

## Exact fixture inputs

Use these repository PDFs, in this order, without changing their bytes:

| Source | Repository path | SHA-256 |
| --- | --- | --- |
| 1 | `tests/fixtures/synthetic-proposal.pdf` | `08402d562dd08c8b409ecc8d4e5107288d2a5f9a9b91e8f2573a5ba9226e24ff` |
| 2 | `tests/fixtures/multiple-role-proposal.pdf` | `0f6e37ae1b4d6fc72f3eb1f43b3d92b13bb09c73662ca6a2a6e5da4495f3820e` |

The recorded selection in Source 2 must show:

> Morgan Example is trustee of the Fictional Trust.

The reopened-Matter selection in Source 1 must show:

> Alice Example is the parent of Ben Example.

Source 2 also supports Morgan Example's separate settlor and beneficiary roles.
No family connection between Alice, Ben and Morgan is asserted. Exact quotations,
entity names and practitioner-entered Source titles remain English in the Chinese
version. The PDFs were staged as `01-family-note.pdf` and `02-trust-roles.pdf` to
preserve Source order in the native picker. Their bytes match the hashes above;
only the filenames changed.

## Recorded transaction

- Matter reference: `DEMO/2026/001`
- Matter title: `Fictional relationships review`
- Source 1 title: `Family note`; Source 2 title: `Trust roles`
- Proposal: `/app/matter-proposals/98dfc7a9-c685-4c5c-939f-1c291c1b7e3a`
- Accepted Matter: `/app/matters/7759bfa7-cbe0-4a50-8bbb-3419bf2ea90f`

One analysis and one whole-proposal confirmation were performed through the real
application. Both locales show the same persisted transaction. The accepted row
was reopened and Source 1's parent quotation verified. The intake was subsequently
re-entered for full-page framing captures, without submitting another analysis or
creating another Matter. Intermediate file-picker and relationship-selector
operations are editorially omitted. The final trustee selection was verified
through the application's relationship selector with Source 2 active.

Paid provider invocations for the entire task: **0**.

## Authentic application areas

| Demonstrated area | Source implementation |
| --- | --- |
| Practitioner shell and register | `web/src/features/matters/PractitionerApp.tsx`, `MatterLedger.tsx`, `web/src/features/matter-proposals/ProposalCollection.tsx` |
| Intake and selected PDFs | `web/src/features/matter-proposals/CreateMatter.tsx`, `SourceDocuments.tsx` |
| Saved proposal and decision | `web/src/features/matter-proposals/ProposalWorkspace.tsx`, `ProposalDecision.tsx` |
| Graph, selected Evidence and Source | `web/src/features/review/SourceAwareReviewWorkspace.tsx`, `RelationshipGraph.tsx`, `GraphView.tsx`, `EvidencePanel.tsx`, `SourcePanel.tsx` |
| Accepted Matter and reopen | `web/src/features/matters/MatterWorkspace.tsx` |
| Localization | `web/src/shared/locale.tsx`, `locale-catalogue.ts`, `LanguageControl.tsx` |

Preserve the actual component styles in `web/src/styles/global.css`,
`web/src/styles/fonts.css`, `web/src/features/matters/practitioner.css`,
`web/src/features/matter-proposals/proposals.css`,
`web/src/features/review/review.css` and `source-aware-review.css`, including the
ReactFlow stylesheet. The Remotion layer may frame, crop, magnify and annotate
these captures, but must not paint replacement UI states, graph facts, quotations
or highlights into them.

## Completed capture inventory

All twelve states have English (`en`) and Simplified Chinese (`zh-CN`) variants.
There are 24 viewport PNGs at 1440×900 and 22 original-height full-page PNGs;
only the initial ledger needs no full-page variant. The browser tool emitted JPEGs,
which `scripts/prepare-captures.py` decoded to PNG without retouching. The manifest
records both original JPEG and packaged PNG hashes. The video crops only the
empty rightmost 14 pixels to exclude the parked capture-tool pointer.

| Image key | Required actual state |
| --- | --- |
| `ledger` | Authenticated register before this intake |
| `intake-empty` | Create Matter form before entering details |
| `intake-reference` | Unique synthetic external reference entered |
| `intake-title` | Fictional Matter title entered |
| `intake-files` | Both fixture PDFs, Source titles and synthetic confirmation |
| `proposal` | Actual saved proposal awaiting confirmation |
| `selected-trustee` | Morgan trustee relationship selected; Source 2 attribution |
| `source-trustee` | Exact Source 2 quotation after View in source |
| `confirmation` | Actual whole-proposal decision and confirmation control |
| `accepted` | Actual created-Matter notice and accepted relationships |
| `ledger-saved` | Persisted accepted row after return to Matters |
| `reopened-parent` | Reopened saved Matter; Alice parent relationship and Source 1 |

`public/captures/manifest.json` records each PNG's SHA-256, local route, viewport,
document height, scroll position and capture origin. Full-page images begin at
page Y=0; viewport images begin at the recorded scroll position. Selected
relationship and Source identities follow the table above. The generated
`src/captured-pages.ts` selects the authentic full-page image and its height for
each shot, preserving the original aspect ratio.

The renderer must reject an incomplete capture inventory. No placeholder capture,
public `/demo` screen or manufactured accepted state can satisfy this gate.
Detailed UI capture steps are in [README.md](README.md); the shot sequence and
caption authority are [STORYBOARD.md](STORYBOARD.md) and `src/story.ts`.

## Boundaries and verification

- Only synthetic repository fixtures are used; no real client information.
- No paid provider calls are needed or authorized for this workflow recording.
- Analysis output is a deterministic local fixture, not a measured live result.
- The four-second analysis handoff is editorial timing, not latency evidence.
- Confirmation accepts the entire proposal and supplied Source state. No
  per-relationship acceptance, edit history or incremental Matter update is shown.
- PDF files are acquisition inputs; the demonstration does not claim retained PDFs.
- Reopening uses persisted accepted state, without another extraction.
- This prototype's authenticated synthetic flow does not establish confidential
  client readiness, per-user Matter permissions or a production tenancy design.

Keep the visible captions “Synthetic workflow demonstration” / “合成资料流程演示”
and, during the analysis handoff, “Local fixture analysis · timing edited” /
“本地预设分析结果 · 时长经剪辑”. `QA.md` records visual and media verification.
The timeline keeps exact quotations and real highlighted passages in both locales.
The source images are a recording of the app, not a recreated interface.
