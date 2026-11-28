import { useId, useState, type ComponentProps, type ReactNode } from "react";
import { LayoutGroup, motion, useReducedMotion } from "motion/react";
import { metric, researchText, type ResearchText } from "./presentation";
import { RunPerformancePlot, type PlotPoint, type PlotTick } from "./RunPerformancePlot";
import { PerformanceRunTable, type PerformanceTableRun } from "./PerformanceRunTable";
import "./run-performance-chart.css";

export { metric } from "./presentation";
export type PerformanceMetricOptions = Record<string, { label: string; scope?: string }>;

type MetricDefinition = { key: string; label: string; description?: string };
type Comparison = {
  metrics: PerformanceMetricOptions;
  adjusted: MetricDefinition;
  supporting: readonly MetricDefinition[];
  loadingEvidence: boolean;
  refreshEvidence?: () => void;
};

type PerformanceMeasure = {
  value: number | null;
  label: string;
  coverage?: PerformanceRun["coverage"];
  coverageLabel?: string;
  basis?: string;
  qualifier?: string;
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
  scoreQualifier?: string;
  scoreBasis?: string;
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
type ChartView = "run" | "cost";
type ComparisonSeries = {
  definition: MetricDefinition;
  scores: PerformanceRun[];
  points: PlotPoint[];
  loading: boolean;
  empty: string;
};

export function RunPerformanceChart({
  experiment, runs, selected, select, tactile = false, showRunIdentifiers = false, comparison, t = researchText,
}: {
  experiment: PerformanceExperiment;
  runs: PerformanceRun[];
  selected: string | null;
  select: (id: string) => void;
  tactile?: boolean;
  showRunIdentifiers?: boolean;
  comparison?: Comparison;
  t?: ResearchText;
}) {
  const [tab, setTab] = useState<ChartView>("run");
  const [inspected, setInspected] = useState<string | null>(null);
  const [inputMode, setInputMode] = useState("all");
  const [metricKey, setMetricKey] = useState<string | null>(null);
  const [metricTab, setMetricTab] = useState("f1");
  const chartId = useId();
  const graphKey = metricKey ?? (comparison && Object.keys(comparison.metrics)[0]);
  const graphMetric = graphKey ? comparison?.metrics[graphKey] : undefined;
  const supportingMetric = comparison?.supporting.find(metric => metric.key === metricTab);
  const visible = runs.filter(run => inputMode === "all" || run.inputMode === inputMode);
  const legacyCandidates = comparison ? [] : visible.filter(run => isEligible(run, tab));
  const pricedRuns = comparison && tab === "cost"
    ? visible.filter(run => run.measures && run.eligibility.f1_vs_cost && hasCost(run))
    : legacyCandidates;
  const costs = costScale(pricedRuns, tab);
  const legacyEligible = legacyCandidates.filter(run => !costs.incompatible(run));
  const positionForRun = (id: string) => (experiment.runIds.indexOf(id) + 1) / (experiment.runIds.length + 1);
  const runNumber = (id: string) => experiment.runNumbers?.[id] ?? experiment.runIds.indexOf(id) + 1;
  const costTicks = comparison && tab === "cost" ? costAxisTicks(costs.max) : undefined;
  const ticks = costTicks?.ticks ?? (tab === "run" ? runTicks(experiment.runIds, comparison ? 5 : Infinity, positionForRun, runNumber) : []);
  const axis = tab === "run"
    ? t("Run number within this experiment")
    : comparison
      ? `Estimated full pipeline cost (${costs.currency})`
      : legacyCostAxis(legacyEligible, costs.currency, costs.max, t);
  const points = (items: PerformanceRun[]): PlotPoint[] => items.map(run => ({
    run, number: runNumber(run.id),
    x: tab === "run" ? positionForRun(run.id) :
      costTicks ? (run.cost.total ?? 0) / costTicks.max : 0.05 + 0.9 * (run.cost.total ?? 0) / costs.max,
  }));
  const plotProps = { ticks, axis, selected, select, t };
  const empty = t("No Runs are eligible for this chart yet. Inspect their status below.");
  const activeMetrics = supportingMetric ? [supportingMetric] : comparison && graphKey && graphMetric
    ? [{ key: graphKey, label: graphMetric.label, description: graphMetric.scope }, comparison.adjusted]
    : [];
  const series = activeMetrics.map(definition => {
    const scores = visible.map(run => withMetric(run, definition.key));
    const eligible = scores.filter(run => isEligible(run, tab) && !costs.incompatible(run));
    return {
      definition, scores, points: points(eligible),
      loading: definition.key !== graphKey && !!comparison?.loadingEvidence,
      empty: definition.key === graphKey ? empty : `No ${definition.label} scores are available to plot.`,
    };
  });
  const plottedRuns = comparison ? series.flatMap(item => item.points.map(point => point.run)) : legacyEligible;
  const references = tab === "cost" && plottedRuns.some(run => run.costBasis === "reference_rate_estimate");
  const scopesDiffer = new Set(runs.map(run => run.scopeIdentity).filter(Boolean)).size > 1;
  const tooltip = runs.find(run => run.id === (inspected ?? selected));
  const axisTabs: ChartTab<ChartView>[] = [
    { key: "run", label: comparison ? "By Run" : t("F1 by Run") },
    { key: "cost", label: comparison ? "Vs Cost" : t("F1 vs Cost") },
  ];
  const metricTabs = comparison ? [{ key: "f1", label: "F1 scores" }, ...comparison.supporting] : [];
  const metricTabId = `${chartId}-metric`;
  const metricPanelId = `${metricTabId}-panel`;
  const metricPanel = comparison ? {
    id: metricPanelId, role: "tabpanel", "aria-labelledby": `${metricTabId}-${metricTab}`,
  } : {};

  const inputFilter = <label className="chart-filter">
    {t("Input mode")}
    <select value={inputMode} onChange={event => setInputMode(event.target.value)}>
      <option value="all">{t(comparison ? "All inputs" : "All inputs · Discrete points")}</option>
      <option value="saved">{t("Saved extraction")}</option>
      <option value="fresh">{t("Fresh extraction")}</option>
    </select>
  </label>;

  return (
    <LayoutGroup id={chartId}>
      <section className={`research-visual run-chart${comparison ? " run-chart-comparison" : ""}`} data-tactile={tactile || undefined} aria-label={t("Run history and performance")}>
        <div className="section-heading">
          <h2>{t("Run history & performance")}</h2>
          <span>{t(experiment.runIds.length === 1 ? "{count} Run retained" : "{count} Runs retained", { count: experiment.runIds.length })}</span>
        </div>
        {scopesDiffer && <p className="scope-notice">
          {t("These Runs use different benchmark scopes. Inspect scope differences before comparing outcomes.")}
        </p>}
        {comparison && <ChartTabs
          id={metricTabId} panelId={metricPanelId} label="Performance metrics"
          className="performance-metric-tabs" tabs={metricTabs} selected={metricTab} select={setMetricTab}
        />}
        <div {...metricPanel}>
          <div className={comparison ? "comparison-controls" : undefined}>
            <ChartTabs
              id={chartId} panelId={`${chartId}-plot`} label={t("Performance chart")}
              className="chart-tabs" tabs={axisTabs} selected={tab} select={setTab} tactile={tactile}
            />
            {comparison && <div className="comparison-filters">
              {inputFilter}
              {!supportingMetric && <label className="chart-filter">
                {t("Graph metric")}
                <select value={graphKey} onChange={event => setMetricKey(event.target.value)}>
                  {Object.entries(comparison.metrics).map(([key, { label }]) => <option key={key} value={key}>{label}</option>)}
                </select>
              </label>}
            </div>}
          </div>
          <div id={`${chartId}-plot`} role="tabpanel" aria-labelledby={`${chartId}-${tab}`}>
            {!comparison && inputFilter}
            {comparison ? (
              visible.length ? <>
                <div className="comparison-legend" aria-label="Resolver configurations">
                  <span><i className="performance-marker baseline" aria-hidden="true" />{t("No resolver")}</span>
                  <span><i className="performance-marker" aria-hidden="true" />{t("Generative resolver")}</span>
                  {plottedRuns.some(run => run.scoreState === "provisional") &&
                    <span><i className="performance-marker provisional" aria-hidden="true" />{t("Provisional")}</span>}
                </div>
                <ComparisonResults
                  series={series}
                  showSharedQualifier={!!supportingMetric}
                  plotProps={plotProps}
                  costNote={references && <CostNote t={t} />}
                  rows={visible.map(run => ({
                    run, number: runNumber(run.id),
                    costIssue: tab === "cost" ? exclusionReason(run, tab, costs.incompatible(run), costs.currency, t) : "",
                  }))}
                />
                {comparison.refreshEvidence && <button className="secondary comparison-refresh" onClick={comparison.refreshEvidence}>
                  Refresh evidence scores
                </button>}
              </> : <p className="chart-empty" role="status">No Runs match this input mode.</p>
            ) : (
              <>
                <div className="chart-legend">
                  <span>{legacyEligible.find(run => run.metricLabel)?.metricLabel ?? t("F1 · 0–1")}</span>
                  <span>◇ {t("No resolver")}　● {t("Generative resolver")}　○ {t("Provisional")}</span>
                </div>
                {references && <CostNote t={t} />}
                {!runs.length ? <p className="chart-empty">{t("Run your first configuration to begin comparing results.")}</p> : <>
                  <RunPerformancePlot
                    {...plotProps}
                    points={points(legacyEligible)}
                    inspect={setInspected}
                    tooltipId={`${chartId}-tooltip`}
                    tactile={tactile}
                  />
                  {!legacyEligible.length && <p>{empty}</p>}
                </>}
                <p className="chart-footnote">
                  {t("{plotted}/{total} Runs plotted · Discrete points; no trend or improvement is implied across different scopes.", {
                    plotted: legacyEligible.length, total: experiment.runIds.length,
                  })}
                </p>
                <RunInspection
                  id={`${chartId}-tooltip`} run={tooltip} name={experiment.name}
                  number={tooltip ? runNumber(tooltip.id) : 0} tab={tab} showRunIdentifiers={showRunIdentifiers} t={t}
                />
                {!!runs.length && <div className="run-history-list" aria-label={t("All Runs")}>
                  {runs.map(run => (
                    <div key={run.id}>
                      <button className="secondary" aria-pressed={selected === run.id} onClick={() => select(run.id)}>
                        {run.displayName ?? <>{t("Run {run}", { run: runNumber(run.id) })} · {t(run.resolver ? "Generative resolver" : "No resolver")}</>}
                        <small>{run.lifecycle && <>{t(run.lifecycle)} · </>}F1 {metric(run.f1)} · {t(run.scoreState)}</small>
                      </button>
                      {(!isEligible(run, tab) || costs.incompatible(run)) &&
                        <small>{exclusionReason(run, tab, costs.incompatible(run), costs.currency, t)}</small>}
                    </div>
                  ))}
                </div>}
              </>
            )}
          </div>
        </div>
      </section>
    </LayoutGroup>
  );
}

function ComparisonResults({ series, showSharedQualifier, plotProps, rows, costNote }: {
  series: ComparisonSeries[];
  showSharedQualifier: boolean;
  plotProps: Pick<ComponentProps<typeof RunPerformancePlot>, "ticks" | "axis" | "selected" | "select" | "t">;
  rows: PerformanceTableRun[];
  costNote: ReactNode;
}) {
  const sharedQualifier = showSharedQualifier ? commonQualifier(series[0]?.scores ?? []) : undefined;
  return (
    <>
      <div className="comparison-plots" data-paired={series.length > 1 || undefined}>
        {series.map(({ definition, points, loading, empty }) => (
          <RunPerformancePlot
            key={definition.key}
            {...plotProps}
            title={definition.label}
            description={definition.description}
            note={sharedQualifier === "Exact-only" ? "Exact-only evaluation" : sharedQualifier}
            points={points}
            message={points.length ? undefined : loading ? `Loading ${definition.label} scores…` : empty}
          />
        ))}
      </div>
      {costNote}
      <PerformanceRunTable
        columns={series.map(({ definition }) => ({ key: definition.key, label: definition.label }))}
        rows={rows.map((row, index) => ({
          ...row,
          scores: series.map(({ definition, scores, loading }) => {
            const score = scores[index];
            return {
              key: definition.key,
              value: score.f1,
              basis: score.scoreBasis,
              qualifier: sharedQualifier ? undefined : score.scoreQualifier,
              loading: loading && row.run.scoreState === "complete",
            };
          }),
        }))}
        selected={plotProps.selected}
        select={plotProps.select}
      />
    </>
  );
}

function commonQualifier(scores: PerformanceRun[]) {
  const qualifiers = new Set(scores.filter(run => run.f1 !== null).map(run => run.scoreQualifier));
  return qualifiers.size === 1 ? qualifiers.values().next().value : undefined;
}

type ChartTab<Key extends string> = { key: Key; label: string };

function ChartTabs<Key extends string>({ id, panelId, label, className, tabs, selected, select, tactile = false }: {
  id: string; panelId: string; label: string; className: string;
  tabs: ChartTab<Key>[]; selected: Key; select: (tab: Key) => void; tactile?: boolean;
}) {
  const reducedMotion = useReducedMotion();
  return (
    <div className={className} role="tablist" aria-label={label}>
      {tabs.map(({ key, label: tabLabel }, index) => (
        <button
          key={key}
          type="button"
          id={`${id}-${key}`}
          role="tab"
          aria-selected={selected === key}
          aria-controls={panelId}
          tabIndex={selected === key ? 0 : -1}
          onKeyDown={event => {
            const nextIndex = nextTabIndex(event.key, index, tabs.length);
            if (nextIndex === null) return;
            event.preventDefault();
            const next = tabs[nextIndex].key;
            select(next);
            document.getElementById(`${id}-${next}`)?.focus();
          }}
          onClick={() => select(key)}
        >
          {tactile && selected === key && <motion.i
            className="chart-tab-surface" aria-hidden="true"
            layoutId={reducedMotion ? undefined : "chart-tab"}
            initial={false}
            transition={{ type: "spring", stiffness: 1218, damping: 70 }}
          />}
          <span className="chart-tab-label">{tabLabel}</span>
        </button>
      ))}
    </div>
  );
}

function nextTabIndex(key: string, index: number, count: number) {
  switch (key) {
    case "ArrowLeft": return (index + count - 1) % count;
    case "ArrowRight": return (index + 1) % count;
    case "Home": return 0;
    case "End": return count - 1;
    default: return null;
  }
}

function RunInspection({ id, run, name, number, tab, showRunIdentifiers, t }: {
  id: string; run?: PerformanceRun; name: string; number: number; tab: ChartView;
  showRunIdentifiers: boolean; t: ResearchText;
}) {
  return (
    <div id={id} className="chart-inspection" aria-live="polite">
      {run ? <>
        <strong>{name} · {run.displayName ?? t("Run {run}", { run: number })}</strong>
        <span>
          {run.metricLabel
            ? `${run.metricLabel}: ${t(metric(run.f1))} · ${t(run.scoreState)}${run.coverageLabel ? ` · ${run.coverage.scored}/${run.coverage.planned} ${run.coverageLabel}` : ""}`
            : t("F1 {f1} · {state} · {scored}/{planned} scored", { f1: t(metric(run.f1)), state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned })}
        </span>
        {tab === "cost" && run.costBasis === "verified_provider_estimate" && <span>
          {t("Estimated provider spend · {currency} {amount}", { currency: run.cost.currency ?? "", amount: String(run.cost.total) })}
        </span>}
        {tab === "cost" && run.costBasis === "reference_rate_estimate" && <span>
          {t("Reference-rate estimate · {currency} {amount}", { currency: run.cost.currency ?? "", amount: run.cost.total?.toFixed(4) ?? "" })}
        </span>}
        {run.recorded && <span>{t("Recorded demonstration · Not live quality")}</span>}
        {showRunIdentifiers && <>
          <small>{run.id}</small>
          <p>{t("{mode} inputs · {model} · Scope {scope}", {
            mode: t(run.inputMode ?? "Unavailable"), model: run.model ?? t("Unavailable"),
            scope: run.scopeIdentity ?? t("unavailable"),
          })}</p>
        </>}
      </> : <span>{t("Focus or select a point to inspect its Run.")}</span>}
    </div>
  );
}

function CostNote({ t }: { t: ResearchText }) {
  return <p className="scope-notice chart-cost-note">
    {t("Reference-rate estimates use retained token usage at the configured DeepSeek rates. Actual charges can differ.")}
  </p>;
}

function withMetric(run: PerformanceRun, key: string): PerformanceRun {
  const measure = run.measures?.[key];
  return {
    ...run,
    f1: measure?.value ?? null,
    metricLabel: measure?.label,
    coverage: measure?.coverage ?? { scored: 0, planned: 0 },
    coverageLabel: measure?.coverageLabel,
    scoreQualifier: measure?.qualifier,
    scoreBasis: measure?.basis,
    scoreState: measure ? run.scoreState : "unavailable",
  };
}

function isEligible(run: PerformanceRun, tab: ChartView) {
  if (run.f1 === null || !Number.isFinite(run.f1)) return false;
  return tab === "run" ? run.eligibility.f1_by_run : run.eligibility.f1_vs_cost && hasCost(run);
}

function hasCost({ cost }: PerformanceRun) {
  return cost.total !== null && Number.isFinite(cost.total) && cost.total >= 0 && !!cost.currency;
}

function costScale(candidates: PerformanceRun[], tab: ChartView) {
  // Historical Runs retain their axis currency when mixed with verified estimates.
  const currency = (candidates.find(run => !run.costBasis) ?? candidates[0])?.cost.currency ?? "USD";
  const incompatible = (run: PerformanceRun) => tab === "cost" && !!run.costBasis && run.cost.currency !== currency;
  const max = Math.max(...candidates.filter(run => !incompatible(run)).map(run => run.cost.total ?? 0), 0.0001);
  return { currency, max, incompatible };
}

function legacyCostAxis(eligible: PerformanceRun[], currency: string, max: number, t: ResearchText) {
  const label = eligible.some(run => run.fullPipelineCost)
    ? "Estimated full pipeline cost ({currency}) · 0–{max}"
    : "Estimated provider spend incurred by Run ({currency}) · 0–{max}";
  return t(label, { currency, max: max.toFixed(4) });
}

function runTicks(
  ids: string[], limit: number, position: (id: string) => number, number: (id: string) => number,
): PlotTick[] {
  const step = Math.max(1, Math.ceil((ids.length - 1) / (limit - 1)));
  return ids.flatMap((id, index) => index % step === 0 || index === ids.length - 1
    ? [{ at: position(id), label: String(number(id)) }]
    : []);
}

function costAxisTicks(upper: number) {
  const unit = 10 ** Math.floor(Math.log10(upper / 4));
  const step = unit * ([1, 2, 2.5, 5, 10].find(value => value * unit >= upper / 4) ?? 10);
  const intervals = Math.ceil(upper / step);
  const max = intervals * step;
  return {
    max,
    ticks: Array.from({ length: intervals + 1 }, (_, index) => ({
      at: index / intervals,
      label: String(Number((index * step).toPrecision(6))),
    })),
  };
}

function exclusionReason(run: PerformanceRun, tab: ChartView, incompatible: boolean, currency: string, t: ResearchText) {
  if (incompatible) return t("Estimated provider spend is in {currency}. This plot uses {plotCurrency}.", {
    currency: run.cost.currency ?? "", plotCurrency: currency,
  });
  return (tab === "run" ? run.eligibility.f1_reasons : run.eligibility.cost_reasons).map(reason => t(reason)).join(" ");
}
