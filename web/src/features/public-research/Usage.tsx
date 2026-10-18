import { useLocale } from "../../shared/locale";
import type { PublicCall, PublicRun } from "./types";
import { ResearchAccordion } from "./ResearchAccordion";
import { runName } from "./RunComparison";
export function Usage({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  const number = (value: number | null) =>
    value === null ? t("Unavailable") : value.toLocaleString();
  const price = (value: number | null) =>
    value === null ? t("Unpriced") : `USD ${value.toFixed(6)}`;
  return (
    <section id="usage" className="research-section">
      <h2>{t("Execution and resource usage")}</h2>
      <p>
        {t(
          "Cached tokens are included within input tokens, not additional tokens. Provider duration is summed provider time, not end-to-end wall time. Attempt counts include failures. Missing prices are explicitly Unpriced.",
        )}
      </p>
      <p id="research-usage-scroll-hint" className="research-table-hint">{t("Scroll horizontally to inspect all recorded columns.")}</p>
      <div
        className="research-table-scroll"
        role="region"
        aria-label={t("Run usage totals")}
        aria-describedby="research-usage-scroll-hint"
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th>{t("Run")}</th>
              <th>{t("Attempts")}</th>
              <th>{t("Input tokens")}</th>
              <th>{t("Output tokens")}</th>
              <th>{t("Cached tokens")}</th>
              <th>{t("Total tokens")}</th>
              <th>{t("Provider seconds")}</th>
              <th>{t("Recorded cost")}</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.label}>
                <th scope="row">{runName(run.label)}</th>
                <td>{run.usage.attempts}</td>
                <td>{number(run.usage.input_tokens)}</td>
                <td>{number(run.usage.output_tokens)}</td>
                <td>{number(run.usage.cached_tokens)}</td>
                <td>{number(run.usage.total_tokens)}</td>
                <td>{number(run.usage.provider_seconds)}</td>
                <td>{price(run.usage.cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        {t(
          "A′ made zero provider calls. B reused the retained A extractions; its recorded calls are resolution attempts only. Reused extraction is lineage, not newly executed usage.",
        )}
      </p>
      <ResearchAccordion items={runs.map(run => ({ id: run.label, title: t("Run {run}: {count} provider calls", { run: runName(run.label), count: run.usage.attempts }), content: <>
          <p className="research-id">{run.run_id}</p>
          {run.calls.length ? (
            <div className="research-call-list">
              {run.calls.map((call) => (
                <Call
                  key={call.attempt_id}
                  call={call}
                  number={number}
                  price={price}
                />
              ))}
            </div>
          ) : (
            <p>
              {t(
                "Zero provider calls. This control used deterministic replay.",
              )}
            </p>
          )}
        </> }))} />
    </section>
  );
}
function Call({
  call,
  number,
  price,
}: {
  call: PublicCall;
  number: (value: number | null) => string;
  price: (value: number | null) => string;
}) {
  const { t } = useLocale();
  const stage = call.stage === "extraction" ? t("Extraction") : t("Resolution");
  const status =
    call.status === "completed" || call.status === "succeeded"
      ? t("Completed")
      : call.status === "failed"
        ? t("Failed")
        : call.status;
  return (
    <ResearchAccordion items={[{ id: call.attempt_id, title: <>{call.case_id} · {stage} · {call.model ?? t("Unavailable")} · {status}</>, content: <>
      <dl className="research-metadata">
        <dt>{t("Attempt ID")}</dt>
        <dd>{call.attempt_id}</dd>
        <dt>{t("Run ID")}</dt>
        <dd>{call.run_id}</dd>
        <dt>{t("Completion status")}</dt>
        <dd>{status}</dd>
        <dt>{t("Input tokens")}</dt>
        <dd>{number(call.input_tokens)}</dd>
        <dt>{t("Output tokens")}</dt>
        <dd>{number(call.output_tokens)}</dd>
        <dt>{t("Cached tokens")}</dt>
        <dd>{number(call.cached_tokens)}</dd>
        <dt>{t("Provider seconds")}</dt>
        <dd>{number(call.provider_seconds)}</dd>
        <dt>{t("Recorded cost")}</dt>
        <dd>{price(call.cost)}</dd>
      </dl>
    </> }]} />
  );
}
