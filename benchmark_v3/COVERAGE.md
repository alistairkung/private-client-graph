# Benchmark v3 coverage register

Generated with `uv run python -m benchmark_v3.architect coverage`.
Each row counts one admitted Matter family. Matched conditions share its history.
Keep this register outside the blind packets.

## Admitted development families

| Family | Primary axis | Secondary axes | Intended difficulty |
| --- | --- | --- | --- |
| [A · Wrenhollow](family_a/DOSSIER.md) | temporal effectiveness | documentary authority, evidence sufficiency, presentation order | Reconstruct one effective transfer at a bank-meeting cut-off despite signed papers and a later administrative message. |
| [B · Estate administration](family_b/DOSSIER.md) | entity identity | incomplete information, origin and copies, evidence sufficiency | Resolve the speaker of a parentage report with an independently maintained attendance field. Withhold the named edge when attribution is open. |
| [C · Two trusts](family_c/DOSSIER.md) | cross source reasoning | evidence sufficiency, incomplete information, entity identity | Identify which of two trusts an operative designation applies to from a separately maintained custody reference. |

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

## Remaining research gaps

- **contradictory assertions, origin and copies.** Independent same-scope reports can disagree. B tests one report and its forward, and A tests stale administrative material against operative evidence.
- **versions and amendments, documentary authority.** No primary matched test covers a partial amendment or correction that leaves unrelated prior clauses intact.
- **entity identity, incomplete information.** B tests an unlabeled speaker among two distinct names. Distinguishable near-name identities and collisions across complete records remain open.
- **graph completeness, administrative context.** C verifies a rich invariant graph under target intervention. An incidental assertion buried in plausible business correspondence has no dedicated control.
- **axis interactions, custody and absence.** Withholding on insufficient evidence is covered locally in B and C. A missing original or interacting authority paths need a separately interpretable contrast.
- **source discovery, physical document quality.** Record these workload needs outside the supplied-text graph benchmark.

## Hypothesis decisions

| Hypothesis | Family | Status | Revision digest |
| --- | --- | --- | --- |
| `scoped-trust-amendment@1` · Scoped replacement within one trust instrument | D | proposed | `20288d9f35aa29585353393c40d6f6e317fc9fee302b7e35a989b8306224fcb8` |
| `independent-parentage-disagreement@1` · Independent reports about the same relationship | E | proposed | `1c6fbc49c9be191bc6dab14845e0db2afe94675f10f6634c54d897bacede2cae` |
| `complete-record-label-collision@1` · A shared display label across complete records | F | proposed | `86c152a0d7816d83f3de38c16d265f7619ce7ccf08223d22e116b04bb98ea09c` |
| `incidental-kinship-in-correspondence@1` · Ordinary kinship in routine correspondence | G | proposed | `18ac2949770a2beb57602a12d705c08ae482c443c7f2991c225e2158c644cd01` |
