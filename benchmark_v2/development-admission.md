# Benchmark v2 development admission review

On 22 November 2026, the independent Codex fixture-review agent (`/root/dev_fixture_review`) audited D9, D10, D11, D12 and D14 in revision `21da01734e2ee92be422ea591d7df3126b48bdf6`. The frozen development lock has SHA-256 `9ec8f3667d3f7d7613b9873ab2506b8d2be882d4d802f302bbf7f2c3c5ae1401`. The review used the five development packages, their public development controls, the protocol and the prior recorded audit. The technical audit preceded human sign-off. Alistair Kung approved all five on 22 November 2026. [Signed disposition and reviewed commitments](reviews/development-2026-11-22.json) [Protocol](README.md) · [Development lock](development.lock.json) · [Prior offline review](implementation.md)

| Condition | Package SHA-256 | Annotation SHA-256 |
| --- | --- | --- |
| D9 | `18d6bc35c0488c62296649e8241fc9b3f4df24b4da08574d1f482058c7c97551` | `11a917205b57fa748521f1161b79bdc009e51db44dbc27eaf9560894e99c9381` |
| D10 | `b4645029ad21cd68bee82d03941a24dc579a5e27b8a9c982a30d4b230cf76d3b` | `1766ad31c8faefdef578be161f9b13ec1e8953c2a26ecf8c065aa24d1d77bff8` |
| D11 | `0a8285fb209bbb0e92accedaea7877a510a2ce435322f00ad93690561d54af52` | `066d50f71a1e87e174c0920d41c35a8fdbcbabe27013758deda6b7de161255e1` |
| D12 | `de7ad37cb7f3f9250a13bb1da284cd927afd8358b49495e9258522d3f3494cdf` | `bbdf8b371e9afa7d81be5069501c84f867bd35a3fb6cbb5617a3008643771af7` |
| D14 | `cb770b0ab81b3e8526239c3f0dc97a59170b205e434418fd7a39016a140b294e` | `d1d3b1d2d66ee452e812ad833fa4bbb05c78ad531eb9cfe6e1834a24e136a48f` |

The package digest covers each relative file path and its content hash. The annotation digest covers the canonical validated condition row, including the input ID and diagnostic targets. All five package digests match the lock. I checked the complete graph against the Sources in both directions, read every ordinary approval for semantic support, and verified all 24 approved edge-to-Source/quotation pairs against exact Source text. The directly loaded saved ideals reopened with 23 TP, zero FP and FN, 23/23 eligible quotation passes and 23/23 eligible Source-attribution passes. D12's annotated sufficient set also passed. Each named package accepted a saved plan and its pending marker caused a live plan to fail validation. The checks made zero provider attempts.

## D9 · Temporal presentation order

The 10 January 2025 note supports Alice Tan as settlor, Chloe Tan as beneficiary, and Alice and Benedict each as Chloe's parent. It also records the then-reported marriage and Benedict's purported trusteeship. The March 2026 note records the divorce. The August correction says Benedict was never appointed and identifies Alice as sole trustee. The December proposal names Benedict as a possible replacement and confirms that Alice still holds office as of 5 December 2026. Those facts account for all five current edges and both forbidden edges. The two approved trustee alternatives are individually sufficient with their local context. The August quote names the trust outright, and the December quote resolves the office from the note's heading and immediately preceding discussion.

D7 and D8 match every file in their pinned T0 and T3 packages at `d54832285b160f8626b7ca8f9388b7865d4fda79`. D9 reverses the order of D8's four Sources in the model-facing array and preserves each Source ID, title and original bytes. Truth, approvals, both ideals and diagnostic targets match. The three conditions share `benchmark_v1_temporal_progressive`. The three repeats for each T3 order measure order sensitivity within this one snapshot. A single Benedict false-positive edge can arise from accepting the corrected historical claim or promoting the December proposal. [D8](../benchmark_v1/temporal/dev/case_5/README.md) · [D9](../benchmark_v1/temporal/dev/case_7/README.md)

## D10 and D11 · Alderwick authority pair

The signed instrument establishes the appointment rule and names Nora Pike as sole trustee effective 1 May 2025. The mailing email identifies Felix Marr as the brother of its sender, Helen Marr. The exact approval for that sibling edge relies on the unambiguous From header. Helen's claim that Owen Rook holds office has no appointment authority under the file's rule, and the mailing requests give no participant a beneficial interest or other office. The file supports those two current edges as of 30 June 2025.

Both authored conditions share `benchmark_v2_alderwick`, with the original Evergreen authority example as a separate easy reference. The serialized Sources differ only in the mail's sending date, 16 April versus 16 June 2025. The Source order, titles, IDs, instrument bytes, complete truth, approvals, ideals and targets match. The change moves the informal claim from earlier to later than execution. The design can detect a latest-by-date error in D11. Selecting the last-presented document also yields the correct trustee in both conditions, which limits what success can establish about authority reasoning. [D10](../benchmark_v1/authority/dev/case_2/README.md) · [D11](../benchmark_v1/authority/dev/case_3/README.md) · [Evergreen reference](../benchmark_v1/authority/dev/case_1/README.md)

## D12 · Direct identification control

The notice states that Anna Dale took office as trustee of Seaforth Trust on 14 April 2026. The approved sentence is one sufficient exact pair, including when the index is withheld. The correspondence letter supplies the exact approvals for Kit Nash as settlor of Seaforth and Rhea Barr as settlor of Hillstone. The index maps L-29 to Seaforth without appointing anyone. Hillstone is a real alternative in the file and the direct notice rules it out for Anna. The mailing instructions add no graph relationship.

D12 and its public matched condition D13 share `benchmark_v2_settlement_files`, all three Source IDs, titles and ordering, the index and letter bytes, both candidate trusts, all semantic edges and the required, forbidden and unaffected targets. The linked notice deletes exactly “of Seaforth Trust”. In the full linked bundle the appointment under L-29 and the index's positive L-29 mapping jointly identify Anna and Seaforth. Masking the mapping leaves Seaforth and Hillstone both plausible and removing the appointment sentence leaves no asserted Anna trusteeship. The IDs, titles and letter supply no further mapping, and neither linked span suffices alone. D12's singleton is the appropriate direct-control attachment. No disposition for D13 is made in this record. [D12](../benchmark_v1/cross_source/dev/case_2/README.md) · [D13 matched development condition](candidates/D13/README.md) · [Frozen evidence policy](evidence-policy-v1.md)

## D14 · Fernbank composite

The complete graph as of 30 September 2026 contains eleven edges across eight Sources in the `benchmark_v2_fernbank` lineage. Both counts exceed the D1–D7 controls. The exact serialized system and user contents total 5,220 UTF-8 bytes. The protocol's estimate is 1,305 message tokens, excluding provider framing and the structured output schema.

| Source withheld | Current relationships that lose sufficient support |
| --- | --- |
| `formation` | Miriam Kwan settled Fernbank Trust. |
| `appointment` | Colin Webb is Fernbank Trust's sole trustee. |
| `contact` | Sender Miriam Kwan is married to Adrian Kwan. |
| `attendance` | Adrian Kwan and Elin Moss are each a parent of Tessa Kwan. |
| `distribution` | Tessa Kwan is a beneficiary of Fernbank Trust. |
| `orchard` | Logan Price settled Orchard Lane Trust and Elin Moss is its trustee. |
| `accounts` | Tess Kwan and Sidney Cross are each beneficiaries of Orchard Lane Trust. Tess Kwan and Logan Price are siblings. |
| `pending` | None. The 28 September message proposes a replacement and records that there has been no signed appointment or acceptance. |

Seven Sources each contribute unique current relationships. The spouse and sibling quotes are locally resolved by the From header and the beneficiary sentence in the same Accounts return, respectively. `attendance` identifies TK as Tessa Kwan and distinguishes Tess Kwan by name and address. `distribution` corroborates Tessa's initials and explicitly names her as the Fernbank beneficiary. `accounts` independently names Tess as an Orchard Lane beneficiary. Colin's executed appointment certificate establishes who currently holds office, and Tessa's proposed appointment is excluded. Miriam's marriage to Adrian does not establish Miriam as Tessa's parent. Shared surnames, co-parenthood, addresses, invitations and envelope handling supply no other supported edges. The three required, four forbidden and two unaffected diagnostic edges match these facts. The positive answer key can be recovered from full names even when the extractor leaves TK unresolved. Use this composite to describe breadth and identity errors, with volume effects reserved for the matched scaling study. [D14 answer key and Source map](../benchmark_v1/composite/dev/case_1/README.md)

## Human disposition

Alistair Kung signed approval of D9, D10, D11, D12 and D14 on 22 November 2026, after receiving the ledger above. Workbench verifies the signed record, package bytes and normalized annotations. The original pending-marker files are included in those package digests. Their prior status remains visible in historical snapshots. [Signed disposition](reviews/development-2026-11-22.json)
