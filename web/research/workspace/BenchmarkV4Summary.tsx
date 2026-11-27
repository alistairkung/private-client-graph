import type { BenchmarkV4Operations, BenchmarkV4Summary as Summary, DeliveredGraphMetrics, EvidenceQuality, RunDetail } from "../shared/contracts";
import { metric, money } from "./RunChart";

export function BenchmarkV4Summary({ run }: { run: RunDetail }) {
  const summary = run.benchmark_v4!;
  return (
    <>
      <p>Mixed reference scope · 35 evaluation inputs</p>
      {summary.observation_origin === "offline_fixture" && <p>Synthetic fixture results.</p>}
      {run.quality && summary.state !== "unmeasured" ? (
        <details>
          <summary>Graph delivery by reference scope</summary>
          {summary.state === "provisional" && <p>Unobserved inputs contribute their expected edges to the combined missing count.</p>}
          <GraphMetrics summary={summary} quality={run.quality} />
        </details>
      ) : summary.state === "unmeasured" ? (
        !run.quality && <p role="status">Graph metrics will appear after the first retained observation.</p>
      ) : (
        <>
          {summary.state === "provisional" && <p role="status">Provisional. Unobserved inputs contribute their expected edges to the combined missing count.</p>}
          <GraphMetrics summary={summary} />
        </>
      )}
      <details>
        <summary>U revision 8 evidence adjudication</summary>
        <p>{summary.consensus_evidence.adjudicated_relationships} reference relationships accepted after Source-body review.</p>
        <BenchmarkEvidence summary={summary} />
        <p>The diagnostic compares the relationship, Source ID and exact quotation. Evaluation Protocol v1 assesses formal proofs on the qualified cohort.</p>
      </details>
      {summary.observation_origin === "live" && run.pipeline_usage && (
        <details>
          <summary>Provider usage and cost</summary>
          <PipelineUsage usage={run.pipeline_usage} complete={summary.state === "complete"} />
        </details>
      )}
    </>
  );
}

export function GraphMetrics({ summary, quality }: { summary: Summary; quality?: EvidenceQuality | null }) {
  const slices: Array<[string, DeliveredGraphMetrics | null]> = [
    ["Combined · mixed references", quality ? quality.combined_graph : summary.combined],
    ["Benchmark v3 · 34 qualified Conditions", quality ? quality.qualified_graph : summary.qualified],
    ["U revision 8 · consensus reference", summary.consensus],
  ];
  return (
    <div className="table-scroll">
      <table>
        <caption>Graph delivery across planned inputs</caption>
        <thead>
          <tr>
            <th scope="col">Reference scope</th><th scope="col">Precision</th><th scope="col">Recall</th>
            <th scope="col">Graph F1</th><th scope="col">TP / FP / FN</th>
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

export function BenchmarkEvidence({ summary }: { summary: Summary }) {
  const evidence = summary.consensus_evidence;
  return (
    <>
      <p>U8 exact adjudicated citation matches {evidence.assessed
        ? `${evidence.matched_citations} / ${evidence.reference_citations}`
        : "unavailable until graph construction succeeds"}.</p>
    </>
  );
}

export function PipelineUsage({ usage, complete }: { usage: BenchmarkV4Operations; complete: boolean }) {
  const rows = [
    { label: usage.origin_run_id ? "Incremental resolver" : "Extraction", value: usage.incremental },
    ...(usage.inherited_extraction ? [{ label: "Inherited extraction", value: usage.inherited_extraction }] : []),
    { label: "Full pipeline", value: usage.full_pipeline },
  ];
  return (
    <div className="table-scroll">
      <table>
        <caption>{complete ? "Recorded usage" : "Recorded usage to date"}</caption>
        <thead><tr>
          <th scope="col">Stage</th><th scope="col">Attempts</th><th scope="col">Estimated cost</th>
          <th scope="col">Provider latency</th><th scope="col">Input tokens</th><th scope="col">Output tokens</th>
        </tr></thead>
        <tbody>
          {rows.map(({ label, value }) => (
            <tr key={label}>
              <th scope="row">{label}</th><td>{value.attempts}</td>
              <td>{money(value.estimated_cost, value.currency)}{value.unpriced_attempts > 0 ? ` · ${value.unpriced_attempts} unpriced` : ""}</td>
              <td>{seconds(value.provider_seconds)}</td>
              <td>{value.tokens.input_tokens?.toLocaleString() ?? "Unavailable"}</td>
              <td>{value.tokens.output_tokens?.toLocaleString() ?? "Unavailable"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>Reconstructed pipeline latency, including local edits and graph construction · {seconds(usage.full_pipeline_seconds)}.</p>
    </div>
  );
}

function seconds(value: number | null) {
  return value === null ? "Unavailable" : `${value.toFixed(2)} s`;
}
