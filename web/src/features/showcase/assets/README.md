# Evergreen sample capture

`evergreen-sample.png` is a 2× browser capture of the actual shared `GraphView`,
after explicitly loading sample analysis at `/` on base commit `7783e3a`.
The sample request used the backend-owned Case 01 extraction fixture and real
deterministic graph construction. No relationships, labels, or geometry were
drawn separately. Only browser zoom controls and renderer attribution were hidden
for the capture; the graph was unselected.

To refresh: build and run the application, open `/` at a 1600×1100 viewport with
device scale factor 2, explicitly load sample analysis, wait for graph fitting
and fonts, then capture the `Relationship graph` element. Keep the complete
graph and its current connector conventions. This is a static sample image,
never a live result or an interactive control.

## Practitioner workflow captures (issue #65)

`create-matter.png`, `proposal-review.png`, `confirm-matter.png`, and
`accepted-matter.png` are actual Chromium captures of the practitioner application
at base commit `e531e4d`, taken on 2026-10-06. Their `-mobile.png` counterparts
capture the same states at the native narrow-screen layout. All images use a 2×
device scale factor; desktop viewport is 1100×1000 and mobile is 390×844.

The environment was the existing `tests/practitioner_browser_server.py` HTTPS
harness against a fresh, migrated local PostgreSQL database. Authentication,
sessions, PDF acquisition, deterministic graph construction, persistence, and
confirmation ran through the real application. Only the external Google boundary
and model call used the existing deterministic development/test substitutes.
These captures illustrate workflow, not a live model's extraction quality.

A new intake used `tests/fixtures/synthetic-proposal.pdf`, reference
`SYNTHETIC/065`, Matter title `Fictional Example family`, and source title
`Fictional attendance note`. The source says “Alice Example is the parent of Ben
Example.” The same parent relationship and exact Evidence were selected before
and after the actual **Confirm whole graph and create Matter** action. The API's
accepted `current_graph` was checked for equality with that intake's
`proposed_graph`. This is a newly confirmed intake, not the Evergreen seed or a
saved public sample.

To reproduce, build the frontend, migrate a disposable PostgreSQL database and
run the browser harness with its `DATABASE_URL`. Open `/app`, follow the normal
synthetic sign-in, choose Create Matter, fill the above identity fields, select
the fixture PDF, and confirm it is synthetic. Capture `.ledger-content` before
uploading. Upload and analyse, select the parent relationship, and capture
`.review-workspace` and `.confirm-matter`. Confirm the whole graph, select the
same relationship in the accepted Matter, and capture `.review-workspace` again.
At each state capture both viewport widths after fonts and graph fitting settle.
Use a new reference for each repeated intake.

Captures are cropped directly to these application regions, excluding the account
header. No text, graph geometry, controls, or status was redrawn or edited. The
confirmation image is an illustration, not a public confirmation control. No
Ledger image is needed to explain this journey.
