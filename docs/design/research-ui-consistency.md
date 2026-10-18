# Public research: shared components and a quieter case reader

The post-deployment review identified five separate problems: the research
header differed from the landing, the graph used the retired renderer,
disclosures felt abrupt, the case index competed with the evidence, and the
folio's future research direction was missing. Each received an independent
investigation before implementation.

## Shared presentation boundaries

`PublicHeader` owns the exact public masthead, including its container, brand,
links, language control and responsive styles. Landing and research compose the
same component; research supplies only the current-page indication. Page-specific
content and skip links remain separate. Its CSS is self-contained so research
form styles cannot change the masthead.

Recorded research graphs consume the same `GraphDrawing` as Matter review. They
receive the retained canonical state directly. Research still owns the A/B
selection and recorded evaluation/Evidence inspection. No Matter orchestration,
mutation, graph construction or scoring enters this public view. Graph styling
is owned by the renderer and scoped to its workspace. The retired graph/layout
copy is removed; the research Source reader remains separate.

## Disclosure interaction

The implementation adapts the authenticated source of Motion's
[Base UI accordion](https://motion.dev/examples/react-base-accordion), read through
`motion://examples/react/base-accordion`. It uses Base UI's activation and panel
semantics with Motion's height/mask reveal, local content opacity/blur and
chevron rotation. The research variant uses a restrained spring. Reduced motion
explicitly disables these effects, including height and blur; the page's
MotionConfig alone would not disable them. Closing content is made inert.
Stable item identities preserve open panels across language changes. Multiple
panels can be open for comparing retained usage records.

This uses the public `motion` package and `@base-ui/react`, without a Motion+
runtime dependency. Source inspection is separate from application provider
calls; this implementation makes no paid extraction or resolution calls.

## Case reader

The primary task is to trace a recorded outcome to its exact Evidence. A native
case selector replaces ten tall cards repeating three scores each. No case is
selected initially. The correction shortcut opens Case 03 and moves focus to
its heading; ordinary case selection keeps focus on the selector and does not
scroll the page.

A compact two-row matrix preserves the baseline/B comparison. One selected
Run's relationship list sits beside the Evidence reader, removing the nested
three-column composition. A′ remains the default replay control, with A still
available. Run changes show recorded data immediately; the existing Motion
selection indicator acknowledges the change without interpolating values.

Full Source text is revealed deliberately. Exact expected/predicted quotations,
Source identity and separate provenance diagnostics remain inspectable. A
selection that no longer belongs to the visible run/filter must not leave stale
Evidence behind. Language changes preserve the selected record and quotation.
The two panes stack on narrower screens; all controls retain keyboard access.

## Research roadmap

The roadmap follows the folio's English pages 18–19 / Chinese pages 38–39:
identity and uncertainty; richer documents and Evidence; change and disagreement;
and practitioner usefulness with a safe scope. Each direction links a research
question to an application decision. Five development scenarios have authored
cases and fifteen remain planned. This is distinct from the ten-case held-out
comparison and is not a delivery schedule or claim of implemented capabilities.

The frozen published snapshot, contracts, benchmark ground truth, metrics,
provenance scoring and application access boundaries remain unchanged.
