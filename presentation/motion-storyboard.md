# Private Client Graph — motion storyboard and production plan

Text-only extension of the [twelve-slide proposal](12-slide-proposal.md), on [draft PR #153](https://github.com/alistairkung/private-client-graph/pull/153). The twelve headlines, persuasive sequence, evidence and scientific boundaries remain the foundation. This plan authorizes no implementation, capture, rendering, evaluation, merge or deployment.

## Delivery and creative direction

P0 production, after separate approval: two silent 1920×1080 MP4s (`en`, `zh-CN`) and two static multipage PDFs, each containing exactly twelve complete slides. Planned outputs: `private-client-graph-en.mp4`, `private-client-graph-zh-CN.mp4`, `private-client-graph-en.pdf` and `private-client-graph-zh-CN.pdf`. Plan 30 fps. Estimated English runtime is **4:54**; the Chinese reading allowance produces **5:06**. These are budgeting estimates, not timed audience-test results. Prefer a six-second overrun to hiding scientific qualifications or accelerating silent reading.

The signature is a stable relationship and its unchanged documentary Evidence. Use six substantial explanatory sequences: documents/current trustee across scenes 2–3; Evidence inspection in 5; actual Workbench chain in 7; paired control in 8; actual F1 plot in 9; endpoint correction in 10. Scenes 1, 4, 6, 11 and 12 mostly hold readable compositions. Treat the closing callback as reuse, not a seventh bespoke sequence.

“Scroll-inspired” means stable visual anchors, paced disclosure and chapter continuity. It does not mean simulated scrolling of long pages, sweeping cameras or an autoplaying product walkthrough. The [Lissom site](https://lissom.ai/) provides a useful outcome → problem → product-mechanism editorial progression. Its page text was inspected; its exact motion choreography was not visually audited. The requested cinematic influence is a creative interpretation, not a claim to reproduce its implementation, imagery, customers, performance or brand.

The motion plan changes how meaning is revealed, not what the product can do. **Scenes 3, 5 and 10 may use faithful conceptual transformations**, visibly labelled “Conceptual animation — based on the supplied synthetic documents” (3/5) or “Conceptual animation — recorded endpoint edits” (10), with localized equivalents. Editorial layers may connect, reveal and reposition documentary assertions, relationship labels or recorded endpoint edits to explain their meaning. Keep these layers visually distinct from unaltered authentic UI captures; do not pass them off as application footage. Preserve exact names, roles, Source identities and quotations, except for the two explicitly recorded endpoint substitutions in scene 10. Conceptual connectors explain correspondence, not new domain relationships.

No fake pointer, fabricated loading, simulated provider execution, self-updating accepted Matter, invented relationship or metric count-up. Scenes 7 and 9 retain the **actual Workbench chain and F1 plot**; this permission does not allow their reconstruction or replacement. Scene 8's protocol diagram is also editorial, not a product screen. Synthetic/fixture labels and material research qualifications appear from each scene's initial reveal and remain readable throughout the hold.

## Consulted guidance and feasibility decisions

Installed guidance read: [Remotion Best Practices](https://github.com/remotion-dev/skills), installed version `4.0.536`, including multi-scene structure, compositions/stills, timing, transitions, local fonts, rendering, Player and video layout; [Apple Design Skill](https://github.com/dickwu/apple-design-skill), including accessibility, layout, typography, color, motion, charting data, branding, macOS context and cross-platform translation. Both are available. They are references only; no setup commands were executed.

| Question | Verified reference | Planning decision |
|---|---|---|
| Deterministic scenes and animation | Installed `remotion-markup/REFERENCE.md`, `timing.md`, `multi-scene-video.md`; [Sequence](https://www.remotion.dev/docs/sequence) | Use explicit scene timing, frame-derived progress and clamped interpolation. Installed guidance prefers a named Track with connected scenes; Sequence scopes local timing. No CSS transitions, browser timers, clicks or requestAnimationFrame as animation clocks. |
| Spring and transition behavior | Installed `timing.md`, `transitions.md` | Default to restrained Bézier opacity/mask reveals. A highly damped spring is technically supported but unnecessary here. Use contiguous scenes; if later using TransitionSeries, subtract overlaps and regenerate the timing sheet. Never overlap reading holds accidentally. |
| Reusing real UI | Existing local `AnalysisPipeline` and `RunPerformanceChart`, plus Workbench adapters | Presentation reuse is real; automatic frame control is not. Both contain interaction state; the chain also has DOM scrolling/focus effects. Prefer captures and external emphasis for P0. Controlled presentation props are an optional later bounded adaptation, not an existing capability. |
| Still/PDF outputs | Installed composition/render guidance; [renderStill](https://www.remotion.dev/docs/renderer/render-still) | Register intentional still states. Current official renderStill docs list single-frame PDF output as well as images; verify support in the eventual pinned runtime. Assemble twelve intentional page outputs in order. Do not assume Remotion supplies a complete accessible multipage deck exporter. |
| Scroll seeking | Installed Player guidance; [Player / PlayerRef](https://www.remotion.dev/docs/player/player) | The same scene component can appear in a React Player; its ref supports `pause` and `seekTo(frame)`. Scroll mapping is custom integration, not a built-in scroll-story export. Recommend deferral below. |

Reference paths above are relative to the installed Remotion skill's folder. Remotion APIs must be rechecked against the runtime pinned at implementation; installing/upgrading dependencies is outside this task. Official references establish capabilities, not successful integration with this repository.

## Visual rules and continuity

Evidence Folio takes precedence over native Apple interface conventions. Apply the principles to a fixed canvas and optional web reader; do not import SF branding, Liquid Glass, native navigation conventions or desktop minimum type sizes into a judge deck.

- **Hierarchy:** one dominant idea; headline first, explanatory visual second, visible qualification third. Start with a 96 px headline, 40–44 px supporting copy and 30–32 px material caveats on the 1920×1080 canvas. These are proposed production values, not measurements of existing assets. Allow a two-line title; a denser scientific scene may use an 84 px title after readability review. Prefer reflow/cropping to smaller text. This adapts the installed video's broad type-size advice to the existing editorial identity and required real UI; do not shrink a whole screenshot to force compliance.
- **Spacing:** approximately 120 px side margins and 90 px top/bottom safety, with a consistent title baseline and dedicated qualification region. Keep chart labels and complete endpoint names inside the safe area. Reserve 25–30% text expansion space for localization.
- **Color:** ledger green `#173e38`, paper `#f6f6f1`, burgundy `#773b46`, Evidence gold `#efdda0`. Computed flat-color contrast: green/paper **10.87:1**, burgundy/paper **7.75:1**, green/gold **8.71:1**. These do not certify screenshot, texture, anti-aliasing or compressed-video contrast. Gold marks exact documentary words only; stage emphasis uses outline, label and opacity, never “gold = correct.”
- **Motion:** only the current explanatory region moves. Restrained position changes stay within a panel; primary text and full-canvas backgrounds remain stable during reading. No blur, parallax, pulse loops, bounce, spin, depth fly-through or metric interpolation. State changes have persistent text labels in addition to color.
- **Reading access:** no narration or audio-dependent message. MP4 users need ordinary player pause/seek; a baked MP4 cannot automatically honor reduced-motion preferences. The PDFs provide the complete motion-free alternative. This is not a claim of screen-reader accessibility for raster pages; preserve this Markdown reading version, and check PDF text/tagging separately during production.

Apple sources actually consulted: `layout.md › Visual hierarchy`, “Order content by relative importance”; `typography.md › Ensuring legibility`, “Test legibility in different contexts”; `motion.md › Best practices`, “Make motion optional”; `charting-data.md › Best practices` and `Designing effective charts`; `color.md › Inclusive color`; `accessibility.md › Cognitive`; `branding.md › Best practices`. Adaptations and size/timing estimates here are design judgment. [Layout](https://developer.apple.com/design/human-interface-guidelines/layout), [typography](https://developer.apple.com/design/human-interface-guidelines/typography), [motion](https://developer.apple.com/design/human-interface-guidelines/motion), [charting data](https://developer.apple.com/design/human-interface-guidelines/charting-data), [color](https://developer.apple.com/design/human-interface-guidelines/color), [accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility), [branding](https://developer.apple.com/design/human-interface-guidelines/branding).

Chapter continuity: scenes 1–5 use paper, graph and source panels; 5→6 retains the selected Evidence while broadening to the three reasoning questions. 6→7 aligns the three questions with the real chain, without implying each is solved. 7→8 holds the research boundary while introducing the frozen input. 8→9 preserves A/A′/B labels; only the method panel is replaced by the genuine chart. 9→10 retains B and identifies the one changed case, not another trial. 10→11 returns to a calm paper composition. 11→12 returns to the exact opening crop and framing. Outgoing transitions use the final half-second of each scene to soften the panel edge or return to paper; next-scene content is not counted twice.

## Timing budget and reading test

Seconds below are additive and non-overlapping. Initial reveal includes the title, scene label and essential caveat. Main animation means the total beat window, including brief pauses. The reading hold begins only when the full final composition is stable. Outgoing transition is part of that scene's duration, not an extra crossfade overlap. No outgoing transition on 12.

| Scene | Initial reveal | Main animation | Reading hold | Transition | Total EN | Extra zh-CN hold | EN interval | Resting frame, local @30fps |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 1 | 1 | 13.5 | 0.5 | 16 | 0 | 0:00–0:16 | 60 |
| 2 | 1 | 3 | 15.5 | 0.5 | 20 | 0 | 0:16–0:36 | 120 |
| 3 | 1 | 8 | 18.5 | 0.5 | 28 | 2 | 0:36–1:04 | 270 |
| 4 | 1 | 2 | 14.5 | 0.5 | 18 | 0 | 1:04–1:22 | 90 |
| 5 | 1 | 9 | 17.5 | 0.5 | 28 | 2 | 1:22–1:50 | 300 |
| 6 | 1 | 3 | 15.5 | 0.5 | 20 | 0 | 1:50–2:10 | 120 |
| 7 | 1 | 10 | 18.5 | 0.5 | 30 | 2 | 2:10–2:40 | 330 |
| 8 | 1 | 10 | 20.5 | 0.5 | 32 | 2 | 2:40–3:12 | 330 |
| 9 | 1 | 8 | 26.5 | 0.5 | 36 | 2 | 3:12–3:48 | 270 |
| 10 | 1 | 8 | 20.5 | 0.5 | 30 | 2 | 3:48–4:18 | 270 |
| 11 | 1 | 2 | 16.5 | 0.5 | 20 | 0 | 4:18–4:38 | 90 |
| 12 | 1 | 2 | 13 | 0 | 16 | 0 | 4:38–4:54 | 90 |
| **Total** | **12** | **66** | **210.5** | **5.5** | **294** | **12** | **4:54** | |

English: **8,820 frames**. Chinese: **306 seconds / 9,180 frames**, with scene order and beats unchanged; only six holds gain two seconds. The closing frame is stable for **13 seconds**, exceeding the eight-second requirement. Frame markers identify deliberate complete states, before the outgoing transition; they are not arbitrary screenshots. A locale-specific hold extension changes later global offsets, not these local resting states.

Reading assumptions: aim for about 25–50 unique English words on product scenes and no more than roughly 75 on scientific scenes, excluding repeated UI labels/names. A provisional 150–180 words/minute means 50 words need 17–20 seconds and 75 words need 25–30 seconds, before allowing for a novel graphic. Chinese planning assumption is 3–4 characters/second, with extra time for original English quotes/names. These are conservative planning heuristics, not research findings about this audience. Scene 9 gets the longest hold; 3, 5, 7, 8 and 10 retain extra localized reading time. Show labels/caveats early so reading can begin before the final hold.

After approval, test both silent versions with readers unfamiliar with the project. Ask them to identify the trustee, trace a quote, distinguish practitioner/research configurations, explain A′ and qualify 100% F1. If readers cannot do so without pausing, add 2–4 seconds to affected holds or cut secondary copy, never the limitations. The 4–5-minute target is not a reason to accelerate qualifiers. Verify actual Chinese copy and screenshot legibility before locking runtime; no audience test or rendering has occurred here.

<a id="scene-1"></a>

## Scene 1 — See the relationships. Read the evidence.

### Motion Storyboard

**A. Initial frame:** Opening headline, product name, user description and “Synthetic research prototype” on paper. Asset A's graph/Evidence crop is already identifiable on the right; no blank suspense opening.

**B. Animation beats:** After the 1s entry, a 1s soft focus outline introduces the selected relationship and its adjacent Evidence. Then hold 13.5s; 0.5s outgoing panel fade. This is a low-cost opening, not an extraction animation.

**C. Final resting frame:** Original slide 1 layout, complete graph selection and exact quote visible beside the promise. Capture local frame 60 for the static version. No ghosted or half-revealed copy.

**D. Trigger:** Deterministic local timeline; optional future scroll uses only this same frame range, with a fully readable end state.

**E. Narrative purpose:** Establish that the visual subject is documentary relationship review, before explaining mechanics.

**F. Technical approach:** One image layer plus frame-derived outline/opacity emphasis, not a recreated graph. Fixed crop and typography; no camera zoom required.

**G. Asset dependencies:** A and E from the proposal register; A requires packaging from the pinned submission asset, E supplies identity only. Opening crop must be reused on 12.

**H. Complexity:** **Simple.** Risk: squeezing source text into the hero. Crop to the selected edge/quote with full names, not the whole product page.

<a id="scene-2"></a>

## Scene 2 — The facts arrive as documents. The questions span relationships.

### Motion Storyboard

**A. Initial frame:** Two actual Case 04 source excerpts with distinct Source titles. Practitioner questions remain visible on the right; synthetic label is present.

**B. Animation beats:** Within a 3s window, disclose one exact supporting passage (1s), then the other (1s), then align the question labels with their evidence regions (1s). Hold 15.5s after the 1s entry, then 0.5s transition. Do not turn every name mention into an edge.

**C. Final resting frame:** Both excerpts and all three questions remain. Retain “A family connection does not establish a trust role.” No partial graph or unsupported relationship appears.

**D. Trigger:** Timeline beats; future scroll may advance the same highlights, never change input documents or infer facts.

**E. Narrative purpose:** Direct attention from isolated words to distinct family/role/source questions. This begins the six-sequence document-to-relationship chapter; its concrete result arrives on 3.

**F. Technical approach:** Genuine source excerpt layers with masks restricted to exact text coordinates; captions outside the UI. No generated paper image or source text rewriting.

**G. Asset dependencies:** B, actual Case 04 Sources and approved Evidence. Existing selected-state asset may require a later faithful capture/packaging; exact excerpt selection must be checked against the fixture, not inferred from the image.

**H. Complexity:** **Moderate.** Risk: visually connecting Case 04 facts to Case 05's result. Scene boundary explicitly changes the synthetic example; do not morph names across cases.

```text
START  CASE 04: SOURCE EXCERPTS       MID  DISTINCT QUESTIONS
[Source 1]     [Source 2]             [family words]    [trust-role words]
                                              \         /
END    [Which family link?] [Which trust role?] [Which Source?]
       No new graph facts; next scene explicitly switches to Case 05.
```

<a id="scene-3"></a>

## Scene 3 — Who is the current trustee—and which document establishes that?

### Motion Storyboard

**A. Initial frame:** “Case 05 — documents supplied together” is explicit. Both dated source excerpts are present on the left; a distinct editorial interpretation area leads to the authentic current-state graph on the right. Show “Conceptual animation — based on the supplied synthetic documents” and “Curated synthetic fixture; not measured model output or a saved-Matter update.”

**B. Animation beats:** After 1s entry: reveal an editorial “earlier assertion: David Ng — trustee” label connected to its exact passage (2s); reveal the completed replacement passage and effective date, then move the earlier assertion into a persistent “historical” position while bringing the Rachel Lim assertion forward (3s); connect the replacement assertion to Rachel's current edge in genuine asset C (3s). Both supplied documents remain visible. Hold 18.5s, then 0.5s exit. This transforms the explanation of supplied facts, not an accepted Matter or a live extraction.

**C. Final resting frame:** Both supplied document excerpts, the completed effective-date label, Rachel Lim → trustee of → Willow Family Trust crop, and David's historical assertion coexist, with editorial connections and the conceptual-animation label retained. The static state preserves the earlier/current distinction and why Rachel is current. Use the exact sole-trustee quotation from slide 3's copy.

**D. Trigger:** Timeline-driven emphasis of existing states. Optional scroll could reveal the same document interpretation, not “upload next Source.”

**E. Narrative purpose:** Answer a real review question while distinguishing current state from a union of every historical statement.

**F. Technical approach:** Reuse genuine source excerpts and final graph; animate separate editorial assertion labels and masked correspondence connectors with frame interpolation. A restrained spatial move from “earlier assertion” to “historical” and a reveal of the effective replacement explain supersession. Do not redraw an intermediate application state, strike out the valid original document or remove a node inside a screenshot. The conceptual label remains visible during the transformation and final hold.

**G. Asset dependencies:** C, Case 05 `sources/note_01.txt`, `sources/note_02.txt`, `expected_state.json` and source-aware approvals; all referenced in the proposal. Required later capture only if the current graph crop lacks a legible Rachel edge.

**H. Complexity:** **Moderate.** Main risk: motion falsely implying incremental accepted-Matter mutation or measured temporal reasoning. Persistent supplied-together/fixture labels prevent that interpretation.

```text
START  CASE 05 — BOTH SOURCES ALREADY SUPPLIED
[1 Sep: David trustee]   [15 Sep: completed replacement]

MID
[David assertion moves to HISTORICAL] [effective 10 Sep: Rachel assertion]
                                            |
END                                        v
[Both original excerpts + labelled conceptual interpretation]
                               [ACTUAL CURRENT GRAPH CROP]
                               Rachel Lim -- trustee_of --> Willow Family Trust
```

<a id="scene-4"></a>

## Scene 4 — From synthetic PDFs to a reviewable Matter.

### Motion Storyboard

**A. Initial frame:** Three workflow panels are present with the authenticated synthetic workflow label. The public-demo preview limitation is already visible.

**B. Animation beats:** After 1s entry, one 2s left-to-right emphasis across Intake → Review → Confirm/reopen. No animated button click. Hold 14.5s, then 0.5s exit.

**C. Final resting frame:** All three states simultaneously readable; 1–5 synthetic PDFs, exact Evidence review, whole-proposal confirmation and “Public demo: fixed examples; confirmation is a preview.” Remains a process overview, not a live transaction.

**D. Trigger:** Fixed timeline; future web reading can simply show the static end state.

**E. Narrative purpose:** Make the complete workflow understandable without adding another provenance demonstration.

**F. Technical approach:** Fixed existing UI crops and text panel; restrained outline progression using frame interpolation. No application API or operational UI import.

**G. Asset dependencies:** A and existing lifecycle schematic G. Accepted-Matter imagery must be verified or remain the approved text panel; no new mockup.

**H. Complexity:** **Simple.** Risk: public demo looking writable. Keep authenticated workflow and read-only preview explicitly distinguished.

<a id="scene-5"></a>

## Scene 5 — Every proposed relationship has a route back to its source.

### Motion Storyboard

**A. Initial frame:** Authentic selected-relationship graph and Source/Evidence panels are visible. Outside the UI, label the explanation “Conceptual animation — based on the supplied synthetic documents” and retain “Synthetic sample; not a live-model result.” No fake pointer.

**B. Animation beats:** After 1s entry, reveal an editorial selected-relationship label anchored to the genuine edge (2s); draw a correspondence connector from that label to the identified Source, progressively revealing the Source title/ID (3s); continue the connection into the exact supporting passage, reveal its gold highlight and bring an exact-quote detail into readable focus (4s). Hold all regions 17.5s; exit 0.5s. The Source identity stays visible as quotation focus increases; the path is relationship → identified Source → exact quotation.

**C. Final resting frame:** Selected graph edge left; identified Source and matched exact quotation right, connected through clearly editorial annotations. Outside-UI captions “Selected relationship → identified Source → exact supporting quotation” and the conceptual-animation label preserve the full correspondence in one readable static view. Keep the genuine Evidence panel and complete endpoint names visible.

**D. Trigger:** Deterministic timeline. A later scroll mapping may advance the emphasis; it must not require a click to reveal the essential quote.

**E. Narrative purpose:** Teach where the proposed fact came from, rather than merely asserting explainability.

**F. Technical approach:** Combine unaltered authentic product crops with separate editorial layers: a connecting-path reveal, progressive Source/quote disclosure and restrained focus transitions. An enlarged quote detail must reproduce the exact source text and remain attached to its Source identity. Use shared frame-based reveal/focus primitives, not simulated clicks or fabricated UI states. Genuine corresponding selection captures can be crossfaded; conceptual connections must remain labelled, and must not imply a provider run or a newly discovered edge.

**G. Asset dependencies:** A or B with one consistent actual edge/Evidence/Source selection. Required preparation: confirm the chosen selection appears in every crop, package exact source text and capture coordinates. If missing, require later genuine captures; do not fabricate UI states.

**H. Complexity:** **Moderate.** Risk: focus movement removes the relationship endpoint or attribution. Keep them visible and validate the correspondence against canonical state.

```text
START [ACTUAL GRAPH: selected edge]     [Identified Source + Evidence]
MID   [relationship label] ----------> [Source title / ID] --> [passage]
END   [selected relationship] -------> [identified Source] --> [exact quote]
      Labelled conceptual connections; authentic product crops unchanged.
```

<a id="scene-6"></a>

## Scene 6 — The difficult part is deciding what the documents mean together.

### Motion Storyboard

**A. Initial frame:** Three sparse challenge columns: identity, Source attribution, current state. Limitations are visible from entry.

**B. Animation beats:** Three 1s emphasis steps after 1s entry: Bea/Beatrice; two distinct Sources; historical/current role. All remain on screen for 15.5s; 0.5s exit. No name merges or changing graphs here.

**C. Final resting frame:** All three questions and “Tested synthetic challenges; no general conflict-resolution claim.” One small authentic case detail may remain, as in the proposal.

**D. Trigger:** Timeline-only caption emphasis; optional scroll can leave this scene static.

**E. Narrative purpose:** Separate the failure categories without implying universal solutions. This is a quiet explanation, not another bespoke animation.

**F. Technical approach:** Fixed text/example panels; opacity of an external border changes in sequence. No semantic transformation.

**G. Asset dependencies:** Existing proposal examples, B/C/F details and held-out index. Use the same spellings/Source identities as the approved copy.

**H. Complexity:** **Simple.** Risk: challenge cards looking like three solved features. Retain question marks, labels and scope statement.

<a id="scene-7"></a>

## Scene 7 — Let AI interpret. Make the mechanics deterministic.

### Motion Storyboard

**A. Initial frame:** Required genuine refined chain H occupies most width; full stage outlines and external evaluation remain identifiable. Persistent text: “Practitioner baseline: extraction + deterministic construction. Research comparison: add endpoint resolution.” Separate caption: “Professional review is a product action.”

**B. Animation beats:** After 1s entry: emphasize supplied Sources and Extract (3s); optional research Resolve (3s); deterministic Build graph (2s); evaluation outside the chain and separate professional-review caption (2s). Hold 18.5s; exit 0.5s. Use captions “AI interpretation” and “Deterministic checks”; do not depict a guarantee or autonomous legal decision.

**C. Final resting frame:** Actual complete chain, resolver labelled optional/research-only, evaluation outside, practitioner no-resolver distinction and professional acceptance caption. No ghosted essential stage. The static frame must not look like the application enables research resolution by default.

**D. Trigger:** Timeline progression around existing stages. Future scroll uses the same emphasis order, not live component configuration changes.

**E. Narrative purpose:** Make control boundaries legible: where language is interpreted, where mechanics are checked and where human acceptance occurs.

**F. Technical approach:** **Prefer faithful capture plus external highlight masks for P0.** Read-only `AnalysisPipeline` accepts configuration and renders actual stage components, but expansion/menu/scroll/focus are state/effect-driven, not controlled frame props. Unmodified reuse cannot promise deterministic staged states. Genuine component reuse is feasible with frozen props and no clicks if render stability/font sizing pass; choose it only if a small isolated adapter can drive presentation without altering domain/operational components. No parallel chain recreation. A capture remains the required actual refined visual, not a simplified diagram.

**G. Asset dependencies:** H: required future capture of actual refined `AnalysisPipeline` through Workbench `configuration/Pipeline.tsx`; existing implementation currently local/under review. Include full external evaluation boundary and stage metadata, no execution authority or sensitive operational controls. Lock reviewed commit/provenance before production. Historical D is insufficient.

**H. Complexity:** **Moderate** with capture; **complex** if attempting state-driven component animation. Risk: font/canvas sizing or retained live effects changing frames. Fall back to authentic capture, not a drawn substitute.

```text
START [ACTUAL CHAIN: Extract | optional Resolve | Build] | Evaluate
MID   [Extract focus] --> [Resolve focus: research only] | Evaluate
END   [COMPLETE ACTUAL CHAIN]                            | Evaluate
      Practitioner: no resolver.  Professional review: separate action.
```

<a id="scene-8"></a>

## Scene 8 — Change one stage. Keep the evidence fixed.

### Motion Storyboard

**A. Initial frame:** Dataset strip: **“5 development cases → 10 held-out synthetic test cases”**; **“14 Sources · 39 expected relationships”** underneath, scoped to the ten test cases. “Project-authored synthetic data; post-hoc exploratory resolver comparison” remains readable.

**B. Animation beats:** After 1s entry: show original A and retain/freeze its output (3s); reveal two branches from the same retained-output block (3s); label A′ exact zero-call replay and B same inputs + ten resolver calls (4s). Hold 20.5s; exit 0.5s. A′ does not spawn fresh extractions and is not independent validation.

**C. Final resting frame:** Dataset distinction above the fully labelled fork; one common frozen-input object, two branches, no extra extraction boxes. “One execution per case and condition; A′ is exact replay, not an independent repetition.” Separate AI-validator/internal-development caveat remains visible. The PDF contains the entire design, not just B.

**D. Trigger:** Fixed timeline. Future scroll should stop at the fork for reading; same deterministic frame states only.

**E. Narrative purpose:** Teach what is controlled before presenting scores. The development/test arrow means experimental preparation followed by evaluation, not that development cases became test cases.

**F. Technical approach:** Layered protocol labels and simple connectors from existing G flow; frame-clamped reveals. Freeze is an editorial label for retained immutable inputs, not a security seal or animated new software feature.

**G. Asset dependencies:** Existing #136 replay protocol, benchmark index, pinned A/A′/B records and verification procedure in the proposal. No new evaluation or data computation. Do not pool Issue #92 pilot repetitions.

**H. Complexity:** **Moderate.** Risk: confusing reuse with replication, or dataset split with participant counts. Persistent labels and one shared input block address both.

```text
START  5 development cases --> 10 held-out synthetic test cases
       [A: original extraction] --> [RETAINED OUTPUT]
MID                                [FROZEN, IDENTICAL INPUTS]
                                       /              \
END                     [A': no resolution]       [B: resolution]
                        0 new provider calls      10 resolver calls
                        exact replay of A         no new extraction
       14 Sources / 39 expected relationships belong to the test set.
```

<a id="scene-9"></a>

## Scene 9 — On this synthetic set, relationship F1 rose from 94.87% to 100%.

### Motion Storyboard

**A. Initial frame:** Required actual Workbench F1-by-Run plot I already shows its genuine 0–1 y-axis, Run-number x-axis, legend and scope notice. Qualification visible: “Project-authored synthetic; post-hoc exploratory comparison; not production reliability.” No empty chart implying work is running.

**B. Animation beats:** After 1s entry: external focus on A at 0.9487… (2s); A′ at the same value with “exact replay” (2s); B at 1.0000 (2s); expose the complete recorded comparison/coverage emphasis (2s). All genuine points remain present; each focus caption reveals its fixed recorded percentage, never counts upward. Hold 26.5s; exit 0.5s.

**C. Final resting frame:** Complete unmodified plot plus A/A′ 94.87%, B 100.00%, TP/FP/FN summary and 10/10 scored per condition; actual fresh versus saved-input scope distinction and verified replay bridge are readable. No trend line. “Two endpoint corrections in one case explain the entire gain.” All material caveats visible without notes or hover.

**D. Trigger:** Timeline-driven focus, never polling. Optional scroll can select the focus window; it cannot change the plotted values or calculate metrics.

**E. Narrative purpose:** Show measured outcomes while making the relationship between A and its replay control explicit.

**F. Technical approach:** **Prefer an actual complete chart capture with external focus annotations.** This avoids editing its plotting or aggregation code. Existing `RunPerformanceChart` can render supplied frozen values, but tooltip, selected point and filters use interaction state; no existing frame-controlled highlight API is assumed. For a reusable component path, use the actual shared chart with verified immutable props and separate frame-driven annotation layers, no clicks or custom redrawn axes. If capture resolution is inadequate, require a better genuine capture; do not replace the chart with a table.

**G. Asset dependencies:** I, required future capture of the retained experiment in Workbench F1 by Run, all-input mode; `RunChart.tsx` / shared `RunPerformanceChart.tsx`; pinned snapshot/Run identities from proposal. Preserve scope/coverage captions in the crop. A/B costs unpriced, so no F1-versus-Cost panel. Historical D does not contain these measurements.

**H. Complexity:** **Moderate.** Risk: a 0–1 full-scale plot makes the 0.9487→1 difference visually small. Keep real axes and use exact fixed-value annotations; never truncate the axis or exaggerate separation. Different scope identities must stay disclosed.

```text
START [ACTUAL COMPLETE PLOT: real axes + legend + scope notice]
MID   Focus Run 1=A: 94.87%  --> Run 2=A': 94.87% (exact replay)
END   Run 1=A        Run 2=A'       Run 3=B
      0.9487...      0.9487...      1.0000
      [All points remain in their genuine positions; NO connecting trend]
      10/10 each; exploratory synthetic comparison, not reliability.
```

<a id="scene-10"></a>

## Scene 10 — Two endpoint corrections. The same original evidence.

### Motion Storyboard

**A. Initial frame:** Actual heldout_03 context, with a separate editorial “Before: A” summary of the two original Bea source endpoints beside authentic graph/Evidence detail. Show “Conceptual animation — recorded endpoint edits.” Source identity, exact quotation and existing strict evidence-check failures are visible from entry.

**B. Animation beats:** After 1s entry, progressively reveal the two editorial before-state relationship rows (2s); duplicate each source-name label into its “After: B” position and replace only Bea with Beatrice Ng, leaving the before-state labels visible (3s); align both before/after rows on their unchanged relationship types and targets while the shared Source/quote region remains fixed, then reveal “Names changed. Evidence did not.” (3s). Hold 20.5s; exit 0.5s. Both recorded substitutions refer to the same person; no new edge is drawn.

**C. Final resting frame:** Two fully labelled “Before: A / After: B” endpoint-edit rows for the same person beside genuine resolved detail; original quotation, Source attribution and conceptual-animation label persist. Show “Strict evidence-check failures remained” and one concise overhead block: **“+10 calls · 9,821 tokens · 9.06s summed provider-call time, not end-to-end latency.”** Cost unpriced and repeatability unknown remain visible. Detailed metric populations stay linked, as in the proposal.

**D. Trigger:** Deterministic reveal of saved A/B states. Scroll could vary emphasis, never rerun the resolver or animate newly discovered relationships.

**E. Narrative purpose:** Explain the narrow source of the score change and prevent perfect-F1 overinterpretation.

**F. Technical approach:** Use a shared editorial before/after layout with frame-driven name-label movement and replacement, populated from the two retained endpoint edits. Keep each row's type, target and attribution fixed, with one unchanged documentary Evidence region. These explanatory labels live outside authentic screenshots; do not paint replacement names into screenshots or morph product graph nodes. Genuine A/B captures may support the explanation, but conceptual transformation does not depend on fabricating a missing UI state. No new relationship discovery or rewritten quotation.

**G. Asset dependencies:** F packaged original/resolved/Evidence assets; retained heldout_03 endpoint edits, original source, exact quotations and usage. This is heldout_03/Beatrice Ng, not development Case 03/Rebecca Tan or the older pilot. Overhead totals apply to the ten-case treatment, not the two edits alone.

**H. Complexity:** **Moderate.** Risk: implying two people were merged, relationship types changed, or the extra cost was worthwhile. Same-person label, fixed roles/quotes and unpriced disclosure remain in the final state.

```text
START  A: Bea -- settlor_of --> Larch Family Trust
          Bea -- parent_of  --> Isaac Ng
       [Exact Source + quotation stay fixed throughout]
MID    EDITORIAL BEFORE / AFTER — two recorded edits; ONE person
       Before: Bea -- settlor_of --> Larch Family Trust
       After:  Beatrice Ng -- settlor_of --> Larch Family Trust
END    Before: Bea -- parent_of --> Isaac Ng
       After:  Beatrice Ng -- parent_of --> Isaac Ng
       Same roles. Same Source. Same quotation.
       Names changed. Evidence did not. Strict failures remained.
```

<a id="scene-11"></a>

## Scene 11 — Next: keep the Matter current, without losing the review boundary.

### Motion Storyboard

**A. Initial frame:** Built-today and proposed-next panels with explicit status labels. Real-client prerequisites already present.

**B. Animation beats:** After 1s entry, a 2s emphasis shift from delivered synthetic workflow to labelled future Source → proposed changes → reviewed current state. Hold 16.5s; 0.5s exit. No application screenshot morphs into an implemented update screen.

**C. Final resting frame:** Both statuses, future update path, access/tenancy/ownership/data-handling requirements and fresh-case/practitioner validation needs are simultaneously readable.

**D. Trigger:** Timeline; static reading is preferred for future web.

**E. Narrative purpose:** Make the next step credible without spending more animation effort on unbuilt capabilities.

**F. Technical approach:** Existing text-only lifecycle G with future labels; restrained border emphasis. No fabricated product UI.

**G. Asset dependencies:** Approved proposal copy and product/ADR boundaries; optional A crop only for built-today panel. No required new image.

**H. Complexity:** **Simple.** Risk: incremental updates appearing delivered. Status labels remain explicit; no release dates or integration promises.

<a id="scene-12"></a>

## Scene 12 — Make every relationship reviewable.

### Motion Storyboard

**A. Initial frame:** Opening graph/Evidence motif returns in the identical frame position, with closing headline and both URLs already readable. Synthetic-only notice persists.

**B. Animation beats:** After 1s entry, reuse the opening's 2s relationship-to-quote emphasis, then freeze everything for **13s**. No fade-out, countdown or disappearing links. The video ends on the full final frame.

**C. Final resting frame:** Closing proposition, recognisable actual product crop, synthetic notice and full readable URLs: **https://private-client-graph-production.up.railway.app/** and **https://github.com/alistairkung/private-client-graph**. Long URLs may occupy separate full-width lines; no ellipsis or QR-only alternative. Resting frame is complete at local frame 90.

**D. Trigger:** Timeline then permanent final hold; future scroll ends at this stable frame, never loops or forces a return to the beginning.

**E. Narrative purpose:** Connect the product promise to an actionable route for inspection, with a familiar visual callback.

**F. Technical approach:** Reuse scene 1's asset/crop/outline treatment, change only closing copy and URL layout. Frame-derived opacity settles fully before the hold. MP4 text URLs are readable, not assumed clickable; PDF link annotations require a later export check.

**G. Asset dependencies:** Same A crop as 1; Railway domain from the verified existing deployment reference. Root returned HTTP 200 again during this planning task. Reachability does not establish latest research-feature deployment. Repository access may be required.

**H. Complexity:** **Simple.** Risk: unreadable URL length or implying open #152 is deployed. Use separate lines and retain the prototype label; no research-route availability promise.

## Static PDF production contract

Every C subsection specifies its complete resting state; the timing table supplies an intentional local marker. Plan shared scene content, exact evidence records, typography and locale values, with a `resting` presentation mode that removes transitional masks and retains any necessary before/after labels. Prefer the same layout as the video's final hold; when a comparison needs extra space, the video must settle into that same static arrangement rather than leaving a contradictory still-only explanation.

| Slide | Resting-state strategy | Critical context retained |
|---|---|---|
| 1 | Promise plus selected product detail | Synthetic prototype, user and provenance proposition |
| 2 | Sources plus questions | Family connection does not establish trust role |
| 3 | Earlier/current context side by side | Both documents supplied together; fixture; Rachel current/David historical |
| 4 | All three workflow states | Whole-proposal acceptance; demo is preview |
| 5 | Selected edge + Evidence + Source | Complete names, exact words and attribution |
| 6 | Three questions simultaneously | Bounded challenges, not universal solutions |
| 7 | Entire actual chain | Practitioner no resolver; research optional; external evaluation; separate human review |
| 8 | Full dataset strip and fork | 5 development / 10 held-out; 14 Sources / 39 edges; identical saved inputs; replay qualification |
| 9 | Entire actual plot plus fixed values | Real axes, one point/Run, fresh/saved scopes, 10/10, synthetic/post-hoc limits |
| 10 | Recorded endpoint before/after summary | One person, unchanged Evidence, remaining failures, treatment overhead/time meaning |
| 11 | Built/future comparison | Governance prerequisites and validation needs |
| 12 | Opening motif plus closing links | Full URLs and synthetic-only notice |

After implementation approval, use explicit Still registrations or renderStill at these complete states, not a video frame sampled by percentage or the last frame of a transition. Current docs list PDF imageFormat; test the pinned renderer before relying on that path. Alternative: export the same twelve intentional lossless stills and assemble twelve 16:9 PDF pages with a standard PDF tool. That is an assembly step, not another presentation framework. Check page count, order, aspect ratio, fonts/glyphs, exact numbers, native-resolution legibility and PDF hyperlink behavior in both locales. Raster output may lack searchable/tagged text; do not claim accessibility compliance. A later PDF skill can govern that production/verification task. No export occurs now.

## Required asset and capture inventory

The [proposal register](12-slide-proposal.md#layout-and-asset-conventions) remains the provenance authority. Cross-branch result data and publication workflow are pinned there to PR #152 commit `21e3ff348757955df805d0d8a1d44d862e1549fd`, not relative links to absent files on #153.

| Item | Availability now | Preparation after approval | Scenes / risk |
|---|---|---|---|
| A, product proposal capture | Pinned repository asset on #131 | Package original; verify full endpoint/quote crop; preserve substitute-provider label | 1, 4, 5, 12; not measured quality |
| B/C, multi-source/current-state sample | Pinned repository screenshots + fixture Sources | Package original; confirm Source/relationship correspondence; capture missing selected state only if needed | 2, 3, 5, 6; curated ideals |
| D, historical Workbench screenshot | Repository asset | Context only; never relabel its demonstration numbers as final experiment | Not a replacement for H/I |
| E, approved Evidence Folio comp | Repository art-direction asset | Tokens/composition reference only; no generated UI text reused | Whole deck identity |
| F, measured original/resolved/Evidence captures | Existing machine-local assets, not portable | Package provenance + exact approved crops; verify both edits and unchanged quote | 10; under-review UI, not deployment proof |
| H, refined actual Workbench chain | Local shared component + adapter; final slide capture not verified | Required capture before production, readable stage metadata and external evaluation; freeze reviewed source commit | 7; no recreated chain |
| I, actual retained-experiment F1 plot | Local shared chart + adapter; final slide capture not verified | Required real Workbench capture in all-input/F1-by-Run mode, actual A/A′/B and scope/coverage; package full legend and axes | 9; no invented/case-index chart |
| Exact experimental records | Commit-pinned snapshot/publication verification | Package approved synthetic fields and values read-only; no provider/raw credentials, no rescoring | 8–10; preserve lineage and null costs |
| Fonts | Existing self-hosted Latin Newsreader/Public Sans; Chinese uses OS fallback in app | Package licensed CJK font for reproducible renderer; glyph/weight/punctuation audit; do not depend on host OS fonts | Both locales; current CJK portability gap |
| Localization | Product catalogs exist; deck translation not yet reviewed | One shared semantic content map; reviewer checks Chinese scientific qualifiers and original-English Evidence | All; avoid two divergent decks |
| Closing URLs | Existing Railway domain verified reachable; repo known | Recheck public root and intended audience access immediately before handoff | 12; no assumed research URL |

No capture was taken, no image edited, no asset copied into a production project and no raw private experiment archive opened by this task. Missing H/I assets are explicit future production gates, not reasons to downgrade the storyboard or launch application work.

## Bilingual design and silent-reading contract

One sequence definition per scene, one shared evidence/metric source and one locale parameter. Separate language outputs are exports, not independent slide implementations. The current English copy stays in the proposal; a future localized content map translates visible headings, captions, limitations and URL labels. Deck translation is still work to do, not proven by the application's existing bilingual UI.

Preserve original entity names, Source titles/IDs where authoritative, quotations, Run IDs, numbers and endpoint edit values. For example, a Chinese explanatory label may translate “current trustee,” but never translate Rachel Lim, substitute the Willow trust name or rewrite the English quotation. Provide Chinese explanations outside exact-evidence highlights; they are translations for explanation, not alternative evidence strings.

Use Newsreader for Latin editorial text and Public Sans for Latin body/UI, with a licensed packaged Simplified Chinese face matched for hierarchy. Existing CSS falls back to PingFang SC/Microsoft YaHei, which is not a portable render asset. Exact font choice and redistribution permission must be settled before rendering. Keep numerals/percentages aligned with consistent widths; allow Chinese qualifications an extra line and preserve Latin names as readable units. Do not apply Latin letter spacing mechanically to CJK or shrink caveats until they fit.

Where localized genuine UI captures exist, verify identical selection/state before pairing them. Otherwise reuse original-English UI with localized outside captions, visibly preserving the source context; do not fabricate a Chinese screenshot or alter original evidence. Avoid captions that compete with simultaneous metric/quote reading. No narration means there is no separate subtitle track to rescue omitted meaning.

## Optional hosted scroll presentation — defer until after submission

**Verdict: defer until after submission.** Reuse is technically plausible, but a low-effort, publicly accessible scroll story is not established. The official [Player documentation](https://www.remotion.dev/docs/player/player) supports embedding the same React scene component and seeking through its ref. A paused Player could map normalized section scroll progress to a clamped integer scene frame. Use the locale's cumulative timing map; do not change the animation clock or maintain a parallel animation framework. Scroll event handling is allowed only in that future host wrapper, not inside MP4 scene semantics.

However, this does not solve mobile readability of a 1920×1080 chart, keyboard navigation, reduced motion, content exposure to assistive technology, asset loading, font packaging, deep links or static deployment. Player seeks can be performance-sensitive; mounting twelve full UI trees or seeking on every raw scroll event needs profiling. Read-only packaged data/assets permit a static hosting design in principle, but no host, public publication authority or deployment is approved here.

If revisited: mount one active shared scene; throttle frame seeking to browser repaint; avoid React rerender loops; retain native document scrolling and explicit next/previous chapter links, pause/play and static-state controls. With reduced motion, show the twelve resting states in normal flow; also provide readable text/evidence outside a canvas and both downloadable PDFs. On mobile prefer responsive static resting states plus optional video rather than shrinking a desktop chart into a sticky postage stamp. These requirements add a distinct QA surface even with shared scenes. Budget it only after all four P0 files pass acceptance; do not begin P1 or create another deck framework during P0.

## Production checkpoint and reuse-driven completion

The production strategy is **one representative scene first, then reuse across the remaining eleven**, after separate production authorization. The approved narrative, timing approach, four P0 outputs and static PDF contract remain. No implementation, previews or export are authorized by this text-only revision.

### Representative-scene checkpoint

Recommend **scene 10**: it tests authentic screenshot handling, a meaningful conceptual transformation, exact English names/quotations, dense scientific disclosures, bilingual reflow and an intentional before/after resting state within a single bounded scene.

1. Establish the shared Remotion visual system: Evidence Folio tokens, type scale, safe areas, deterministic scene clock, localized content, licensed portable CJK font loading and a shared resting-state mode.
2. Implement scene 10 end to end, using the two recorded edits and genuine graph/Evidence assets. Build its motion from reusable primitives rather than a scene-specific animation engine.
3. Render that scene alone as English and Simplified Chinese MP4 previews, using the planned 30s/32s scene budgets. These are checkpoint artifacts, not full-deck exports.
4. Export and inspect its intentional PDF resting frame in both languages: one complete page per language for the checkpoint, not the final twelve-page decks.
5. Review typography and CJK glyph coverage, exact source/name preservation, screenshot resolution at intended display size, visible scientific disclosures, truthful labelling, restrained explanatory motion and readability without narration. Verify the fixed Source/quotes and both before/after endpoints survive the static export. Check the declared frame count and hold timing against each preview.
6. Present the two previews, two resting-page proofs, identified fixes and measured implementation effort for owner checkpoint approval. **Only after that checkpoint is approved** should the approach scale to the remaining eleven scenes. If it fails, fix the representative scene and shared primitives first; do not compensate with eleven bespoke solutions.

The checkpoint proves the reusable approach, not the final Workbench assets: H and I still require authentic, readable chain/chart preparation and scene-specific acceptance. They cannot be replaced with conceptual drawings. No provider call, evaluation, application change or deployment is needed for this production checkpoint.

### Shared primitives and layouts

Reuse one frame-driven motion vocabulary: progressive disclosure/masked reveal; correspondence-connector reveal; focus/detail transition; editorial before/after label transformation; fixed recorded-value annotation; and stable reading hold. Share the title/qualification region, source-plus-result layout, relationship/Source/quote arrangement, recorded before/after rows and authentic full-width UI frame. One locale parameter and one evidence/metric source feed both video and intentional still output. Do not fork English/Chinese scenes or maintain a separate PDF deck implementation.

Reserve bespoke choreography for the six highest-value sequences below. Most work after the checkpoint should configure approved primitives and content; quiet scenes use shared layouts and short focus changes. Use actual checkpoint effort to revise the remaining-work estimate and surface asset blockers before committing to a completion date.

| Priority after checkpoint | Sequence | Reuse / bounded customization | Prior uncertain estimate |
|---|---|---|---|
| 1 | 7 — actual chain and control boundaries | Authentic H in shared UI frame; stage-focus/reveal primitives | 3–5 hours |
| 2 | 9 — actual F1 and replay distinction | Authentic I in same frame; fixed-value annotations, scope disclosure | 3–5 hours |
| 3 | 5 — relationship → Source → exact quotation | Source/detail layout and connecting-reveal/focus primitives | 3–4 hours |
| 4 | 8 — identical saved inputs → paired branches | Shared labels/connectors; only the fork needs custom choreography | 2–3 hours |
| 5 | 2–3 — supplied documents → current trustee | Source/result layout; historical/current assertion transformation | 4–6 hours |
| Representative | 10 — two recorded endpoint substitutions | Establishes before/after and unchanged-Evidence primitives at checkpoint | 3–4 hours |

These hours are **uncertain prior planning estimates, not delivery commitments or independent bookings**. The earlier 18–27h major-sequence subtotal and 34–52h overall estimate are historical planning envelopes, superseded as a scheduling method by this checkpoint. Do not add checkpoint time mechanically to them: checkpoint assets, layout, localization and primitives are reused. No calendar completion promise is made. Re-estimate remaining production, bilingual review and export QA from demonstrated reuse and checkpoint findings.

After checkpoint approval, complete the required chain/chart scenes first, then compose the remaining explanatory scenes from shared primitives and fill the quiet scenes. Inspect each resting state as its scene settles; perform final silent-reading and bilingual checks before generating the four final P0 files. Final PDFs still contain exactly twelve pages each. The optional hosted presentation remains deferred until after submission.

Low-cost supporting motion: 1's opening emphasis; 4's workflow focus; 6's three questions; 11's built/future contrast; and 12's reused opening callback. Genuine component reuse remains optional and read-only: `AnalysisPipeline`, `PipelineNode`, `RunPerformanceChart`, approved graph/Evidence visuals and existing tokens. If state/effects introduce scope, use faithful captures. No operational API, execution authority or domain/evaluator import is required.

Cut fake uploads/clicks/provider runs, invented edges or statistics, metric count-ups, automatic page scrolling, decorative springs/parallax and duplicate scene-specific engines. **Keep the labelled conceptual transformations in 3, 5 and 10:** they explain supplied or recorded facts and are distinct from fabricated application behavior. If time tightens, simplify choreography while preserving the correspondence, actual Workbench chain/plot and scientific qualifications.

## Final planning self-review and acceptance

- **Narrative coherence:** the approved twelve-slide arc, headline order, timing, scientific qualifications and PDF strategy remain. This focused refinement strengthens only the conceptual explanations in 3/5/10 and replaces the scheduling method with a representative-scene checkpoint followed by shared-primitives reuse.
- **Over-animation:** six major sequences; the rest quiet. Scenes 3/5/10 now permit purposeful, persistently labelled conceptual transformations outside authentic screenshots. Reading holds stay stable; opening/closing share one motif. Fake clicks and fabricated application behavior remain excluded.
- **Factual integrity:** Case 05 is supplied-together curated output; heldout_03 is the Bea result. A′ is zero-call exact replay. A/B metrics, Source identities, unchanged quotations, remaining strict failures, tokens, summed duration and unpriced costs retain their meanings. No production reliability or deployment guarantee.
- **Readability:** English 4:54, Chinese allowance 5:06, closing hold 13s. Real silent-reading tests, font/glyph checks and visual verification remain future work; this Markdown cannot certify them. Caveats stay onscreen, not only in notes.
- **Technical feasibility:** frame-based conceptual transformations and genuine capture focus use shared primitives. Scene 10 is the bilingual end-to-end checkpoint before scaling to eleven other scenes; prior hours are uncertain, not commitments. Authentic Workbench chain/chart requirements remain. Stateful components require isolation; no frame-control prop is invented. Explicit stills provide the PDF path; scroll hosting remains deferred.
- **Scope:** this revision changes Markdown only. No scaffolding, dependency installation, screenshot, recording, image edit, animation code, render, export, prototype, application change, evaluation, paid provider call, merge or deployment.

The existing narrative, timing and PDF approvals remain in place. This focused storyboard refinement still stops at the planning boundary: wait for owner approval before production, including the representative-scene checkpoint. No implementation or output production has begun.
