# Family B admission dossier · Estate of Ivor Ellis Kestell

Hollin Sedge Legal is preparing its first substantive meeting with executor Tamsin Vera Kestell. The file closed at **16:00 GMT on 26 March 2026**. The intake note asks the adviser to establish what the file supports about family relationships and identify outstanding papers. The signed will and certified entries were sighted and returned. The date-of-death building society balance is outstanding. [Custody ledger and exact meeting brief](custody.json)

## Complete graphs

| Condition | Supported edges | Withheld named parent edges |
| --- | --- | --- |
| [B0 · incomplete attendance field](sources/B0.json) | Ivor Ellis Kestell `parent_of` Tamsin Vera Kestell | Kellan Hugh Sorrel to Leonie Tess Rindle and to Nella Ruth Verrow |
| [B1 · completed attendance field](sources/B1.json) | Ivor Ellis Kestell `parent_of` Tamsin Vera Kestell. Kellan Hugh Sorrel `parent_of` Leonie Tess Rindle. | Kellan Hugh Sorrel to Nella Ruth Verrow |

The counter clerk recorded the child's and father's names from the certified birth entry and separately read the executor clause describing Tamsin as Ivor's daughter. The will's executor and outright residue provisions confer no in-ontology trust status. The contact sheet supplies current names and routing instructions. It leaves the contacts' specific relationship to the deceased open.

## Original Source inventory

| Source in file order | Origin and purpose |
| --- | --- |
| [q7m4 · Initial enquiry](originals/q7m4.txt) | Executor's enquiry about probate, papers and initial visit. |
| [v2k9 · Family update list](originals/v2k9.txt) | Executor's complete two-contact update list and common desk route. |
| [r8c3 · Desk relay](originals/r8c3.txt) | Attendee's statement in the relay message. Executor supplied the native export to the adviser. |
| [m5x7 · Attendance extract](originals/m5x7.txt) | Registration keeper's separate attendance record, supplied by the executor. B1 completes its name field. |
| [h3p6 · Inline forward](originals/h3p6.txt) | Executor's actual inline copy of the same relay statement. |
| [w9d2 · Counter sighting slip](originals/w9d2.txt) | Clerk's direct sighting of the original will and certified birth and death entries. |
| [n4j8 · Internal intake note](originals/n4j8.txt) | Adviser's meeting instructions, custody and follow-up. |

B0 has 975 Source-body words and B1 has 976. Both contain seven Sources. Only the m5x7 name field changes, from `[not entered]` to `Leonie Tess Rindle`. The exact serialized fields, IDs, titles and order are otherwise identical. [Preblind freeze](freeze.json) · [Exact variant comparison](review/matched-sources.json)

## Documentary decision

The relay records `DP-7316`, 12 March 2026, 11:20, followed by “Kellan Hugh Sorrel is my father.” Both named contacts were given the shared update route. The clerk's registration convention assigns one attendee and one reference to the specific conversation and matches the issued text to that reference. Leonie or Nella could be the sole attendee in B0. The route, clear recipient, or two copies of the statement supply no additional speaker identification.

B1's completed name field ties the sole attendee to Leonie for that conversation. The statement supplies the kinship. Registration supplies the speaker identity. The native export and inline forward preserve one informant's account. Trust roles, legal authentication of the parentage and the contacts' relationship to Ivor remain outside the licensed conclusions. A further registration confirmation could resolve attribution in B0. Separate corroboration would answer a different question about the reported parentage.

## Blind review and realism

All four blind readings agreed on the complete graph within each condition. Both B1 readers independently identified the same two documentary locations for the statement and the same attendance evidence. They varied in the ordinary quotation boundaries and documentary routes for Ivor and Tamsin. The provisional adjudicators retained the distinct birth-entry and will origins recorded by the clerk and resolved the quotation rulings before matched disclosure. [Agreement](review/agreement.json) · [B0 ruling](review/outputs/B0-judgment.json) · [B1 ruling](review/outputs/B1-judgment.json)

The initial intake note asserted that the name remained missing in both copies. The single repair replaced that interpretation with a custody-only account and kept the meeting brief identical. The transmission ledger now distinguishes the displayed inline copy from the native export. A fresh realism reviewer passed both revised files. The relay is a fictional local procedure. The file has no full transport headers or underlying check-in paperwork, and staff's sighting slip supplies no conclusion about probate entitlement. [Initial review](review/realism-initial.json) · [Fresh review](review/realism-final.json) · [HMCTS probate intake genre](https://www.gov.uk/government/publications/myhmcts-how-to-apply-for-probate-online/apply-for-probate-with-myhmcts)

## Evidence necessity and shortcuts

The approved target proof attaches the exact keyed statement from r8c3 and the sole-attendee record from m5x7 to the same edge. A fresh native-excerpt read supported the edge. A second fresh read supported it with the native relay header included. Both forward-only readers withheld the edge, including when given the full forwarding wrapper. They distinguished issuing the text to the attendee from identifying the first-person speaker. That adverse result excludes the h3p6 route from the scored key. The file retains the copy and its provenance. [Comparative audit](review/outputs/comparison.json) · [Mask and excerpt readings](review/mask-results.json) · [Final evidence ruling](review/outputs/closing-audit.json)

Removing the parent statement from both copies or hiding the session identifiers on the named attendance record independently defeated the named edge. These packets retained the needed verbatim passages for the corresponding one-member deletions of the approved set. B0 independently verifies the missing-name intervention while the two message bodies remain complete. Both fresh whole-file masks preserved the Ivor-to-Tamsin edge. [Exact proof deletion checks](review/proof-deletions.json)

Titles, IDs, order and the latest note are fixed. They supply no B1 addition. Picking the first listed contact in each file yields a B0 false positive. Treating the forward as an independent witness supplies no speaker identity. A rule that gates on field completion and then picks the first contact could coincidentally select the right edge in these two files. The Source-attributed proof requires the name actually written against the conversation. The design covers restraint under one shared route and two distinct names. [Shortcut findings in comparative audit](review/outputs/comparison.json)

## Saved-ideal replay

| Condition | Planned / replayed / scored | TP / FP / FN | P / R / F1 | Exact graph | Ordinary quote / Source association | Complete joint proofs |
| --- | --- | --- | --- | --- | --- | --- |
| B0 | 1 / 1 / 1 | 1 / 0 / 0 | 1 / 1 / 1 | Yes | 1 of 1 / 1 of 1 | N/A |
| B1 | 1 / 1 / 1 | 2 / 0 / 0 | 1 / 1 / 1 | Yes | 1 of 1 / 1 of 1 | 1 / 1 |

The Workbench reopened the retained Run with resolver `none`. Critical edges are graph-scored and have ordinary quotation and attribution marked N/A. The same-edge diagnostic checks every pair in the approved alternative. The receipt retains the historical scorer output, exact decisions, case counts, timing and input digests. The preview allowed zero paid slots and both replays recorded **zero paid PCG extraction attempts**. [Offline replay receipt](review/offline-replay.json) · [Replay procedure](../../docs/workflows/benchmark-v3-packets.md)

## Admission and commitments

**`pending_human_admission`.** The owner can accept, return or quarantine this family separately. Review the documentary proof and the unresolved condition against the committed package, annotation and evidence-policy digests. All conditions remain undispatched. [Admission commitments](admission.json) · [Manifest](manifest.json) · [Scored targets](review/scored-targets.json)

This family used **25** Codex scientific sessions (2 adjudication, 4 annotation, 2 audit, 8 author, 1 designer, 6 masked, 2 realism). The combined task used **60 of 70**, including the custodian and successful harmless isolation probe. Reported packet usage totals 601,761 input and 252,419 output tokens across both families. Codex usage is unpriced. [Session ledger](../families_b_c_sessions.jsonl) · [Isolation record](../families_b_c_isolation.md)
