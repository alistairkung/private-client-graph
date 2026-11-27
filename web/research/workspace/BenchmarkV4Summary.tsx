import type { BenchmarkV4Summary as Summary, DeliveredGraphMetrics, RunDetail } from "../shared/contracts";
import { metric, money } from "./RunChart";

export function BenchmarkV4Summary({ run }: { run: RunDetail }) {
  const summary = run.benchmark_v4!;
  const evidence = summary.consensus_evidence;
  const cost = run.evaluation.cost;
  const attempts = run.attempts;
  const inputTokens = observed(attempts.map((attempt) => usage(attempt, "input_tokens")));
  const outputTokens = observed(attempts.map((attempt) => usage(attempt, "output_tokens")));
  const seconds = observed(attempts.map((attempt) => attempt.provider_seconds));

  return (
    <section className="benchmark-run-summary" aria-label="Benchmark v4 results">
      <p>35 evaluation inputs · Mixed reference methodologies</p>
      {summary.observation_origin === "offline_fixture" && <p>Synthetic fixture results.</p>}
      {summary.state === "unmeasured" ? (
        <p role="status">Graph metrics will appear after the first retained observation.</p>
      ) : (
        <>
          {summary.state === "provisional" && <p role="status">Provisional. Unobserved inputs contribute their expected edges to the combined missing count.</p>}
          <GraphMetrics summary={summary} />
        </>
      )}
      <details>
        <summary>U revision 8 evidence adjudication</summary>
        <p>{evidence.adjudicated_relationships} reference relationships accepted after Source-body review.</p>
        <p>Exact adjudicated citation matches {evidence.assessed
          ? `${evidence.matched_citations} / ${evidence.reference_citations}`
          : "unavailable until graph construction succeeds"}.</p>
        <p>The diagnostic compares the relationship, Source ID and exact quotation. Formal proof sufficiency is assessed under Evaluation Protocol v1 for the qualified cohort.</p>
      </details>
      {summary.observation_origin === "live" && attempts.length > 0 && (
        <details>
          <summary>Provider usage and cost</summary>
          <p>Estimated spend {money(cost.total, cost.currency)} · {cost.unpriced_attempts} unpriced attempts.</p>
          {inputTokens && <p>{inputTokens.total.toLocaleString()} input tokens across {inputTokens.count} of {attempts.length} attempts with usage.</p>}
          {outputTokens && <p>{outputTokens.total.toLocaleString()} output tokens across {outputTokens.count} of {attempts.length} attempts with usage.</p>}
          {seconds && <p>Mean provider latency {(seconds.total / seconds.count).toFixed(2)} s across {seconds.count} of {attempts.length} attempts with timing.</p>}
        </details>
      )}
    </section>
  );
}

export function GraphMetrics({ summary }: { summary: Summary }) {
  const slices: Array<[string, DeliveredGraphMetrics | null]> = [
    ["Combined · mixed references", summary.combined],
    ["Benchmark v3 · 34 qualified Conditions", summary.qualified],
    ["U revision 8 · consensus reference", summary.consensus],
  ];
  return (
    <div className="table-scroll">
      <table>
        <caption>Graph delivery across planned inputs</caption>
        <thead>
          <tr>
            <th scope="col">Reference scope</th><th scope="col">Precision</th><th scope="col">Recall</th>
            <th scope="col">Micro-F1</th><th scope="col">TP / FP / FN</th>
            <th scope="col">Valid / planned</th><th scope="col">Without graph</th><th scope="col">Exact</th>
          </tr>
        </thead>
        <tbody>{slices.map(([label, value]) => (
          <tr key={label}>
            <th scope="row">{label}</th>
            <td>{metric(value?.precision ?? null)}</td><td>{metric(value?.recall ?? null)}</td>
            <td><strong>{metric(value?.f1 ?? null)}</strong></td>
            <td>{value ? `${value.counts.tp} / ${value.counts.fp} / ${value.counts.fn}` : "Unavailable"}</td>
            <td>{value ? `${value.valid_graphs} / ${value.inputs}` : "Unavailable"}</td>
            <td>{value?.without_graph ?? "Unavailable"}</td><td>{value?.exact_graphs ?? "Unavailable"}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function observed(values: unknown[]) {
  const known = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  return known.length ? { count: known.length, total: known.reduce((sum, value) => sum + value, 0) } : null;
}

function usage(attempt: Record<string, unknown>, field: string) {
  const response = attempt.response as { usage?: Record<string, unknown> } | undefined;
  return response?.usage?.[field];
}
