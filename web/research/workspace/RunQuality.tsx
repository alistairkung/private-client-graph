import { percentMetric } from "../../src/shared/research/presentation";
import type { BenchmarkV4Comparison, EvidenceQuality } from "../shared/contracts";
import {
  evidenceMetricLabels, multiSourceEvidenceCoverageDescription, multiSourceProofCompletionLabel,
} from "./benchmark-metrics";

export type EvidenceMetric = keyof typeof evidenceMetricLabels;
export const evidenceMetrics = Object.keys(evidenceMetricLabels) as EvidenceMetric[];

export function qualityValue(quality: EvidenceQuality | null, key: EvidenceMetric) {
  if (!quality) return null;
  switch (key) {
    case "combined_graph": return quality.combined_graph?.f1 ?? null;
    case "qualified_graph": return quality.qualified_graph?.f1 ?? null;
    case "complete_proof": return quality.complete_proof.rate;
    case "joint_only_coverage": return quality.joint_only_coverage.mean;
  }
}

export function qualityScope(quality: EvidenceQuality, key: EvidenceMetric) {
  switch (key) {
    case "combined_graph": return quality.planned_inputs === quality.qualified_inputs
      ? `${quality.planned_inputs} evaluation inputs`
      : `${quality.planned_inputs} evaluation inputs · mixed references`;
    case "qualified_graph": return `${quality.qualified_inputs} qualified Conditions`;
    case "complete_proof": return `${quality.complete_proof.targets} formal proof targets · qualified cohort`;
    case "joint_only_coverage": return `${quality.joint_only_coverage.targets} multi-Source proof targets · qualified cohort`;
  }
}

const primaryMetrics = ["qualified_graph", "complete_proof"] as const;
const primaryMeanings = {
  qualified_graph: "Expected relationships recovered and extra relationships penalized",
  complete_proof: "Expected relationships with a complete approved proof",
};

export function RunQuality({ quality, inline = false }: { quality: EvidenceQuality; inline?: boolean }) {
  const multiSource = quality.joint_only_complete_proof;
  return (
    <section className={inline ? "run-quality run-quality-inline" : "benchmark-run-summary run-quality"} aria-label="Evidence quality">
      <h3>{inline ? "Deterministic benchmark metrics" : "Evidence quality"}</h3>
      {quality.state === "unmeasured" && <p role="status">Awaiting retained observations.</p>}
      {quality.state === "provisional" && (
        <p role="status">Provisional · {quality.observed_inputs} of {quality.planned_inputs} inputs observed.</p>
      )}
      <dl className="quality-primary">
        {primaryMetrics.map((key) => (
          <div key={key}>
            <dt>{evidenceMetricLabels[key]}</dt>
            <dd>{percentMetric(qualityValue(quality, key))}</dd>
            <dd className="quality-scope">
              {inline && key === "complete_proof" && quality.complete_proof.rate !== null
                ? `${quality.complete_proof.complete} of ${quality.complete_proof.targets} formal targets`
                : qualityScope(quality, key)}
              <small>{primaryMeanings[key]}</small>
            </dd>
          </div>
        ))}
        {inline && <>
          <div className="quality-diagnostic">
            <dt>{multiSourceProofCompletionLabel}</dt>
            <dd>{multiSource.rate === null ? "Unavailable" : `${multiSource.complete} / ${multiSource.targets}`}</dd>
            <dd className="quality-scope">Complete approved multi-Source proofs</dd>
          </div>
          <div className="quality-diagnostic">
            <dt>{evidenceMetricLabels.joint_only_coverage}</dt>
            <dd>{percentMetric(qualityValue(quality, "joint_only_coverage"))}</dd>
            <dd className="quality-scope">Average exact coverage across {quality.joint_only_coverage.targets} targets</dd>
          </div>
        </>}
      </dl>
      <p className="quality-combined">
        {evidenceMetricLabels.combined_graph} <strong>{percentMetric(qualityValue(quality, "combined_graph"))}</strong>
        <span>{qualityScope(quality, "combined_graph")}</span>
      </p>
      <details>
        <summary>Evidence metrics and counts</summary>
        <dl className="quality-counts">
          <dt>Observed evaluation inputs</dt><dd>{quality.observed_inputs} / {quality.planned_inputs}</dd>
          <dt>Observed qualified Conditions</dt><dd>{quality.observed_qualified_inputs} / {quality.qualified_inputs}</dd>
          <dt>Expected qualified relationships</dt><dd>{quality.expected_relationships}</dd>
          <dt>{evidenceMetricLabels.complete_proof}</dt><dd>{quality.complete_proof.complete} / {quality.complete_proof.targets} · {quality.observed_proof_targets} targets observed</dd>
          <dt>{multiSourceProofCompletionLabel}</dt>
          <dd>{percentMetric(quality.joint_only_complete_proof.rate)} · {quality.joint_only_complete_proof.complete} / {quality.joint_only_complete_proof.targets} complete</dd>
          <dt>{evidenceMetricLabels.joint_only_coverage}</dt>
          <dd>{percentMetric(quality.joint_only_coverage.mean)} · {quality.observed_joint_targets} / {quality.joint_only_coverage.targets} targets observed</dd>
        </dl>
        <p>{multiSourceEvidenceCoverageDescription} These synthetic benchmark measures do not assess legal sufficiency.</p>
      </details>
    </section>
  );
}

export function RunQualityComparison({ comparison }: { comparison: BenchmarkV4Comparison }) {
  const { left_quality: left, right_quality: right, quality_delta: delta } = comparison;
  if (!left && !right) return null;
  const metrics = [...primaryMetrics, "combined_graph", "joint_only_coverage"] as const;
  return (
    <div className="quality-comparison">
      <div className="table-scroll">
        <table>
          <caption>Evidence quality comparison</caption>
          <thead><tr>
            <th scope="col">Metric</th>
            <th scope="col">Comparison Run{left?.state === "provisional" && " · provisional"}</th>
            <th scope="col">Selected Run{right?.state === "provisional" && " · provisional"}</th>
            {delta && <th scope="col">Change</th>}
          </tr></thead>
          <tbody>{metrics.map((key, index) => (
            <tr key={key} className={index < primaryMetrics.length ? "quality-primary-row" : undefined}>
              <th scope="row">{evidenceMetricLabels[key]}</th>
              {[left, right].map((quality, side) => (
                <td key={side}>
                  <span>{percentMetric(qualityValue(quality ?? null, key))}</span>
                  {quality && <small>{qualityScope(quality, key)}</small>}
                </td>
              ))}
              {delta && <td><span className="quality-change">{percentagePointChange(delta[key])}</span></td>}
            </tr>
          ))}</tbody>
        </table>
      </div>
      {!delta && <p>Changes are unavailable without complete, comparable evidence quality results.</p>}
    </div>
  );
}

function percentagePointChange(value: number | null) {
  if (value === null) return "Unavailable";
  const change = (value * 100).toFixed(2);
  return `${value > 0 ? "+" : ""}${change} pp`;
}
