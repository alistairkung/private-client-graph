# Practitioner motion specification

The approved refinement is precise and tactile. Motion acknowledges intent,
keeps the current relationship and Evidence together, and preserves the user's
place across the whole journey. Implementation uses `motion/react`; premium
research does not require a premium runtime dependency.

| Trigger / task | Implemented behavior | Timing / interruption |
| --- | --- | --- |
| Graph / List | Two full clickable tabs, roving keyboard focus, Arrow/Home/End support. The pill follows a pointer drag through a MotionValue; release chooses the nearest side once. No inertia or overshoot. | Spring stiffness 700, damping 53, mass 1. A new gesture stops the current spring. Pointer cancel, lost capture, Escape or resize restores the committed side. Trailing pointer clicks are suppressed without consuming keyboard activation. |
| View change | Both panels stay mounted in a fixed working frame. Hidden panels are inert and hidden from assistive technology. Camera, query and scroll positions survive switching and returning to the Matter. | 120ms opacity acknowledgement; no waiting for an exit before input. |
| Graph exploration | Hover/focus/selection emphasizes a claim and its endpoints. Labels have coordinated placement and leaders; explicit fixed XYFlow endpoint dimensions preserve label DOM through hover changes. | Short color/stroke feedback. No graph relayout, animated edge flow, automatic selection pan or zoom. Pan/zoom remains user controlled. |
| Evidence selection | Persistent compact inspector. Relationship title and all supporting Evidence change together. Source selection updates without moving the outer page. | 120ms opacity; latest selection wins immediately. |
| Inspect in source | Explicit action scrolls only the source container and focuses the exact highlighted span. Phone Source view retains the selected statement above the document. Return resolves the current relationship control and restores focus. | Instant locator jump; no animated travel through unrelated text. Source underline uses a zero-bounce 180ms spring. |
| App navigation / ledger | Native hrefs with client navigation, route acknowledgement, stable shell and restored per-page scroll. Compact rows acknowledge hover and settle when filtering. | Route opacity 160ms; row entry 140ms / exit 80ms; no chained entrance sequence. |
| Intake | PDF drop target responds to drag; rows settle in/out. Draft fields, PDF objects and recovery state remain in tab memory across app links. | Row entry 180ms / exit 80ms. Submission blocks app navigation until resolved; success clears the draft. |
| Menus and decisions | Mobile rail, account popover and native proposal/fictional-source dialogs have short entrance/exit feedback. Focus and Escape follow the nearest open surface. | Account 140ms, rail 180ms, dialog entrance 180ms / exit 120ms. Busy decisions remain open. No blur or text scaling. |
| Controls | Subtle press compression and ledger directional feedback. | Press scale .98; brief color/transform transitions. No hover movement on graph labels. |

## Accessibility and continuity

`MotionConfig reducedMotion="user"` and local `useReducedMotion` remove scale,
translation and source underline layout movement. The draggable control still
tracks direct input, but settles immediately. Inspector/dialog feedback reduces
to a short opacity change. Input, focus and announcements never wait for motion.

Tab-memory is presentation-only: no localStorage, database mutation or persisted
practitioner review state. Reload/close clears it. Sign-out clears mounted draft
values and removes the unload warning before leaving. Native hrefs retain
modifier-click/new-tab behavior; authentication stays in the existing flow.

## Authenticated source research

This refinement inspected the complete premium source for
[Smooth Tabs](https://examples.motion.dev/react/smooth-tabs) and
[Motion UI Segmented toggle](https://motion.dev/ui/components/segmented-toggle).
They informed shared identity, selected-state continuity and control structure.
Neither source implements dragging: pointer capture, MotionValue tracking,
cancellation and click suppression were implemented explicitly using Motion's
[drag guidance](https://motion.dev/docs/react-drag) and
[useDragControls documentation](https://motion.dev/docs/react-use-drag-controls).

Earlier delivery also inspected
[Modal: Shared layout](https://examples.motion.dev/react/modal-shared-layout) and
[Family-style dialog](https://examples.motion.dev/react/family-dialog). Their
layering, native dialog and exit-lifecycle mechanisms remain relevant; gallery
styling, blur and text scaling were omitted.

Tests cover drag/click/keyboard cancellation, rapid switching, reduced motion,
locale changes, camera/query/scroll retention, exact source focus, connector-label
occlusion and interrupted submission. No runtime MotionScore audit or production
performance certification is claimed. No paid application-provider calls.
