# Family D admission dossier · Alder Fold Trust

Priya Sen is preparing a trustee briefing for 23 October 2026. The file closes at **09:00 BST**, an hour before the meeting. The retainer asks which named beneficiary provisions govern at the cut-off. [Meeting brief and custody](custody.json)

## Original Sources and conditions

| Source | Origin and purpose |
| --- | --- |
| [h7m4 · Advice file meeting brief](originals/h7m4.txt) | Priya's diary note records the scope, papers received and cut-off. |
| [w3k8 · Principal instrument extract](originals/w3k8.txt) | Jonah Reed supplies the retained execution extract. The instrument establishes the trust, roles and operative replacement procedure. |
| [n5q2 · Signed instrument](originals/n5q2.txt) | Tess Calder exercises the instrument's limited variation power and delivers the amendment to Jonah for retention. |

[D0](sources/D0.json) uses locator `4.1`. [D1](sources/D1.json) uses `4.2`. The numbered reference in n5q2 changes by one byte. The instrument reference, signatures, dates, IDs, titles and order match. [Source freeze](freeze.json) · [Exact comparison](review/matched-sources.json)

## Complete graphs and evidence

Every edge in the table points to **Alder Fold Trust**. The trust and named people have the same entity IDs in both keys.

| Edge | D0 | D1 |
| --- | --- | --- |
| Livia Keane `settlor_of` | Supported | Supported |
| Jonah Reed `trustee_of` | Supported | Supported |
| Ada Wynn `beneficiary_of` | Supported | Supported |
| Nia Bell `beneficiary_of` | Supported | Supported |
| Milo Hart `beneficiary_of` | Supported | Displaced |
| Elin Voss `beneficiary_of` | Displaced | Supported |

The principal instrument names Tess as Variation Officer and states the exact-reference, signing and effective-date requirements for a single-provision replacement. Tess's amendment uses `PI-67Q4`, carries the selected locator and the new designation, and took effect on 12 October under the file's express terms. Nia's proof attaches the named designation, authority, matching reference, locator and execution from both instruments. Ada and the other surviving designee attach their original clauses alongside passages establishing the limited replacement. The two office edges keep direct and execution-based ordinary approvals from w3k8. [D0 key and exact approvals](D0.json) · [D1 key and exact approvals](D1.json)

The four blind readers agreed on both complete graphs. They differed on the quotation boundaries for the two offices in D0 and the joint proof in both files. The adjudications resolved authority, execution, effect and scope before seeing the intervention. Tess's appointment as Variation Officer, delivery to Jonah and Priya's retainer establish roles outside the graph. [Independent commitments](review/blind-lock.json) · [Blind interpretations and adjudication](review/blind-review.json)

## Realism and verified scope

Both realism reviews passed. The expressly limited fictional office and the reference clause are conspicuous, and the adviser's disclaimer is more explicit than the file needs. The executed extract, amendment and internal diary have distinct purposes. The exact delivery date, terms outside the extract and legal consequences for accrued entitlements remain open. The ordinary invariants are trust relationships. Preservation of an unrelated kinship edge remains untested in D. [Realism assessments](review/documentary-realism.json) · [HMRC record retention guidance](https://www.gov.uk/guidance/trust-record-keeping-for-tax-purposes)

The comparison auditor distinguished a historical designation from proof that it survived at the cut-off. The evidence-only revision adds joint scope sets to the two surviving original beneficiary edges and segments Nia's proof. Both fresh readers recovered all three beneficiary edges from the revised excerpts. They still treated the original designation lines as ordinary evidence of survival, while relying on the observed amendment scope in their explanations. The saved keys take the more demanding scope-proof position. The office quotes remain eligible for the ordinary policy. [Evidence ruling and remaining disagreement](review/evidence-ruling.json)

Each instrument alone failed to establish Nia's current edge. Withholding either copy of the matching reference withheld Nia while preserving both offices and the two unaffected designations in the reviewed file. Omitting the amendment restored the three original designations. Withholding the locator left the two offices and made every named beneficiary unresolved because the governing clause could have reached any of the original provisions. Ada survives the two tested locators. The order-reversed reading reproduced D1. [Mask readings](review/masks.json)

Latest-only, union, full supersession and first-clause rules fail across the pair. The first-clause rule can match D0 by chance. Assigning every amendment in a one-trust file to that trust can guess Nia's endpoint while missing the required textual authority and identity link. [Comparative audit](review/comparison.json)

## Saved-ideal replay and admission

| Condition | Replayed / scored | TP / FP / FN | Ordinary quotation and attribution | Complete same-edge proof |
| --- | --- | --- | --- | --- |
| D0 | 1 / 1 | 5 / 0 / 0 | 2/2 and 2/2 | 3/3 |
| D1 | 1 / 1 | 5 / 0 / 0 | 2/2 and 2/2 | 3/3 |

The Workbench reopened the saved Run twice with resolver `none`, the same decisions and scores, and zero paid PCG calls. [Offline replay receipt](review/offline-replay.json) · [Committed manifest](manifest.json)

The closing audit recommends **accept** after the evidence repair. All active beneficiary edges attach the grouped scope proof. Fresh readings verified the grouped result. Individual fact-level deletions within every segment remain untested. The original and revised interpretations are documented together.

**`pending_human_admission`.** The owner must record a separate disposition. This family used 25 isolated Codex sessions. [Admission commitments](admission.json) · [Portfolio closing audit](../admission_d_f/closing-audit.json) · [Session ledger](../admission_d_f/sessions.jsonl)
