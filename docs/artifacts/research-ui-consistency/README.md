# Research UI consistency review

The screenshots record the post-deployment feedback and the resulting shared
header, shared Matter graph, compact case reader, Motion disclosures and folio
roadmap. All displayed data is synthetic and comes from the existing published
research snapshot.

## Visual evidence

- Before: [research header](before-header.png), [retired graph](before-graph.png).
- Shared masthead: [Chinese desktop](desktop-header-zh-CN.png),
  [English phone](phone-header.png).
- Current Matter renderer in research: [desktop](desktop-graph.png),
  [phone](phone-graph.png), [Chinese phone](phone-graph-zh-CN.png).
- Case reader: [desktop](desktop-reader.png), [phone viewport](phone-reader.png).
- [Reduced-motion disclosure](desktop-reduced-motion.png).
- [Research roadmap](desktop-roadmap.png), based on folio English pages 18–19
  and Chinese pages 38–39.

Separate UX, graph, navigation, Motion and roadmap investigations informed the
implementation. Independent visual review checked desktop and phone in English
and Chinese. Hash identifiers moved behind a disclosure during the visual pass;
the case selector stays available within its section.

## Validation

- Repository: `uv run pytest` — 739 passed.
- Application unit suite — 160 passed; Research Workbench — 26 passed.
- Production and Workbench TypeScript/build checks passed.
- Application browser coverage — all 104 active checks passed, 10 existing
  viewport-specific skips. The full run passed 102; the two Source-navigation
  assertions passed after updating their locator to distinguish the new Source
  region from its native selector. The full affected research and Matter graph
  files then passed all 20 checks after the shared toolbar sizing fix.
- Research Workbench browser suite — 16 passed, 2 existing skips.
- Final reader browser checks — 4 passed. They cover rapid accordion interruption, reduced motion,
  keyboard focus, stable case-selection scroll, exact Source highlights, return
  focus, visible quotations below the sticky selector and stale-selection resets.
- Browser tests used a migrated, seeded, disposable PostgreSQL database and the
  current checkout explicitly on `PYTHONPATH`. No live provider calls were made.

## Code Quality Review

Independent review covered the complete task diff, including new files and the
retired graph implementation. It found a shared graph toolbar sizing rule that
still depended on the Matter shell; the minimum 44px height now belongs to the
renderer and has a rendered-size regression check. No material readability
problems remained. Relevant browser checks were rerun after this correction.
Publication data, evaluation, graph identity and application access rules are
unchanged.
