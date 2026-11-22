# Benchmark v3 development portfolio · revision 1

**Five admitted families and 12 admitted conditions.** H/I/J reserve three pending pilot slots with five planned conditions. The Architect recommends 10 further families with 18 proposed conditions. If the pilot and every selected proposal are eventually admitted, the allocation reaches 18 independent histories and 35 scored conditions. Two target slots currently have no selected lineage.

Conditional Source-volume mix · **10 routine · 6 moderate · 0 complex · 1 large · 1 giant**. All five admitted families and all three pilot reservations are routine by Source count. I and J have more demanding reasoning than H. The original 5/7/6/1/1 mix is a starting hypothesis. More short files would duplicate the current emphasis, while adding Sources to accepted or separately authorized histories would change the file. The independent review kept nominal workloads compact and found no defensible 21–50 Source allocation yet. An intermediate workload gate comes before the large and giant proposals.

New production planning estimate · **488 / 689 / 865** charged factory sessions (low, central, high). Pricing is unobserved. The 79-session H/I/J ceiling is separate. The Architect’s rejected receipt and the one-URL deterministic recovery are documented for owner review. [Batch roadmap](ROADMAP.md)

[Master ledger](master.json) · [Validated portfolio](portfolio.json) · [Versioned hypotheses](../rounds/2026-11-23-development-20.json) · [Practice references](PRACTICE.md) · [Giant design](GIANT.md) · [Review method](REVIEW-METHOD.md) · [Independent critique](CRITICAL-REVIEW.md) · [Evaluation custody](EVALUATION-CUSTODY.md) · [Provenance](PROVENANCE.md)

The factory portfolio binds the existing admissions and only the registered new hypotheses. The master ledger additionally counts the three separate public pilot reservations and lists the returned or deferred candidates outside the allocation. A portfolio slot is a planning hypothesis. Admission requires exact artifacts, review evidence and a dated owner decision.

## Master allocation

| Family | Disposition | Sources per condition | Volume tier | Conditions | Primary axis | Family session ceiling |
| --- | --- | ---: | --- | ---: | --- | ---: |
| A · Trustee handover | Admitted | 7 | routine | 3 | Temporal effectiveness | — |
| B · Estate administration | Admitted | 7 | routine | 2 | Entity identity | — |
| C · Two trusts | Admitted | 7 | routine | 3 | Cross source reasoning | — |
| D · Scoped trust amendment | Admitted | 3 | routine | 2 | Versions and amendments | — |
| F · Complete-record identity collision | Admitted | 5 | routine | 2 | Entity identity | — |
| H · Routine trust records completeness | Pending pilot | 5 | routine | 1 | Graph completeness | 20 |
| I · Certified extract and record basis | Pending pilot | 5 | routine | 2 | Documentary authority | 25 |
| J · Authenticated copy and delivery | Pending pilot | 8 | routine | 2 | Axis interactions | 34 |
| M · Former-name reconciliation | Proposed | 9 | moderate | 2 | Entity identity | 34 |
| P · Repeated quotation from one origin | Proposed | 10 | moderate | 2 | Origin and copies | 35 |
| L · Limits of a civil-record sighting | Proposed | 7 | routine | 2 | Incomplete information | 30 |
| N · Execution status among retained counterparts | Proposed | 10 | moderate | 2 | Versions and amendments | 35 |
| O · Title-application progress with trustee office fixed | Proposed | 8 | routine | 2 | Documentary authority | 31 |
| R · Event date versus report date | Proposed | 12 | moderate | 2 | Temporal effectiveness | 38 |
| Q · Carry-forward across instrument generations | Proposed | 17 | moderate | 2 | Versions and amendments | 49 |
| S · Scoped adoption and concurrent roles | Proposed | 18 | moderate | 2 | Cross source reasoning | 52 |
| U · Completeness in an administrative handover | Proposed | 65 | large | 1 | Administrative context | 125 |
| V · Longitudinal cross-section reconstruction | Proposed | 150 | giant | 1 | Graph completeness | 260 |

The Source-volume bands use 3–8 routine, 9–20 moderate, 21–50 complex, 51–99 large and 100–200 giant. For overlapping endpoints in the starting hypothesis, this plan assigns a count to one band. The factory's `administrative` field maps to large here. Counts indicate inventory sizing. The hypothesis records describe each workload's documentary function and uncertainty.

E is returned and excluded. Its two 7-Source conditions remain diagnostic. The independent parentage comparison reproduced in offline review, but the retainer relevance, witness reference handoff and comparable provenance and scope require further work. A repair requires separate approval. No publicly evidenced quarantined lineage is in this planning ledger. [Owner dispositions](../../admission_d_f/OWNER-DECISIONS.md)

## Coverage matrix

A–C entries report verified axes from the historical record. D and F entries report limited technical observations pending formal reconciliation. Pending and proposed entries indicate intended coverage. An axis appearing in a proposed family does not demonstrate it. E remains outside the matrix.

| Axis | Verified A–C | Limited D/F | H/I/J pending | New primary | New secondary | Scope note |
| --- | --- | --- | --- | --- | --- | --- |
| Temporal effectiveness | A | — | J | R | V | Effective state at the meeting cut-off. |
| Documentary authority | A | — | I | O | N, Q, S | What a record or actor can establish in the stated capacity. |
| Entity identity | B | F | — | M | — | Explicit joins and restraint against unsupported merges. |
| Cross source reasoning | C | — | — | S | M, R, V | Support that depends on independent Source functions. |
| Evidence sufficiency | A, B, C | D, F | H, I, J | — | M, P, L, N, O, R, Q, S, U, V | A sufficient proof set attached to the same edge. |
| Contradictory assertions | — | — | — | — | — | Competing facts from distinct origins and bounded standing. |
| Incomplete information | B, C | — | I | L | — | Supported named relationships and open questions. |
| Origin and copies | B | — | I | P | V | Independence of authors and copies traceable to one origin. |
| Versions and amendments | — | D | — | N, Q | — | Version status, operative scope and provenance. |
| Graph completeness | — | F | H | V | Q, S, U | Full graph and ordinary invariant relationships. |
| Administrative context | — | — | H | U | P, O | Relevant facts embedded in ordinary supplied work. |
| Axis interactions | — | — | J | — | — | Identifiable combinations with interpretable controls. |
| Presentation order | A | — | — | — | — | Identical bytes in a different display order. |
| Custody and absence | — | — | J | — | — | Graph consequences of supplied or missing records. |
| Source discovery | — | — | — | — | — | Deferred outside supplied-text extraction. |
| Physical document quality | — | — | — | — | — | Deferred OCR and physical recovery. |

D retained joint evidence at grouped level for one express scoped amendment. The locator shortcut and incomplete individual fact deletion bound the inference. F retained complete distinct identities under a populated label collision. Positional pairing and a corrected structured surname discrepancy bound its interpretation. [Canonical findings and limitations](../../COVERAGE.md)

## Exact hypothesis inventory

| Family | Revision | SHA-256 commitment | Planning disposition |
| --- | --- | --- | --- |
| M | `former-name-explicit-link@1` | `fa467f9804834d9382162f1e7fb16db15d8b55d08680b2ed3dab060632ecbcc0` | Proposed slot |
| P | `duplicate-origin-salience@1` | `06f97ebd0d9c651404b28ed49fa8a468ea39ba148d49bcb5c8392d97a1f723d0` | Proposed slot |
| L | `civil-record-information-boundary@1` | `ec3efd9fbd411a36c75df375b63fe08aea1aa25961ce74822816beed5f76f9cb` | Proposed slot |
| N | `executed-version-record@1` | `e6aa572b315905421af40e9b8cf5fd698dcc9ac41dbac955ffcb75476a37f9d3` | Proposed slot |
| O | `land-register-lag-invariance@1` | `e9a85561cbd07eaf097bf5bff337d61fa684a8728e5cb4f359a02ce17c2274fa` | Proposed slot |
| R | `typed-event-chronology@1` | `e59adeaeafe55ecc6bf6567932e8d58e6cc11faeb18f35359803818308c2548e` | Proposed slot |
| Q | `restatement-schedule-scope@1` | `b5046dc1860b9735a22a323780c982ac143cb74b5284dec4d957190d8c424888` | Proposed slot |
| S | `named-scope-capacity@1` | `888372b762667bab8ffd03519f92405dd246118df8806798244fb69abf6e3263` | Proposed slot |
| U | `administrative-estate-load@1` | `55e95c4e91d4a99cabbc0c03f4c9831fc0054b0df045983be5ae1af3ace18b90` | Proposed slot |
| V | `longitudinal-cross-section-reconstruction@1` | `925b5fdd603297092c963366da245eea3f95c8d0e4a6804cceff9ae57655156d` | Proposed slot |
| G | `incidental-kinship-in-correspondence@1` | `18ac2949770a2beb57602a12d705c08ae482c443c7f2991c225e2158c644cd01` | Prior proposal held outside allocation |

Canonical portfolio commitment · `5d082eabddc13bc798c6d75c17063205b419440bd6eef12549707d384a03300f`.

## Owner decisions

1. Accept, return or decline the planning allocation and exact hypothesis revisions. Decide which conditional slots and workload bands to retain after pilot reconciliation.
2. After the separate pilot decision, authorize the first new batch against an updated admitted snapshot, the exact portfolio and manifest, model/effort allocation, private custody and session ceilings. Approve exact designs and subsequent admission dossiers at their own gates.
3. Decide whether to fund the large rehearsal, the giant feasibility preflight and the optional diagnostics. Keep any later extraction and scoring release under a separate approved experiment.
4. Approve a separate evaluation custodian and safe projection before considering evaluation authoring. Approve the eventual freeze count based on achieved coverage and the stopping criteria.
