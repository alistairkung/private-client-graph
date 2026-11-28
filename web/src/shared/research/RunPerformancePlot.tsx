import { useId } from "react";
import { motion, useReducedMotion } from "motion/react";
import { metric, percentMetric, type ResearchText } from "./presentation";
import type { PerformanceRun } from "./RunPerformanceChart";

export type PlotTick = { at: number; label: string };
export type PlotPoint = { run: PerformanceRun; number: number; x: number };

export function RunPerformancePlot({
  title, description, note, message, points, ticks, axis, selected, select, inspect, tooltipId, tactile, t,
}: {
  title?: string;
  description?: string;
  note?: string;
  message?: string;
  points: PlotPoint[];
  ticks: PlotTick[];
  axis: string;
  selected: string | null;
  select: (id: string) => void;
  inspect?: (id: string | null) => void;
  tooltipId?: string;
  tactile?: boolean;
  t: ResearchText;
}) {
  const headingId = useId();
  const reducedMotion = useReducedMotion();
  const showValues = title && points.length <= 3 && points.every((point, index) =>
    points.slice(index + 1).every(other => Math.abs(point.x - other.x) >= 0.24),
  );
  const plot = (
    <>
      <div className="plot-area">
        {[1, 0.75, 0.5, 0.25, 0].map(value => (
          <div className="plot-grid" key={value} aria-hidden="true" style={{ top: `${(1 - value) * 100}%` }}>
            <span>{title ? `${value * 100}%` : value.toFixed(2)}</span>
          </div>
        ))}
        {points.map(({ run, number, x }) => {
          const pressed = selected === run.id;
          const position = { left: `${x * 100}%`, top: `${(1 - (run.f1 ?? 0)) * 100}%` };
          const score = title ? percentMetric(run.f1) : metric(run.f1);
          return (
            <div key={run.id}>
              <button
                type="button"
                className={`chart-point ${run.resolver ? "resolved" : "baseline"} ${run.scoreState === "provisional" ? "provisional" : ""}`}
                style={position}
                aria-label={pointLabel(run, number, score, t)}
                aria-pressed={pressed}
                aria-describedby={tooltipId}
                onFocus={inspect && (() => inspect(run.id))}
                onMouseEnter={inspect && (() => inspect(run.id))}
                onMouseLeave={inspect && (() => inspect(null))}
                onBlur={inspect && (() => inspect(null))}
                onClick={() => select(run.id)}
              >
                {tactile && pressed && <motion.i
                  className="chart-selection-ring" aria-hidden="true"
                  initial={reducedMotion ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: reducedMotion ? 0 : 0.08 }}
                />}
                <span />
              </button>
              {showValues && <span
                className="chart-point-value"
                data-below={(run.f1 ?? 0) >= 0.8 || undefined}
                style={position}
                aria-hidden="true"
              >{score}</span>}
            </div>
          );
        })}
        {ticks.map(({ at, label }) => (
          <span className="plot-tick" key={at} style={{ left: `${at * 100}%` }} aria-hidden="true">{label}</span>
        ))}
      </div>
      <div className="plot-axis">{axis}</div>
    </>
  );

  if (!title) return plot;
  return (
    <figure className="performance-plot" aria-labelledby={headingId}>
      <figcaption>
        <h3 id={headingId}>{title}</h3>
        <p>{description}</p>
        {note && <p className="plot-evaluation-basis">{note}</p>}
      </figcaption>
      {message ? <p role="status" className="plot-status">{message}</p> : plot}
    </figure>
  );
}

function pointLabel(run: PerformanceRun, number: number, score: string, t: ResearchText) {
  if (run.metricLabel) {
    const name = run.displayName ?? t("Run {run}", { run: number });
    const basis = run.scoreBasis ?? (run.coverageLabel ? `${run.coverage.scored}/${run.coverage.planned} ${run.coverageLabel}` : "");
    const qualifier = run.scoreQualifier ? `, ${run.scoreQualifier}` : "";
    return `${name}, ${run.metricLabel} ${score}, ${t(run.scoreState)}${basis ? `, ${basis}` : ""}${qualifier}`;
  }
  const values = { f1: score, state: t(run.scoreState), scored: run.coverage.scored, planned: run.coverage.planned };
  return run.displayName
    ? t("{name}, F1 {f1}, {state}, {scored}/{planned} scored", { ...values, name: run.displayName })
    : t("Run {run}, F1 {f1}, {state}, {scored}/{planned} scored", { ...values, run: number });
}
