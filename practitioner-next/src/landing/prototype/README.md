# Scroll interaction prototype

Open `/scroll-prototype.html` on the existing practitioner-next development server. This isolated entry does not change the landing route. It reads only the public curated synthetic Case 01 endpoint; no extraction or paid provider calls run.

The question: can a quick, scroll-controlled document montage make the journey from varied papers to connected relationships and exact Evidence feel continuous?

The headline is “It begins with your documents”. Four fanned sheets represent attendance notes, emails, time sheets, and legal documents. Authored SVG icons identify the formats; email headers, activity rows, and deed clauses make the interiors visibly distinct. The compact disclosure reads “Product vision · Illustrative document formats.” Only the attendance sheet contains actual synthetic source excerpts; the other three are product-vision examples with no fabricated canonical source or Evidence identifiers.

One viewport stays pinned within a 360svh section. The first 30% of travel flicks attendance → email → time sheet → legal document, then converges the stack by 36%. The actual attendance excerpt remains at the same measured coordinates through the merge, rather than becoming another hero chapter. Its exact entity names lift into graph nodes across 39–69%; solid animated SVG masks draw the six existing relationships across 65–86%, preserving family dashes and directional arrows. Across 86–97%, that same graph settles left and the actual full source opens right. Phones stack the working graph above its internally scrolling source pane.

The final graph is labelled “Working synthetic example”. The first relationship is selected initially; explicit selection persists when reversing. Each click highlights every exact occurrence of canonical Evidence in the actual full API source, preserving text, whitespace, source ID and Evidence IDs. Only the source pane scrolls, without page movement or focus changes. No multi-source processing, uploads, extraction calls, persistence, or production integration have been added.

Reduced motion shows all four formats statically, then the complete graph and full source in normal flow. The skip link reaches the final review directly; relationship labels are keyboard buttons. There are no playback timers or new test infrastructure.

Visual direction: Forest & Chalk, self-hosted Public Sans, document-specific typography and structure, and one continuous graph. This remains an isolated interaction study, not a shipping surface.

Research references: [Kevin Gutowski's scroll example](https://codepen.io/KevinGutowski/pen/QwNZYzL), [Motion useScroll](https://motion.dev/docs/react-use-scroll), [Motion useTransform](https://motion.dev/docs/react-use-transform), [Motion SVG drawing](https://motion.dev/docs/react-svg-animation), and [Motion path-drawing example](https://examples.motion.dev/react/path-drawing).

Launch from the repository root with `npm --prefix practitioner-next run dev`, with the existing local synthetic backend running. Open https://127.0.0.1:5443/scroll-prototype.html.

Current verification (18 October 2026): typecheck, formatting and whitespace checks pass. Actual desktop Chrome inspection verified document front switches, measured name emergence and final review. One correction batch and confirmation resolved overlap around the fan and initial Evidence visibility. The first highlight settles 35px below the source pane's top; selecting Carol's beneficiary relationship smoothly reveals its exact quote without moving the outer page. The full source still matches all 6,450 original characters (FNV-1a 383312280). The montage is absent from the accessibility tree during final review and returns on reverse scrolling. Phone and reduced-motion browser checks were not performed for this iteration. The required `uv run pytest` passed all 752 tests in 107.33 seconds. Paid application-provider calls remain 0/5.

Iteration usage: reused one Sol/medium implementation context, one desktop inspection and one correction/confirmation batch. One Motion documentation search and its full scroll-animation resource were read; no additional premium source resources or dependencies were needed.

Code Quality Review: inspected the complete prototype files for scope and readability. The montage is isolated in a focused component, canonical data and final source review stay unchanged, measurements are cached outside animation frames, and scroll never overwrites relationship selection. No material readability issue requires a production refactor.

Decision pending: review this isolated prototype before integrating any choreography into the landing page. No production integration, commit, PR update, or deployment has been performed.
