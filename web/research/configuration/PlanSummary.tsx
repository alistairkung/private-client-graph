import type { Preview } from "../shared/contracts";

export function PlanSummary({
  preview,
  frozen = false,
}: {
  preview: Preview;
  frozen?: boolean;
}) {
  return (
    <section
      className="plan-summary"
      aria-label="Server-provided execution summary"
    >
      <h2>Review execution</h2>
      <p>
        {preview.proposal.execution_mode === "replay"
          ? "Saved extraction replay · No resolution"
          : preview.proposal.execution_mode === "live"
            ? "Live provider · Approval required before execution"
            : "Recorded demonstration · Not live quality"}
      </p>
      <dl>
        <dt>Maximum extraction calls</dt>
        <dd>{preview.extraction_call_maximum}</dd>
        <dt>Maximum resolution calls</dt>
        <dd>{preview.resolution_call_maximum}</dd>
        <dt>Full matrix maximum</dt>
        <dd>{preview.matrix_call_maximum}</dd>
        <dt>Invocation cap</dt>
        <dd>{preview.invocation_cap}</dd>
        <dt>Planned observations</dt>
        <dd>{preview.planned_observations}</dd>
        <dt>
          Task paid calls used / allowance
          {frozen && preview.proposal.execution_mode === "live"
            ? " at freeze"
            : ""}
        </dt>
        <dd>
          {preview.task_paid_usage} / {preview.task_paid_allowance}
        </dd>
        <dt>
          Paid calls remaining
          {frozen && preview.proposal.execution_mode === "live"
            ? " at freeze"
            : ""}
        </dt>
        <dd>{preview.task_paid_remaining}</dd>
      </dl>
      <p className="muted">{preview.cost_reason}</p>
      <section aria-label="Selected inputs">
        <h3>Selected inputs</h3>
        <ul>
          {preview.inputs.map((input) => (
            <li key={input.id}>
              {input.id}
              <small>
                {input.case_id} · {input.cohort}
              </small>
            </li>
          ))}
        </ul>
      </section>
      <details>
        <summary>Input hashes</summary>
        {preview.inputs.map((input) => (
          <div key={input.id}>
            <h3>
              {input.id} · {input.cohort}
            </h3>
            <dl>
              {Object.entries(input.hashes).map(([file, hash]) => (
                <div key={file}>
                  <dt>{file}</dt>
                  <dd>{hash}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </details>
    </section>
  );
}
