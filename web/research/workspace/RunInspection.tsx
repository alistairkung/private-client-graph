import { useCallback, useState } from "react";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
import { ObservationInspection } from "./ObservationInspection";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { compareRuns } from "./api";
import { metric, money } from "./RunChart";

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
            {workspace.name} · {configuration.input_mode} inputs ·{" "}
            {run.lifecycle}
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
                  Run {runs.indexOf(item) + 1}
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
        · {data.matched_inputs} exactly matched inputs
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
