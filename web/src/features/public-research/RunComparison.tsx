import { OutcomeMatrix } from "../../shared/research/OutcomeMatrix";
import { useLocale } from "../../shared/locale";
import { PublishedPerformance } from "./PublishedPerformance";
import type { PublicRun, RunLabel } from "./types";
export const runName = (label: RunLabel) =>
  label === "A_prime" ? "A′" : label;
export const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
export function RunComparison({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  const baseline = runs.find(run => run.label === "A")!;
  const resolver = runs.find(run => run.label === "B")!;
  return (
    <section id="comparison" className="research-section research-evidence-band">
      <div className="research-band-content">
        <h2>{t("Experimental results")}</h2>
        <p>
          {t(
            "A is the extraction baseline. A′ deterministically replays the same frozen extractions without resolution. B adds constrained alias resolution to those extractions. A and A′ have equivalent outcomes; they are not independent replications.",
          )}
        </p>
        <p>{t("Baseline relationship micro-F1 was {baseline}*. With generative resolution it was {resolver}*. Select a retained Run to inspect its recorded score and coverage.", { baseline: percent(baseline.metrics.micro_f1), resolver: percent(resolver.metrics.micro_f1) })}</p>
        <PublishedPerformance runs={runs} />
        <p className="research-caveat">{t("* Small internal development benchmark. The resolver comparison was post-hoc and exploratory; two name corrections in one case accounted for the entire improvement.")}</p>
        <details className="research-recorded-metrics">
          <summary>{t("Recorded metric table")}</summary>
          <p className="research-table-hint">{t("Scroll horizontally to inspect all recorded columns.")}</p>
          <div
            className="research-table-scroll"
            role="region"
            aria-label={t("Run comparison")}
            tabIndex={0}
          >
            <OutcomeMatrix
              caption={t("Run comparison")}
              headings={[t("Metric"), `${t("Naive full-context baseline")} · A`, `${t("With generative entity resolution")} · B`]}
              rows={([
                ["True positives", "tp", false],
                ["False positives", "fp", false],
                ["False negatives", "fn", false],
                ["Relationship micro-F1", "micro_f1", true],
                ["Macro-F1", "macro_f1", true],
                ["Approved-quote provenance", "quote_accuracy", true],
                ["Source-pair attribution", "source_pair_accuracy", true],
              ] as const).map(([label, key, ratio]) => ({
                id: key,
                label: t(label),
                values: [baseline, resolver].map(run => ratio
                  ? `${percent(run.metrics[key])}${key === "micro_f1" ? "*" : ""}`
                  : run.metrics[key]),
              }))}
            />
          </div>
        </details>
        <p>
          {t(
            "Coverage is complete only when every planned Observation is scored. Pending, failed, uncertain and unavailable counts remain explicit below.",
          )}
        </p>
        {runs.map((run) => (
          <details key={run.label}>
            <summary>
              {t("Run {run} identity and coverage", { run: runName(run.label) })}
            </summary>
            <dl className="research-metadata">
              <dt>{t("Run ID")}</dt>
              <dd>{run.run_id}</dd>
              <dt>{t("Code revision")}</dt>
              <dd>{run.git_commit}</dd>
              <dt>{t("Plan digest")}</dt>
              <dd>{run.plan_digest}</dd>
              <dt>{t("Artifact digest")}</dt>
              <dd>{run.artifact_digest}</dd>
            </dl>
            <p>
              {t(
                "Pending: {pending}; failed: {failed}; uncertain: {uncertain}; unavailable: {unavailable}.",
                run.coverage,
              )}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
export function Provenance({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  return (
    <section id="provenance" className="research-section">
      <h2>{t("Provenance has two separate checks")}</h2>
      <p>
        {t(
          "Approved-quote provenance checks exact approved quotation text on correctly matched relationships. Source-pair attribution additionally checks the Source identity and quote together. These are recorded diagnostics with separate denominators, not general confidence scores.",
        )}
      </p>
      <div
        className="research-table-scroll"
        role="region"
        aria-label={t("Provenance results")}
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th>{t("Run")}</th>
              <th>{t("Approved-quote provenance")}</th>
              <th>{t("Source-pair attribution")}</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.label}>
                <th scope="row">{runName(run.label)}</th>
                <td>
                  {run.metrics.quote_passed} / {run.metrics.quote_assessed} ·{" "}
                  {percent(run.metrics.quote_accuracy)}
                </td>
                <td>
                  {run.metrics.source_pair_passed} /{" "}
                  {run.metrics.source_pair_assessed} ·{" "}
                  {percent(run.metrics.source_pair_accuracy)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        {t(
          "Relationship corrections change which relationships enter provenance assessment. The resolver did not repair quotations or Source attribution. An exact quote-boundary mismatch and a wrong Source are different failures; inspect the retained diagnostics with each relationship.",
        )}
      </p>
    </section>
  );
}
