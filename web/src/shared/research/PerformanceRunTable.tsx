import { percentMetric } from "./presentation";
import type { PerformanceRun } from "./RunPerformanceChart";

type RunRow = {
  run: PerformanceRun;
  number: number;
  graph: PerformanceRun;
  evidence: PerformanceRun;
  costIssue: string;
};

export function PerformanceRunTable({
  rows, graphLabel, evidenceLabel, loadingEvidence, selected, select,
}: {
  rows: RunRow[];
  graphLabel: string;
  evidenceLabel: string;
  loadingEvidence: boolean;
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
            <th scope="col">{graphLabel}</th>
            <th scope="col">{evidenceLabel}</th>
            <th scope="col">Est. cost{currency && <small>({currency})</small>}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ run, number, graph, evidence }) => (
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
              <td>{displayScore(graph.f1)}</td>
              <td>
                {loadingEvidence && evidence.f1 === null && run.scoreState === "complete"
                  ? "Loading…"
                  : displayScore(evidence.f1)}
                {evidence.scoreQualifier && <small>{evidence.scoreQualifier}</small>}
              </td>
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

function displayScore(value: number | null) {
  return percentMetric(value !== null && Number.isFinite(value) ? value : null);
}
