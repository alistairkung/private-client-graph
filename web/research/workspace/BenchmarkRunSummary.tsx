import type { BenchmarkRun, RunDetail } from "../shared/contracts";
import { metric, money } from "./RunChart";
import { evidenceMetricLabels, formatF1Basis, multiSourceProofCompletionLabel } from "./benchmark-metrics";
import { RunRelationshipMatrix } from "./RunRelationshipMatrix";
import { RunQuality } from "./RunQuality";
import { SemanticEvidencePanel } from "./SemanticEvidence";
import "./run-relationship-matrix.css";

export function BenchmarkRunSummary({
  run,
  benchmark,
}: {
  run: RunDetail;
  benchmark: BenchmarkRun;
}) {
  const semantic = run.benchmark_v4?.state === "complete"
    ? <SemanticEvidencePanel key={run.id} run={run.id} />
    : null;
  return (
    <section
      className="benchmark-run-summary"
      aria-label="Evaluation Protocol v1 results"
    >
      <p className="overview-population">
        Evaluation Protocol v1 · {benchmark.cohort.planned_conditions}{" "}
        Environment Conditions
      </p>
      {run.quality ? (
        <RunQuality quality={run.quality} inline>{semantic}</RunQuality>
      ) : <>
        <div className={semantic ? "benchmark-overview-line benchmark-overview-line-metrics" : "benchmark-overview-line"}>
          <div>
            <span>All-condition Graph F1</span>
            <strong>{metric(benchmark.cohort.all_condition_micro_f1)}</strong>
            <small>
              {formatF1Basis(
                benchmark.cohort.all_conditions.tp,
                benchmark.cohort.all_conditions.fp,
                benchmark.cohort.all_conditions.fn,
              )}
            </small>
          </div>
          <div>
            <span>{evidenceMetricLabels.complete_proof}</span>
            <strong>
              {benchmark.cohort.planned_proofs
                ? `${benchmark.cohort.complete_proofs} of ${benchmark.cohort.planned_proofs} complete`
                : "Unavailable · 0 eligible"}
            </strong>
            <small>Annotated relationships with a complete approved proof</small>
          </div>
          {!semantic && <RelationshipMatrix benchmark={benchmark} />}
        </div>
        {semantic}
      </>}
      {(run.quality || semantic) && (
        <div className="protocol-results-matrix">
          <RelationshipMatrix benchmark={benchmark} />
        </div>
      )}

      <details className="protocol-metrics">
        <summary>Protocol metrics and denominators</summary>
        <p>
          Graph F1 = 2 × true positives / (2 × true positives + false
          positives + false negatives).
        </p>
        <p>
          Construction success{" "}
          {metric(benchmark.cohort.construction_success_rate)} · valid graphs{" "}
          {benchmark.cohort.valid_graphs}/{benchmark.cohort.planned_conditions}{" "}
          · exact graphs {benchmark.cohort.exact_graphs}/
          {benchmark.cohort.planned_conditions} · exact graph accuracy{" "}
          {metric(benchmark.cohort.exact_graph_accuracy)}
        </p>
        <p>
          All conditions · True positives / false positives / false negatives{" "}
          {benchmark.cohort.all_conditions.tp}/
          {benchmark.cohort.all_conditions.fp}/
          {benchmark.cohort.all_conditions.fn} · Graph F1{" "}
          {metric(benchmark.cohort.all_condition_micro_f1)}
        </p>
        <p>
          Constructed graphs only · True positives / false positives / false
          negatives {benchmark.cohort.valid_graph_only.tp}/
          {benchmark.cohort.valid_graph_only.fp}/
          {benchmark.cohort.valid_graph_only.fn} · Graph F1{" "}
          {metric(benchmark.cohort.valid_graph_only_micro_f1)}
        </p>
        <p>
          {evidenceMetricLabels.complete_proof}{" "}
          {eligibleRatio(
            benchmark.cohort.complete_proofs,
            benchmark.cohort.planned_proofs,
          )}{" "}
          · {multiSourceProofCompletionLabel}{" "}
          {eligibleRatio(
            benchmark.cohort.complete_joint_proofs,
            benchmark.cohort.planned_joint_proofs,
          )}
        </p>
        <p>
          Proof outcomes · {benchmark.cohort.complete_proofs} complete ·{" "}
          {benchmark.cohort.incomplete_proofs} incomplete ·{" "}
          {benchmark.cohort.missed_proofs} missed edges ·{" "}
          {benchmark.cohort.proofs_without_graph} without a valid graph
        </p>
        <p>
          Exact quotation{" "}
          {eligibleRatio(
            benchmark.cohort.quote_passed,
            benchmark.cohort.quote_assessed,
          )}{" "}
          · Source attribution{" "}
          {eligibleRatio(
            benchmark.cohort.attribution_passed,
            benchmark.cohort.attribution_assessed,
          )}
        </p>
        <p>
          Family macro F1 {metric(benchmark.family_macro_f1)} across{" "}
          {Object.keys(benchmark.families).length} families ·
          constructed-graph-only supplemental macro F1{" "}
          {metric(benchmark.valid_graph_only_family_macro_f1)} across{" "}
          {benchmark.valid_graph_only_macro_family_count} eligible families
        </p>
        <p>
          Condition outcomes:{" "}
          {Object.entries(benchmark.cohort.outcomes)
            .map(
              ([outcome, count]) => `${outcome.replaceAll("_", " ")} ${count}`,
            )
            .join(" · ")}
        </p>
        <div className="table-scroll">
          <table>
            <caption>Family protocol metrics</caption>
            <thead>
              <tr>
                <th>Family</th>
                <th>Planned / valid graphs</th>
                <th>True / unsupported / missing relationships</th>
                <th>All-condition Graph F1</th>
                <th>Exact graphs</th>
                <th>{evidenceMetricLabels.complete_proof}</th>
                <th>{multiSourceProofCompletionLabel}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(benchmark.families).map(([family, value]) => (
                <tr key={family}>
                  <th>{family}</th>
                  <td>
                    {value.planned_conditions} / {value.valid_graphs}
                  </td>
                  <td>
                    {value.all_conditions.tp} / {value.all_conditions.fp} /{" "}
                    {value.all_conditions.fn}
                  </td>
                  <td>{metric(value.all_condition_micro_f1)}</td>
                  <td>
                    {value.exact_graphs} / {value.planned_conditions}
                  </td>
                  <td>
                    {eligibleRatio(value.complete_proofs, value.planned_proofs)}
                  </td>
                  <td>
                    {eligibleRatio(
                      value.complete_joint_proofs,
                      value.planned_joint_proofs,
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      {!run.benchmark_v4 && benchmark.scope.observation_origin === "live" && (
        <p>Historical baseline · reference for prospective comparison.</p>
      )}
      <details>
        <summary>Accounting and verified provenance</summary>
        <p>
          Retained attempts {run.evaluation.cost.attempts} · Estimated spend{" "}
          {money(run.evaluation.cost.total, run.evaluation.cost.currency)}
        </p>
        <p>
          Run {run.id} · {run.benchmark_v4 ? "Artifact" : "Archive"} {run.artifact_digest}
        </p>
        <pre>
          {JSON.stringify(
            { scope: benchmark.scope, provenance: run.provenance },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}

function RelationshipMatrix({ benchmark }: { benchmark: BenchmarkRun }) {
  return <RunRelationshipMatrix
    counts={benchmark.cohort.all_conditions}
    expectedEdgesWithoutGraph={benchmark.cohort.expected_edges_without_graph}
  />;
}

function eligibleRatio(count: number, planned: number) {
  return planned ? `${count}/${planned}` : "Unavailable (0 eligible)";
}
