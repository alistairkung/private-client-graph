# Efficiency pilot measurement

**Operational hypothesis.** The batch factory can produce independently
reviewed families with fewer scientific-agent sessions than the serial
workflow while retaining the same quality and independence gates. Use the
pilot for an observed throughput comparison. The historical cases and
pilot differ in workload, contrast count and audit risk, so the comparison
cannot isolate the factory's causal effect. A return or budget stop is an
operational outcome, with its full cost retained.

## Historical comparator

| Serial workload | Family-scoped sessions | Shared entries | Reported tokens |
| --- | ---: | ---: | ---: |
| [A](../../../family_a/DOSSIER.md) | 40 | — | 594,973 |
| [B](../../../family_b/DOSSIER.md) and [C](../../../family_c/DOSSIER.md) | 25 + 33 | 2, including the harmless probe | 854,180 for the task |
| [D–F](../../../admission_d_f/usage.json) | 25 + 31 + 31 | 3, including one custodian unit | 749,122 family-scoped and 65,034 shared |

The admitted A/B/C/D/F family-scoped comparator is 154 total sessions,
median 31, range 25–40. E consumed 31 and was returned. Report that result
alongside comparisons among successful packages. Historical receipts
suggest a rough range of 8,000–15,000 total tokens per family-scoped
session across the previous Matter workloads. This range is a planning
estimate. Larger Sources, verbose output or extra reasoning may exceed
it. Total tokens include input and output. Record cached input and
reasoning output as subsets, without adding them twice. Billed Codex
charges and rates are unknown.

## Recording and comparison

For each family and condition, derive the machine-observable counts from
the custody ledger, packet receipts, agreement, masked responses and
retained Workbench replay. The custodian adds human review time and the
reason for any remaining discrepancy.

| Measure | Record |
| --- | --- |
| Sessions | Attempts charged, completed and unresolved, by family, revision and role. Count each unique reservation once. Report shared planning and human review separately. |
| Workload | Number of natural Sources, Source words and conditions, plus actual role and mask counts. Use mandatory base sessions of Sources + four per condition + two as an explanatory denominator. |
| Repair and reuse | Repair cycles, objection and stage, affected and reused author outputs, exact-mask packet reuses, and receipt recoveries. Distinguish work avoided from repeat review required for a changed lock. |
| Blind agreement | Compare the two pre-adjudication graphs and exact Source/quote and same-edge proof agreement for every condition. Report disagreements and any lost or uncertain reading explicitly. |
| Adjudication and masking | Count disputes and adjudication sessions, mask reasons and independent responses, deleted proof atoms, surviving alternatives and custodian time. Include negative controls and unresolved shortcuts. |
| Time and usage | First reservation to determinate package per family and to the consolidated summary for the batch. Record queue and owner wait separately where available. Report token subsets and priced/unpriced attempts from receipts. |
| Scientific outcome | Technical gate passing, return, quarantine or unfinished, with defects and reason. Track owner admission as a subsequent decision tied to the dossier digest. |

Publish the three family outcomes and role-level counts even if no family
passes. For completed packages compare charged attempts and role counts
against the historical median and the closest serial family by Source and
condition count. Report the number of technically ready packages, then
the eventual number of human admissions. The routine or moderate planning
target is about 10–20 sessions. Exceeding it documents an efficiency
result and may exhaust the approved budget. It has no bearing on the
truth of the graph or eligibility for human admission. Report when the
evidence is mixed or insufficient.

Deterministic reuse covers checkpoint reads, exact input equivalence,
unchanged authors in any allowed repair, safe mask containment, validation,
and saved-ideal replay. Repeat blind readings and adjudication for each
condition and each affected lock. Preserve role-specific independence
even when a new packet is byte-identical. The batch worker dispatches a
job per mask assignment and reuses that job on verified resume. Count
prospective exact-mask consolidation only when a single precommitted
assignment independently answers all the relevant checks. Include
returned and quarantined attempts in the task total. Stop new submissions at the budget or a shared isolation halt.
