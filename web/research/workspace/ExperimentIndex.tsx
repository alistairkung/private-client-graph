import { useCallback, useState } from "react";
import type { RunDetail, WorkspaceHistoryItem } from "../shared/contracts";
import { useRead } from "../shared/useRead";
import { percentMetric } from "../../src/shared/research/presentation";
import { getEvaluationSummary, getRun } from "./api";

const pageSize = 12;

export function ExperimentIndex({ items, executable }: { items: WorkspaceHistoryItem[]; executable: boolean }) {
  const [query, setQuery] = useState("");
  const [order, setOrder] = useState("newest");
  const [page, setPage] = useState(0);
  const search = query.trim().toLocaleLowerCase();
  const filtered = items.filter(item =>
    [item.name, item.hypothesis, item.description].some(value => value?.toLocaleLowerCase().includes(search)),
  );
  if (order === "name") filtered.sort((left, right) => left.name.localeCompare(right.name));
  else filtered.reverse();
  const current = Math.min(page, Math.max(0, Math.ceil(filtered.length / pageSize) - 1));

  return (
    <div className="workbench-home-theme">
      <header className="workspace-heading"><h1>Experiments</h1></header>
      <section className="workbench-index">
        <div className="workbench-index-tools">
          <label>Search experiments
            <input type="search" value={query} placeholder="Find an experiment" onChange={event => {
              setQuery(event.target.value);
              setPage(0);
            }} />
          </label>
          <label>Sort
            <select value={order} onChange={event => { setOrder(event.target.value); setPage(0); }}>
              <option value="newest">Newest experiments</option>
              <option value="name">Name A–Z</option>
            </select>
          </label>
        </div>
        {filtered.length ? <div className="table-scroll" tabIndex={0} role="region" aria-label="Experiment table">
          <table>
            <caption>Scores from the latest completed run in each experiment.</caption>
            <thead><tr>
              <th scope="col">Experiment</th><th scope="col">Latest status</th><th scope="col">Runs</th>
              <th scope="col">Graph F1</th><th scope="col">Evidence-Adjusted F1</th>
              {executable && <th scope="col">New run</th>}
            </tr></thead>
            <tbody>{filtered.slice(current * pageSize, (current + 1) * pageSize).map(item =>
              <ExperimentRow key={item.id} item={item} executable={executable} />,
            )}</tbody>
          </table>
        </div> : <p className="workbench-index-empty">{search ? "No experiments match your search." : "No experiments yet."}</p>}
        <footer className="workbench-index-footer">
          <span role="status">{filtered.length} {filtered.length === 1 ? "experiment" : "experiments"}</span>
          {filtered.length > pageSize && <div className="run-actions">
            <button className="secondary" type="button" disabled={current === 0} onClick={() => setPage(current - 1)}>Previous</button>
            <button className="secondary" type="button" disabled={(current + 1) * pageSize >= filtered.length} onClick={() => setPage(current + 1)}>Next</button>
          </div>}
        </footer>
      </section>
    </div>
  );
}

function ExperimentRow({ item, executable }: { item: WorkspaceHistoryItem; executable: boolean }) {
  const load = useCallback((signal: AbortSignal) => readIndexRun(item, signal), [item]);
  const { data, error } = useRead(load);
  const score = data?.scoredRun;
  const loadAssessment = useCallback((signal: AbortSignal) => score?.benchmark_v4?.state === "complete"
    ? getEvaluationSummary(score.id, signal) : Promise.resolve(null), [score]);
  const assessment = useRead(loadAssessment);
  const summary = assessment.data?.run_id === score?.id ? assessment.data : undefined;
  const scoresLoading = item.integrity === "verified" && !!item.run_ids.length && data === undefined && !error;
  const assessmentLoading = score?.benchmark_v4?.state === "complete" && !summary && !assessment.error;
  const status = item.integrity !== "verified" ? item.integrity
    : item.read_only_import ? "read-only"
    : !item.run_ids.length ? "draft"
    : data?.latest ?? (error ? "unavailable" : "loading");

  return <tr>
    <th scope="row">
      <a href={`#workspace=${item.id}`}>{item.name}</a>
      {score?.benchmark_v4 ? <small>PCG Benchmark v4</small> : score?.benchmark && <small>Evaluation Protocol v1</small>}
    </th>
    <td><span className="experiment-status" data-state={status}>{status.replaceAll("_", " ")}</span></td>
    <td>{item.run_ids.length}</td>
    <td><IndexScore loading={scoresLoading} value={score ? graphF1(score) : undefined} /></td>
    <td><IndexScore loading={scoresLoading || assessmentLoading} value={summary?.evidence_adjusted_f1?.f1} /></td>
    {executable && <td>{!item.read_only_import && item.integrity === "verified" && (
      <a href={`#${new URLSearchParams({ "new-run": "1", target: item.id })}`} aria-label={`Use ${item.name} for new run`}>Use</a>
    )}</td>}
  </tr>;
}

async function readIndexRun(item: WorkspaceHistoryItem, signal: AbortSignal) {
  if (item.integrity !== "verified" || !item.run_ids.length) return null;
  let latest: string | undefined;
  for (const id of [...item.run_ids].reverse()) {
    try {
      const run = await getRun(item.id, id, signal);
      latest ??= run.lifecycle;
      if (run.lifecycle === "complete") return { latest, scoredRun: run };
    } catch (error) {
      if (signal.aborted) throw error;
      latest ??= "unavailable";
    }
  }
  return { latest, scoredRun: undefined };
}

function graphF1(run: RunDetail) {
  if (run.benchmark_v4) {
    const graph = run.quality ? run.quality.combined_graph : run.benchmark_v4.combined;
    return graph?.f1 ?? null;
  }
  return run.benchmark?.cohort.all_condition_micro_f1 ?? run.evaluation.aggregate.f1;
}

function IndexScore({ loading, value }: { loading: boolean; value?: number | null }) {
  if (loading) return <span className="index-score-loading" role="status">Loading…</span>;
  return value == null ? <span aria-label="Score unavailable">—</span> : <strong>{percentMetric(value)}</strong>;
}
