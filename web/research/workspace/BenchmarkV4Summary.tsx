import type { BenchmarkV4Operations, BenchmarkV4Summary as Summary, DeliveredGraphMetrics, Metrics, RunDetail } from "../shared/contracts";
import { metric, money } from "./RunChart";
import { QualityDiagnostics, RunQuality } from "./RunQuality";

export function BenchmarkV4Summary({ run }: { run: RunDetail }) {
  const summary = run.benchmark_v4!;
  return (
    <section className="benchmark-run-summary" aria-label="Benchmark v4 results">
      <p>{run.pipeline_usage?.origin_run_id ? "Extractor v1 candidates + Generative Resolver" : "Extractor v1 only"} · 35 evaluation inputs</p>
      {summary.observation_origin === "offline_fixture" && <p>Synthetic fixture results.</p>}
      {run.quality && <RunQuality quality={run.quality} mixed provisional={summary.state === "provisional"} />}
      {summary.combined && (
        <p>{summary.combined.valid_graphs}/{summary.combined.inputs} graphs constructed · {summary.combined.exact_graphs} exact graphs</p>
      )}
      {summary.state !== "unmeasured" && (
        <details>
          <summary>Evaluation diagnostics</summary>
          {run.quality && <QualityDiagnostics quality={run.quality} />}
          <GraphMetrics summary={summary} />
        </details>
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
      {summary.state === "provisional" && <p>The original planned-input score counts expected edges from inputs awaiting observation as missing.</p>}
      <table>
        <caption>Graph delivery on planned inputs · historical scoring</caption>
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

export function BenchmarkEvidence({ summary, proofs }: { summary: Summary; proofs?: Metrics | null }) {
  const evidence = summary.consensus_evidence;
  return (
    <>
      {proofs && summary.state !== "unmeasured" && (
        <p>Complete qualified proofs {proofs.complete_proofs} / {proofs.planned_proofs} ·
          Joint-only {proofs.complete_joint_proofs} / {proofs.planned_joint_proofs}.</p>
      )}
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
