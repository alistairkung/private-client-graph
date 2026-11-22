# Family C admission dossier · Alder Quay and Flint Orchard Settlements

Kit Wenslow at Tarnstile Advisory is preparing separately recorded discretionary distribution decisions for a 17 June 2026 trustees' meeting. The administered file closed at **16:00 BST on 12 June 2026**. The same meeting note lists Alder Quay first and Flint Orchard second. It asks who may be considered, what payment has been authorised and what remains to check. The revised travel estimate and £8.40 print-shop voucher are absent. [Custody ledger and exact meeting brief](custody.json)

## Complete graphs

The following ten edges occur in every condition. Each named trustee and beneficiary in the table supplies a separate directed edge to the settlement on that row.

| Settlement | `settlor_of` | `trustee_of` | Unaffected `beneficiary_of` |
| --- | --- | --- | --- |
| Alder Quay Settlement | Ellis Harnett | Nell Carvane, Tobin Rell | Ione Berrick, Emmett Vann |
| Flint Orchard Settlement | Cora Teague | Nell Carvane, Tobin Rell | Ione Berrick, Orla Penrick |

| Condition | Additional edge | Withheld endpoints for Rhea Marden |
| --- | --- | --- |
| [C0 · natural reference](sources/C0.json) | Rhea Marden `beneficiary_of` Flint Orchard Settlement | Alder Quay |
| [C1 · swapped reference](sources/C1.json) | Rhea Marden `beneficiary_of` Alder Quay Settlement | Flint Orchard |
| [C2 · partly unreadable reference](sources/C2.json) | None | Alder Quay and Flint Orchard |

The designation adds a discretionary Object without displacing existing Objects or authorising a distribution. Ione's request concerning Sella Quist does not designate Sella. The £12.60 reimbursement came from the office operating account. The file establishes no beneficiary edge for Sella and no authorised trust payment to Rhea.

## Original Source inventory

| Source in file order | Origin and purpose |
| --- | --- |
| [j8f2 · Meeting preparation note](originals/j8f2.txt) | Secretary's diary, separate decision records, cut-off and current appointments-book report. |
| [m4v7 · Alder Quay deed extract](originals/m4v7.txt) | Certified identity, reference, parties, Objects and addition power. |
| [x2c9 · Flint Orchard deed extract](originals/x2c9.txt) | Separately certified identity, reference, parties, Objects and addition power. |
| [h6q3 · Designation transcript](originals/h6q3.txt) | Signing-room clerk's transcript of the signed `SD-Q7M2` text and attestation. |
| [r5n8 · Custody register](originals/r5n8.txt) | Merefold officer's independently maintained entry for joint delivery of the original and the parent deed reference used at handover. |
| [b9k4 · Ione's letter](originals/b9k4.txt) | Expected travel expense, wishes and a paperwork contact. |
| [t3w6 · Expense reconciliation](originals/t3w6.txt) | Separate office reimbursement and outstanding voucher. |

Each condition has seven Sources and 1,392 Source-body words. Only the parent reference in r5n8 changes. C0 uses `PD-6894-R`, C1 `PD-6834-R` and C2 `PD-68?4-R`. The comparisons cover each pair of files, including C1/C2, and verify all serialized fields and order. [Preblind freeze](freeze.json) · [Exact variant comparison](review/matched-sources.json)

## Documentary decision

The designation names Rhea and supplies the instrument reference, signatures and terms for effective delivery. The custody entry links that same instrument to the parent reference jointly given at immediate delivery on 26 March. The relevant foundation deed maps the reference to its settlement and supplies the power, parties and prescribed mechanism. The register memorialises delivery and the association. The operative designation supplies eligibility.

In C2 the unreadable digit can be **9**, establishing Flint Orchard, or **3**, establishing Alder Quay. Each interpretation places the one signed instrument with a single viable settlement. Both use the same trustees, power, signature and joint-delivery mechanism. The common vault, shared-stock identifier and absent digit supply no basis to choose one. A legible contemporary parent reference could resolve the allocation.

## Blind review and realism

The six blind readings agreed within each condition on every edge, including the two withheld alternatives in C2. C0 and C1 each contain 11 supported edges. C2 contains ten. Readers differed on quotation boundaries and the use of the meeting note to corroborate trustee capacity. [Agreement](review/agreement.json) · [C0 ruling](review/outputs/C0-judgment.json) · [C1 ruling](review/outputs/C1-judgment.json) · [C2 ruling](review/outputs/C2-judgment.json)

The single repair clarified the question-mark convention and separated the certified entry from the officer's explanation. One re-review treated the alternative files as a bundle of co-present copies and is retained as inconclusive. A fresh reviewer assessed the same revised bytes as three separate files and passed each one. The deed provisions and common registry are stipulated local conventions. The full deeds, appointments book and underlying financial records remain outside the file. The review addresses these fictional documents' internal mechanics. [Initial review](review/realism-initial.json) · [Inconclusive review](review/realism-inconclusive.json) · [Fresh review by condition](review/realism-final.json) · [HMRC trust record genres](https://www.gov.uk/guidance/trust-record-keeping-for-tax-purposes)

## Evidence necessity and shortcuts

Each supported Rhea edge has one approved set with three verbatim Source attachments. C0 uses x2c9, h6q3 and r5n8. C1 uses m4v7, h6q3 and r5n8. The deed supplies the settlement, reference and power. The transcript supplies the named designation and signing. The custody entry supplies the particular joint delivery and its link to the parent. Fresh readers recovered each supported edge from the exact three excerpts. The adjudicators considered current-office material from j8f2 separately. The custody act and foundation deed already establish capacity for this March addition. The appointments-book report supports the ordinary June trustee edges. [Comparative evidence rulings](review/outputs/comparison.json) · [Exact approved C0 key](C0.json) · [Exact approved C1 key](C1.json) · [C2 key](C2.json)

The exact parent-field obscuration yields C2 from either supported file. Both C2 readers withheld the two named claims. The eight fresh full-file masks separately hide the designation, the mappings in both deed extracts, evidence of actual joint delivery, and the evidence tying that delivery to this designation. All eight readings withheld the two named target edges and retained the ten ordinary edges. Each proper one-member deletion is covered by a fresh withheld reading with the remaining exact passages. [Masked packets and readings](review/mask-results.json) · [Proof deletion coverage](review/proof-deletions.json) · [Final evidence ruling](review/outputs/closing-audit.json)

Picking Alder Quay first happens to hit C1 and fails on C0 and C2. Choosing Flint Orchard throughout fails on C1 and C2. Assigning both endpoints fails in every condition. The last presented expense reconciliation supplies no operative designation. Titles, identifiers and item order are constant. A single character in the body carries the intervention, and two differently named foundation deeds are needed to interpret the two possible readings. [Per-Source and shortcut audit](review/outputs/comparison.json)

## Saved-ideal replay

| Condition | Planned / replayed / scored | TP / FP / FN | P / R / F1 | Exact graph | Ordinary quote / Source association | Complete joint proofs |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | 1 / 1 / 1 | 11 / 0 / 0 | 1 / 1 / 1 | Yes | 10 of 10 / 10 of 10 | 1 / 1 |
| C1 | 1 / 1 / 1 | 11 / 0 / 0 | 1 / 1 / 1 | Yes | 10 of 10 / 10 of 10 | 1 / 1 |
| C2 | 1 / 1 / 1 | 10 / 0 / 0 | 1 / 1 / 1 | Yes | 10 of 10 / 10 of 10 | N/A |

The Workbench reopened the retained Run with resolver `none`. Critical edges are graph-scored and have ordinary quotation and attribution marked N/A. The same-edge diagnostic checks every pair in the approved alternative. The receipt retains the historical scorer output, exact decisions, case counts, timing and input digests. The preview allowed zero paid slots and both replays recorded **zero paid PCG extraction attempts**. [Offline replay receipt](review/offline-replay.json) · [Replay procedure](../../docs/workflows/benchmark-v3-packets.md)

## Admission and commitments

**`pending_human_admission`.** The owner can accept, return or quarantine this family separately. Review the documentary proof and the unresolved condition against the committed package, annotation and evidence-policy digests. All conditions remain undispatched. [Admission commitments](admission.json) · [Manifest](manifest.json) · [Scored targets](review/scored-targets.json)

This family used **33** Codex scientific sessions (3 adjudication, 6 annotation, 2 audit, 8 author, 1 designer, 10 masked, 3 realism). The combined task used **60 of 70**, including the custodian and successful harmless isolation probe. Reported packet usage totals 601,761 input and 252,419 output tokens across both families. Codex usage is unpriced. [Session ledger](../families_b_c_sessions.jsonl) · [Isolation record](../families_b_c_isolation.md)
