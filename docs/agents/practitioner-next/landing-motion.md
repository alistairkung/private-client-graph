# Landing motion: documents become a structure, with Evidence intact

The user approved the isolated scroll prototype and asked to put it into the
independent landing page. Production implements that direction in separate
components; it imports no throwaway code or stylesheet. The approved reference
is preserved on `codex/landing-documents-prototype` at
`15288805f7dea7c723d2b73f7a4772db2a307dde`.

## One scroll-controlled sequence

A 360svh track pins one viewport. Scroll progress, rather than a timer, drives
MotionValues. There is no autoplay, replay clock or capability-tab stage.

| Progress     | Visible result                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| 0–30%        | Attendance notes, emails, time sheets and legal documents flick to the front of the fanned deck.                               |
| 30–36%       | Papers gather at the actual attendance excerpt.                                                                                |
| 39–69%       | Exact entity names move from their measured source positions into person and Trust symbols.                                    |
| 65–86%       | Solid white SVG masks progressively expose the canonical relationship paths.                                                   |
| 86–97%       | The same graph settles left; the full source enters on the right. Phones stack graph and source.                               |
| Final review | Relationship buttons select exact canonical Evidence and smoothly reveal the first matching occurrence inside the source pane. |

The masks animate pathLength rather than changing the canonical paths' dash
patterns. Symmetric relationships have no direction marker; directed parents and
Trust roles have visible arrows at the target glyph boundary. Scoped IDs avoid
marker or mask collisions. Actual node centers, canonical identifiers, types,
ordering and directions remain unchanged.

Phone relationship labels clear measured entity captions, with short leaders
associating displaced Trust-role labels to their connections. Near-vertical and
diagonal parent labels have separate positions; every target remains at least
44px. The source follows its selected passage through text reflow until manual
reader input cancels following.

## Continuity, control and lifecycle

Names start with dark ink on a pale-green chip over the paper, then switch to
chalk on forest near their final position. They stay above the fading sheet.
Origins are measured outside animation frames, observing the actual paper,
deck, introduction and graph dimensions. Resize, font readiness and locale
changes refresh them; observer/listener/pending-font cleanup guards unmount.

The skip link reaches the finished review and focuses its container. Invisible
relationship controls remain inert and absent from accessibility until review.
Explicit selection is independent of scroll, preserving it through reversal,
resizing and locale changes. Interface translations never rewrite source words.

The source contains the complete API text and highlights every exact selected
Evidence occurrence, including repeated or overlapping support. Only its pane
scrolls; page position and relationship focus remain stable. Reader wheel,
touch, pointer and scrolling keys cancel automatic movement; newer selection,
hiding the review and unmount also cancel it. Reduced motion reveals instantly.

Reduced-motion preferences are reactive. Reduced motion, any viewport at most
580px tall, or phones at most 700px wide and 800px tall use a static in-flow
collection, finished graph and full reader without a long track. Compact phones
need that space for readable captions and 44px targets. Taller phone layouts
retain scroll animation, with the same source and selection.

## Backgrounds and product truth

The story and following proposal-review chapter share forest #173F31. Former
70px desktop / 45px phone exterior margins exposed an empty white strip; spacing
now stays inside the forest field. Light returns at the substantive research
chapter. The four formats represent the labelled product vision, while the
working example remains the existing curated synthetic Case 01. No fabricated
Source/Evidence IDs, ingestion, automatic analysis or provider calls are added.

## Inspected references and budget

The implementation reuses already read Motion useScroll/useTransform and SVG
path-drawing documentation, the actual Path Drawing example, and the approved
scroll study inspired by Kevin Gutowski's CodePen. Earlier authenticated Motion+
research remains recorded in the landing direction. No new lookup, premium
runtime dependency, registry key or account write was needed for this integration.
No runtime MotionScore claim is made. Shared paid application-provider usage
remains **0/5**, including all prior attempts and continuations.
