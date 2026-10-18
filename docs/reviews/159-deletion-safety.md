# PR 159 deletion safety

Reviewed against `9907029e` with the accepted public-read policy in
[ADR 0011](../adr/0011-make-synthetic-matter-reads-public.md). The review found one
accidental product regression, now corrected: capability loading/failure was
being presented as confirmed sign-in unavailability. The simulated demo and
public showcase execution interface are intentionally retired. They are not
feature-equivalent replacements for every old illustration.

## Production publication audit

On 18 October 2026 at 12:15 UTC, the running production service contained three
Matters, four Sources and **zero pending proposals**. Read the complete collections
and every Matter detail through the existing authenticated production GET APIs,
using the normal Google sign-in flow. The collection endpoints enumerate all
records without pagination or owner filtering. Inspected full Source text,
identities, entities and retained relationship/Evidence state. No production
record, deployment, access policy, SSH key or network setting was changed.
At 12:20 UTC, a second inventory returned the same three Matter IDs and zero
pending proposals.

| Existing production record | Sources / relationships / Evidence | Publication assessment |
| --- | --- | --- |
| `PC/2026/0142` — Evergreen Family Trust | 1 / 6 / 5 | Source matches `cases/case_01/source.txt` byte-for-byte by SHA-256; established synthetic example. |
| `TestMatterMulti` — MultiSource | 2 / 4 / 4 | Full text matches the extracted text of `multiple-role-proposal.pdf` and `synthetic-proposal.pdf` in `tests/fixtures`; explicitly fictional Example people and Fictional Trust. |
| `TestMatter` — Test Trust | 1 / 1 / 1 | Full text matches the extracted `synthetic-proposal.pdf` fixture; fictional Example parent/child. |

All existing Source text is accounted for by these three fingerprints:

| Input | Characters | SHA-256 |
| --- | --- | --- |
| Evergreen source | 6450 | `191f8cd171748f5721922e742323bbe913354d1fbbb3c2891a9a50fd079739a7` |
| Multiple-role PDF extracted text | 153 | `4dfbc01757d85c5cba924b9c5e975a4b2139b8f0ec2974148104720c6b18ca3e` |
| Synthetic-proposal PDF extracted text, present twice | 43 | `4204eca54b5be9769171977c6568c87450c0aafc234a935d65e45794f9a66fb0` |

No real-client material was found. These records are suitable for the agreed
synthetic public prototype. This is a point-in-time content audit, not a guarantee
about later submissions; recheck if the inventory or text changes before release.
Raw Source text and credentials are not copied into this report.

### Meaning of public pending Sources

After release, anyone can enumerate pending proposals and read every stored
Source title and the **entire extracted Source text**, including passages with no
relationship or Evidence. Proposed, professionally unaccepted relationships and
Matter references are also public. Saving a proposal is the publication point;
confirmation is not a confidentiality or publication gate. Anonymous readers
need neither an account nor a previously shared detail URL. The API does not
provide original uploaded PDF bytes under this contract.

Confirmation keeps the accepted state public. Discard removes the stored pending
state but cannot retract copies already read, downloaded or indexed. Authentication
protects mutations, not confidentiality. Upload disclosure and synthetic-only
attestation remain visible. The accepted policy has not changed; no redaction,
tenant authorization or real-client-data capability is introduced.

## Before/after feature parity

Old behavior was verified from `DemoApp.tsx` and its browser tests at the base
commit. Every `/demo*` URL now returns a permanent 308 redirect to `/app`.

| Before | After / accessible destination | Classification |
| --- | --- | --- |
| `/demo` fixed ledger | `/app` real accepted Matter and pending-proposal collections | Real public reading retained; separate simulated ledger retired. |
| Disabled intake preview at `/demo/matter-proposals/new` | `/app/matter-proposals/new` real intake, with sign-in for writes | Disabled imitation retired; useful workflow retained behind the agreed write gate. |
| Always-present Hillcrest proposal at `/demo/matter-proposals/hillcrest` | `/app/matter-proposals/{uuid}` reviews any actual pending proposal; Hillcrest Sources/graph/Evidence remain on `/`, selecting Case 04 | Generic proposal review retained. Fixed pending Hillcrest illustration deliberately retired; no pending sample is seeded or currently present in production. |
| Anonymous whole-proposal confirmation preview at `/demo/confirmation/hillcrest` | Authenticated real proposal decision explains whole-state acceptance and offers confirmation/discard | Static preview and anonymous confirmation explanation deliberately retired. Real protected decisions retained; this is not full explanatory parity for anonymous readers. |
| Completed Hillcrest Matter at `/demo/matters/hillcrest` | Curated Hillcrest Case 04 on `/` | Multi-source graph/Evidence retained; fixed accepted-Matter illustration deliberately retired. No Hillcrest Matter seed is added. |
| Completed Evergreen at `/demo/matters/evergreen` | Real seeded `/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369`, reachable from `/app` | Useful persisted completed example retained; old example URL itself redirects to the ledger. |
| Example-specific demo deep links and refresh | All old links reach `/app`, losing old example identity; real Matter/proposal UUID deep links and refresh remain supported | Intentional compatibility reduction, not equivalent deep-link preservation. |
| Unauthenticated legacy sample/live showcase execution | Curated showcase reads; authenticated real intake; separate authorized local Research Workbench | Obsolete public execution feature deliberately retired; semantic pipeline and research execution retained. |

No duplicate demo machinery, permanent pending sample lifecycle, redesign or
domain changes are required by this review.

## Useful first anonymous visit

Production actually contains the persisted Evergreen Matter above. `railway.toml`
also explicitly runs the insert-only Evergreen seed after migrations before
deployment, so a new deployment is initialized independently of browser traffic.
The seed preserves existing state. Anonymous `/app` reading and opening the
seeded Matter's graph/Evidence, direct navigation and refresh have real-backend
browser coverage. Reads do not silently fabricate state. A manually launched
unseeded database can legitimately be empty; the setup guide requires migration
and explicit seeding.

## Standards

No remaining executable import, test consumer, documentation hyperlink or tracked
presentation asset depends on the retired endpoints/modules. Both independent
review passes inspected the complete PR diff. A tracked-file byte scan included
presentation scripts, HTML, JavaScript, images, video and font assets. Remaining
retired names are intentional route-removal tests, marked historical records,
an illustrative composition example, and immutable historical quota storage.

Corrected stale active instructions in `DESIGN.md`, `WEB_APP_GUIDELINES.md` and
the public-landing visual handoff that named deleted analysis controls or asked
the browser to request a retired execution mode. No broken Markdown links were
found. The focused follow-up diff has no material readability or scope findings.

A separate untracked local `presentation/remotion/qa/capture-host` snapshot in
the landing checkout still contains copied historical source/tests. It is not
part of this PR, the production package, CI or the tracked presentation pipeline;
it is retained capture history, not an active consumer. It was not modified.

## Spec

The confirmed access-state regression is fixed with distinct loading, error and
ready states. Loading makes no claim that sign-in is unavailable; a failed check
offers retry while public collection/detail reads remain usable. Confirmed writer
capability restores creation and account actions without reloading. Only an actual
unavailable response shows unavailable copy. New deferred-response, retry and
real-browser cases cover this behavior. The account menu treats unknown access
as unknown, and proposal decisions remain disabled until write eligibility is
confirmed. Server authentication, absolute expiry, current allowlist, Origin and
CSRF gates remain unchanged.

Research Workbench, research publication, curated Sources/graphs, exact Evidence,
canonical identity/validation, benchmark fixtures, migrations and mutation
protections are preserved. No paid provider calls or new data-handling permissions
were used. Intentional retirements in the table are not presented as parity.

## Validation and CI

The reviewed head `e50d43b6` passed `python`, `browser-e2e`, `docker-smoke` and the
aggregate `tests` job. Focused-fix local validation and the new-head CI snapshot
are reported in PR 159 and at handoff. Local validation passed 739 Python tests,
124 production-web units, 26 research units, 70 desktop/phone application browser
checks and 16 Research Workbench history/Evidence browser checks. The two existing
viewport-specific history skips are unchanged. Both builds and TypeScript checks
passed. An independent follow-up confirmed that the Matter error mocks and
confirmation-status locator corrections retain their original assertions.
Pending CI never implies merge readiness.
No automatic merge or deployment is authorized or performed.
