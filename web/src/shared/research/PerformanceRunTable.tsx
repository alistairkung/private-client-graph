import { percentMetric } from "./presentation";
import type { PerformanceRun } from "./RunPerformanceChart";

export type PerformanceTableRun = {
  run: PerformanceRun;
  number: number;
  costIssue: string;
};

type RunScore = { key: string; value: number | null; basis?: string; qualifier?: string; loading: boolean };
type RunRow = PerformanceTableRun & { scores: RunScore[] };

export function PerformanceRunTable({
  rows, columns, selected, select,
}: {
  rows: RunRow[];
  columns: { key: string; label: string }[];
  selected: string | null;
  select: (id: string) => void;
}) {
  const currencies = new Set(rows.flatMap(({ run }) => run.cost.currency ? [run.cost.currency] : []));
  const currency = currencies.size === 1 ? [...currencies][0] : null;
  const exclusions = rows.filter(row => row.costIssue);
  return (
    <>
      <table className="performance-run-table" aria-label="Run scores and cost estimates">
        <thead>
          <tr>
            <th scope="col">Run</th>
            {columns.map(column => <th key={column.key} scope="col">{column.label}</th>)}
            <th scope="col">Est. cost{currency && <small>({currency})</small>}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ run, number, scores }) => (
            <tr key={run.id}>
              <th scope="row">
                <button type="button" aria-pressed={selected === run.id} onClick={() => select(run.id)}>
                  <i className={`performance-marker${run.resolver ? "" : " baseline"}`} aria-hidden="true" />
                  <span>
                    {run.displayName ?? `Run ${number}`}
                    <small>{run.resolver ? "Generative resolver" : "No resolver"}</small>
                    {run.recorded && <small>Recorded demonstration</small>}
                    {run.scoreState === "provisional" && <small>Provisional</small>}
                  </span>
                </button>
              </th>
              {scores.map(({ key, value, basis, qualifier, loading }) => {
                const available = value !== null && Number.isFinite(value);
                return <td key={key}>
                  {loading && !available ? "Loading…" : percentMetric(available ? value : null)}
                  {available && basis && <small>{basis}</small>}
                  {available && qualifier && <small>{qualifier}</small>}
                </td>;
              })}
              <td>
                {run.cost.total !== null && run.cost.currency && Number.isFinite(run.cost.total)
                  ? <>{!currency && <small>{run.cost.currency}</small>}{run.cost.total.toFixed(4)}</>
                  : <span className="performance-unavailable"><span aria-hidden="true">—</span><span className="performance-visually-hidden">Unavailable</span></span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!!exclusions.length && (
        <details className="performance-cost-exclusions">
          <summary>Cost exclusions</summary>
          <ul>
            {exclusions.map(({ run, number, costIssue }) => (
              <li key={run.id}>{run.displayName ?? `Run ${number}`} · {costIssue}</li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}
