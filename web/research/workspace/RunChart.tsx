import { useId, useState } from "react";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
export const metric = (value: number | null) =>
  value === null ? "Unavailable" : value.toFixed(3);
export const money = (value: number | null, currency: string | null) =>
  value === null
    ? "Unavailable"
    : `${currency ?? "Currency unavailable"} ${value.toFixed(4)}`;

export function RunChart({
  workspace,
  runs,
  selected,
  select,
}: {
  workspace: WorkspaceDetail;
  runs: RunDetail[];
  selected: string | null;
  select: (id: string) => void;
}) {
  const [tab, setTab] = useState<"run" | "cost">("run");
  const [inspected, setInspected] = useState<string | null>(null);
  const chartId = useId();
  const [inputMode, setInputMode] = useState("all");
  const runNumber = (id: string) => workspace.run_ids.indexOf(id) + 1;
  const visible = runs.filter(
    (run) =>
      inputMode === "all" || run.plan.preview.proposal.input_mode === inputMode,
  );
  const eligible = visible.filter((run) =>
    tab === "run"
      ? run.evaluation.eligibility.f1_by_run
      : run.evaluation.eligibility.f1_vs_cost,
  );
  const maxCost = Math.max(
    ...eligible.map((run) => run.evaluation.cost.total ?? 0),
    0.0001,
  );
  const tooltip = runs.find((run) => run.id === (inspected ?? selected));
  return (
    <section className="run-chart" aria-label="Run history and performance">
      <div className="section-heading">
        <h2>Run history &amp; performance</h2>
        <span>
          {workspace.run_ids.length}{" "}
          {workspace.run_ids.length === 1 ? "Run" : "Runs"} retained
        </span>
      </div>
      {new Set(
        runs.map((run) => run.evaluation.scope?.identity).filter(Boolean),
      ).size > 1 && (
        <p className="scope-notice">
          These Runs use different benchmark scopes. Inspect scope differences
          before comparing outcomes.
        </p>
      )}
      <div className="chart-tabs" role="tablist" aria-label="Performance chart">
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
            {value === "run" ? "F1 by Run" : "F1 vs Cost"}
          </button>
        ))}
      </div>
      <div
        id={`${chartId}-plot`}
        role="tabpanel"
        aria-labelledby={`${chartId}-${tab}`}
      >
        <label className="chart-filter">
          Input mode
          <select
            value={inputMode}
            onChange={(event) => setInputMode(event.target.value)}
          >
            <option value="all">All inputs · Discrete points</option>
            <option value="saved">Saved extraction</option>
            <option value="fresh">Fresh extraction</option>
          </select>
        </label>
        <div className="chart-legend">
          <span>F1 · 0–1</span>
          <span>◇ No resolver　● Generative resolver　○ Provisional</span>
        </div>
        {!runs.length ? (
          <p className="chart-empty">
            Run your first configuration to begin comparing results.
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
                const aggregate = run.evaluation.aggregate;
                const resolver =
                  run.plan.preview.proposal.resolver === "generative";
                const x =
                  tab === "run"
                    ? (index + 1) / (workspace.run_ids.length + 1)
                    : 0.05 + (0.9 * (run.evaluation.cost.total ?? 0)) / maxCost;
                return (
                  <button
                    key={run.id}
                    className={`chart-point ${resolver ? "resolved" : "baseline"} ${aggregate.state === "provisional" ? "provisional" : ""}`}
                    style={{
                      left: `${x * 100}%`,
                      top: `${(1 - (aggregate.f1 ?? 0)) * 100}%`,
                    }}
                    aria-label={`Run ${index + 1}, F1 ${metric(aggregate.f1)}, ${aggregate.state}, ${aggregate.coverage.scored}/${aggregate.coverage.planned} scored`}
                    aria-pressed={selected === run.id}
                    aria-describedby={`${chartId}-tooltip`}
                    onFocus={() => setInspected(run.id)}
                    onMouseEnter={() => setInspected(run.id)}
                    onMouseLeave={() => setInspected(null)}
                    onBlur={() => setInspected(null)}
                    onClick={() => select(run.id)}
                  >
                    <span />
                  </button>
                );
              })}
              {tab === "run" &&
                workspace.run_ids.map((id, index) => (
                  <span
                    key={id}
                    className="plot-tick"
                    style={{
                      left: `${((index + 1) / (workspace.run_ids.length + 1)) * 100}%`,
                    }}
                  >
                    {index + 1}
                  </span>
                ))}
            </div>
            <div className="plot-axis">
              {tab === "run"
                ? "Run number within this experiment"
                : `Estimated provider spend incurred by Run (${eligible[0]?.evaluation.cost.currency ?? "USD"}) · 0–${maxCost.toFixed(4)}`}
            </div>
            {!eligible.length && (
              <p>
                No Runs are eligible for this chart yet. Inspect their status
                below.
              </p>
            )}
          </>
        )}
        <p className="chart-footnote">
          {eligible.length}/{workspace.run_ids.length} Runs plotted · Discrete
          points; no trend or improvement is implied across different scopes.
        </p>
        <div
          id={`${chartId}-tooltip`}
          className="chart-inspection"
          aria-live="polite"
        >
          {tooltip ? (
            <>
              <strong>
                {workspace.name} · Run {runNumber(tooltip.id)}
              </strong>
              <span>
                F1 {metric(tooltip.evaluation.aggregate.f1)} ·{" "}
                {tooltip.evaluation.aggregate.state} ·{" "}
                {tooltip.evaluation.aggregate.coverage.scored}/
                {tooltip.evaluation.aggregate.coverage.planned} scored
              </span>
              <small>{tooltip.id}</small>
              <p>
                {tooltip.plan.preview.proposal.execution_mode === "recorded"
                  ? "Recorded demonstration · Not live quality · "
                  : ""}
                {tooltip.plan.preview.proposal.input_mode} inputs ·{" "}
                {tooltip.plan.preview.proposal.model} · Scope{" "}
                {tooltip.evaluation.scope?.identity ?? "unavailable"}
              </p>
            </>
          ) : (
            <span>Focus or select a point to inspect its Run.</span>
          )}
        </div>
        {!!runs.length && (
          <div className="run-history-list" aria-label="All Runs">
            {runs.map((run) => (
              <div key={run.id}>
                <button
                  className="secondary"
                  aria-pressed={selected === run.id}
                  onClick={() => select(run.id)}
                >
                  Run {runNumber(run.id)} ·{" "}
                  {run.plan.preview.proposal.resolver === "none"
                    ? "No resolver"
                    : "Generative resolver"}
                  <small>
                    {run.lifecycle} · F1 {metric(run.evaluation.aggregate.f1)} ·{" "}
                    {run.evaluation.aggregate.state}
                  </small>
                </button>
                {!(tab === "run"
                  ? run.evaluation.eligibility.f1_by_run
                  : run.evaluation.eligibility.f1_vs_cost) && (
                  <small>
                    {(tab === "run"
                      ? run.evaluation.eligibility.f1_reasons
                      : run.evaluation.eligibility.cost_reasons
                    ).join(" ")}
                  </small>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
