# Independent case validation — first batch

Validator: practitioner_demo agent, independent of P1 case author. Read-only review of author worktree on 17 October 2026. No fixtures changed and no paid calls made.

Reviewed documentary sources, complete current truth, approved evidence, source manifests, source-aware expectations and authoring notes in both directions. Deterministic authoring suite: `19 passed, 16 deselected` for Cases 04/05 and heldout01–05. Pytest emitted only a sandbox cache-write warning; all assertions passed.

These results establish mechanical integrity plus an independent semantic audit; the user's Case 04/05 review and held-out benchmark approval remain required. Authored ideal evaluation is not model performance.

| Case | Hypothesis | Current edges | Evidence coverage | Outcome and uncertainties |
| --- | --- | ---: | --- | --- |
| cases/case_04 | Cross-document corroboration and deduplication | 7 | All 7 supported edges have approved exact Source/quote support; Andrew beneficiary support correctly appears in both notes. | No blocker. Victoria is the unambiguous local antecedent for She. Lucy and Marcus have no asserted family links. Fixture correctly does not invent trustees. |
| cases/case_05 | Completed effective trustee replacement | 6 | All 6 final-current edges supported: five unchanged facts from note_01, Rachel trustee from note_02. Initial control separately has David trustee. | No semantic blocker. David is historical only; Rachel is not a rename. README retains historical sequential-design wording; final-day addendum correctly disclaims a sequential implementation requirement. |
| evaluation_cases/heldout_01 | Confirmation-letter genre | 5 | 5/5 edges supported, including the two parent edges from the joint-parent sentence. | No blocker; signature/procedural prose adds no relationship. |
| evaluation_cases/heldout_02 | Dense multi-edge sentence | 4 | 4/4 edges supported by the same exact sentence; one evidence item can legitimately support all four. | No blocker. No parentage is asserted for Felix. Approved support is deliberately the complete sentence, so an equally valid shorter model quote may fail approved-quote scoring under unchanged policy; report as annotation granularity rather than semantic-edge error. |
| evaluation_cases/heldout_03 | Explicit local alias | 3 | 3/3 supported; Bea is explicitly Beatrice Ng and canonical endpoints correctly use Beatrice Ng while quotes retain Bea. | No blocker. This tests extraction interpretation in the no-resolution configuration; it does not require enabling experimental resolver strategies. |
| evaluation_cases/heldout_04 | Identical corroborating quotes in two Sources | 3 | 3/3 edges supported; Keira beneficiary quote occurs in both Sources and each attribution is separately approved. | No blocker. An identical quote attributed to either Source is valid in this case: it exercises distinct-source identity/pooling, not detection of attribution swaps between identical texts. |
| evaluation_cases/heldout_05 | Effective trustee replacement with retained earlier facts | 4 | 4/4 final-current edges supported: three from initial Source, Nora trustee from replacement Source; Oscar excluded. | No blocker. Explicit dates and completed wording remove proposed/future and wall-clock ambiguity. |

## Batch limitations

No accidental supported relationships or unsupported approved spans were identified. Local pronouns and explicit aliases are unambiguous in their full source context. New held-out examples are short, explicit, synthetic and often include artificial scope/negative clarifications. They provide useful targeted spike checks but weak evidence of robustness on long, messy practice files; final claims must be confined accordingly. Cases deliberately vary one difficulty at a time and do not establish general temporal or alias-resolution accuracy.

Case 04 and heldout04 have selected duplicate corroboration, but the agreed policy does not require a real model to return every corroborating quote. Preserve the distinction between deterministic pooling when evidence is supplied and extraction evidence recall.

## Reviewed artifact digests

Digests freeze exactly what this independent pass inspected. If the author changes these artifacts, revalidate the changed cases before benchmark approval.
