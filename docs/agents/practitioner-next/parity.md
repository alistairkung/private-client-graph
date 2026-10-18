# Practitioner functionality parity

The explorer traced current source and existing tests before implementation.
`practitioner-next/` is an independent implementation; none of the reference
frontend, backend, API contracts, domain, database, existing tests or deployment
files were changed. See `verification.md` for environment and execution limits.

| Existing capability | New implementation / verification |
| --- | --- |
| Accepted Matters and pending proposals | Independent ledger; real GET collections, titles/references, separate states and local search. Browser ledger/search/deep-link/refresh test. |
| Matter and saved proposal direct entry | `/app/matters/:id`, `/app/matter-proposals/:id`; loading, missing and failed states. Browser refresh and not-found tests. |
| Full canonical relationship drawing | All returned entities/relationships, Trust triangles and Person markers, parent direction, non-directional Trust roles. New presentation unit tests and graph rendering. |
| Graph exploration | Pan/zoom, zoom buttons, fit graph, entity selection and connected relationship list; searchable keyboard-operable list provides a diagram equivalent. |
| Exact Evidence inspection | All Evidence IDs/quotes and source titles; selected relationship, source highlight, explicit return-to-relationship focus. Keyboard/reduced-motion browser test. |
| Multiple Sources | Distinct source IDs/titles/text and Evidence attribution; source switching and exact highlight. Real multi-PDF browser/API tests. |
| Single PDF intake | External reference, Matter title, Source title, synthetic consent, existing multipart contract. Real UI proposal/confirmation test. |
| Multiple PDF intake | One to five titled PDF Sources, stable distinct IDs, add/remove, 10 MiB combined; backend retains page/text/acquisition limits. Unit admission tests and multi-PDF UI/API tests. |
| Fictional source assistance | Copyable source-only fictional prompt with manual-copy fallback; no model invocation or fabricated source. |
| Whole-proposal professional acceptance | Explicit native dialog, existing POST `/api/matters`, require `201` plus valid Location, reopen current Matter. Real browser and exact-state API tests. |
| Whole-proposal discard | Explicit native dialog, existing DELETE, return to ledger. Real browser test. |
| Duplicate reference recovery | Safe mapped message, actual existing record link and preserved form/PDF state. Isolated error-response browser test. |
| Retry, quotas and uncertain outcomes | Structured errors mapped to safe copy, input preservation, reset-time release, uncertain mutation outcomes require checking current state. API helper/component tests. |
| OIDC, session and CSRF | Existing Google/allowlist/session flow; same-origin secure cookies and CSRF mutation headers. Actual backend auth/CSRF integration, expired-session browser test. |
| Account and public showcase | Native account control with Escape/outside/focus dismissal; CSRF signout and configurable link to the original showcase. |
| English / Simplified Chinese | Independent translated UI and persisted locale, names/source text unchanged; switching preserves intake values. Real phone/desktop browser test. |
| Responsive/keyboard/reduced motion | Independent phone workspace controls, source return focus, native modal focus/escape, visible focus and reduced-motion equivalents. Browser and unit checks. |

## Reference source map

- Existing routes/shell: `web/src/app/App.tsx`,
  `web/src/features/matters/PractitionerApp.tsx`.
- Existing Matter/proposal contracts: `web/src/features/matters/api.ts`,
  `web/src/features/matter-proposals/api.ts`, `private_client_graph/api/app.py`,
  `private_client_graph/api/matter_proposals.py`, `private_client_graph/api/auth.py`.
- Existing review and graph: `web/src/features/review/SourceAwareReviewWorkspace.tsx`,
  `GraphView.tsx`, `RelationshipGraph.tsx`, `SourcePanel.tsx`, `EvidencePanel.tsx`.
- Existing intake/errors: `web/src/features/matter-proposals/CreateMatter.tsx`,
  `SourceDocuments.tsx`, `FictionalSourcePrompt.tsx`, `error-presentation.ts`.
- Existing account/language: `web/src/features/matters/AccountMenu.tsx`,
  `web/src/shared/LanguageControl.tsx` and `locale.tsx`.

Successful end-to-end journeys use the real unchanged API and deterministic
construction/persistence with only the pre-existing synthetic Google/extraction
boundaries substituted. Explicitly labelled isolated failure responses exercise
UI errors; they do not replace successful integration coverage. No provider
quality, production tenancy, real-data admission, new backend workflow or
runtime MotionScore performance certification is claimed.

Validation result: 752 repository tests, 33 new-app unit tests, typecheck/build,
formatting and 18 desktop/phone parity checks passed; the separate short recording
also passed. The new CI workflow repeats the new-app gates; its remote status is
reported at PR handoff. See verification.md for the finite graph-routing and
runtime/model-observability limits.
