import { useState } from "react";
import type { RunStatus } from "../shared/contracts";

export function LiveReview({
  data,
  busy,
  continuing,
  error,
  approve,
  refresh,
}: {
  data: RunStatus;
  busy: boolean;
  continuing: boolean;
  error: string;
  approve: () => void;
  refresh: () => void;
}) {
  const [checked, setChecked] = useState(false);
  const budget = data.task_budget;
  if (!budget)
    return (
      <p role="alert">
        Live task accounting is unavailable. Restore the ledger before approving
        execution.
      </p>
    );
  return (
    <section
      className="live-review"
      aria-label="Approve bounded live execution"
    >
      <h2>
        {continuing
          ? "Approve remaining live execution"
          : "Approve live execution"}
      </h2>
      <p>{budget.label}</p>
      <dl>
        <dt>Task identity</dt>
        <dd>{budget.task_id}</dd>
        <dt>Task paid attempts used</dt>
        <dd>{budget.used}</dd>
        <dt>Current task allowance</dt>
        <dd>{budget.cap}</dd>
        <dt>Current remaining allowance</dt>
        <dd>{budget.remaining}</dd>
        <dt>Proposed total task cap</dt>
        <dd>{data.plan.preview.proposal.task_call_cap}</dd>
        <dt>This invocation: maximum new calls</dt>
        <dd>{data.plan.preview.invocation_cap}</dd>
        <dt>Unattempted calls in frozen matrix</dt>
        <dd>{data.remaining_attempts}</dd>
      </dl>
      <p>
        Approval applies only to this frozen plan and this invocation. Uncertain
        attempts remain counted and will not be retried. A call cap is not a
        guaranteed dollar cap.
      </p>
      <p>{data.plan.preview.cost_reason}</p>
      <button type="button" disabled={busy} onClick={refresh}>
        Refresh task budget
      </button>
      {error && <p role="alert">{error}</p>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (checked) approve();
        }}
      >
        <label className="approval-choice">
          <input
            type="checkbox"
            checked={checked}
            required
            disabled={busy}
            onChange={(event) => setChecked(event.target.checked)}
          />
          <span>
            I approve this task cap and bounded live invocation for the frozen
            plan.
          </span>
        </label>
        <button
          type="submit"
          disabled={busy || !checked || !!data.active_plan_id || !!error}
        >
          {busy
            ? "Submitting approval…"
            : continuing
              ? "Authorize and continue"
              : "Authorize and start"}
        </button>
      </form>
    </section>
  );
}
