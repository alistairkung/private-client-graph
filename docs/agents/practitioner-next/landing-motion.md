# Landing motion: source → relationship → exact Evidence

Use a synthetic microdemo labelled “Illustrative synthetic example”; Forest strokes and Chalk paper. Use selectable text, two Person circles and one Trust triangle. Final state remains explorable. Explicit professional acceptance is a separate visible decision, never an automated green tick.

## Choreography

| Trigger | Action / timings |
| --- | --- |
| First hero view, once | Headline and CTA readable immediately. Paper lifts y:12→0/opacity over 360ms ease [0.22,1,0.36,1]. At 200ms, reveal the exact source highlight with scaleX:0→1, origin left, 280ms. At 430ms, labelled entities settle y:8→0/opacity over 240ms. At 600ms, draw the single relevant connector pathLength:0→1 over 380ms. At 900ms, reveal its relationship label and Evidence locator over 160ms. Finish by ~1.1s; no autoplay loop or cursor pantomime. |
| Claim/source fragment activated | Highlight that text, corresponding relationship and Evidence together. Immediate selected state, 140ms colour/opacity. Inspector quotation is the same exact synthetic substring; source identity and locator stay visible. Label buttons are real buttons; pointer, Enter and Space work. Latest interaction cancels the intro and wins. |
| Scroll walkthrough | Three real content sections: identify words; inspect relationship; return to source. One sticky desktop product stage follows whichever section crosses a central reading band. Keep stable entity positions; change emphasis, selected relationship and quote. 180ms panel opacity, 240ms small transforms only where identity moves. No scroll hijacking. |
| Explicit walkthrough step clicked | Select stage directly and scroll its corresponding section into view; manual choice wins until the next actual user scroll. Retain focus on the activating button. Show the current step textually, not only by colour. |

## Adaptation and safeguards

Desktop: compact sticky stage, normal scrolling copy. Phone/reduced motion: three inline illustrations, all copy readable, no long pinned region. Reduced motion skips intro draw/translation and shows complete diagram immediately; interaction changes are immediate or ≤80ms opacity. Do not let MotionConfig alone govern imperative animation. Hidden visual states must be noninteractive/aria-hidden; provide a concise textual relationship equivalent. No auto-announcements on scroll.

Use useAnimate-scoped sequences; retain controls and stop on interaction/unmount, clear timers/listeners and disconnect any custom observers. Opacity/transform via MotionValues, no per-frame React state; SVG path drawing limited to this tiny illustration. No live provider calls or product mutations.

Final implementation keeps the six canonical connector paths static, including
their family dash patterns and parent arrows. A temporary nested overlay traces
the selected claim during the intro, then disappears. Early input and reduced
motion remove that overlay and settle the source/entity/locator transforms.
This avoids Motion's pathLength normalization changing canonical stroke styles.

## Actual inspected references

- Premium **Scroll spotlight**, full component plus theme source read: https://motion.dev/ui/components/scroll-spotlight (`motion://ui/react/scroll-spotlight`, motion-plus). Uses reading-band viewport entry, shared active item, stable stage and responsive inline/sticky visual modes. Adapt these mechanisms; retain readable inactive copy rather than its 0.4 opacity. Free motion dependency only.
- Free **Path drawing**, full source read: https://examples.motion.dev/react/path-drawing (`motion://examples/react/path-drawing`). Replace repeated sample shapes with one meaningful connector; no perpetual drawing.
- Official docs read: https://motion.dev/docs/react-svg-animation and https://motion.dev/docs/react-use-scroll . Installed package verified 14.3.0; declarations confirm useAnimate/useScroll/useTransform/useReducedMotion exports from motion/react. No upgrade or motion-plus runtime required.

Usage: 2 targeted concept searches, 1 source lookup, 1 actual premium resource read, 1 free source read. No account writes, providers, browser or app edits.
