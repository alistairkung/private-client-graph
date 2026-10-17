import { useLocale } from "../../shared/locale";
import type { PublicRun, RunLabel } from "./types";
export const runName = (label: RunLabel) =>
  label === "A_prime" ? "A′" : label;
export const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
export function RunComparison({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  return (
    <section id="comparison" className="research-section">
      <h2>{t("Three Runs, one paired comparison")}</h2>
      <p>
        {t(
          "A is the extraction baseline. A′ deterministically replays the same frozen extractions without resolution. B adds constrained alias resolution to those extractions. A and A′ have equivalent outcomes; they are not independent replications.",
        )}
      </p>
      <div
        className="research-table-scroll"
        role="region"
        aria-label={t("Run comparison")}
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th>{t("Run")}</th>
              <th>{t("Precision")}</th>
              <th>{t("Recall")}</th>
              <th>{t("Relationship micro-F1")}</th>
              <th>{t("Macro-F1")}</th>
              <th>{t("True positives")}</th>
              <th>{t("False positives")}</th>
              <th>{t("False negatives")}</th>
              <th>{t("Scored / planned")}</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.label}>
                <th scope="row">{runName(run.label)}</th>
                <td>{percent(run.metrics.micro_precision)}</td>
                <td>{percent(run.metrics.micro_recall)}</td>
                <td>{percent(run.metrics.micro_f1)}</td>
                <td>{percent(run.metrics.macro_f1)}</td>
                <td>{run.metrics.tp}</td>
                <td>{run.metrics.fp}</td>
                <td>{run.metrics.fn}</td>
                <td>
                  {run.coverage.scored} / {run.coverage.planned}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
