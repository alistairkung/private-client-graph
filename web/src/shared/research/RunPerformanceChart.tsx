import { useId, useState } from "react";
import { LayoutGroup, motion, useReducedMotion } from "motion/react";
import { researchText, type ResearchText } from "./presentation";
import "./run-performance-chart.css";

export type PerformanceRun = {
  id: string;
  displayName?: string;
  lifecycle: string | null;
  resolver: boolean;
  inputMode: string | null;
  model: string | null;
  recorded: boolean;
  f1: number | null;
  scoreState: string;
  coverage: { scored: number; planned: number };
  cost: { total: number | null; currency: string | null };
  scopeIdentity: string | null;
  eligibility: {
    f1_by_run: boolean;
    f1_vs_cost: boolean;
    f1_reasons: string[];
    cost_reasons: string[];
  };
};
export type PerformanceExperiment = { name: string; runIds: string[] };
export const metric = (value: number | null) =>
  value === null ? "Unavailable" : value.toFixed(3);
export function RunPerformanceChart({
  experiment,
  runs,
  selected,
  select,
  tactile = false,
  t = researchText,
}: {
  experiment: PerformanceExperiment;
  runs: PerformanceRun[];
  selected: string | null;
  select: (id: string) => void;
  tactile?: boolean;
  t?: ResearchText;
}) {
  const [tab, setTab] = useState<"run" | "cost">("run");
  const [inspected, setInspected] = useState<string | null>(null);
  const chartId = useId();
  const reducedMotion = useReducedMotion();
  const [inputMode, setInputMode] = useState("all");
  const runNumber = (id: string) => experiment.runIds.indexOf(id) + 1;
  const visible = runs.filter(
    (run) =>
      inputMode === "all" || run.inputMode === inputMode,
  );
  const eligible = visible.filter((run) =>
    tab === "run"
      ? run.eligibility.f1_by_run
      : run.eligibility.f1_vs_cost,
  );
  const maxCost = Math.max(
    ...eligible.map((run) => run.cost.total ?? 0),
    0.0001,
  );
  const tooltip = runs.find((run) => run.id === (inspected ?? selected));
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
            <span className="chart-tab-label">{t(value === "run" ? "F1 by Run" : "F1 vs Cost")}</span>
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
        <div className="chart-legend">
          <span>{t("F1 · 0–1")}</span>
          <span>◇ {t("No resolver")}　● {t("Generative resolver")}　○ {t("Provisional")}</span>
        </div>
        {!runs.length ? (
          <p className="chart-empty">
            {t("Run your first configuration to begin comparing results.")}
          </p>
        ) : (
          <>
            <div className="plot-area">
              {[1, 0.75, 0.5, 0.25, 0].map((value) => (
                <div
                  key={value}
                  className="plot-grid"
                  style={{ top: `${(1 - value) * 100}%` }}
                >
                  <span>{value.toFixed(2)}</span>
                </div>
              ))}
              {eligible.map((run) => {
                const index = runNumber(run.id) - 1;
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
                    aria-label={run.displayName
                      ? t("{name}, F1 {f1}, {state}, {scored}/{planned} scored", { name: run.displayName, f1: metric(run.f1), state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned })
                      : t("Run {run}, F1 {f1}, {state}, {scored}/{planned} scored", { run: index + 1, f1: metric(run.f1), state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned })}
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
                    {index + 1}
                  </span>
                ))}
            </div>
            <div className="plot-axis">
              {tab === "run"
                ? t("Run number within this experiment")
                : t("Estimated provider spend incurred by Run ({currency}) · 0–{max}", { currency: eligible[0]?.cost.currency ?? "USD", max: maxCost.toFixed(4) })}
            </div>
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
                {t("F1 {f1} · {state} · {scored}/{planned} scored", { f1: t(metric(tooltip.f1)), state: t(tooltip.scoreState), scored: tooltip.coverage.scored, planned: tooltip.coverage.planned })}
              </span>
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
        </div>
        {!!runs.length && (
          <div className="run-history-list" aria-label={t("All Runs")}>
            {runs.map((run) => (
              <div key={run.id}>
                <button
                  className="secondary"
                  aria-pressed={selected === run.id}
                  onClick={() => select(run.id)}
                >
                  {run.displayName ?? <>{t("Run {run}", { run: runNumber(run.id) })} ·{" "}
                    {!run.resolver ? t("No resolver") : t("Generative resolver")}</>}
                  <small>
                    {run.lifecycle && <>{t(run.lifecycle)} · </>}F1 {metric(run.f1)} ·{" "}
                    {t(run.scoreState)}
                  </small>
                </button>
                {!(tab === "run"
                  ? run.eligibility.f1_by_run
                  : run.eligibility.f1_vs_cost) && (
                    <small>
                      {(tab === "run"
                        ? run.eligibility.f1_reasons
                        : run.eligibility.cost_reasons
                      ).map(reason => t(reason)).join(" ")}
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
