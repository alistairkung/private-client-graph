# Practitioner motion specification

Motion reinforces the document-led workspace: a selection acquires a location,
evidence stays inspectable, and confirmation establishes a deliberate boundary.
Use free `motion/react`; no premium runtime is required. Values below are design
recommendations, not copied source defaults. Align colours with the UX tokens.

| Trigger / task | Choreography and implementation | Timing / interruption |
| --- | --- | --- |
| Select a Matter | Move one narrow active marker between Matter rows using a scoped `layoutId`. Replace workspace content under the committed Matter title; clear previous Matter selection and evidence atomically. Keep the outer document frame stationary. | Marker spring `{ type: "spring", visualDuration: 0.22, bounce: 0 }`; new content opacity 0→1 over 120ms. Latest Matter wins; no queued page exits. |
| Select graph node or relationship | Apply the selected outline immediately; reveal its Evidence inspector content in the existing inspector frame. Header, source label and exact quotation change together. A 120ms opacity entrance acknowledges new evidence without moving text from graph to document. | No graph relayout, zoom or animated edges on selection. Keep inspector mounted, including its empty state. Repeated selection updates immediately; never show an old quotation beneath a new title. |
| First open Evidence on a narrow screen | Open a labelled document sheet with `y: 16→0` and opacity 0→1. Keep the selected item visually marked behind it to explain context. | Spring `visualDuration: 0.24, bounce: 0`; backdrop opacity 140ms. Closing reverses from current state. Desktop inspector remains nonmodal. |
| Switch source / evidence occurrence | Move the source-tab underline via scoped `layoutId`; replace quotation and locator as a single keyed unit. Retain inspector position. If a deliberate locator jump is needed, scroll to it instantly, then apply a persistent highlight. | Underline spring 0.18s, bounce 0; content opacity 100ms. No smooth scroll through unrelated legal text; no character-by-character reveal. |
| Review whole proposal | Open an explicit confirmation dialog; surface opacity 0→1, `y: 8→0`. Show the complete proposal scope before enabling confirmation under existing workflow rules. | 180ms ease-out; backdrop 120ms. Keep open during submission. Show success only after API success, using a static status label. Error keeps proposal and focus available. |

## Accessibility and state

Use `MotionConfig reducedMotion="user"` and `useReducedMotion`: remove layout,
translation and scrolling motion; use immediate state changes or ≤80ms opacity.
Do not delay input, announcements or data correctness for animation completion.
Cancel stale requests or ignore stale responses using existing request identity.

Desktop graph selection retains keyboard focus; provide an explicit “Inspect
evidence” action that focuses the inspector heading. Modal sheets/dialogs use
native `dialog.showModal()`, labelled headings, contained focus, Escape dismissal,
and focus restoration to the invoking control (or its surviving context).
Synchronize native close with React state; test repeated Escape during exit.

## Read sources and verification

Authenticated premium sources inspected in full:
[Modal: Shared layout](https://examples.motion.dev/react/modal-shared-layout)
(`motion://examples/react/modal-shared-layout`: identity continuity, layering)
and [Family-style dialog](https://examples.motion.dev/react/family-dialog)
(`motion://examples/react/family-dialog`: zero-bounce spring, native dialog,
exit lifecycle). Adapt mechanisms; omit gallery styling, blur and text scaling.

Verify rapid reselection, source/title/quote consistency, keyboard focus,
reduced motion and submission failure. No runtime MotionScore audit performed.
Research usage: one concept search, two source lookups, two premium resource
reads; no paid application-provider calls.
