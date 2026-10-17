# Private Client Graph — 12-slide judge pitch proposal

Planning document for review. Exactly 12 proposed slides; no slide production is authorized by this document.

## Persuasive arc

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
| D — Implemented Workbench | [desktop capture](../docs/design/assets/research-workbench-117-desktop.png), [capture record](../docs/design/research-workbench-117-implementation.md), merged #120. Deterministic synthetic observations, including intentional recovery states. | Pipeline and retained-review mechanics only. Its chart numbers are not the final experiment. |
| E — Approved visual direction | [Evidence Folio comp](../docs/design/assets/public-landing-evidence-folio.png), [design record](../docs/design/public-landing-visual-direction.md). Existing generated/approved composition reference, not product truth. | Palette, typography and spatial rhythm only; do not reuse generated interface text as evidence. |
| F — Measured study captures | [capture index](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/screenshots.json), [results capture](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-results-en-desktop.png), [original graph](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-original-en-desktop.png), [resolved graph and Evidence](/Users/alistair/.codex/visualizations/2026/10/17/01a14a16-72ec-7c70-bb57-228da5a981ee/research-editorial/editorial-graph-en-desktop.png). Genuine existing local #152 implementation captures of retained results; implementation under review. Machine-local paths are not portable published assets. | Result comparison and the two endpoint corrections. Use only relevant regions; historical header treatment is irrelevant to these crops. |
| G — Architecture and workflow schematics | Existing text diagrams in [shared pipeline design](../docs/design/shared-analysis-pipeline.md), [intake design](../docs/design/matter-intake-slice.md), [aggregate contract](../docs/design/research-workbench-run-aggregate-evaluation.md), and [publication workflow](../docs/workflows/public-research-publication.md). | Simplify their existing logic as text in the planned slides; no new rendered diagram in this task. |

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

## Slide 3 — A graph you can question, one relationship at a time.

**Purpose:** Translate the problem into a memorable product proposition before introducing architecture.

**Key takeaway:** The useful unit is a relationship with inspectable Evidence, rather than an unsupported summary.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  A graph you can question, one relationship at a time.                |
|                                                                      |
|  +----------------------------------------+  SEE THE STRUCTURE        |
|  |                                        |  People, trusts, roles.  |
|  |     [EXISTING GRAPH UI]                |                           |
|  |                                        |  FOLLOW THE EVIDENCE      |
|  |     one relationship selected          |  Exact words. Named source.|
|  |                                        |                           |
|  |     relationship label remains legible |  KEEP THE JUDGMENT         |
|  |                                        |  Review before acceptance.|
|  +----------------------------------------+                           |
|                                                                      |
|  Machine proposal --> professional review --> accepted Matter         |
|                                                                      |
|  Synthetic workflow demonstration                                     |
+----------------------------------------------------------------------+
```

**Actual slide copy:** “A graph you can question, one relationship at a time.”; “See the structure”; “Follow the Evidence”; “Keep the judgment”; “Machine proposal → professional review → accepted Matter”; “Synthetic workflow demonstration.”

**Visual asset reference:** A, using the graph as approximately 60% of the content width. Three short annotations sit outside the screenshot; do not fabricate UI controls.

**Speaker notes:** Explain the opportunity in practitioner terms: a navigable relationship structure with a route back to the record. Professional acceptance is a separate action after review of the complete proposal. The current workflow does not allow selective relationship approval, corrections or automatic legal conclusions.

**Evidence:** [professional acceptance ADR](../docs/adr/0006-require-professional-confirmation-before-current-matter-state.md); [review/evaluation separation ADR](../docs/adr/0001-separate-professional-review-from-benchmark-evaluation.md); merged [#53](https://github.com/alistairkung/private-client-graph/pull/53), [#59](https://github.com/alistairkung/private-client-graph/pull/59), [#138](https://github.com/alistairkung/private-client-graph/pull/138).

**Unsupported claims / validation:** Inspection supports review; it does not prove correctness or establish legal assurance.

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

**Purpose:** Explain the trust mechanism in terms a non-specialist judge can retain.

**Key takeaway:** AI proposes semantic structure inside explicit boundaries; deterministic checks construct it, and the practitioner decides acceptance.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Let AI interpret. Make the mechanics deterministic.                  |
|                                                                      |
|  [Sources] --> [AI extracts] --> [Validate & build] --> [Review]       |
|                  relationships       graph              human       |
|                    |                    |                  |          |
|               understands          exact quotes,      explicit       |
|               language             types, references  acceptance     |
|                                                                      |
|          [Optional research resolver: endpoint names only]            |
|          Same relationships. Same quotations.                         |
|                                                                      |
|  ---------------------------------------------------------------     |
|  Research evaluation compares output with a frozen answer key.        |
|                                                                      |
|  Fixed workflow; constrained AI operations.                           |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “Sources → AI extracts relationships → Validate & build graph → Professional review”; “Optional research resolver: endpoint names only”; “Same relationships. Same quotations.”; “Research evaluation uses a frozen answer key”; “Fixed workflow; constrained AI operations.”

**Visual asset reference:** G's existing shared-pipeline schematic, simplified as planned text. A small crop of D's pipeline stage can establish that the research configuration UI exists, but omit its demonstration scores.

**Speaker notes:** The model interprets language. Code handles reference integrity, quote occurrence, type rules, IDs, ordering and canonical graph construction. Research can test a constrained resolver that substitutes endpoint names while preserving relationships and quotes. The approved practitioner pipeline uses no resolution; experimental success does not automatically promote a resolver into the product. Evaluation stays outside both the semantic pipeline and professional acceptance. This is bounded orchestration, not an autonomous legal adviser or an arbitrary agent planner.

**Evidence:** merged [#5](https://github.com/alistairkung/private-client-graph/pull/5), [#6](https://github.com/alistairkung/private-client-graph/pull/6), [#7](https://github.com/alistairkung/private-client-graph/pull/7), [#98](https://github.com/alistairkung/private-client-graph/pull/98), [#136](https://github.com/alistairkung/private-client-graph/pull/136); [shared pipeline design](../docs/design/shared-analysis-pipeline.md); [ADR 0009](../docs/adr/0009-share-one-fixed-configurable-analysis-pipeline.md).

**Unsupported claims / validation:** Position this as the project's design differentiation, not a proven unique competitive moat. Mechanical validity does not imply semantic correctness.

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

**Evidence:** merged [#125](https://github.com/alistairkung/private-client-graph/pull/125), [#128](https://github.com/alistairkung/private-client-graph/pull/128), [#136](https://github.com/alistairkung/private-client-graph/pull/136); [benchmark validation record](../research/final-day/validation/README.md) (historical pre-execution status); [aggregate design decisions](../docs/design/research-workbench-run-aggregate-evaluation.md); [retained publication identities and verification](../docs/workflows/public-research-publication.md), in open [#152](https://github.com/alistairkung/private-client-graph/pull/152).

**Unsupported claims / validation:** No statistical significance, external validation, unseen-test resolver generalisation or production reliability claim. The older Issue #92 pilot has different cohorts/repetitions and is not pooled into these results.

## Slide 9 — On this synthetic set, relationship F1 rose from 94.87% to 100%.

**Purpose:** Give the judge the actual measured result, together with enough context to interpret it correctly.

**Key takeaway:** A narrow resolver intervention corrected the observed exact-name errors in one case; the result covers ten synthetic cases only.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  On this synthetic set, relationship F1 rose                         |
|  from 94.87% to 100%.                                                 |
|                                                                      |
|  +----------------------------------------+  A / A'       B           |
|  | [EXISTING RETAINED-RESULT COMPARISON]   |  94.87%       100.00%     |
|  | F1: 0-1; cases 01-10                   |  micro-F1     micro-F1    |
|  |                                        |                           |
|  | baseline/resolver overlap in 9 cases  |  Correct       37 -> 39    |
|  | heldout_03: 0.3333 -> 1.0000           |  Extra          2 -> 0     |
|  |                                        |  Missing        2 -> 0     |
|  +----------------------------------------+                           |
|                                                                      |
|  10/10 scored per condition; no recorded execution failures.           |
|  Post-hoc, project-authored synthetic comparison.                      |
|  Two name corrections in one case explain the entire gain.            |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “A / A′: 94.87% micro-F1”; “B: 100.00% micro-F1”; “Correct: 37 → 39 · Extra: 2 → 0 · Missing: 2 → 0”; “10/10 scored per condition; no recorded execution failures”; “Post-hoc, project-authored synthetic comparison”; “Two name corrections in one case explain the entire gain.”

**Visual asset reference:** F's actual retained-result comparison region. Reuse an existing case-level table or chart only if it displays the ten cases with these exact values. The existing #120 Workbench chart is demonstration data and must not substitute. If no legible final F1 chart exists, the existing measured case table is the visualisation; no new chart is commissioned in this planning task. Keep the two large micro-F1 values separate from the case-level visual; do not imply a trend across cases or show A′ as independent replication.

**Speaker notes:** Micro-F1 pools relationship counts: baseline is 74/78; B is 78/78. The change is approximately 5.13 percentage points, not “5.13% more accurate.” Nine cases have unchanged F1 of 1.0. Heldout_03 moves from one correct, two extra and two missing relationships to three correct. Exact-name scoring drives the gain. Macro-F1 is a different number: 93.33% to 100%, so do not label the displayed aggregate as a case average. These results do not establish production accuracy or reliability.

**Evidence:** [retained snapshot](../private_client_graph/published/research-results.v1.json), snapshot `final-heldout-a-aprime-b-v1`; [verification procedure](../docs/workflows/public-research-publication.md); open [#152](https://github.com/alistairkung/private-client-graph/pull/152). Original A Run `97d26d8e5f9d5964826b144c9ca45ad7`; A′ `d67a391bc95a5ad39e1b5786a04795c0`; B `841389cef51957ce8523ea41c03d2baa`. Snapshot integrity digest: `111a22dcb092d60b6354a89ab7b69293ef492175a412315735e0379d62ab1160`.

**Unsupported claims / validation:** Actual retained observations are available, but the publication UI is under review. No repeated-run consistency, confidence interval or live deployment of the research viewer is claimed. Keep the qualifications onscreen at readable size.

## Slide 10 — Two names changed the score. The quotations stayed the same.

**Purpose:** Explain the improvement, then make the remaining evidence and resource trade-offs visible.

**Key takeaway:** Better relationship F1 does not mean perfect provenance, and the incremental resolver has measurable overhead.

**Text wireframe:**

```text
+----------------------------------------------------------------------+
|  Two names changed the score. The quotations stayed the same.         |
|                                                                      |
|  +--------------------------+ --> +-------------------------------+  |
|  | [EXISTING ORIGINAL GRAPH]|     | [EXISTING RESOLVED GRAPH]      |  |
|  | Bea                      |     | Beatrice Ng                    |  |
|  | settlor / parent edges   |     | same roles, corrected names     |  |
|  +--------------------------+     +-------------------------------+  |
|  "Bea is the parent of Isaac Ng."  [EXACT SOURCE EVIDENCE]           |
|                                                                      |
|  Quote checks: 36/39             Source/quote checks: 37/41            |
|  +10 resolver calls             +9,821 tokens; 9.06s summed duration   |
|                                                                      |
|  B results; distinct diagnostic denominators.                         |
|  USD cost unpriced. One execution per case; repeatability unknown.     |
|                                                                      |
+----------------------------------------------------------------------+
```

**Actual slide copy:** Headline; “Bea → Beatrice Ng”; “Settlor and parent endpoints corrected”; exact quote “Bea is the parent of Isaac Ng.”; “B: approved-quote checks 36/39”; “B: Source/quote checks 37/41”; “+10 resolver calls · +9,821 tokens · 9.06s summed provider duration”; “USD cost unpriced. Repeatability unknown.”

**Visual asset reference:** F's original/resolved heldout_03 graph captures and exact Evidence region. Crop the matching settlor/parent endpoints at readable size; do not depict invented missing edges. Existing retained Source text establishes that Bea means Beatrice Ng. These are #152 implementation-under-review captures, supported by retained data rather than by merge status.

**Speaker notes:** Resolution changes two endpoint labels, without discovering new relationship candidates or rewriting quotations. Quote accuracy rises from 34/37 to 36/39; the separate saved Source-pair diagnostic rises from 35/39 to 37/41. These populations and checks differ, so the fractions cannot be compared as one score. Three approved-quote checks and four Source-pair checks still fail in B. Exact approved-quote boundaries may reject semantically adequate excerpts, but the retained Source-pair diagnostics do not classify all failure causes: do not label every failure a boundary mismatch or wrong document. B adds ten resolver calls and 9,821 total tokens, including 3,456 cached tokens within input tokens. The 9.06 seconds is summed recorded provider-call duration, not end-to-end latency or a per-user response-time promise. Dollar costs are unavailable. The earlier [Issue #92 pilot](../research/issue-92-findings.md) is separate evidence with different scope, not extra repetitions of this final comparison.

**Evidence:** [heldout_03 source and truth](../evaluation_cases/heldout_03/README.md); [retained snapshot](../private_client_graph/published/research-results.v1.json), edits, per-Run diagnostics and usage; [endpoint-edit constraints](../docs/design/entity-resolution-research-experiment.md); merged [#136](https://github.com/alistairkung/private-client-graph/pull/136); open [#152](https://github.com/alistairkung/private-client-graph/pull/152).

**Unsupported claims / validation:** No assertion that identity is generally solved, all provenance failures are understood, the resolver is cost-effective, or B's perfect relationship score implies perfect documentary support.

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

**Evidence:** merged [#18](https://github.com/alistairkung/private-client-graph/pull/18), [#75](https://github.com/alistairkung/private-client-graph/pull/75), [#138](https://github.com/alistairkung/private-client-graph/pull/138), [#143](https://github.com/alistairkung/private-client-graph/pull/143), [#147](https://github.com/alistairkung/private-client-graph/pull/147); [PRODUCT.md](../PRODUCT.md); [retained results](../private_client_graph/published/research-results.v1.json). Railway domain was verified via read-only domain metadata; the public root returned HTTP 200 during proposal research. That establishes reachability, not complete deployed feature acceptance.

**Unsupported claims / validation:** Recheck audience access and deployed routes before eventual presentation. Avoid “production-ready,” validated ROI, competitive superiority or guaranteed accuracy.

## Evidence reconciliation and material deliberately left out

The final measured A/A′/B result is distinct from both the earlier Issue #92 pilot and the deterministic Workbench demonstration. Do not mix their sample counts, costs, models or charts. The retained final snapshot records `deepseek-flash` provider metadata; the label is not proof of immutable model weights. The original baseline uses ten extraction attempts; the replay uses zero provider attempts; treatment uses ten resolver attempts. Shared extraction lineage does not create ten additional extraction calls in B.

The data snapshot, public viewer and screenshot each establish different facts. Retained observations establish what was measured. Merged PRs establish delivered capabilities. Local captures establish what the captured implementation looked like. An open PR, approved design or successful deployment metadata alone establishes neither live feature correctness nor production suitability.

Deliberately omitted from the judge-facing slides: the chronological PR journey; AI-assisted coding workflow; migration numbers and relational schema details; authentication cookie mechanics; CI test-count growth; task-budget ledgers; package refactors; arbitrary agent-framework comparisons; historical HTML report tooling retired by #121; and the earlier ten-slide draft outputs in open #131. These help engineering review but consume time without strengthening the product proposition. Provenance integrity, explicit acceptance, shared semantic boundaries and frozen experimental controls remain because they explain why judges should trust the experience and evidence.

No images, mockups, interactive prototypes, slide code, rendered slides or exports were created for this proposal. This document is the stopping point pending narrative review and approval.
