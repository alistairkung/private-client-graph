# Practitioner product demo

An 84-second founder-style walkthrough of the existing authenticated practitioner
application. English and Simplified Chinese use the same timeline: 30 fps,
2,520 frames. The story begins already signed in and follows one intake all the
way to a saved, reopened Matter. It does not introduce a separate sign-in screen.

The on-screen copy and timing authority is `src/story.ts`. Titles are at most
seven English words; each supporting cue is at most twelve. Cue times are relative
to their shot. Exact source quotations remain English in both versions.

## Capture and timeline

Capture the real application at 1440×900 in both locales. The image key is locale-independent; filenames use
`public/captures/{locale}-{imageKey}.png` for `en` and `zh-CN`.
Do not paint replacement interface text, graph relationships or source highlights
into the captures. A shot may move the camera over its authentic capture without
changing application content. Full-page variants keep their original pixel height.
A constant-size drawn pointer indicates actions; the reference and title reveal
uses the actual before/after captured pixels. Camera endpoints match across the
proposal → relationship → evidence → source → decision sequence. Page navigation
uses purposeful cuts, as in an edited founder demonstration.

| Seconds | Frames, start inclusive | Image key          | Story beat and actual action                                                    |
| ------- | ----------------------- | ------------------ | ------------------------------------------------------------------------------- |
| 0–6     | 0–179                   | `ledger`           | Already signed in; introduce the Matter workspace.                              |
| 6–10    | 180–299                 | `intake-empty`     | Choose **Create Matter**.                                                       |
| 10–14   | 300–419                 | `intake-reference` | Fill **External Matter reference**.                                             |
| 14–18   | 420–539                 | `intake-title`     | Fill **Matter title**.                                                          |
| 18–26   | 540–779                 | `intake-files`     | Select both PDFs, name each Source and confirm synthetic material.              |
| 26–30   | 780–899                 | `intake-files`     | Choose **Upload and analyse**; edit forward to the saved proposal.              |
| 30–38   | 900–1139                | `proposal`         | **Proposed relationships**, saved and awaiting confirmation.                    |
| 38–47   | 1140–1409               | `selected-trustee` | Select **Morgan Example — Trustee of — Fictional Trust**; identify Source 2.    |
| 47–56   | 1410–1679               | `source-trustee`   | **View in source**; keep the exact highlighted quotation readable.              |
| 56–64   | 1680–1919               | `confirmation`     | Show the whole-proposal decision, then **Confirm and create Matter**.           |
| 64–70   | 1920–2099               | `accepted`         | **Matter created** and **Accepted relationships**.                              |
| 70–74   | 2100–2219               | `ledger-saved`     | **Back to Matters**; reopen the accepted row.                                   |
| 74–80   | 2220–2399               | `reopened-parent`  | Select **Alice Example — Parent of — Ben Example**; Source 1 remains available. |
| 80–84   | 2400–2519               | `reopened-parent`  | Short closing message; no additional capability or transaction.                 |

The four-second analysis beat is an editorial interval, not measured execution
time. It reuses the submitted intake capture and cuts to the actual saved result;
do not fabricate a loading state, progress bar, live inference or speed claim.
The confirmation shot must show the real decision control before the accepted
Matter shot. The reopened shot must come from the saved Matter route.

## Demonstration provenance

Use the existing deterministic local workflow documented in the repository
`README.md`, “Protected local development.” It retains real authentication
callback/session checks, PDF parsing, graph construction, proposal review,
confirmation and PostgreSQL persistence. Only external Google and model
boundaries are substituted by `local_development/server.py` and
`local_development/model.py`. This is a workflow demonstration, not a live-model
quality result or recording of Google's sign-in page.

The existing two-document browser journey in `web/e2e/proposals.spec.ts` supplies
the exact fixture pair:

1. `tests/fixtures/synthetic-proposal.pdf`: **Alice Example is the parent of Ben Example.**
2. `tests/fixtures/multiple-role-proposal.pdf`: Morgan Example's three separate
   roles in Fictional Trust. This demo selects the trustee relationship and its
   quotation: **Morgan Example is trustee of the Fictional Trust.**

Use a unique synthetic Matter reference and a plainly fictional title. Source
titles are practitioner-entered labels; keep the titles in captions consistent
with the actual captures. The story identifies Sources by number to avoid
inventing or silently changing their titles. The two fixture components do not
assert a family connection between Alice, Ben and Morgan.

## Scope and visible disclosures

Keep `scopeBadge` visible: **Synthetic workflow demonstration** /
**合成资料流程演示**. Show `fixtureNotice` during the upload/analysis and proposal
handoff: **Local fixture analysis · timing edited** /
**本地预设分析结果 · 时长经剪辑**. Preserve the application's synthetic-only
notice whenever its captured region is in view.

Current intake supports one to five text-layer PDFs, up to 10 MiB combined,
50 pages per PDF and 100,000 extracted characters combined. This walkthrough
uses two. The current implementation and browser tests supersede older
single-PDF design prose for the demonstrated workflow.

Analysis saves a proposal, not an accepted Matter. Confirmation accepts the
whole proposal and its supplied Sources; there is no per-relationship acceptance
or editing step. Accepted state reopens without another analysis. Do not imply
retained PDF files, arbitrary live-model accuracy, incremental Matter updates,
review-history functionality, confidential-client readiness or per-user Matter
permissions. All allowlisted practitioners in the synthetic deployment share
access. No paid provider calls are needed for this demonstration.
