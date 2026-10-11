# Research Workbench: Case investigation

> Approved workspace revision (2026-10-11): see [the continuous workspace implementation handoff](research-workbench-approved-workspace.md) for Connector rail with inline settings and Comparison bench B. Earlier functional and safety contracts remain in force.

Status: selected structural direction; detailed design proposed for approval. The user selected `navigator` / **Case investigation** in the Impeccable decision page. This document does not authorize React implementation or paid execution. It develops the [accepted functional handoff](research-workbench.md) without changing its architecture.

## Job and design thesis

The researcher arrives with a hypothesis or an unexpected result and needs to establish what changed, which observations support that conclusion, and where a relationship diverged from ground truth. This is an **Operate** surface: repeated investigation, precise comparisons and safe explicit execution take precedence over presentation.

Keep the case list visible while the researcher moves through paired results, relationship errors and exact Evidence. The defining interaction is a continuous selection chain: **metric → sample/repetition → relationship → Evidence → Source**. Each step preserves the parent context; going back restores the previous selection and filters. The graph is an optional inspection view, not the mandatory gateway to an error.

## Visual direction

Extend PCG's existing identity rather than creating a separate brand. Use a restrained ledger-green header, warm paper workspace and white working surfaces separated by fine rules. Public Sans carries controls, labels, prose and tabular numerals; reserve the existing Newsreader face for modest page titles. Avoid oversized editorial type, decorative textures, metric-card walls and ornamental motion.

Use ledger green for primary actions and current selection, muted ink for secondary metadata, burgundy for errors and visible keyboard focus, and gold only for exact Evidence highlights. Baseline and treatment have persistent text labels rather than relying on red/green or implying that treatment is better. Pair every status colour with a readable label. Metrics use aligned numeric columns, stable precision and explicit units; unavailable values read “Unavailable” with a reason.

Controls follow PCG's existing modest radii and conventional form/table vocabulary. Give primary controls at least 44px targets; density comes from alignment and concise labels, not illegible text or tiny controls. Final contrast and focus visibility are implementation acceptance checks, not assumed from token names.

## Application shell and navigation

A compact shared header identifies **Private Client Graph / Research**, marks the local synthetic context, and provides **Experiments** and **New experiment** navigation when execution capabilities are available. Results belong to an experiment, not to a global “Results” destination with no selected run. Read-only composition omits creation/execution navigation entirely.

Opening a result establishes a breadcrumb back to the filtered history and a compact experiment header containing identity, execution mode, lifecycle, input cohort and configuration. A secondary detail disclosure carries full hashes, code/dependency provenance and artifact integrity. Never bury interrupted or uncertain execution behind that disclosure.

Within an experiment, use three explicit views: **Overview**, **Investigate**, and **Execution & artifacts**. Overview supports aggregate comparison; Investigate is the persistent case workspace; Execution & artifacts holds operational detail. These are views over one result, not new domain entities.

## Experiment history

Lead with a searchable table, not summary tiles. Place search and filters directly above the rows they affect. Each row shows experiment identity/date, cases, resolver/input mode, model, execution status and scored/planned coverage. Distinguish execution completion from quality: a completed experiment can contain missing relationships or failed observations.

Use explicit selection checkboxes to choose two historical experiments for comparison. A nearby comparison action names the selected pair. The comparison starts by disclosing matched inputs and differences in code/configuration, then exposes only server-supported paired results. Unmatched observations remain inspectable under an explicitly labelled group; never hide them to improve apparent coverage.

Open rows through a named experiment link, preserving normal browser navigation. Long identities wrap or expose full selectable text rather than making hover the only way to inspect them. History empty state explains that retained experiment artifacts will appear after indexing; a filtered-empty state offers “Clear filters.” Neither invents upload or import capabilities.

## Experiment configuration

Use one working form with three ordered sections: **Inputs**, **Pipeline & repetitions**, and **Review execution**. On wide screens a persistent summary sits beside the form; on narrow screens it follows the relevant fields and precedes the final action. It is a live server-provided plan summary, not a separate wizard or client-side budget calculator.

- Inputs select repository-owned cases and saved extraction snapshots or fresh extraction. Show snapshot provenance and cohort beside the selection. Fresh extraction sample count is separate from resolver repetitions.
- Pipeline configuration exposes only supported capabilities. Baseline is labelled “No resolution”; treatment identifies its actual resolver. Model controls follow backend capabilities. Explain directly beside input mode that saved extraction plus generative resolution can still make paid calls.
- Review shows maximum extraction calls, maximum resolution calls, full matrix maximum, task usage/remaining allowance and the proposed invocation bound. Monetary estimates have units, pricing provenance and unknowns; never imply a call cap guarantees a dollar cap.

“Review frozen plan” freezes configuration without starting execution. The resulting read-only plan retains case/configuration details and displays its digest with access to the full value. “Edit configuration” returns to an editable proposal and clearly invalidates prior approval. Existing immutable plans/results are never overwritten.

For deterministic work, the final action says **Run replay** or **Run recorded demonstration**, as appropriate. For live work, an explicit approval section states the bounded new allowance and task identity; **Authorize and start** applies only to that frozen plan. This inline review replaces a vague “Are you sure?” dialog. While submitting, disable duplicate actions and show the server's outcome. Approval failure never looks like a running experiment.

## Results: the selected Case investigation structure

On a wide desktop, keep three aligned working areas below the experiment context:

1. **Case navigator:** a compact left column listing cases and extraction samples, with outcome filters and scored/planned coverage. Group by cohort and preserve predictable case order; do not dynamically reorder during execution. Selection is visible in text and shape as well as colour.
2. **Relationship investigation:** the main working column starts with the selected sample and repetition, then a compact baseline/treatment metric table. Below it, filters expose missing, extra and provenance-failing relationships alongside all scored relationships. Show endpoint names, relationship type and which configuration produced the outcome.
3. **Evidence inspector:** a generously sized right column follows the selected relationship. Show expected and predicted relationship/Evidence separately, then exact quotations and a selectable Source passage with the relevant quote highlighted. A missing prediction explicitly says “No predicted relationship”; do not create synthetic Evidence to fill the space.

The paired metric table shows baseline, treatment and backend-supplied delta with sample coverage. Selecting an error count opens the corresponding relationship filter without losing the sample/repetition selection. A selected relationship exposes the evaluator's recorded outcome; descriptive copy must not invent a causal explanation the artifact does not contain.

Selecting “View in Source” reveals the exact quote in context. Repeated occurrences are not unique citations: retain Evidence identity by Source and exact text, indicate multiple matches where applicable, and do not claim an authoritative occurrence. Highlighted content remains selectable text. Expected and predicted quotations are labelled even when their text matches.

Switching case or repetition preserves a relationship selection only when its identity remains valid. Otherwise clear the inspector and explain “Select a relationship in this result,” rather than showing stale Evidence. The optional Canonical Graph view synchronizes relationship selection using existing identities and presentation conventions; it does not calculate evaluation status.

Overview presents aggregate comparison and cohort/sample coverage in aligned tables. Metric links lead into Investigate. Execution & artifacts presents provider attempts, stage failures, usage/cost/latency and artifact provenance, distinguishing experiment spend from hypothetical single-pipeline estimates.

## Running, interruption and exceptional states

| State | Presentation and permitted action |
| --- | --- |
| Running | Stable status strip names current work and completed/planned counts; existing results remain inspectable. “Stop after current attempt” is explicit. No invented percentage if total progress is unknown. |
| Stop requested | “Stopping after the current attempt.” Prevent repeat submission; never claim provider cancellation or refund. |
| Interrupted | Persistent explanation that execution did not resume. Show uncertain attempts and their budget effect; “Review continuation” opens the remaining plan and allowance for explicit approval. |
| Another experiment active | Link to that run; disable start with a reason. Do not offer a queue. |
| Provider/parse/graph/evaluation failure | Name the recorded stage and retained outputs. No generic retry action, fallback success or zero-quality score. |
| Unavailable diagnostics/cost | State the missing annotation, usage or pricing reason supplied by the API. |
| Missing/corrupt artifact | Preserve discoverable identity and integrity status; explain which result cannot be inspected. No execution action on imported history. |
| Code/ledger/approval mismatch | Explain the backend rejection and keep execution disabled; do not offer an accounting reset. |
| Loading/read failure | Preserve context with bounded placeholders or a local read error. Read retry is distinct from prohibited automatic provider retry. |

Browser closure does not stop a run. State this beside active execution once, without modal interruption. Updates should not steal focus, scroll the document, reorder observations, or automatically open new results.

## Responsive and accessible behaviour

Desktop uses the three working areas while they remain readable. At intermediate widths, the case list becomes a collapsible labelled navigator and relationship/Evidence inspection retains two columns. At narrow widths, use a linear case → relationship → Evidence sequence with explicit back controls and preserved selection; do not shrink three columns onto a phone. Paired values stack under persistent Baseline/Treatment labels. Configuration remains available without requiring a desktop-only budget preview.

Use native links, buttons, labelled inputs, tables and disclosures. Keyboard order follows navigation → case → result → Evidence. Scope polite live announcements to selection/results updates; reserve alerts for actionable failures. Visible focus must remain unobscured by sticky controls. Error filters expose their active state programmatically. Respect reduced motion; only brief state feedback is useful, never animated counters or page-load choreography.

Plan for one case and one repetition through multi-case histories with long names, many relationship errors and long exact quotations. Lists can scroll/paginate through explicit backend contracts; never add a truncation rule that hides results. Initial design acceptance checks include 1440px desktop, 1024px compact desktop and 390px narrow layouts, plus keyboard and zoom/reflow review.

## Implementation handoff and approval

Reuse existing font assets, brand mark, graph presentation, Source and Evidence components where their behaviour matches this design. Keep research-specific evaluation filters and operational controls within cohesive research features. Do not force practitioner components to acquire research authority or create a generic component framework.

Implement this design in the existing three slices: history/read-only inspection (#101), deterministic configuration and lifecycle (#102), and explicit bounded live controls (#103). API contracts supply all scoring, comparison, accounting and lifecycle truth. If required information is absent, surface a concrete contract gap with regression tests rather than fabricate values in React.

Design approval covers this visual/interaction direction and its responsive/state behaviour. Implementation approval remains separate. The approval review should verify that a researcher can find an experiment, compare matched results, reach an individual error and its exact Evidence, then understand and approve a bounded next experiment without losing the distinction between scientific outcomes and execution status.
