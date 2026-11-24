# Benchmark v3 coverage register

Generated with `uv run python -m benchmark_v3.architect coverage`.
The [admission register](admissions/2026-11-24.md) covers all 19 admitted development families.
The [research catalogue](RESEARCH-CATALOGUE.md) describes their reasoning tests and limits.
Each family counts once. Matched conditions share its history.
Keep this register outside the blind packets.

## Original five admissions and coverage reconciliations

| Family | Primary axis | Secondary axes | Intended difficulty |
| --- | --- | --- | --- |
| [A · Wrenhollow](family_a/DOSSIER.md) | temporal effectiveness | documentary authority, evidence sufficiency, presentation order | Reconstruct one effective transfer at a bank-meeting cut-off despite signed papers and a later administrative message. |
| [B · Estate administration](family_b/DOSSIER.md) | entity identity | incomplete information, origin and copies, evidence sufficiency | Resolve the speaker of a parentage report with an independently maintained attendance field. Withhold the named edge when attribution is open. |
| [C · Two trusts](family_c/DOSSIER.md) | cross source reasoning | evidence sufficiency, incomplete information, entity identity | Identify which of two trusts an operative designation applies to from a separately maintained custody reference. |
| [D · Alder Fold Trust](family_d/DOSSIER.md) | versions and amendments | documentary authority, evidence sufficiency, graph completeness | Changing only the amendment's provision locator switches which earlier beneficiary assertion survives without changing the replacement beneficiary, trust or unaffected relationships. Reject the design if either branch is ambiguous, has a wider effect, or supports the replacement without the planned cross-Source link. |
| [F · Park will planning](family_f/DOSSIER.md) | entity identity | evidence sufficiency, graph completeness | Creating a collision in one populated display field leaves the complete named graph and valid evidence routes invariant when stable references and explicit identity links remain fixed. Reject the design if the field has authority to alter the mapping, the alternative label is not credible, or the proposed identity link is dispensable. |

### A · Trustee handover

[Historical admission](family_a/admission.json) under the earlier protocol.

**Independently verified findings**

- **Temporal effectiveness.** An affirmative hold preserves the incumbent. A registered release effects simultaneous retirement and replacement. (`family_a/review/blind-review.md`)
- **Documentary authority.** The operative instrument and custodian disposition jointly determine the changing office. (`family_a/review/necessity.md`)
- **Evidence sufficiency.** Fresh excerpt readings established the two-Source routes and rejected a proposed short alternative. (`family_a/review/necessity.md`)
- **Presentation order.** An order-only sibling preserves the key and ordinary context. (`family_a/review/matched-sources.json`)

- **Incidental challenges.** Administrative email and bank paperwork contain a supported kinship and non-operative details.
- **Matched controls.** A0/A1 reorder identical Sources. A0/A2 replace only the release disposition with a positive hold through the cut-off.
- **Shortcuts and limits.** A later note and the most frequent name favour the incumbent. Draft promotion favours the successor. One two-person office and explanatory wording limit the inference.
- **Genres.** Bank mandate, Office-book certification, Executed instrument, Escrow disposition register, Diary, archive enquiry and expense proposal.
- **Overlap.** Joint proof overlaps with B and C. The verified switch concerns effectiveness under one instrument.

### B · Estate administration

[Historical admission](family_b/admission.json) under the earlier protocol.

**Independently verified findings**

- **Entity identity.** A separately maintained session record binds the native statement to one named speaker only with the completed field. (`family_b/review/outputs/comparison.json`)
- **Incomplete information.** Two compatible speakers remain in the incomplete condition. Both readings preserve the ordinary parent edge. (`family_b/review/agreement.json`)
- **Origin and copies.** The forward and export share one informant. Two forward-only readings fail to fix the speaker. (`family_b/review/mask-results.json`)
- **Evidence sufficiency.** Deleting a needed identity or statement fact defeats the edge without removing unaffected kinship. (`family_b/review/proof-deletions.json`)

- **Incidental challenges.** A clerk’s original-document sighting supports ordinary kinship through distinct sources of information.
- **Matched controls.** B0/B1 complete one name field for the same dated conversation. All other Source bytes remain fixed.
- **Shortcuts and limits.** Testing field completeness and then selecting the first contact can reproduce the edge delta. Two distinct names and a fictional desk convention bound the result.
- **Genres.** Executor enquiry, Family contact list, Native desk relay and inline forward, Attendance extract, Original-document sighting, Intake note.
- **Overlap.** Like C, an incomplete identifier leaves a named edge unresolved. The link here identifies a speaker.

### C · Two trusts

[Historical admission](family_c/admission.json) under the earlier protocol.

**Independently verified findings**

- **Cross source reasoning.** The linked parent-deed reference switches the supported trust endpoint. Both mappings remain possible when it is obscured. (`family_c/review/outputs/comparison.json`)
- **Evidence sufficiency.** Independent excerpt readers verify the three-Source proof. Whole-file masks defeat the target while preserving ten ordinary edges. (`family_c/review/proof-deletions.json`)
- **Incomplete information.** Both readers withhold both trust endpoints with the partial reference. (`family_c/review/agreement.json`)

- **Incidental challenges.** Shared trustees and ten ordinary relationships provide a completeness check. An expense, a wish and routine meeting details contribute context.
- **Matched controls.** C0/C1 swap the parent-deed reference. C2 obscures its distinguishing character with both allocations viable.
- **Shortcuts and limits.** First trust, fixed trust and assigning both fail across variants. One register entry, two parallel settlements and selective deed extracts bound the decision.
- **Genres.** Certified deed extracts, Signed designation transcript, Custody register, Meeting note, Wish letter, Expense reconciliation.
- **Overlap.** Shares joint proof and restraint with A/B. Graph completeness and distraction are present without separate matched interventions.

### D · Scoped trust amendment

[Human admission](family_d/admission.json) under approved hypothesis `scoped-trust-amendment@1` (`20288d9f35aa29585353393c40d6f6e317fc9fee302b7e35a989b8306224fcb8`).

**Independently verified findings**

No verified findings recorded.

- **Incidental challenges.** The principal instrument supplies separate office and beneficiary provisions. The signed variation has its own effective date.
- **Matched controls.** D0 and D1 change only the operative provision locator. The earlier survivor changes, the replacement and unaffected relationships persist, and the saved keys attach joint scope proof to each current beneficiary. Grouped proof was independently verified in the closing audit.
- **Shortcuts and limits.** Individual fact-level deletions remain incomplete. Reading the locator alone can reproduce the graph without demonstrating the full intended reasoning. The invariant edges cover trust relationships. Unrelated kinship remains outside this comparison.
- **Genres.** Principal instrument extract, Signed variation, Advice meeting brief.
- **Overlap.** A tests whether an instrument took effect. D fixes effectiveness and varies the reach of the operative provision.

### F · Complete-record identity collision

[Human admission](family_f/admission.json) under approved hypothesis `complete-record-label-collision@1` (`86c152a0d7816d83f3de38c16d265f7619ce7ccf08223d22e116b04bb98ea09c`).

**Independently verified findings**

No verified findings recorded.

- **Incidental challenges.** The working index uses ancillary display forms for distinct people. The authoritative reconciliation gives complete identities and stable references.
- **Matched controls.** F0 and F1 change only one populated display label. Both complete named graphs and their separately attached proof sets remain invariant. Withholding an exact identity entry defeated its dependent edge in the masked review.
- **Shortcuts and limits.** Positional pairing can reproduce the graph. The original isolated excerpt reader entered a different structured surname despite identifying the correct person in the explanation. The independent identical-packet repeat returned the correct surname. The result is bounded to this display-label collision.
- **Genres.** Signed relationship confirmations, Identity reconciliation note, Working index.
- **Overlap.** B tests incomplete attribution. F retains complete, distinguishing records and varies an ancillary label.

## Difficulty taxonomy

| Axis | Category | Scope | Meaning |
| --- | --- | --- | --- |
| temporal effectiveness | reasoning | in scope | Establish the state at the cut-off from effective acts, chronology and operative conditions. |
| documentary authority | reasoning | in scope | Determine what a document or actor can establish, using the file’s own authority and capacity terms. |
| entity identity | reasoning | in scope | Resolve distinguishable named entities from explicit links and withhold unsupported mergers. |
| cross source reasoning | reasoning | in scope | Combine dependent statements from different Sources into one licensed decision. |
| evidence sufficiency | reasoning | in scope | Attach every necessary member of an independently verified sufficient proof to the same edge. |
| contradictory assertions | reasoning | in scope | Reconcile or withhold competing relationship assertions according to their scope, independence and authority. |
| incomplete information | reasoning | in scope | Distinguish a supported negative or positive from an underdetermined named assertion. |
| origin and copies | documentary | in scope | Distinguish independent origins, quoted material and copied or administratively relayed evidence. |
| versions and amendments | documentary | in scope | Recognise the scope and provenance of co-present drafts, partial amendments, and corrections. |
| graph completeness | reasoning | in scope | Recover every supported relationship, including ordinary invariant edges across a mixed file. |
| administrative context | documentary | conditional | Preserve relevant facts embedded in routine material and reject unsupported role cues. Volume is descriptive absent a matched workload control. |
| axis interactions | reasoning | conditional | Test a specified interaction only when simpler contrasts explain what each axis contributes. |
| presentation order | documentary | in scope | Vary presentation order with original chronology and the document bytes held fixed. |
| custody and absence | workflow discovery | conditional | Represent received, copied or missing artifacts in the supplied file. Score only the consequences for supported graph claims. |
| source discovery | workflow discovery | deferred | Find, retrieve or request a Source outside the supplied file. |
| physical document quality | workflow discovery | deferred | Acquire, OCR or recover physical text. A stipulated missing field in text can test reasoning within the supplied bundle. |

## Earlier coverage gaps

- **contradictory assertions, origin and copies.** E reproduced its concordance-to-withholding contrast and was returned at the documentary-realism gate. Retainer relevance and witness reference provenance remain open. E0 and E1 are diagnostic only. B covers a single origin and its forward. [Returned candidate and owner decisions](admission_d_f/OWNER-DECISIONS.md)
- **versions and amendments, documentary authority.** D covers one express scoped amendment. Other amendment mechanisms and full individual fact-level deletion coverage remain open.
- **entity identity, incomplete information.** B covers incomplete speaker attribution and F covers a populated display-label collision with complete identity records. F permits a positional shortcut. Broader identity collisions and interacting information gaps remain open.
- **graph completeness, administrative context.** C verifies a rich invariant graph under target intervention. An incidental assertion buried in plausible business correspondence has no dedicated control.
- **axis interactions, custody and absence.** Withholding on insufficient evidence is covered locally in B and C. A missing original or interacting authority paths need a separately interpretable contrast.
- **source discovery, physical document quality.** Record these workload needs outside the supplied-text graph benchmark.

## Hypothesis decisions

| Hypothesis | Family | Status | Revision digest |
| --- | --- | --- | --- |
| `routine-trust-records-completeness@1` · P1: Routine trust records review | H | approved | `06ef87b2ff166f92519c45234f36ffe6c63bcbe614eba22a92c0a966bbf7a670` |
| `certified-extract-record-basis@1` · P2: Record authority with issue status held fixed | I | approved | `c85fc859ea1e432e456a3debe241432e44b94467d0d0b754243ab52801ccf737` |
| `authenticated-copy-and-delivery@1` · P3: An authenticated copy linked to timely delivery | J | approved | `ae0b12a8394582bbeaab5b0280c1da93390b4e35cb249c743001bdfd454e89d5` |
| `scoped-trust-amendment@1` · Scoped replacement within one trust instrument | D | approved | `20288d9f35aa29585353393c40d6f6e317fc9fee302b7e35a989b8306224fcb8` |
| `independent-parentage-disagreement@1` · Independent reports about the same relationship | E | approved | `1c6fbc49c9be191bc6dab14845e0db2afe94675f10f6634c54d897bacede2cae` |
| `complete-record-label-collision@1` · A shared display label across complete records | F | approved | `86c152a0d7816d83f3de38c16d265f7619ce7ccf08223d22e116b04bb98ea09c` |
| `incidental-kinship-in-correspondence@1` · Ordinary kinship in routine correspondence | G | proposed | `18ac2949770a2beb57602a12d705c08ae482c443c7f2991c225e2158c644cd01` |
| `former-name-explicit-link@1` · Former-name reconciliation | M | approved | `fa467f9804834d9382162f1e7fb16db15d8b55d08680b2ed3dab060632ecbcc0` |
| `duplicate-origin-salience@1` · Repeated quotation from one origin | P | approved | `06f97ebd0d9c651404b28ed49fa8a468ea39ba148d49bcb5c8392d97a1f723d0` |
| `civil-record-information-boundary@1` · Limits of a civil-record sighting | L | approved | `ec3efd9fbd411a36c75df375b63fe08aea1aa25961ce74822816beed5f76f9cb` |
| `executed-version-record@1` · Execution status among retained counterparts | N | approved | `e6aa572b315905421af40e9b8cf5fd698dcc9ac41dbac955ffcb75476a37f9d3` |
| `land-register-lag-invariance@1` · Title-application progress with trustee office fixed | O | approved | `e9a85561cbd07eaf097bf5bff337d61fa684a8728e5cb4f359a02ce17c2274fa` |
| `typed-event-chronology@1` · Event date versus report date | R | approved | `e59adeaeafe55ecc6bf6567932e8d58e6cc11faeb18f35359803818308c2548e` |
| `restatement-schedule-scope@1` · Carry-forward across instrument generations | Q | approved | `b5046dc1860b9735a22a323780c982ac143cb74b5284dec4d957190d8c424888` |
| `named-scope-capacity@1` · Scoped adoption and concurrent roles | S | approved | `888372b762667bab8ffd03519f92405dd246118df8806798244fb69abf6e3263` |
| `administrative-estate-load@1` · Completeness in an administrative handover | U | approved | `55e95c4e91d4a99cabbc0c03f4c9831fc0054b0df045983be5ae1af3ace18b90` |
| `longitudinal-cross-section-reconstruction@1` · Longitudinal cross-section reconstruction | V | proposed | `925b5fdd603297092c963366da245eea3f95c8d0e4a6804cceff9ae57655156d` |
| `testamentary-trust-versus-outright-distribution@1` · Two completed testamentary dispositions, only one a trust provision | DA | approved | `1894d78619d67f766332fd298f019c41bece57ed4c238eeb2fb924fb8245ec62` |
| `parentage-direction-across-record-frames@1` · The same person is a child in one record and a parent in another | DB | approved | `dc04dbb3e78408f58f216be291627a8e882d682846add8e067f6fd67f1cb7973` |
| `continuing-office-reference-follows-holder@1` · A companion trust follows one continuing office, not the whole trustee roster | DC | proposed | `9f2ae38c277b4a5516cc712a54c82c49db0bf4117ead2b5954f3257af64ea20e` |
| `bounded-negative-receipt-coverage@1` · A default provision requires complete negative receipt coverage | AG | approved | `aa9daf7b4f40611a569bc456466e5f3ab3cc54ddd74f93e1e9803c33d58344c8` |
| `mixed-origin-field-attestation@1` · A signed check vouches only for the fields it covers | AH | approved | `675663a370b5acb848e500fc799f042b1ded8e0e3121c331fd9f029a814e58db` |
| `fixed-versus-rolling-incorporation@1` · A later issue matters only under rolling incorporation | AJ | proposed | `7e65cd45da7a876ff28d23046307bc5296b44be293f28ff645a03b67b6fcda6f` |
| `selective-ending-of-parallel-benefit-bases@1` · One beneficiary edge, a different surviving provision | AP | approved | `a89b748456f1c32487795600ff6bdbd88114314e54540d9e34646f6e048b8f37` |
| `representative-signature-without-personal-office@1` · A named signatory is not necessarily a named trustee | AQ | proposed | `fb5530db9f86ba9e6b38b63c718e3966d7dc1146f244d1db3de281ad4fc4aecb` |
| `authority-at-exercise-before-deferred-effect@1` · A decision survives the end of its maker's office | AR | approved | `c009d18694f204128719997fddba0759c43293d52e3a32d55da33d030db81d9f` |
| `separate-or-joint-commencement-of-appointments@1` · One acceptance, separate or joint commencement | AX | proposed | `f816be9e56b0c0a7f7a2191b74686c71ec81b2aed98f8dd9512e34c01f154324` |
| `named-benefit-with-or-without-continuing-spousal-condition@1` · A named designation need not depend on continuing marriage | AY | approved | `d119f024401d75371a224354169a4dfbb246ff464001dc4d77a026e08e60b4e0` |
| `testamentary-group-definition-versus-factual-kinship@1` · A will's defined group is not a family assertion | AZ | approved | `b158525daad26a7f8aa30d52e18a9a9784157b78305646f7bce6125c96f6506c` |
| `settlement-contribution-versus-remittance@1` · The person remitting the closing funds is not necessarily the settlor | BF | proposed | `ad60c7de71790bbaf57f24680c99815e0f6c0a3304a366e95ca2cdc209cd42bc` |
| `asset-transfer-without-relationship-migration@1` · Moving assets does not move the named relationships | BG | approved | `29d8aaa32033487f69f4eec69ef821877b066f65d10402d173a9f700f6557e63` |
| `bounded-age-proof-of-named-commencement@1` · An age check can establish commencement without an exact birth date | BN | approved | `1a4cc06acbd0b4aeb614632439fdc522f46f7e232f67a86b1c12875bc3585b41` |
| `cumulative-benefit-cap-versus-posted-debits@1` · Posted debits do not necessarily exhaust a capped named benefit | BO | approved | `d55453096200efc2ff0db3cb3b2b64f988876f4e618b6f1182b9a9a746d6bd67` |
| `late-notice-with-separate-operative-cure@1` · An acknowledged late notice is not an accepted late notice | BV | approved | `c34ed48b67b88ea08cb8fc1936a3a8775dde0ef8016400e0e2321f73924c7497` |
| `derivative-correction-with-historical-scope@1` · A corrected founding record does not reset the current roster | BW | approved | `e1cd810853a60fa9a80df9b6b671997a8c002135341c75e2d4401ef63238f233` |
| `trust-specific-live-register-cutover@1` · Authority to make an entry transfers trust by trust | BX | proposed | `6949a545a1f33e7a39367b7779b10e1d00e03fb167e42d00f20a17feee0f1dd5` |
| `personal-benefit-surrender-with-continuing-office@1` · A trustee gives up a named benefit without leaving office | CD | proposed | `46137c30e9f82fddbd876a265c8e88ccbb7bf57ef9ce88d9a72699eeabb32600` |
| `withdrawn-drafting-instruction-retains-factual-identification@1` · Dropping a proposed gift does not retract its factual identification | CE | approved | `5d790f2f4443d3b394793211f9691462d41e7bf5e4f8d23041cc1accb221af66` |
| `dual-capacity-decision-and-personal-consent@1` · A trustee's vote does not supply their separately required personal consent | CL | proposed | `9840b092e7ff0d60433bb71bf7fbba33779f69491f059edf887e13226076b9fc` |
| `cumulative-settlors-declaration-and-addition@1` · One continuing trust, two independently established settlors | CM | approved | `983c09573510e09c3c58e4c28f6b34738a9ad8e7a3214e70074f01467647b7d5` |
| `concurrent-assent-to-one-decision@1` · Separate assents must concern the same decision | AA | proposed | `4156635b4a723dd63ab71c9919f574e6cfe882ed2a8d74d463399d7663528c3b` |
| `shared-parent-without-sibling-assertion@1` · Supported common parentage does not supply a sibling edge | AB | approved | `9dd22215c301d0855fa3660b14caa92651730dbf325c2928eb7a9d7ff20994df` |
| `automatic-reversion-after-temporary-substitution@1` · A suspended provision resumes without a new act | AC | proposed | `11735f0da17407c28981c349d865eaed29adc508305e3a19eef40edccd8b4d1b` |
| `independent-alternative-sufficient-proofs@1` · One valid route is enough when a second route also exists | AD | approved | `c5d4db92b6a4ec98f6b23c2bc76a1e8e261470e35f5870755b5367375d824324` |
| `independent-documentary-disagreement@1` · Independent handover accounts of current trustee office | W | approved | `ac18d1c2ef9f3f72b0544a4ddf1d62e7af230be3375dab180f28306bc06352ed` |
| `incidental-correspondence-support@1` · Firsthand relationship support in valuation-access correspondence | X | proposed | `194a1ec56fa6374aa71cfe426dcb6738915ea611b11c3cd767dfe17a1142758d` |
| `bounded-inspection-scope-reconciliation@1` · Which received records did the verification actually cover? | T | approved | `c8c529dfe55f59bf78ae08ce5c7a901b7d8c1ccc16f1b029338dd00bc0e366d4` |
