# Private Client Graph — 12-slide judge pitch proposal

Planning document for review. Exactly 12 proposed slides; no slide production is authorized by this document.

## Persuasive arc

This is a submitted reading deck: every essential product boundary and research qualification must be understandable without narration. Speaker notes provide optional depth, not missing context.

The judge should move from **“I recognise the review problem” → “I can see the product working” → “I understand why its output is inspectable” → “I can interrogate its measured result” → “This deserves a carefully governed next step.”**

Slides 1–5 establish the user, opportunity and experience. Slides 6–7 explain the difficulty and trust mechanism. Slides 8–10 establish research credibility through a controlled comparison, its actual outcome and its limits. Slide 11 proposes the next product step; slide 12 invites exploration. Engineering supports those beliefs throughout, without a separate development-history chapter.

The opportunity is a practitioner workflow hypothesis, not a quantified market claim: private-client solicitors and advisers need to reconstruct family and trust relationships while checking their documentary support. This pitch promises reviewable structure, with professional judgment remaining explicit. It makes no claim about time saved, revenue, adoption or legal correctness.

## Research basis and truth labels

Research checked all **97 GitHub PR records**, from #1 through #152 (issue numbering contains gaps), including bodies, states, available issue comments and submitted reviews. All PR/discussion connections were exhausted; most PRs have no separate discussion or submitted review. Review summaries inside PR descriptions are attributed accounts, not independent review transcripts. Relevant linked issue discussions, design decision records, ADRs, benchmark definitions, retained results and existing visual artifacts were also examined.

Key review decisions shaping this narrative:

- [#73](https://github.com/alistairkung/private-client-graph/pull/73) reverted #68–#71. Their old landing composition is not current product evidence. [#74](https://github.com/alistairkung/private-client-graph/pull/74) and [#75](https://github.com/alistairkung/private-client-graph/pull/75) establish the replacement Evidence Folio identity.
- [#125](https://github.com/alistairkung/private-client-graph/pull/125) supersedes closed #80's benchmark work. Its review distinguishes authored ideals, separate AI-validator checks and the human execution gate. It does not establish external human validation.
- [#136's discussion](https://github.com/alistairkung/private-client-graph/pull/136#issuecomment-6231106341) confirms exact retained-input pairing and endpoint-only edits; its implementation review explicitly made no actual A′/B execution claim. Actual outcomes come from retained experiment evidence below.
- [#143](https://github.com/alistairkung/private-client-graph/pull/143) integrates the bilingual public demo; #144–#146 are review slices, not three additional releases. Its confirmation preview opens a pre-existing example and performs no write.
- [#148's design discussion](https://github.com/alistairkung/private-client-graph/issues/148) records the choice of paired comparison C and later implementation authorization. [#152](https://github.com/alistairkung/private-client-graph/pull/152) contains the research publication implementation but was **open at research time**. Its local captures demonstrate an implementation under review, not a merged or deployed research page.

Capability labels used below:

| Label | Meaning |
|---|---|
| **Merged capability** | Delivered in merged PRs; deployment and production suitability are separate questions. |
| **Demonstration fixture** | Genuine application UI using curated synthetic inputs or substituted providers; not measured model performance. |
| **Retained experiment** | Saved actual observations, with identities, coverage and metrics; not a new execution. |
| **Implementation under review** | Existing local/open-PR implementation or capture; not claimed merged/live. |
| **Future work** | Product direction requiring separate design, approval and validation. |

Some older root/design documents retain superseded scope statements. For example, original one-PDF intake design is extended by merged #130/#138; the current application supports 1–5 synthetic PDFs. Current merged behavior and explicit supersession decisions take precedence over stale status paragraphs.

## Layout and asset conventions

Each box below represents one 16:9 slide. The boxes specify composition, not final typography. Use approximately 6% safe margins, one dominant headline, no more than two principal reading regions and generous space around UI crops. On later production, target roughly 40–48 pt headlines, 24–28 pt body copy and at least 18–20 pt visible qualifications. A full webpage squeezed into a slide is unacceptable: use a focused crop with complete endpoint names, relationship label and source attribution intact.

Preserve [Evidence Folio](../DESIGN.md): ledger green `#173e38`, warm paper `#f6f6f1`, Newsreader headings, Public Sans supporting text, restrained burgundy annotations and gold only for exact Evidence. Retain the existing Trust triangle and role semantics. No stock imagery or decorative network diagrams. Reserve approximately 25% text expansion space for later Simplified Chinese production; translate UI labels and narrative, preserving original names, source quotations and identities.

All references are text links; no assets are embedded or generated here.

| Asset | Existing source and status | Proposed reuse |
|---|---|---|
| A — Product proposal capture | [practitioner-proposal.png](https://github.com/alistairkung/private-client-graph/blob/dc668c5a31f900bf384e2fcc79a500b3f095e823/submission/assets/practitioner-proposal.png), with [provenance](https://github.com/alistairkung/private-client-graph/blob/dc668c5a31f900bf384e2fcc79a500b3f095e823/submission/assets/PROVENANCE.md). Genuine local two-PDF journey; Google/model substitutes; real construction/persistence. Preserved on open #131, not a performance observation. | Product overview and source/graph/Evidence detail. |
| B — Multi-source sample | [showcase-case-04.png](https://github.com/alistairkung/private-client-graph/blob/dc668c5a31f900bf384e2fcc79a500b3f095e823/submission/assets/showcase-case-04.png). Genuine UI with authored ideal fixture; same provenance record as A. | Source identity and corroboration. |
| C — Temporal sample | [showcase-case-05.png](https://github.com/alistairkung/private-client-graph/blob/dc668c5a31f900bf384e2fcc79a500b3f095e823/submission/assets/showcase-case-05.png). Genuine UI with authored ideal fixture. | Current-state example; never imply measured model success from this screenshot. |
| D — Implemented Workbench | [desktop capture](../docs/design/assets/research-workbench-117-desktop.png), [capture record](../docs/design/research-workbench-117-implementation.md), merged #120. Deterministic synthetic observations, including intentional recovery states. | Historical UI context only. Its chart numbers are not the final experiment; it cannot substitute for the required refined chain or measured F1 capture. |
| E — Approved visual direction | [Evidence Folio comp](../docs/design/assets/public-landing-evidence-folio.png), [design record](../docs/design/public-landing-visual-direction.md). Existing generated/approved composition reference, not product truth. | Palette, typography and spatial rhythm only; do not reuse generated interface text as evidence. |
| F — Measured study captures | [capture index](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/screenshots.json), [results capture](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-results-en-desktop.png), [original graph](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-original-en-desktop.png), [resolved graph and Evidence](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-graph-en-desktop.png). Genuine existing local #152 implementation captures of retained results; implementation under review. Machine-local paths are not portable published assets. | Endpoint-correction inspection. Local assets requiring packaging before production; not verified final captures of the refined chain or Workbench F1 plot. Historical headers are irrelevant to these crops. |
| G — Architecture and workflow schematics | Existing text diagrams in [shared pipeline design](../docs/design/shared-analysis-pipeline.md), [intake design](../docs/design/matter-intake-slice.md), [aggregate contract](../docs/design/research-workbench-run-aggregate-evaluation.md), and [publication workflow](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/docs/workflows/public-research-publication.md). | Workflow context for slides 4, 8 and 11. Not a substitute for the actual Workbench chain required on slide 7. |

### Production asset readiness

- **Available repository asset:** A–E have repository links. A–C are pinned assets on open #131; D is a historical implementation capture; E is art direction only. Availability does not make any of them measured final-experiment visuals.
- **Local asset requiring packaging:** F exists only at the listed machine-local paths. Preserve its capture provenance and package approved crops before handing off to a production agent. Do not silently assume those paths are available on another machine.
- **Required capture before production — H, refined Workbench chain:** capture the actual refined `AnalysisPipeline` view, as used by `web/research/configuration/Pipeline.tsx`, large enough to read Extract → optional Resolve → Build graph, with evaluation visibly outside the pipeline. The refinement currently exists in local work under review (`web/src/shared/research/AnalysisPipeline.tsx`); it is not an available packaged slide asset. Existing D does not satisfy this requirement.
- **Required capture before production — I, retained-experiment F1 plot:** capture the actual `RunPerformanceChart` in the Workbench's Run history & performance → F1 by Run view (`web/research/workspace/RunChart.tsx`; shared refinement `web/src/shared/research/RunPerformanceChart.tsx`), displaying the retained A/A′/B experiment. Preserve its real 0–1 axis, Run-number axis, legend, coverage and scope disclosures. One point represents one Run's observation-weighted micro-F1. The local public `PublishedPerformance` view reuses that component, but is not proof that the required Workbench capture has been made. No substitute table, case plot, synthetic chart or newly drawn diagram is permitted.

H and I are production prerequisites, not actions authorized by this revision. Leave their placeholders until captures are separately authorized and supplied. Keep the local refinement's eventual reviewed source commit and capture provenance with the packaged assets. The following evidence links are pinned to PR #152 commit `21e3ff348757955df805d0d8a1d44d862e1549fd`; they do not depend on #152 being merged.

## Slide 1 — See the relationships. Read the evidence.

**Purpose:** Make the value understandable immediately, with the actual product as the hero.

**Key takeaway:** Private Client Graph turns synthetic private-client documents into relationship graphs a practitioner can inspect.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  PRIVATE CLIENT GRAPH                                     FTEC5660   |
|                                                                      |
|  See the relationships.          +---------------------------------+  |
|  Read the evidence.              |                                 |  |
|                                 |  [ACTUAL PRODUCT GRAPH]         |  |
|  Family and trust relationships |                                 |  |
|  linked to their source text.   |  selected edge --> Evidence     |  |
|                                 |                                 |  |
|                                 |  [EXACT QUOTE DETAIL]           |  |
|                                 +---------------------------------+  |
|                                                                      |
|  For private-client solicitors and advisers.                          |
|                                                                      |
|  Synthetic research prototype                                        |
+----------------------------------------------------------------------+
```

**Actual slide copy:** “Private Client Graph”; “See the relationships. Read the evidence.”; “Family and trust relationships linked to their source text.”; “For private-client solicitors and advisers.”; “Synthetic research prototype.”

**Visual asset reference:** A, cropped to graph and selected Evidence; E supplies art direction only. Preserve the genuine screenshot's own names and labels. Do not put benchmark scores in this opening.

**Speaker notes:** Introduce the practitioner task: understanding who is connected to whom, in which family or trust role, and why the record supports that connection. The product offers an inspectable starting point for review. The screenshot is a synthetic workflow demonstration, not a fresh extraction or a claim about accuracy on client files.

**Evidence:** [PRODUCT.md](../PRODUCT.md); merged [#17](https://github.com/alistairkung/private-client-graph/pull/17), [#75](https://github.com/alistairkung/private-client-graph/pull/75), [#138](https://github.com/alistairkung/private-client-graph/pull/138); [trust presentation decisions](../docs/design/trust-structure-presentation.md).

**Unsupported claims / validation:** Practitioner value remains a hypothesis; no adoption, time-saving or market-size claim.

## Slide 2 — The facts arrive as documents. The questions span relationships.

**Purpose:** Make the review problem concrete without relying on generic “too much paperwork” rhetoric.

**Key takeaway:** A practitioner must distinguish family connections, trust roles and the documentary basis for each.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  The facts arrive as documents.                                      |
|  The questions span relationships.                                   |
|                                                                      |
|  +-----------------------------+   Who belongs to this family?        |
|  | [SOURCE 1: ATTENDANCE NOTE]  |                                      |
|  | actual short excerpt        |   Who holds each trust role?         |
|  +-----------------------------+                                      |
|       +--------------------------+ Which source supports that link?   |
|       | [SOURCE 2: FOLLOW-UP]     |                                   |
|       | actual short excerpt     |                                   |
|       +--------------------------+                                   |
|                                                                      |
|  A family connection does not establish a trust role.                 |
|                                                                      |
|  Illustrative synthetic Matter                                       |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline as above; “Who belongs to this family?”; “Who holds each trust role?”; “Which source supports that link?”; “A family connection does not establish a trust role.”; “Illustrative synthetic Matter.” Source excerpts remain verbatim.

**Visual asset reference:** B's two-Source review regions, with text from [Case 04 Sources](../cases/case_04/README.md). Use a maximum of two short passages, not whole pages; retain Source titles.

**Speaker notes:** Use the fictional Matter to show why a list of names is insufficient. A beneficiary can have no asserted family connection; being someone's child does not establish a beneficiary role. This is the reasoning burden the interface is designed to expose. Do not imply a measured frequency of practitioner mistakes.

**Evidence:** [Case 04 specification](../cases/case_04/README.md); [public experience reasoning](../docs/design/public-landing-experience.md), whose product distinctions survive its superseded visual composition; merged [#125](https://github.com/alistairkung/private-client-graph/pull/125) and [#129](https://github.com/alistairkung/private-client-graph/pull/129).

**Unsupported claims / validation:** No empirical claim about document volumes, error rates or review time. Validate workflow prevalence through practitioner research later.

## Slide 3 — Who is the current trustee—and which document establishes that?

**Purpose:** Give the judge a concrete practitioner question that the product can help inspect, before explaining its workflow.

**Key takeaway:** The current relationship is Rachel Lim → trustee of → Willow Family Trust, supported by the completed replacement note; the earlier trustee entry is historical.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Who is the current trustee—                                          |
|  and which document establishes that?                                |
|                                                                      |
|  DOCUMENTS SUPPLIED TOGETHER         CURRENT RELATIONSHIP              |
|  +-----------------------------+    +------------------------------+ |
|  | 1 September: David Ng       |    | [EXISTING CASE 05 GRAPH CROP] | |
|  | earlier trustee entry       |    | Rachel Lim                    | |
|  +-----------------------------+    |       trustee of               | |
|  +-----------------------------+    | Willow Family Trust            | |
|  | 15 September: replacement   |    +------------------------------+ |
|  | effective 10 September      |                                     |
|  | [EXACT SOURCE EXCERPT]      |    Rachel Lim is current.           |
|  +-----------------------------+    David Ng's entry is historical.  |
|                                                                      |
|  Synthetic sample: both documents analysed together.                  |
|  Curated fixture; not a measured model result or saved-Matter update. |
+----------------------------------------------------------------------+
```

**Actual slide copy:** “Who is the current trustee—and which document establishes that?”; “Earlier note: David Ng”; “Completed replacement: effective 10 September 2026”; “Current trustee: Rachel Lim”; exact Source quotation: “Rachel Lim is the sole trustee of the Willow Family Trust as at 15 September 2026.”; “Synthetic sample: documents analysed together. Curated fixture; not a measured model result or saved-Matter update.”

**Visual asset reference:** C's existing Case 05 graph crop, showing Rachel Lim's current trustee relationship. Pair it with the actual [completed replacement note](../cases/case_05/sources/note_02.txt) and its Source title. The earlier [1 September note](../cases/case_05/sources/note_01.txt) supplies documentary context, not a second current trustee edge. Use a question-and-answer composition, reserving the interaction walkthrough for slide 5.

**Speaker notes:** The two supplied documents describe a completed replacement. The current graph includes Rachel, while the earlier document remains evidence of David's historical position. This existing synthetic sample shows the intended current-state interpretation; its authored ideal output is not measured extraction quality. Both documents are supplied in one analysis. No new Source is being added to an already accepted Matter, and no sequential update capability is implied.

**Evidence:** [Case 05 specification and full-context annotations](../cases/case_05/README.md); [current-state fixture](../cases/case_05/expected_state.json); merged [#125](https://github.com/alistairkung/private-client-graph/pull/125), [#128](https://github.com/alistairkung/private-client-graph/pull/128), [#129](https://github.com/alistairkung/private-client-graph/pull/129); C's pinned screenshot provenance.

**Unsupported claims / validation:** No measured time saving, general temporal reasoning, conflict adjudication or incremental accepted-Matter update claim. This is the existing completed-replacement scenario, not a newly invented case.

## Slide 4 — From synthetic PDFs to a reviewable Matter.

**Purpose:** Show that the product has a coherent delivered workflow, with a clear human decision point.

**Key takeaway:** Intake, proposal review and explicit whole-proposal confirmation form one practitioner journey.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  From synthetic PDFs to a reviewable Matter.                          |
|                                                                      |
|  01  INTAKE            02  REVIEW             03  CONFIRM & REOPEN     |
|  +------------------+  +-------------------+  +---------------------+  |
|  | [PDF / SOURCE    |  | [PROPOSAL CAPTURE] |  | [ACCEPTED MATTER   |  |
|  | REGION FROM     |  |                   |  | REGION / EXISTING  |  |
|  | EXISTING UI]    |  | Graph + Evidence  |  | WORKFLOW TEXT]     |  |
|  |                  |  |                   |  |                     |  |
|  +------------------+  +-------------------+  +---------------------+  |
|  1-5 synthetic PDFs    Inspect each link      Accept whole proposal   |
|                                                                      |
|  Authenticated practitioner workflow                                  |
|  Public demo: fixed examples; confirmation is a preview.               |
|                                                                      |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “1–5 synthetic PDFs”; “Inspect each link”; “Accept whole proposal”; “Authenticated practitioner workflow”; “Public demo: fixed examples; confirmation is a preview.”

**Visual asset reference:** A for intake/Source and proposal details; G for the existing confirm/reopen workflow. The third panel can remain large text if an existing accepted-Matter capture cannot be verified. Do not invent a composite application screen.

**Speaker notes:** Distinguish two experiences. The authenticated synthetic application can construct, confirm and reopen a persisted Matter. The public read-only demo lets judges explore fixed examples without credentials; its confirmation preview performs no mutation. Authentication exists, but real client data remains out of scope.

**Evidence:** merged [#52](https://github.com/alistairkung/private-client-graph/pull/52), [#59](https://github.com/alistairkung/private-client-graph/pull/59), [#130](https://github.com/alistairkung/private-client-graph/pull/130), [#138](https://github.com/alistairkung/private-client-graph/pull/138), [#143](https://github.com/alistairkung/private-client-graph/pull/143); [intake design decisions](../docs/design/matter-intake-slice.md), extended by #130/#138.

**Unsupported claims / validation:** No arbitrary PDF/OCR support, document-management integration, multi-firm ownership or real-client suitability claim. Screenshot providers are substituted, as recorded in asset A's provenance.

## Slide 5 — Every proposed relationship has a route back to its source.

**Purpose:** Deliver the product's signature demonstration at readable scale.

**Key takeaway:** A selected relationship connects to exact supporting words and an identified Source.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Every proposed relationship has a route back to its source.         |
|                                                                      |
|  +--------------------------------+  +-----------------------------+ |
|  |                                |  | 02  INSPECT EVIDENCE        | |
|  | 01  SELECT RELATIONSHIP        |  | [ACTUAL EVIDENCE PANEL]     | |
|  |                                |  | quotation + Source title   | |
|  | [EXISTING GRAPH UI]            |  +-----------------------------+ |
|  |                                |  +-----------------------------+ |
|  | one complete selected edge     |  | 03  READ IN SOURCE           | |
|  |                                |  | [ACTUAL SOURCE PANEL]       | |
|  |                                |  | exact passage highlighted   | |
|  +--------------------------------+  +-----------------------------+ |
|                                                                      |
|  Select. Inspect. Read in context.                                    |
|  Synthetic sample; not a live-model result.                           |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “Select relationship”; “Inspect Evidence”; “Read in Source”; “Select. Inspect. Read in context.”; “Synthetic sample; not a live-model result.” The screenshot supplies the actual names and verbatim quote.

**Visual asset reference:** A or B, with a large graph crop left and matched Evidence/Source regions right. Reuse one selection consistently across all regions. Gold marks the exact source passage, not the surrounding explanatory callouts.

**Speaker notes:** Walk the judge through one actual relationship. Identify both endpoints and its role, then read the supporting quote and show which Source contains it. Multiple Sources can contribute support without losing attribution. A quote existing in the text is mechanically checkable; whether it supports the proposed interpretation still requires judgment.

**Evidence:** merged [#17](https://github.com/alistairkung/private-client-graph/pull/17), [#43](https://github.com/alistairkung/private-client-graph/pull/43), [#129](https://github.com/alistairkung/private-client-graph/pull/129), [#138](https://github.com/alistairkung/private-client-graph/pull/138); [canonical provenance ADR](../docs/adr/0008-enforce-canonical-provenance-and-aggregate-integrity.md); [trust presentation specification](../docs/design/trust-structure-presentation.md).

**Unsupported claims / validation:** Avoid “verified truth,” “hallucination-free” or “all evidence recovered.” Exact occurrence is not semantic validation.

## Slide 6 — The difficult part is deciding what the documents mean together.

**Purpose:** Show why credible relationship reconstruction requires more than extracting names.

**Key takeaway:** Identity, Source attribution and current-state interpretation create different failure modes.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  The difficult part is deciding what                                 |
|  the documents mean together.                                        |
|                                                                      |
|  IDENTITY                 SOURCES                 TIME               |
|  +--------------------+   +--------------------+  +----------------+ |
|  | Bea                |   | Note A / Note B    |  | old trustee    | |
|  |      ?             |   | same quote         |  |      -->       | |
|  | Beatrice Ng        |   | distinct identities|  | replacement    | |
|  +--------------------+   +--------------------+  +----------------+ |
|  Same person?             Which document?         Current role?     |
|                                                                      |
|  [small EXISTING CASE 04 / CASE 05 detail, not a full screenshot]      |
|                                                                      |
|  Tested synthetic challenges; no general conflict-resolution claim.  |
|                                                                      |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “Same person?”; “Which document?”; “Current role?”; “Tested synthetic challenges; no general conflict-resolution claim.” Names and Source labels in the examples remain exact.

**Visual asset reference:** F for the recorded Bea/Beatrice naming issue; B and C for Source and temporal fixture details. Use three sparse text examples with one small genuine UI crop beneath, rather than three illegible dashboards.

**Speaker notes:** Distinguish an alias error from a missing role and a Source attribution error. A later trustee replacement must be interpreted as current state, even if Sources arrive out of chronological order. These are bounded benchmark challenges. Arbitrary contradictions, uncertain identity, homonyms and a full temporal history are not solved by this demonstration. Incrementally updating an accepted Matter is also separate from analysing several supplied documents together.

**Evidence:** [held-out case index](../evaluation_cases/README.md), especially 03, 05, 06 and 08; [Case 05](../cases/case_05/README.md); merged [#125](https://github.com/alistairkung/private-client-graph/pull/125), [#128](https://github.com/alistairkung/private-client-graph/pull/128); [resolver experiment design](../docs/design/entity-resolution-research-experiment.md).

**Unsupported claims / validation:** Do not claim a general temporal engine, contradiction adjudication, or production identity resolution. Same-title Sources remain distinct; visual labels are not identity keys.

## Slide 7 — Let AI interpret. Make the mechanics deterministic.

**Purpose:** Explain the trust mechanism through the actual refined Workbench chain, with the practitioner/research distinction visible to a reader.

**Key takeaway:** The practitioner baseline uses extraction and deterministic construction; research separately tests endpoint resolution.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Let AI interpret. Make the mechanics deterministic.                  |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |                                                                | |
|  | [REQUIRED: ACTUAL REFINED WORKBENCH CHAIN VISUALISATION]        | |
|  |                                                                | |
|  | Large readable stages; optional resolver; real connectors.      | |
|  | Evaluation remains outside the Shared Analysis Pipeline.       | |
|  |                                                                | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  Practitioner baseline: extraction + deterministic construction.     |
|  Research comparison: add endpoint resolution.                        |
|                                                                      |
|  Same relationships. Same quotations. Explicit professional review.   |
+----------------------------------------------------------------------+
```

**Actual slide copy:** “Let AI interpret. Make the mechanics deterministic.”; “Practitioner baseline: extraction + deterministic construction.”; “Research comparison: add endpoint resolution.”; “Same relationships. Same quotations.”; “Professional acceptance remains explicit.” The actual chain retains its own stage labels and external evaluation boundary.

**Visual asset reference:** **H is required:** the refined, actual Workbench chain visualisation, occupying most of the slide width. Source/view: `AnalysisPipeline` through the Workbench `configuration/Pipeline.tsx` adapter; see the production asset readiness register. **Required capture before production.** Do not substitute a simplified text schematic, newly drawn architecture diagram, historical D crop or tiny optional pipeline thumbnail. Inspecting/capturing an existing configuration later must not start a Run or paid provider call.

**Speaker notes:** AI interprets language; deterministic code checks references, quote occurrence and types, then constructs the canonical graph. In research, the optional resolver substitutes endpoint names without changing relationship candidates or quotations. The approved practitioner configuration has no resolver. Evaluation uses benchmark truth outside the pipeline; professional acceptance is a separate product action. This is bounded orchestration, not an autonomous legal adviser or arbitrary agent planner.

**Evidence:** merged [#5](https://github.com/alistairkung/private-client-graph/pull/5), [#6](https://github.com/alistairkung/private-client-graph/pull/6), [#7](https://github.com/alistairkung/private-client-graph/pull/7), [#98](https://github.com/alistairkung/private-client-graph/pull/98), [#136](https://github.com/alistairkung/private-client-graph/pull/136); [shared pipeline design](../docs/design/shared-analysis-pipeline.md); [ADR 0009](../docs/adr/0009-share-one-fixed-configurable-analysis-pipeline.md). H's refined shared component is local work under review; packaging must record its eventual reviewed commit.

**Unsupported claims / validation:** Do not imply the research resolver is enabled in the practitioner baseline, a general agent framework exists, mechanical validity proves semantics, or the refined capture is already packaged. No proven competitive moat claim.

## Slide 8 — Change one stage. Keep the evidence fixed.

**Purpose:** Establish why the comparison is interpretable before showing the score.

**Key takeaway:** Replaying identical retained extractions isolates the observed effect of resolution from new extraction variability.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Change one stage. Keep the evidence fixed.                          |
|                                                                      |
|  10 synthetic cases       14 Sources       39 expected relationships  |
|                                                                      |
|  A: original extraction --> retained, frozen candidates               |
|                                     |                                |
|                     +---------------+---------------+                |
|                     v                               v                |
|              A': no resolver                  B: resolver            |
|              zero provider calls              10 resolver calls       |
|                     |                               |                |
|              reproduces A exactly        same inputs, names may change|
|                                                                      |
|  One execution per case and condition. Post-hoc exploratory comparison.|
|  Project-authored; separate AI-validator checks, not external review. |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “10 synthetic cases · 14 Sources · 39 expected relationships”; “A: original extraction”; “A′: exact zero-call replay”; “B: same saved inputs + resolver”; “One execution per case and condition. Post-hoc exploratory comparison.”; “Project-authored; separate AI-validator checks, not external review.”

**Visual asset reference:** G's retained-input replay flow from #136; a narrow D pipeline strip may accompany it. These are method visuals, not performance evidence. Do not use earlier prototype screenshots as if they contain this final experiment.

**Speaker notes:** Five development cases established the method; ten separately stored synthetic cases formed the final baseline evaluation. After seeing the baseline, resolution was explored on its saved extractions. A′ first reproduced A's outputs exactly without a new model call; B reused those inputs for ten resolver calls. There is one observation per case in each condition, not independent A/A′ replications or repeated reliability trials. Inputs, truth, configuration, usage, failures and coverage are retained. “Held-out” describes the original split; the post-hoc comparison is exploratory, and published cases cannot serve as unseen tests again.

**Evidence:** merged [#125](https://github.com/alistairkung/private-client-graph/pull/125), [#128](https://github.com/alistairkung/private-client-graph/pull/128), [#136](https://github.com/alistairkung/private-client-graph/pull/136); [benchmark validation record](../research/final-day/validation/README.md) (historical pre-execution status); [aggregate design decisions](../docs/design/research-workbench-run-aggregate-evaluation.md); [retained publication identities and verification](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/docs/workflows/public-research-publication.md), in open [#152](https://github.com/alistairkung/private-client-graph/pull/152).

**Unsupported claims / validation:** No statistical significance, external validation, unseen-test resolver generalisation or production reliability claim. The older Issue #92 pilot has different cohorts/repetitions and is not pooled into these results.

## Slide 9 — On this synthetic set, relationship F1 rose from 94.87% to 100%.

**Purpose:** Show the measured result using the actual Workbench F1 plot, with its true Run aggregation and scope visible.

**Key takeaway:** On identical saved inputs, a narrow resolver intervention corrected exact-name errors in one case; ten synthetic cases do not establish general reliability.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  On this synthetic set, relationship F1 rose                         |
|  from 94.87% to 100%.                                                 |
|                                                                      |
|  +--------------------------------------------+  A / A'      B        |
|  | [REQUIRED: ACTUAL WORKBENCH F1 BY RUN PLOT] |  94.87%      100.00%  |
|  |                                            |  micro-F1    micro-F1 |
|  | Actual 0-1 F1 axis, Run-number axis,       |                       |
|  | legend, scope and coverage preserved.      |  Correct    37 -> 39  |
|  | One aggregate point per Run: A, A', B.     |  Extra       2 -> 0   |
|  | No trend line or invented case axis.       |  Missing     2 -> 0   |
|  +--------------------------------------------+                       |
|                                                                      |
|  A' exactly replays A; it is not an independent replication.          |
|  10/10 scored per condition; no recorded execution failures.           |
|  Post-hoc synthetic comparison; two endpoint corrections in one case. |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “A / A′: 94.87% micro-F1”; “B: 100.00% micro-F1”; “Correct: 37 → 39 · Extra: 2 → 0 · Missing: 2 → 0”; “One aggregate point per Run; A′ exactly replays A.”; “10/10 scored per condition; no recorded execution failures.”; “Post-hoc, project-authored synthetic comparison. Two endpoint corrections in one case explain the entire gain; not production reliability.”

**Visual asset reference:** **I is required:** the actual refined Workbench **F1 by Run** plot displaying the retained A/A′/B experiment, large enough to read the genuine axes, legend and disclosures. Source/view: `web/research/workspace/RunChart.tsx`, using shared `RunPerformanceChart`; see the readiness register. **Required capture before production.** Preserve one observation-weighted micro-F1 point per Run, with Run 1 = A, Run 2 = A′, Run 3 = B in retained order. A has a fresh-input scope; A′/B have the paired saved-input scope, bridged by verified exact replay. Keep scope differences visible. Use all-input mode so A remains visible. Do not substitute a case table, a case-index chart, the historical D demonstration chart, a newly drawn plot or an unrelated experiment. Do not use F1 vs Cost: A/B are unpriced.

**Speaker notes:** Micro-F1 pools relationship counts: baseline is 74/78; B is 78/78, a gain of approximately 5.13 percentage points. A′ is zero-call exact replay, not new extraction evidence. Nine cases retain F1 of 1.0; heldout_03 moves from one correct, two extra and two missing relationships to three correct. Exact-name scoring drives the gain. Macro-F1 is a different statistic, 93.33% to 100%; the plot shows Run-level micro-F1, not mean case F1. Discrete Run points do not imply a temporal improvement trend or statistically independent replications.

**Evidence:** [retained snapshot](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/private_client_graph/published/research-results.v1.json), snapshot `final-heldout-a-aprime-b-v1`; [verification procedure](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/docs/workflows/public-research-publication.md); open [#152](https://github.com/alistairkung/private-client-graph/pull/152). Original A Run `97d26d8e5f9d5964826b144c9ca45ad7`; A′ `d67a391bc95a5ad39e1b5786a04795c0`; B `841389cef51957ce8523ea41c03d2baa`. Snapshot integrity digest: `111a22dcb092d60b6354a89ab7b69293ef492175a412315735e0379d62ab1160`.

**Unsupported claims / validation:** Required final capture is not yet verified or packaged. No repeated-run consistency, confidence interval, production accuracy, or deployed research viewer claim. Keep qualifications in readable slide copy.

## Slide 10 — Two endpoint corrections. The same original evidence.

**Purpose:** Explain exactly what improved without overloading the slide with the analysis report.

**Key takeaway:** Two endpoint labels changed; original Evidence and existing strict evidence-check failures remained.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Two endpoint corrections. The same original evidence.                |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  | [EXISTING ENDPOINT-EDIT / GRAPH DETAILS: HELDOUT_03]              | |
|  |                                                                | |
|  | Bea -- settlor of --> Larch Family Trust                        | |
|  | Bea -- parent of  --> Isaac Ng                                 | |
|  |          Both source endpoints: Bea --> Beatrice Ng              | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  "Bea is the parent of Isaac Ng."  [UNCHANGED EXACT SOURCE QUOTE]     |
|  Names changed; evidence did not. Strict evidence-check failures remain.|
|                                                                      |
|  +10 calls; 9.06s summed provider-call time, not end-to-end latency.    |
|  USD cost unpriced. One execution per case; repeatability unknown.     |
|  [Research details: distinct evidence-check populations and definitions]|
+----------------------------------------------------------------------+
```

**Actual slide copy:** “Two endpoint corrections. The same original evidence.”; “Bea → Beatrice Ng”; “Settlor and parent endpoints”; exact quote “Bea is the parent of Isaac Ng.”; “Names changed; evidence did not. Existing strict evidence-check failures remained.”; “+10 calls · 9.06s summed provider-call time, not end-to-end latency”; “USD cost unpriced. One execution per case; repeatability unknown.”; “Research details: evidence checks assess different populations.”

**Visual asset reference:** F's existing heldout_03 original/resolved graph and Evidence details, using one dominant endpoint-correction region rather than two miniature full graphs. Show both affected source endpoints mapping from the same alias to the same canonical name; these are two endpoint corrections for one person. Reuse existing recorded edit details if they show the same two changes legibly. F is a local asset requiring packaging, not a new capture request in this revision. Keep the exact quote and Source identity intact. Detailed diagnostics should link to the [pinned research publication record](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/docs/workflows/public-research-publication.md) and [retained snapshot](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/private_client_graph/published/research-results.v1.json); replace the reader-facing details link with the verified research page only when that page is available. Do not imply it is deployed now.

**Speaker notes:** Resolution changes two source endpoint labels for Beatrice Ng, without adding relationship candidates or rewriting quotations. Detailed fractions are intentionally off the slide: approved-quote checks move from 34/37 to 36/39; the separate Source-pair diagnostic moves from 35/39 to 37/41. These assess different populations, not interchangeable scores. B still has three approved-quote failures and four Source-pair failures; not all causes are classified. B adds ten resolver calls and 9,821 total tokens. Summed provider duration is 9.06 seconds, not end-to-end latency or a user response-time promise. Pricing is unavailable. The earlier Issue #92 pilot has different scope and is not extra repetition of this comparison.

**Evidence:** [heldout_03 source and truth](../evaluation_cases/heldout_03/README.md); [retained snapshot](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/private_client_graph/published/research-results.v1.json), endpoint edits, per-Run diagnostics and usage; [endpoint-edit constraints](../docs/design/entity-resolution-research-experiment.md); merged [#136](https://github.com/alistairkung/private-client-graph/pull/136); open [#152](https://github.com/alistairkung/private-client-graph/pull/152).

**Unsupported claims / validation:** No claim that two different people's names changed, identity is generally solved, all provenance failures are understood, the resolver is cost-effective, or perfect relationship F1 means perfect documentary support. A future reader-facing research link requires deployment/access verification.

## Slide 11 — Next: keep the Matter current, without losing the review boundary.

**Purpose:** Present a credible adoption path anchored in the current product's explicit limits.

**Key takeaway:** Incremental updates and real-client deployment require new review semantics, governance and evidence.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Next: keep the Matter current,                                      |
|  without losing the review boundary.                                 |
|                                                                      |
|  BUILT TODAY                  PROPOSED NEXT                          |
|  +-----------------------+    +-----------------------------------+  |
|  | Synthetic PDFs        |    | New Source arrives                 |  |
|  | Reviewable proposal   |    |        v                            |  |
|  | Explicit confirmation |    | Review proposed changes             |  |
|  | Persisted Matter      |    |        v                            |  |
|  +-----------------------+    | Accept with traceable history       |  |
|                               +-----------------------------------+  |
|                                                                      |
|  Before real clients: Matter access, tenancy, ownership, data handling.|
|  Validate next: practitioner workflow value and fresh unseen cases.    |
|                                                                      |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “Built today: synthetic intake, Evidence review, whole-proposal acceptance”; “Future: new Source → proposed changes → reviewed current state”; “Before real clients: Matter access, tenancy, ownership and data handling”; “Validate workflow value and fresh unseen cases.”

**Visual asset reference:** G's existing proposal-to-Matter lifecycle as text. Extend it only with explicitly labelled future steps in this wireframe. No new mockup or implied existing update screen. The existing A capture can anchor “Built today” if it remains legible.

**Speaker notes:** Analysing several PDFs together already exists. Adding a new document to an accepted Matter and reviewing a delta is a different future capability. It needs decisions on conflicts, identity, effective dates, correction, history and acceptance. Existing authentication does not provide multi-firm ownership or full real-client safeguards. A practising lawyer's interest in direct document-management acquisition, including iManage, is a product signal recorded in PRODUCT.md, not an integration, customer endorsement or market validation. Next evidence should include workflow studies and fresh synthetic cases, with any real-data study separately governed.

**Evidence:** [PRODUCT.md](../PRODUCT.md); [Matter workflow design](../docs/design/matter-workflow-implementation.md); [canonical persistence design](../docs/design/canonical-persistence-slice.md); [prototype tenancy ADR](../docs/adr/0004-use-the-deployment-as-the-synthetic-prototype-tenant.md); [intake design security boundaries](../docs/design/matter-intake-slice.md); merged [#138](https://github.com/alistairkung/private-client-graph/pull/138).

**Unsupported claims / validation:** Future direction, not a committed release plan. No delivery date, security certification, iManage integration, automated conflict adjudication or real-client readiness claim.

## Slide 12 — Make every relationship reviewable.

**Purpose:** Leave judges with a clear reason to back the direction and an immediate route to inspect it.

**Key takeaway:** Private Client Graph combines a tangible practitioner experience, explicit AI boundaries and inspectable experimental evidence.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  PRIVATE CLIENT GRAPH                                                |
|                                                                      |
|  Make every relationship reviewable.                                  |
|                                                                      |
|  +-----------------------------------+  A working synthetic product  |
|  |                                   |                               |
|  | [EXISTING PRODUCT GRAPH +         |  Constrained AI, explicit      |
|  | EXACT EVIDENCE DETAIL]            |  professional judgment        |
|  |                                   |                               |
|  +-----------------------------------+  Measured, inspectable evidence|
|                                                                      |
|  Explore the prototype                 Inspect the repository         |
|  [LIVE RAILWAY APP LINK]                [GITHUB REPOSITORY LINK]       |
|                                                                      |
|  Synthetic research prototype. Do not use real client information.    |
+----------------------------------------------------------------------+
```

**Actual slide copy:** “Private Client Graph”; “Make every relationship reviewable.”; “A working synthetic product”; “Constrained AI. Explicit professional judgment.”; “Measured, inspectable evidence”; “Explore the prototype”; “Inspect the repository”; “Synthetic research prototype. Do not use real client information.”

**Visual asset reference:** A's strongest graph/Evidence crop, returning to the opening. Use plain text links, not generated QR codes. [Live Railway app](https://private-client-graph-production.up.railway.app/) and [GitHub repository](https://github.com/alistairkung/private-client-graph).

**Speaker notes:** Close with the proposition, rather than repeating the perfect score: source-backed structure that a professional can interrogate. Ask judges to explore the synthetic prototype and inspect the research evidence. The next stage worth backing is practitioner validation and governed development. The repository may require access; the app is the primary exploration route. Do not promise that the open research-publication PR is deployed.

**Evidence:** merged [#18](https://github.com/alistairkung/private-client-graph/pull/18), [#75](https://github.com/alistairkung/private-client-graph/pull/75), [#138](https://github.com/alistairkung/private-client-graph/pull/138), [#143](https://github.com/alistairkung/private-client-graph/pull/143), [#147](https://github.com/alistairkung/private-client-graph/pull/147); [PRODUCT.md](../PRODUCT.md); [retained results](https://github.com/alistairkung/private-client-graph/blob/21e3ff348757955df805d0d8a1d44d862e1549fd/private_client_graph/published/research-results.v1.json). Railway domain was verified via read-only domain metadata; the public root returned HTTP 200 during proposal research. That establishes reachability, not complete deployed feature acceptance.

**Unsupported claims / validation:** Recheck audience access and deployed routes before eventual presentation. Avoid “production-ready,” validated ROI, competitive superiority or guaranteed accuracy.

## Evidence reconciliation and material deliberately left out

The final measured A/A′/B result is distinct from both the earlier Issue #92 pilot and the deterministic Workbench demonstration. Do not mix their sample counts, costs, models or charts. The retained final snapshot records `deepseek-flash` provider metadata; the label is not proof of immutable model weights. The original baseline uses ten extraction attempts; the replay uses zero provider attempts; treatment uses ten resolver attempts. Shared extraction lineage does not create ten additional extraction calls in B.

The data snapshot, public viewer and screenshot each establish different facts. Retained observations establish what was measured. Merged PRs establish delivered capabilities. Local captures establish what the captured implementation looked like. An open PR, approved design or successful deployment metadata alone establishes neither live feature correctness nor production suitability.

Deliberately omitted from the judge-facing slides: the chronological PR journey; AI-assisted coding workflow; migration numbers and relational schema details; authentication cookie mechanics; CI test-count growth; task-budget ledgers; package refactors; arbitrary agent-framework comparisons; historical HTML report tooling retired by #121; and the earlier ten-slide draft outputs in open #131. These help engineering review but consume time without strengthening the product proposition. Provenance integrity, explicit acceptance, shared semantic boundaries and frozen experimental controls remain because they explain why judges should trust the experience and evidence.

Astra review revision: retained the twelve-slide structure, made refined Workbench chain/F1 captures mandatory, replaced slide 3 with the existing trustee-replacement question, moved essential distinctions into visible copy, simplified slide 10 and pinned cross-branch evidence. Narrative approval remains separate from slide-production approval.

No images, mockups, interactive prototypes, slide code, rendered slides or exports were created for this proposal. This document is the stopping point pending narrative review and approval.
