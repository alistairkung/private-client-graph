# Family A admission dossier · Wrenhollow Settlement

Fennick Vale Solicitors has a 14:30 BST meeting with Lintmere Bank on 17 September 2026. The practical question is what the trustees can send the bank. The reference graph describes the solicitor’s file at **14:20 BST**. The bank’s live signing authorities remain an enquiry for the meeting.

## The three decisions

| Condition and exact ordered file | Required Second Seat trustee | Forbidden Second Seat trustee | Complete reference and evidence |
| --- | --- | --- | --- |
| [A0 · completed](sources/A0.json) | Tamsin Kell | Darren Brell | [A0 key](A0.json) |
| [A1 · reordered](sources/A1.json) | Tamsin Kell | Darren Brell | [A1 key](A1.json) |
| [A2 · deferred](sources/A2.json) | Darren Brell | Tamsin Kell | [A2 key](A2.json) |

The trustee edges all point to **Wrenhollow Settlement**. Each complete graph also contains **Iona Brell trustee_of Wrenhollow Settlement** and **Darren Brell sibling_of Iona Brell**. Iona’s archive enquiry supplies the sibling relationship in her own words. The bank’s old mandate details in that same email serve the archive search. Maren’s power to appoint replacements supplies no settlor or trustee office for her. The pencilled bank slip and roof proposal remain proposals.

## Read the file

| Original document | Why the adviser has it |
| --- | --- |
| [QF8M · Opening mandate](originals/QF8M.txt) | Iona supplied her copy of the 2023 bank record. |
| [VJ3K · Certified office-book extract](originals/VJ3K.txt) | The keeper answered a standing-records request. The founding acceptances remain with her. |
| [LX6R · Executed instrument extract](originals/LX6R.txt) | The solicitor holds a copy. Orrel holds the sole executed original. |
| [HC9W · Meeting diary](originals/HC9W.txt) | The solicitor recorded the meeting and a possible mandate submission. |
| [BD4T · Roof proposal](originals/BD4T.txt) | The property administrator sought a spending decision. The referenced survey is absent. |
| [MP2Z · Register extract](originals/MP2Z.txt) | The custodian supplied the escrow disposition. The A2 file substitutes the deferred field. |
| [SY7G · Archive enquiry](originals/SY7G.txt) | Iona copied the solicitor on her request for named statement packs. |

A0 and A1 each have 1,540 Source-body words. A1 moves the archive enquiry from seventh to first and the instrument from third to seventh. All seven serialized Source objects match by ID. A2 has 1,547 words and keeps the A0 order. One literal field in MP2Z changes. All six other objects and the other MP2Z fields match. The custodian set the 14:20 cut-off before authoring so both late records could enter the file, and specified a binding 15:00 lock in the deferred condition. [Custody and receipts](custody.json) · [Preblind freeze](freeze.json) · [Byte and order comparison](review/matched-sources.json)

## Decide whether the office transferred

The office book independently identifies Darren as the original Second Seat holder. LX6R names him as the retiring trustee and Tamsin as his replacement. It makes retirement and appointment simultaneous and exclusive “only upon delivery under clause 2.” Only Perrin Saye’s permitted RELEASED entry against the sole original, OC-517, can deliver this instrument. Signing, retaining the original and circulating copies have different documentary effects.

In A0/A1, MP2Z identifies OC-517, Perrin as the operator and a committed “RELEASED — 12:20 BST on 17 September 2026” entry. Its controls exclude a release while a time lock is in force. In A2 the row reads “HOLD — release locked until 15:00 BST on 17 September 2026; no earlier release permitted”. That positive lock prevents the specified act at 14:20. It keeps both retirement and appointment from taking effect. The register snapshot covers events through 14:00. The completed entry predates that snapshot, and the deferred restriction extends beyond the cut-off.

All six independent annotators recovered all three graph edges for their file. Each pair agreed that the changing edge needs LX6R and MP2Z. All three pairs differed on exact quotation boundaries. A1 reader P miscopied a line break. The original answer and the mechanically checked approvals are available separately. Three adjudicators committed their rulings before receiving any comparison. [Blind disagreements and provisional registers](review/blind-review.md) · [Cross-condition adjudication](review/outputs/comparison.txt)

Ten fresh full-file mask readings tested disposition, identity, operative terms, settlement name, time coverage and the link between the register and the instrument. Six more readers tested exact excerpt packages. The two direct proofs succeeded. Removing either necessary document left insufficient evidence. An additional proposed A2 route using shorter deed excerpts and an earlier certificate failed even with every proposed quotation present. [Mask and deletion results](review/necessity.md) · [Final independent disposition](review/outputs/final-audit.txt)

No single Source establishes the changing trustee. The latest-document and most-frequent-name rules select Darren when forced to choose. Draft promotion always selects Tamsin. Each fails on at least one state, and keeping both candidates fails in all three. These tests concern one synthetic file and its controlled variants. [Shortcut predictions and limitations](review/shortcuts.md)

Two realism reviews identified one material defect in the register’s operator provenance. The responsible author used the one repair cycle, followed by two fresh realism reviews before blinding. Shared register metadata now establishes who could commit a permitted disposition. The 11:30 instrument uses present-tense custody language before the documented 11:45 physical intake. The repeated bank wording and explanatory family email may cue attention. The instruments and institutions are fictional, and practitioner validation remains outside this pilot. [Per-Source realism reviews and public conventions](review/documentary-review.md)

## Offline replay

| Condition | Planned / replayed / scored | TP / FP / FN | P / R / F1 | Exact graph | Ordinary quote / Source association | Same-edge critical proof |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | 1 / 1 / 1 | 3 / 0 / 0 | 1 / 1 / 1 | Yes | 2 of 2 / 2 of 2 | Complete |
| A1 | 1 / 1 / 1 | 3 / 0 / 0 | 1 / 1 / 1 | Yes | 2 of 2 / 2 of 2 | Complete |
| A2 | 1 / 1 / 1 | 3 / 0 / 0 | 1 / 1 / 1 | Yes | 2 of 2 / 2 of 2 | Complete |

The Research Workbench reconstructed the saved ideals with resolver `none` and reopened the retained Run. The historical scorer output is retained per condition. The v2 policy overlay treats the joint-only trustee as ineligible for ordinary quotation and Source attribution, and requires both approved passages on that same edge. All three planned critical positives passed. The aggregate counts this single family three times. Each replay used zero provider tokens with zero incremental extraction cost. The receipt includes per-condition runtimes, the prompt and input commitments, and the retained Run digest. [Offline replay receipt](review/offline-replay.json) · [Replay command and workflow](../../docs/workflows/benchmark-v3-packets.md)

## Admission decision

**Technically reviewed; pending the owner’s decision.** The final adjudicator excluded the failed A2 alternative, confirmed the direct proof and found no outstanding scored dispute. The accepted critical proof for each condition contains exactly two Source/quotation pairs. The final keys also retain the office-book extract and the instrument as independent ordinary approvals for Iona’s unaffected seat across all three conditions. Her certification date bounds what the keeper reported. It does not expire the office.

All 40 authorised Codex scientific sessions were used. They comprise one designer, seven original authors, one author revision, four realism reads, six full blind reads, three provisional adjudications, two comparative audits, ten full-file masks and six excerpt readings. Runtime receipts report 448,512 input tokens, including 53,120 cached, and 146,461 output tokens, including 45,678 reasoning tokens. Agent charges are unpriced. **Paid PCG extraction attempts were zero.** [Session receipts and commitments](review/sessions.jsonl) · [Verified visibility boundary](review/isolation.md)

The remaining decision is the student owner’s. Review the deed and disposition together in both states, the independent incumbent record, the unchanged kinship assertion and the evidence exclusions. Record a dated accept, return or quarantine against the package, keys and evidence policy. The signature and decision are empty, and dispatch is disabled. [Admission commitments](admission.json) · [Reproducible package](manifest.json)
