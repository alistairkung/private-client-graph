# Public research publication — design for review

Status: design C approved by the owner in conversation on 2026-10-17 (Asia/Hong_Kong). Specification and implementation approved by the owner invoking implement-spec #148. No new experiment, paid call or deployment is included. Governing specification: [#148](https://github.com/alistairkung/private-client-graph/issues/148); implementation lanes [#149](https://github.com/alistairkung/private-client-graph/issues/149), [#150](https://github.com/alistairkung/private-client-graph/issues/150), [#151](https://github.com/alistairkung/private-client-graph/issues/151).

## Job and audience

Competition judges arrive from the public landing page with limited time and a reasonable question: what was actually measured, and can I inspect the evidence? The results page uses Read mode, with an Operate-style evidence inspector inside it. The landing section uses Persuade mode within the approved Evidence Folio composition. Success is a short, truthful reading path from measured relationship improvement to the exact two edits, original Sources and limitations.

## Outcome and proof

The publication answers five questions in order: what was measured; what changed; where the Evidence is; what the execution used; and what cannot be concluded. Its distinctive fact is narrow: A/A′ relationship micro-F1 was 94.87%; B was 100.00%; two canonical-name edits in one case explain all improvement. These are retained outcomes from ten project-authored synthetic development cases, not a fresh model run or production validation.

Both prominent figures get an asterisk. The full internal-development disclosure and the post-hoc/two-edits explanation remain visible immediately below, including on mobile. Source text is original selectable text. Gold marks exact Evidence, never a performance badge. Do not put perfect-score celebration, green success stamps or an accuracy gauge around 100.00%.

## Visual authority

Extend the approved Evidence Folio from the existing landing direction, PRODUCT.md, DESIGN.md and actual public source. Keep Newsreader Display for editorial headings, Public Sans for interface/body copy, deep ledger green #173e38, paper #f6f6f1, white, restrained burgundy #773b46 and Evidence gold #efdda0. Use the public application's implemented fluid gutters and shared fonts; DESIGN.md's nominal width is not authority to override current component layout. Chinese uses the existing catalogue and glyph fallback; permit shorter headings, taller text and natural wrapping without reducing the caveat to small print.

No new identity, illustration, paper texture asset, display metaphor or framework is required. Existing gold quote highlighting and the professional Evidence inspector provide the signature. The public results page has the familiar brand/navigation/language control; its primary task is reading, so do not reuse the landing hero's oversized type in controls or metrics tables.

## Common landing composition

Sequence remains hero → deep-green approach chapter → new light research section → contained demonstration. The new section uses one editorial heading, a small internal-benchmark label, two adjacent labelled figures and one reading-width caveat/disclosure block. There is no dashboard card grid or separate chart just to repeat two numbers.

Desktop: heading occupies the left editorial column; baseline and resolver micro-F1 sit on a common baseline in the right area, with the visible asterisk explanation directly below both. Supporting context and full disclosure span a comfortable reading measure. End with Explore the research results →. Tablet: the heading moves above the figures. Mobile: figures stack, each with its complete label; the shared asterisk paragraph follows immediately, then the full disclosure and link. The existing contained demonstration begins as a separate framed section below.

English heading: Measured against a controlled synthetic benchmark.

Chinese heading: 基于受控合成基准数据集的评估.

English disclosure: Evaluated on ten project-authored, held-out synthetic cases used as an internal development benchmark. No real client data was used. These results do not establish production accuracy or reliability.

Chinese disclosure: 本次评估使用项目自行编制的十个留出合成测试案例，作为内部开发基准。未使用真实客户数据。这些结果不代表系统在实际生产环境中的准确率或可靠性。

Asterisk: Small internal development benchmark. The resolver comparison was post-hoc and exploratory; two name corrections in one case accounted for the entire improvement.

Chinese asterisk: 小规模内部开发基准。实体解析比较为事后开展的探索性比较；全部提升来自同一个案例中的两处名称修正。

## Results composition choices

**Selected: C — Paired comparison and Evidence workspace.** The owner approved C; A/B below are archived alternatives, not implementation directions. The common landing, disclosure, bilingual, responsive and inspection requirements remain part of the approved design.

The identity, content, landing section and all inspection capabilities are fixed across these alternatives. Only page topology and reading path vary. These are wireframe schematics for composition review, not screenshots of a built application. Image generation is excluded by this task's no-paid-calls constraint; the repository's standing comp-first preference remains unchanged.

### A — Research report with section navigation

A slim numbered contents rail sits beside a calm report column. The opening answers the research question with paired figures and adjacent caveat, followed by a compact three-Run comparison. Findings, Cases and Evidence, Provenance, Usage, Methodology and Limitations are ordinary anchored sections; the full disclosure is also present at the top.

The signature moment is an inline link, Inspect the two corrections, which moves to heldout_03 and selects the retained endpoint-edit view beside exact Source Evidence. Section navigation makes usage/methodology reachable without hiding the reading column behind application tabs. Lower inspection sections may be denser while the introduction stays readable. On mobile the rail becomes a compact contents disclosure above the article; the scientific caveat never goes inside it.

Strength: the most natural scientific reading sequence, with familiar document wayfinding. Risk: the page is long; the jump links and a clear return to summary must earn their place.

### B — Tabbed research reference

The top keeps the title, paired result, caveat and disclosure visible before four plain tabs: Findings; Cases and Evidence; Usage; Methodology and Limits. Findings shows A/A′/B relationship and provenance tables. Cases and Evidence exposes the full ten-case index and the shared inspector. Usage exposes Run totals and individual call rows. The methodology tab holds full detail, while its essential limitations remain outside the tabs.

The signature moment is persistent selection: switch between the case, provenance and usage context without losing which case/Run/relationship was selected. On mobile tabs wrap into a conventional labelled control without sideways page overflow; each panel has a heading and a clear reading order. Tab changes do not reset the case inspector or locale.

Strength: shortest page and clear separation of reference material. Risk: deeper content is less discoverable until a judge chooses a tab; essential claims/limits must stay in the shared opening.

### C — Paired comparison and Evidence workspace

A concise opening and visible caveat lead directly into a compact A/A′/B comparison table. Beneath it, a ten-case index and paired baseline/replay-versus-treatment relationship view sit beside the original Source inspector. Use baseline A′ and treatment B for the direct paired inspection; A remains accessible with its exact replay-equivalence explanation. Do not misrepresent A/A′ as independent replications.

The signature moment is linked inspection: choosing either of the two endpoint edits exposes the before/after name, corresponding relationship outcome and exact quote/Source in one place. An unchanged-case selection shows an explicit unchanged result. Provenance, usage and methodology remain ordinary anchored sections below. On mobile the case selector precedes the relationship list and the Source follows the selected relationship inline; no three-column miniaturization or narrow nested scrolling.

Strength: fastest route from aggregate score to the actual difference. Risk: the first working section is denser and can feel closer to the internal Workbench; strict editorial framing and the curated contract prevent that drift.

## Shared interaction and state design

- Comparison: compact rows for A, A′ and B, with exact Run IDs available as copyable/wrapping text in run details. Show precision, recall and micro-/macro-F1, TP/FP/FN and scored coverage without compressed acronym-only labels. A/A′ share outcomes, not identity. Explain zero-call replay separately.
- Case selector: all ten named case identities with per-Run results and change status. Default overview covers all cases; the deliberate Inspect the two corrections action selects the changed case. No silent selection implying that one case represents the whole dataset.
- Relationship inspection: expected and retained predicted relationships are explicitly labelled. Outcome filters such as false positives/false negatives operate on saved results. B's zero-error view says No recorded relationship errors, while still allowing all expected/predicted relationships to be inspected.
- Corrections: render two recorded edits as before/after endpoint names tied to their actual relationships. The display establishes exact-label changes, not unmeasured identity-disambiguation success. Do not invent or paraphrase an evidence quote for a mockup.
- Source/Evidence: show original Source title/ID and exact quote, with a full-Source reading area and existing quote highlight behavior. Source switching is visible when multiple Sources apply. Identical quotation strings from distinct Sources remain distinct records. Distinguish expected approved Evidence from predicted Evidence and show exact-boundary diagnostics honestly.
- Provenance: use two separately named rows/definitions with numerator and denominator visible. Explain why relationship corrections change the evaluated population. A wrong Source and an exact-boundary mismatch are distinguishable diagnostic reasons. Colour alone never identifies outcomes.
- Usage: a small Run totals table above a read-only call list. Stage/case/model/status lead; token breakdown, provider duration and Unpriced follow. Per-call detail is expandable for metadata density only, with no raw payload area. A′ explicitly shows 0 calls, with an explanatory zero-call control state. Missing metadata says Unavailable; unavailable pricing says Unpriced. Cached tokens are a subset, never a new additive total.
- Publication identity: Download results / 下载研究结果 is a modest secondary action near the title and publication metadata. Show schema version, snapshot identity and digest in a plain metadata section; long digests wrap/copy without expanding page width. Download uses the exact artifact shown, not a separately generated export. No giant JSON block or generic log browser in the default view.
- Loading/unavailable: quiet labelled loading region if needed; an unavailable artifact replaces claims/figures with safe translated explanation. No stale numerical fallback or zero-valued pseudo-results. Optional missing per-call fields remain distinguishable from a missing publication.
- Navigation and state: native document links for route/section navigation, no publication-management sidebar. Locale changes preserve current case, Run/comparison, relationship, Source, Evidence and active tab/section context. Back/refresh follow established routing; deep-linking every ephemeral selection is not newly required.

## Responsive and accessibility acceptance

Use the actual application's desktop/mobile breakpoints as the starting point; verify at representative 1440px and 390px widths in both languages. Reading text stays around 16px with a comfortable 60–75-character measure on desktop. Full original Sources can use existing professional-review density. Avoid fixed-height text containers and fixed-width Chinese controls.

Tables retain semantic headers. On mobile permit a labelled local table scroller only when the comparison genuinely needs one; keep critical metrics and limitations readable without horizontal scrolling. Case/relationship/Evidence layout stacks in task order. Primary targets retain at least 44px usable height, visible focus and keyboard-operable selection. Announce changed inspection headings/status politely without repeatedly reading the complete Source. Outcomes have text labels and accessible names, not just colour. No score counters, celebratory animation or motion-dependent understanding. Respect reduced motion.

The implementation screenshot matrix is English/Chinese × desktop/mobile for the landing section and results overview, with representative correction/Evidence and call metadata states. These will be genuine implementation captures later; the current decision page is only a schematic.

## Delivery constraints and approval status

All surfaces consume one verified snapshot, with exact original Sources/identities and no live/private fallback. This design does not change the internal Workbench, practitioner application, domain semantics or extraction/resolver defaults. Contract ownership remains Lane A, viewer Lane B, shared header/catalogue/landing/combined acceptance Lane C.

Design C is approved. The completed specification #148 still requires separate owner approval before implementation. This design selection alone does not authorize starting application work. Shape stops at design approval; no direction contract, UI code, public snapshot or application acceptance screenshots have been created in this planning stage.

## Implementation direction contract

Preserve Evidence Folio and selected C: editorial opening, paired A′/B comparison, selectable case index, recorded relationship outcomes and original Source inspector. SourcePanel is the shared safe presentation seam; no internal Workbench operations or styles enter the public surface. Gold marks exact quotations, including selectable occurrences; a missing exact match is explicitly reported. Read mode with Operate inspection. Use plain anchored provenance, usage and methodology below the workspace. Follow the source artifact exactly, with no browser evaluation or invented outcomes.
