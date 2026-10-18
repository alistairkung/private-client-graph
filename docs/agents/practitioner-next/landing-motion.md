# Landing motion: build the structure, trace the Evidence

The finished-graph opening underplayed construction. The replacement reveals
the actual returned entities and six canonical connections, then yields to
selectable exact Evidence. It remains an illustrative synthetic sequence; no
model runs when it plays.

## One frame, two capabilities

Tabs are **Build the trust structure** and **Trace the Evidence**. A scoped
shared indicator uses spring stiffness 700, damping 53 and mass 1. Tabs support
pointer, Enter/Space, arrows and Home/End with roving focus. Source identity,
graph geometry and selected relationship persist across switches. The caption
uses a 160ms opacity transition; source content changes directly within the
same paper so reading does not wait for an exit animation.

Canonical excerpt paragraphs remain fully readable, with pale-green verbatim
entity-name emphasis. Evidence mode keeps that natural paper height and shows
an independently scrollable exact passage and locator. The internal reader
resets on selection, without moving focus or scrolling the outer page.

## Construction clock

One retained Motion `animate` control drives a four-second MotionValue clock.
Derived values update the diagram without per-frame React rendering.

| Clock | Visible result |
| --- | --- |
| 0–0.6s | Readable Source excerpts; graph geometry reserved and empty. Caption: Synthetic source. |
| 0.6–1.5s | Person circles and Trust triangle reveal opacity 0→1 and y 8→0, 260ms each with 90ms stagger. Names remain attached. |
| 1.5–3.3s | Six connections and corresponding claim controls reveal in backend order, 300ms each starting 300ms apart. |
| 3.3–4s | Complete diagram holds; at four seconds the caption becomes Six proposed relationships. Ready to inspect. |

Canonical paths animate opacity only. Their geometry, family dash patterns and
parent arrows remain unchanged; no pathLength normalization or duplicate overlay
can overwrite those roles. Each diagram scopes its marker IDs independently.
Invisible claim controls stay disabled until their reveal begins.

## Lifecycle and accessibility

Playback starts when at least 20% of the drawing is visible, including on phones.
Offscreen/document-hidden playback pauses. Return resumes eligible playback;
a deliberate user pause persists. Pause and Resume operate the same clock.
Replay resets presentation only. Evidence/tab/claim input settles construction
immediately, and return to Builder retains completion until explicit Replay.

An explicit reactive media-query subscription handles initial and live reduced
motion: the complete graph appears immediately, and Replay remains static.
The browser regression asserts settling within 500ms. When completion removes a
focused Pause/Resume button, focus moves to Replay; unrelated focus stays put.
Generations guard stale completion callbacks; observers, listeners and controls
clean up on unmount and React StrictMode remount.

## Actual inspected sources

- [Smooth Tabs](https://examples.motion.dev/react/smooth-tabs): scoped shared
  indicator and continuous panels; reused already inspected source.
- [Path Drawing](https://examples.motion.dev/react/path-drawing): actual source
  previously read. Final construction uses per-edge opacity to preserve canonical
  dash/arrow roles rather than its pathLength technique.
- Premium [Scroll Spotlight](https://motion.dev/ui/components/scroll-spotlight):
  full component/theme source was read during initial landing research. Its
  viewport eligibility and stable stage informed this design; the former long
  scroll walkthrough has been removed.
- Official [SVG animation docs](https://motion.dev/docs/react-svg-animation) and
  [useScroll docs](https://motion.dev/docs/react-use-scroll) were inspected earlier.
  Installed free `motion/react` is 14.3.0. No upgrade or premium runtime is needed.

This continuation made no new Motion query or source read. Initial landing
research used two concept queries, one source lookup, one premium and one free
source read. Paid application-provider calls remain **0/5** across continuations.
No account writes, private registry token, live model or MotionScore audit.
