import { useId, useState } from "react";
import { LayoutGroup, motion, useReducedMotion } from "motion/react";
import { percentMetric, researchText, type ResearchText } from "./presentation";
import "./run-performance-chart.css";

export type PerformanceMetricOptions = Record<string, { label: string; scope?: string; description?: string }>;

type PerformanceMeasure = {
  value: number | null;
  label: string;
  coverage: PerformanceRun["coverage"];
  coverageLabel: string;
};

export type PerformanceRun = {
  id: string;
  displayName?: string;
  lifecycle: string | null;
  resolver: boolean;
  inputMode: string | null;
  model: string | null;
  recorded: boolean;
  f1: number | null;
  metricLabel?: string;
  measures?: Record<string, PerformanceMeasure>;
  coverageLabel?: string;
  scoreState: string;
  coverage: { scored: number; planned: number };
  cost: { total: number | null; currency: string | null };
  costBasis?: "verified_provider_estimate" | "reference_rate_estimate";
  fullPipelineCost?: boolean;
  scopeIdentity: string | null;
  eligibility: {
    f1_by_run: boolean;
    f1_vs_cost: boolean;
    f1_reasons: string[];
    cost_reasons: string[];
  };
};
export type PerformanceExperiment = { name: string; runIds: string[]; runNumbers?: Record<string, number> };
export const metric = (value: number | null) =>
  value === null ? "Unavailable" : value.toFixed(3);
export function RunPerformanceChart({
  experiment,
  runs,
  selected,
  select,
  tactile = false,
  metrics,
  t = researchText,
}: {
  experiment: PerformanceExperiment;
  runs: PerformanceRun[];
  selected: string | null;
  select: (id: string) => void;
  tactile?: boolean;
  metrics?: PerformanceMetricOptions;
  t?: ResearchText;
}) {
  const [tab, setTab] = useState<"run" | "cost">("run");
  const [inspected, setInspected] = useState<string | null>(null);
  const chartId = useId();
  const reducedMotion = useReducedMotion();
  const [inputMode, setInputMode] = useState("all");
  const [metricKey, setMetricKey] = useState<string | null>(null);
  const activeMetric = metrics ? metricKey ?? Object.keys(metrics)[0] : undefined;
  const metricOption = activeMetric ? metrics?.[activeMetric] : undefined;
  const metricName = metricOption?.label;
  const formatValue = metricName ? percentMetric : metric;
  const chartRuns = activeMetric
    ? runs.map((run) => withMetric(run, activeMetric, metricName ?? "Metric"))
    : runs;
  const runNumber = (id: string) => experiment.runNumbers?.[id] ?? experiment.runIds.indexOf(id) + 1;
  const visible = chartRuns.filter(
    (run) =>
      inputMode === "all" || run.inputMode === inputMode,
  );
  const isEligible = (run: PerformanceRun) =>
    run.f1 !== null && Number.isFinite(run.f1) && (tab === "run"
      ? run.eligibility.f1_by_run
      : run.eligibility.f1_vs_cost && run.cost.total !== null &&
        Number.isFinite(run.cost.total) && run.cost.total >= 0 && !!run.cost.currency);
  const candidates = visible.filter(isEligible);
  // Preserve the historical currency when those Runs are visible. With only
  // verified estimates, the first visible estimate sets the cost axis.
  const historicalCost = candidates.find((run) => !run.costBasis);
  const costCurrency = (historicalCost ?? candidates[0])?.cost.currency ?? "USD";
  const incompatibleCost = (run: PerformanceRun) =>
    tab === "cost" &&
    !!run.costBasis &&
    run.cost.currency !== costCurrency;
  const eligible = candidates.filter((run) => !incompatibleCost(run));
  const maxCost = Math.max(
    ...eligible.map((run) => run.cost.total ?? 0),
    0.0001,
  );
  const fullPipelineCost = !!metricName || eligible.some((run) => run.fullPipelineCost);
  const costAxis = !fullPipelineCost
    ? t("Estimated provider spend incurred by Run ({currency}) · 0–{max}", { currency: costCurrency, max: maxCost.toFixed(4) })
    : eligible.length > 0
      ? t("Estimated full pipeline cost ({currency}) · 0–{max}", { currency: costCurrency, max: maxCost.toFixed(4) })
      : "Estimated full pipeline cost";
  const showPlot = !metricName || eligible.length > 0;
  const tooltip = chartRuns.find((run) => run.id === (inspected ?? selected));
  return (
    <LayoutGroup id={chartId}><section className="research-visual run-chart" data-tactile={tactile || undefined} aria-label={t("Run history and performance")}>
      <div className="section-heading">
        <h2>{t("Run history & performance")}</h2>
        <span>
          {t(experiment.runIds.length === 1 ? "{count} Run retained" : "{count} Runs retained", { count: experiment.runIds.length })}
        </span>
      </div>
      {new Set(
        runs.map((run) => run.scopeIdentity).filter(Boolean),
      ).size > 1 && (
          <p className="scope-notice">
            {t("These Runs use different benchmark scopes. Inspect scope differences before comparing outcomes.")}
          </p>
        )}
      {metrics && (
        <div className="chart-filter chart-metric-filter">
          <label htmlFor={`${chartId}-metric`}>{t("Performance metric")}</label>
          <select
            id={`${chartId}-metric`}
            value={activeMetric}
            aria-describedby={metricOption?.scope ? `${chartId}-metric-scope` : undefined}
            onChange={(event) => setMetricKey(event.target.value)}
          >
            {Object.entries(metrics).map(([key, { label }]) => <option key={key} value={key}>{label}</option>)}
          </select>
          {metricOption?.scope && <small id={`${chartId}-metric-scope`}>{metricOption.scope}</small>}
        </div>
      )}
      <div className="chart-tabs" role="tablist" aria-label={t("Performance chart")}>
        {(["run", "cost"] as const).map((value) => (
          <button
            key={value}
            id={`${chartId}-${value}`}
            role="tab"
            aria-selected={tab === value}
            aria-controls={`${chartId}-plot`}
            tabIndex={tab === value ? 0 : -1}
            onKeyDown={(event) => {
              if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
                event.preventDefault();
                setTab(value === "run" ? "cost" : "run");
                document
                  .getElementById(
                    `${chartId}-${value === "run" ? "cost" : "run"}`,
                  )
                  ?.focus();
              }
            }}
            onClick={() => setTab(value)}
          >
            {tactile && tab === value && <motion.i
              className="chart-tab-surface" aria-hidden="true"
              layoutId={reducedMotion ? undefined : "chart-tab"}
              initial={false}
              transition={{ type: "spring", stiffness: 1218, damping: 70 }}
            />}
            <span className="chart-tab-label">{metricName
              ? (value === "run" ? "By Run" : "Vs Cost")
              : t(value === "run" ? "F1 by Run" : "F1 vs Cost")}</span>
          </button>
        ))}
      </div>
      <div
        id={`${chartId}-plot`}
        role="tabpanel"
        aria-labelledby={`${chartId}-${tab}`}
      >
        <label className="chart-filter">
          {t("Input mode")}
          <select
            value={inputMode}
            onChange={(event) => setInputMode(event.target.value)}
          >
            <option value="all">{t("All inputs · Discrete points")}</option>
            <option value="saved">{t("Saved extraction")}</option>
            <option value="fresh">{t("Fresh extraction")}</option>
          </select>
        </label>
        {metricName && <h3 className="chart-plot-title">{metricName} {tab === "run" ? "by Run" : "vs Cost"}</h3>}
        <div className="chart-legend">
          <span>{metricName ? `${metricName} (%)` : eligible.find(run => run.metricLabel)?.metricLabel ?? t("F1 · 0–1")}</span>
          <span>◇ {t("No resolver")}　● {t("Generative resolver")}　○ {t("Provisional")}</span>
        </div>
        {tab === "cost" && eligible.some((run) => run.costBasis === "reference_rate_estimate") && (
          <p className="scope-notice">{t("Reference-rate estimates use retained token usage at the configured DeepSeek rates. Actual charges can differ.")}</p>
        )}
        {!runs.length ? (
          <p className="chart-empty">
            {t("Run your first configuration to begin comparing results.")}
          </p>
        ) : (
          <>
            {showPlot && <div className="plot-area">
              {[1, 0.75, 0.5, 0.25, 0].map((value) => (
                <div
                  key={value}
                  className="plot-grid"
                  style={{ top: `${(1 - value) * 100}%` }}
                >
                  <span>{metricName ? `${value * 100}%` : value.toFixed(2)}</span>
                </div>
              ))}
              {eligible.map((run) => {
                const index = experiment.runIds.indexOf(run.id);
                const number = runNumber(run.id);
                const x =
                  tab === "run"
                    ? (index + 1) / (experiment.runIds.length + 1)
                    : 0.05 + (0.9 * (run.cost.total ?? 0)) / maxCost;
                return (
                  <button
                    key={run.id}
                    className={`chart-point ${run.resolver ? "resolved" : "baseline"} ${run.scoreState === "provisional" ? "provisional" : ""}`}
                    style={{
                      left: `${x * 100}%`,
                      top: `${(1 - (run.f1 ?? 0)) * 100}%`,
                    }}
                    aria-label={run.metricLabel
                      ? `${run.displayName ?? t("Run {run}", { run: number })}, ${run.metricLabel} ${formatValue(run.f1)}, ${t(run.scoreState)}, ${run.coverage.scored}/${run.coverage.planned} ${run.coverageLabel ?? ""}`
                      : run.displayName
                        ? t("{name}, F1 {f1}, {state}, {scored}/{planned} scored", { name: run.displayName, f1: metric(run.f1), state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned })
                        : t("Run {run}, F1 {f1}, {state}, {scored}/{planned} scored", { run: number, f1: metric(run.f1), state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned })}
                    aria-pressed={selected === run.id}
                    aria-describedby={`${chartId}-tooltip`}
                    onFocus={() => setInspected(run.id)}
                    onMouseEnter={() => setInspected(run.id)}
                    onMouseLeave={() => setInspected(null)}
                    onBlur={() => setInspected(null)}
                    onClick={() => select(run.id)}
                  >
                    {tactile && selected === run.id && <motion.i
                      className="chart-selection-ring" aria-hidden="true"
                      initial={reducedMotion ? false : { opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: reducedMotion ? 0 : 0.08 }}
                    />}
                    <span />
                  </button>
                );
              })}
              {tab === "run" &&
                experiment.runIds.map((id, index) => (
                  <span
                    key={id}
                    className="plot-tick"
                    style={{
                      left: `${((index + 1) / (experiment.runIds.length + 1)) * 100}%`,
                    }}
                  >
                    {runNumber(id)}
                  </span>
                ))}
            </div>}
            {showPlot && <div className="plot-axis">
              {tab === "run" ? t("Run number within this experiment") : costAxis}
            </div>}
            {!eligible.length && (
              <p>
                {t("No Runs are eligible for this chart yet. Inspect their status below.")}
              </p>
            )}
          </>
        )}
        <p className="chart-footnote">
          {t("{plotted}/{total} Runs plotted · Discrete points; no trend or improvement is implied across different scopes.", { plotted: eligible.length, total: experiment.runIds.length })}
        </p>
        <div
          id={`${chartId}-tooltip`}
          className="chart-inspection"
          aria-live="polite"
        >
          {tooltip ? (
            <>
              <strong>
                {experiment.name} · {tooltip.displayName ?? t("Run {run}", { run: runNumber(tooltip.id) })}
              </strong>
              <span>
                {tooltip.metricLabel
                  ? `${tooltip.metricLabel}: ${t(formatValue(tooltip.f1))} · ${t(tooltip.scoreState)}${tooltip.coverageLabel ? ` · ${tooltip.coverage.scored}/${tooltip.coverage.planned} ${tooltip.coverageLabel}` : ""}`
                  : t("F1 {f1} · {state} · {scored}/{planned} scored", { f1: t(metric(tooltip.f1)), state: t(tooltip.scoreState), scored: tooltip.coverage.scored, planned: tooltip.coverage.planned })}
              </span>
              {tab === "cost" && tooltip.costBasis === "verified_provider_estimate" && (
                <span>
                  {t(metricName ? "Estimated full pipeline cost · {currency} {amount}" : "Estimated provider spend · {currency} {amount}", {
                    currency: tooltip.cost.currency ?? "",
                    amount: String(tooltip.cost.total),
                  })}
                </span>
              )}
              {tab === "cost" && tooltip.costBasis === "reference_rate_estimate" && (
                <span>{t("Reference-rate estimate · {currency} {amount}", {
                  currency: tooltip.cost.currency ?? "",
                  amount: tooltip.cost.total?.toFixed(4) ?? "",
                })}</span>
              )}
              <small>{tooltip.id}</small>
              <p>
                {tooltip.recorded
                  ? t("Recorded demonstration · Not live quality · ")
                  : ""}
                {t("{mode} inputs · {model} · Scope {scope}", { mode: t(tooltip.inputMode ?? "Unavailable"), model: tooltip.model ?? t("Unavailable"), scope: tooltip.scopeIdentity ?? t("unavailable") })}
              </p>
            </>
          ) : (
            <span>{t("Focus or select a point to inspect its Run.")}</span>
          )}
          {metricOption?.description && <p>{metricOption.description}</p>}
        </div>
        {!!runs.length && (
          <div className="run-history-list" aria-label={t("All Runs")}>
            {chartRuns.map((run) => (
              <div key={run.id}>
                <button
                  className="secondary"
                  aria-pressed={selected === run.id}
                  onClick={() => select(run.id)}
                >
                  {run.displayName ?? <>{t("Run {run}", { run: runNumber(run.id) })} ·{" "}
                    {!run.resolver ? t("No resolver") : t("Generative resolver")}</>}
                  <small>
                    {run.lifecycle && <>{t(run.lifecycle)} · </>}{metricName ?? "F1"} {formatValue(run.f1)} ·{" "}
                    {t(run.scoreState)}
                  </small>
                </button>
                {(!isEligible(run) || incompatibleCost(run)) && (
                    <small>
                      {incompatibleCost(run)
                        ? t("Estimated provider spend is in {currency}. This plot uses {plotCurrency}.", {
                            currency: run.cost.currency ?? "",
                            plotCurrency: costCurrency,
                          })
                        : metricName && run.f1 === null
                          ? t("This metric is unavailable for this Run.")
                          : (tab === "run" ? run.eligibility.f1_reasons : run.eligibility.cost_reasons)
                            .map(reason => t(reason)).join(" ")}
                    </small>
                  )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section></LayoutGroup>
  );
}

function withMetric(run: PerformanceRun, key: string, label: string): PerformanceRun {
  const measure = run.measures?.[key];
  return {
    ...run,
    f1: measure?.value ?? null,
    metricLabel: measure?.label ?? label,
    coverage: measure?.coverage ?? { scored: 0, planned: 0 },
    coverageLabel: measure?.coverageLabel,
    scoreState: measure ? run.scoreState : "unavailable",
  };
}
