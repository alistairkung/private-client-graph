import { useCallback, useState } from "react";
import type {
  BenchmarkRun,
  RunDetail,
  WorkspaceDetail,
} from "../shared/contracts";
import { ObservationInspection } from "./ObservationInspection";
import { ConditionInspection } from "./ConditionInspection";
import { BenchmarkFamilyExplorer } from "./BenchmarkFamilyExplorer";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { compareRuns } from "./api";
import { metric, money } from "./RunChart";
import { BenchmarkEvidence, BenchmarkV4Summary, GraphMetrics, PipelineUsage } from "./BenchmarkV4Summary";
import { BenchmarkRunSummary } from "./BenchmarkRunSummary";
import { RunQuality, RunQualityComparison } from "./RunQuality";
import { SemanticEvidenceComparison } from "./SemanticEvidence";
import { evidenceMetricLabels, multiSourceProofCompletionLabel } from "./benchmark-metrics";

export function RunInspection({
  workspace,
  run,
  number,
  runs,
  copy,
  busy,
}: {
  workspace: WorkspaceDetail;
  run: RunDetail;
  number: number;
  runs: RunDetail[];
  copy?: () => void;
  busy: boolean;
}) {
  const [other, setOther] = useState("");
  if (run.benchmark)
    return (
      <BenchmarkRunInspection
        workspace={workspace}
        run={run}
        benchmark={run.benchmark}
        number={number}
        runs={runs}
        copy={copy}
        busy={busy}
      />
    );
  if (!run.plan || !run.evaluation)
    return (
      <section className="run-inspection" aria-label={`Run ${number} details`}>
        <p role="status">Run inspection data unavailable.</p>
      </section>
    );
  const { aggregate, cost, scope } = run.evaluation;
  const configuration = run.plan.preview.proposal;
  return (
    <section className="run-inspection" aria-label={`Run ${number} details`}>
      <div className="section-heading">
        <div>
          <h2>
            Run {number} ·{" "}
            {configuration.resolver === "none"
              ? "No resolver"
              : "Generative resolver"}
          </h2>
          <small>
            {workspace.name} ·{" "}
            {configuration.execution_mode === "recorded"
              ? "Recorded demonstration · Not live quality"
              : configuration.execution_mode === "live"
                ? "Live provider execution"
                : "Provider-free replay"}{" "}
            · {configuration.input_mode} inputs · {run.lifecycle}
          </small>
        </div>
        <strong>F1 {metric(aggregate.f1)}</strong>
      </div>
      <section className="frozen-run">
        <div className="section-heading">
          <h3>Frozen pipeline for Run {number}</h3>
          {copy && (
            <button className="secondary" disabled={busy} onClick={copy}>
              Use as next draft
            </button>
          )}
        </div>
        <ol className="frozen-stages">
          <li>
            {configuration.input_mode === "saved"
              ? "Saved extraction"
              : "Fresh extraction"}
          </li>
          <li>
            {configuration.resolver === "none"
              ? "No resolver"
              : "Generative resolver"}
          </li>
          <li>Build graph</li>
          <li>Evaluate</li>
        </ol>
        <details>
          <summary>
            Configuration, input identities &amp; execution record
          </summary>
          <p>{workspace.hypothesis ?? "Hypothesis not supplied"}</p>
          {workspace.description && <p>{workspace.description}</p>}
          <dl>
            <dt>Experiment ID</dt>
            <dd>{workspace.id}</dd>
            <dt>Run ID</dt>
            <dd>{run.id}</dd>
            <dt>Plan digest</dt>
            <dd>{run.plan.digest}</dd>
          </dl>
          <h4>Frozen configuration</h4>
          <pre>{JSON.stringify(configuration, null, 2)}</pre>
          <h4>Input, evaluator and aggregate identities</h4>
          <pre>{JSON.stringify(scope, null, 2)}</pre>
          <h4>Execution provenance</h4>
          <pre>{JSON.stringify(run.provenance, null, 2)}</pre>
          <h4>Pricing and attempts</h4>
          <pre>
            {JSON.stringify(
              {
                pricing: run.pricing,
                attempts: run.attempts,
                authorized_invocations: run.authorized_invocations,
              },
              null,
              2,
            )}
          </pre>
        </details>
      </section>
      <p className="aggregate-line">
        <strong>
          {aggregate.state === "complete"
            ? "Evaluation complete"
            : aggregate.state === "provisional"
              ? "Provisional evaluation"
              : "Evaluation unavailable"}
        </strong>{" "}
        · {aggregate.coverage.scored}/{aggregate.coverage.planned} scored ·{" "}
        {aggregate.coverage.pending} pending · {aggregate.coverage.failed}{" "}
        failed · {aggregate.coverage.uncertain} uncertain ·{" "}
        {aggregate.coverage.unavailable} unavailable
      </p>
      {aggregate.reasons.map((reason) => (
        <p key={reason}>{reason}</p>
      ))}
      <div className="aggregate-counts">
        <span>
          Matched · TP{" "}
          <strong>
            {aggregate.f1 === null ? "Unavailable" : aggregate.tp}
          </strong>
        </span>
        <span>
          Extra · FP{" "}
          <strong>
            {aggregate.f1 === null ? "Unavailable" : aggregate.fp}
          </strong>
        </span>
        <span>
          Missing · FN{" "}
          <strong>
            {aggregate.f1 === null ? "Unavailable" : aggregate.fn}
          </strong>
        </span>
      </div>
      <details>
        <summary>Coverage by case</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Benchmark case</th>
                <th>F1</th>
                <th>TP / FP / FN</th>
                <th>Scored / planned</th>
                <th>Failed / uncertain / unavailable</th>
              </tr>
            </thead>
            <tbody>
              {aggregate.cases.map((item) => (
                <tr key={item.case_id}>
                  <th>
                    {run.observations.find(
                      (observation) => observation.case_id === item.case_id,
                    )?.metadata?.name ??
                      `Case ${item.case_id} (name unavailable)`}
                    <small>{item.case_id}</small>
                  </th>
                  <td>{metric(item.f1)}</td>
                  <td>
                    {item.f1 === null
                      ? "Unavailable"
                      : `${item.tp} / ${item.fp} / ${item.fn}`}
                  </td>
                  <td>
                    {item.coverage.scored}/{item.coverage.planned}
                  </td>
                  <td>
                    {item.coverage.failed} / {item.coverage.uncertain} /{" "}
                    {item.coverage.unavailable}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <details>
        <summary>Cost and comparison</summary>
        <p>
          Estimated provider spend incurred:{" "}
          <strong>{money(cost.total, cost.currency)}</strong>
        </p>
        <p>
          Known subtotal: {money(cost.known_subtotal, cost.currency)} ·{" "}
          {cost.unpriced_attempts} unpriced attempts
        </p>
        {cost.reasons.map((reason) => (
          <p key={reason}>{reason}</p>
        ))}
        <p>
          Reconstructed full-pipeline cost:{" "}
          {money(run.evaluation.full_pipeline_cost, cost.currency)}.{" "}
          {run.evaluation.full_pipeline_cost_reason}
        </p>
        {scope?.unequal_allocation && (
          <p>
            Unequal observation allocation intentionally weights this aggregate.
          </p>
        )}
        <label>
          Compare with Run
          <select value={other} onChange={(e) => setOther(e.target.value)}>
            <option value="">Choose a Run</option>
            {runs
              .filter((item) => item.id !== run.id)
              .map((item) => (
                <option key={item.id} value={item.id}>
                  Run {workspace.run_numbers?.[item.id] ?? workspace.run_ids.indexOf(item.id) + 1}
                </option>
              ))}
          </select>
        </label>
        {other && (
          <RunComparisonPanel
            experiment={workspace.id}
            left={other}
            right={run.id}
          />
        )}
      </details>
      <ObservationInspection run={run} />
    </section>
  );
}
function RunComparisonPanel({
  experiment,
  left,
  right,
}: {
  experiment: string;
  left: string;
  right: string;
}) {
  const load = useCallback(
    (signal: AbortSignal) => compareRuns(experiment, left, right, signal),
    [experiment, left, right],
  );
  const { data, error, retry } = useRead(load);
  if (!data) return <ReadState error={error} retry={retry} />;
  return (
    <div>
      <p>
        {data.comparable_scope
          ? "Comparable benchmark scope"
          : "Different benchmark scopes"}{" "}
        · {data.matched_inputs}{" "}
        {data.benchmark ? "aligned Conditions" : data.benchmark_v4 ? "aligned evaluation inputs" : "exactly matched inputs"}
      </p>
      {!data.unqualified_improvement_allowed && (
        <p>Do not interpret this comparison as an unqualified improvement.</p>
      )}
      {[
        ...data.scope_differences,
        ...data.provenance_differences,
        ...data.reasons,
      ].map((reason, index) => (
        <p key={index}>{reason}</p>
      ))}
      {data.benchmark_v4 && (
        <section aria-label="Benchmark v4 comparison">
          <RunQualityComparison comparison={data.benchmark_v4} />
          {data.benchmark_v4.shared_extraction_run_id && <p>Verified shared extraction candidates.</p>}
          <h4>Comparison Run</h4>
          <GraphMetrics summary={data.benchmark_v4.left} quality={data.benchmark_v4.left_quality} />
          <BenchmarkEvidence summary={data.benchmark_v4.left} proofs={data.benchmark_v4.left_quality ? null : data.benchmark_v4.left_proofs} />
          {data.benchmark_v4.left_usage && <PipelineUsage usage={data.benchmark_v4.left_usage} complete={data.benchmark_v4.left.state === "complete"} />}
          <h4>Selected Run</h4>
          <GraphMetrics summary={data.benchmark_v4.right} quality={data.benchmark_v4.right_quality} />
          <BenchmarkEvidence summary={data.benchmark_v4.right} proofs={data.benchmark_v4.right_quality ? null : data.benchmark_v4.right_proofs} />
          {data.benchmark_v4.right_usage && <PipelineUsage usage={data.benchmark_v4.right_usage} complete={data.benchmark_v4.right.state === "complete"} />}
          <SemanticEvidenceComparison left={left} right={right} />
        </section>
      )}
      {data.benchmark && (
        <section aria-label="Condition-aligned protocol comparison">
          <h4>Condition-aligned comparison · descriptive deltas</h4>
          {data.benchmark.cohort ? (
            <p>
              All-condition Graph F1 Δ{" "}
              {signed(data.benchmark.cohort.all_condition_micro_f1)} · Family
              macro F1 Δ {signed(data.benchmark.family_macro_f1_delta)} ·
              Conditions {signed(data.benchmark.cohort.planned_conditions)} ·
              Exact graphs {signed(data.benchmark.cohort.exact_graphs)} ·
              TP/FP/FN {signed(data.benchmark.cohort.tp)}/
              {signed(data.benchmark.cohort.fp)}/
              {signed(data.benchmark.cohort.fn)} · {evidenceMetricLabels.complete_proof}{" "}
              {signed(data.benchmark.cohort.complete_proofs)}/
              {signed(data.benchmark.cohort.planned_proofs)} · {multiSourceProofCompletionLabel}{" "}
              {signed(data.benchmark.cohort.complete_joint_proofs)}/
              {signed(data.benchmark.cohort.planned_joint_proofs)}
            </p>
          ) : (
            <p>
              Condition deltas withheld because the verified scopes are
              incompatible.
            </p>
          )}
          <p>
            Differences between Runs remain descriptive and do not establish a
            causal effect.
          </p>
          {data.benchmark.families.length > 0 && (
            <div className="table-scroll">
              <table>
                <caption>Family deltas across planned Conditions</caption>
                <thead>
                  <tr>
                    <th>Family</th>
                    <th>Δ Graph F1</th>
                    <th>Δ exact graphs</th>
                    <th>Δ TP / FP / FN</th>
                    <th>Δ complete proofs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.benchmark.families.map((family) => (
                    <tr key={family.family}>
                      <th>{family.family}</th>
                      <td>{signed(family.all_condition_micro_f1)}</td>
                      <td>{signed(family.exact_graphs)}</td>
                      <td>
                        {signed(family.tp)} / {signed(family.fp)} /{" "}
                        {signed(family.fn)}
                      </td>
                      <td>{signed(family.complete_proofs)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {data.benchmark.conditions.length > 0 && (
            <div className="table-scroll">
              <table>
                <caption>
                  Condition-aligned changes, including unavailable outcomes
                </caption>
                <thead>
                  <tr>
                    <th>Family · Condition</th>
                    <th>Outcome left → right</th>
                    <th>Δ TP / FP / FN</th>
                    <th>Δ {evidenceMetricLabels.complete_proof}</th>
                    <th>Δ {multiSourceProofCompletionLabel}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.benchmark.conditions.map((item) => (
                    <tr key={`${item.family}:${item.condition}`}>
                      <th>
                        {item.family} · {item.condition}
                      </th>
                      <td>
                        {item.left_outcome.replaceAll("_", " ")} →{" "}
                        {item.right_outcome.replaceAll("_", " ")}
                      </td>
                      <td>
                        {signed(item.tp)} / {signed(item.fp)} /{" "}
                        {signed(item.fn)}
                      </td>
                      <td>
                        {signed(item.complete_proofs)}/
                        {signed(item.planned_proofs)}
                      </td>
                      <td>
                        {signed(item.complete_joint_proofs)}/
                        {signed(item.planned_joint_proofs)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
      <details>
        <summary>Paired observations and exclusions</summary>
        <pre>
          {JSON.stringify(
            { pairs: data.pairs, exclusions: data.exclusions },
            null,
            2,
          )}
        </pre>
      </details>
    </div>
  );
}
const signed = (value: number | null) =>
  value === null
    ? "Unavailable"
    : `${value > 0 ? "+" : ""}${Number.isInteger(value) ? value : value.toFixed(3)}`;

function BenchmarkRunInspection({
  workspace,
  run,
  benchmark,
  number,
  runs,
  copy,
  busy,
}: {
  workspace: WorkspaceDetail;
  run: RunDetail;
  benchmark: BenchmarkRun;
  number: number;
  runs: RunDetail[];
  copy?: () => void;
  busy: boolean;
}) {
  const [other, setOther] = useState("");
  const mixed = run.benchmark_v4;
  const showProtocol = mixed?.state !== "unmeasured" && (!run.quality || run.quality.observed_qualified_inputs > 0);
  const consensus = run.observations.find((row) => row.benchmark?.role === "consensus");
  return (
    <section className="run-inspection" aria-label={`Run ${number} details`}>
      <div className="section-heading">
        <div>
          <h2>Run {number} · Benchmark {mixed ? "v4" : "v3"}</h2>
          <small>
            {workspace.name} · {mixed ? "Mixed references" : "Verified read-only Run"} · {benchmark.scope.split}{" "}
            split ·{" "}
            {mixed?.state === "unmeasured"
              ? "Awaiting retained observations"
              : benchmark.scope.observation_origin === "live"
                ? mixed ? "Retained live execution" : "Verified live origin"
                : "Synthetic fixture"}
          </small>
        </div>
        {mixed && copy && <button className="secondary" disabled={busy} onClick={copy}>Copy to next draft</button>}
      </div>
      {!showProtocol && run.quality && <RunQuality quality={run.quality} />}
      {mixed && <BenchmarkV4Summary run={run} />}
      {showProtocol && <BenchmarkRunSummary run={run} benchmark={benchmark} />}
      <BenchmarkFamilyExplorer
        key={run.id}
        run={run}
        renderCondition={(observation, selectedEdgeKey, onSelectedEdgeChange) => (
          <ConditionInspection
            key={observation.id}
            runId={run.id}
            observation={observation}
            selectedEdgeKey={selectedEdgeKey}
            onSelectedEdgeChange={onSelectedEdgeChange}
          />
        )}
      />
      {consensus && (
        <details className="family-panel">
          <summary>U revision 8 · Consensus adjudication · Single evaluation input</summary>
          <ConditionInspection runId={run.id} observation={consensus} />
        </details>
      )}
      <label>
        Compare with verified Run
        <select
          value={other}
          onChange={(event) => setOther(event.target.value)}
        >
          <option value="">Choose a Run</option>
          {runs
            .filter((value) => value.id !== run.id)
            .map((value) => (
              <option key={value.id} value={value.id}>
                Run {workspace.run_numbers?.[value.id] ?? workspace.run_ids.indexOf(value.id) + 1}
              </option>
            ))}
        </select>
      </label>
      {other && (
        <RunComparisonPanel
          experiment={workspace.id}
          left={other}
          right={run.id}
        />
      )}
    </section>
  );
}
