import { useRef, useState } from "react";
import type { ExecutionAvailability, RunDetail } from "../shared/contracts";
import { authorizeRun, controlRun } from "./api";
import { PlanSummary } from "../configuration/PlanSummary";

export function RunExecution({
  run,
  availability,
  refresh,
}: {
  run: RunDetail;
  availability: ExecutionAvailability | null;
  refresh: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [review, setReview] = useState(false);
  const [checked, setChecked] = useState(false);
  const [authorized, setAuthorized] = useState<string | null>(null);
  const command = useRef<string | null>(null);
  const lock = useRef(false);
  const live = run.plan.preview.proposal.execution_mode === "live";
  const continuing = ["stopped", "interrupted", "failed"].includes(
    run.lifecycle,
  );
  const active = availability?.active_run_id;
  const ready = run.lifecycle === "frozen" || continuing;
  const budget = availability?.task_budget;
  async function act(action: "authorize" | "start" | "continue" | "stop") {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const request_id =
      action === "stop"
        ? crypto.randomUUID()
        : (authorized ?? command.current ?? crypto.randomUUID());
    if (action !== "stop") command.current = request_id;
    try {
      if (action === "authorize") {
        if (!budget)
          throw new Error("Task accounting unavailable. Refresh status.");
        const approval = await authorizeRun(run.experiment_id, run.id, {
          request_id,
          plan_digest: run.plan.digest,
          approved: true,
          continuation: continuing,
          task_id: budget.task_id,
          expected_task_usage: budget.used,
          expected_task_cap: budget.cap,
          task_cap: run.plan.preview.proposal.task_call_cap,
        });
        setAuthorized(approval.invocation_id);
      } else {
        await controlRun(run.experiment_id, run.id, action, {
          request_id,
          plan_digest: run.plan.digest,
        });
        command.current = null;
        setAuthorized(null);
        setReview(false);
        setChecked(false);
      }
      refresh();
    } catch (error) {
      setError((error as Error).message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <section className="run-execution" aria-label="Run execution">
      <div className="section-heading">
        <h3>Execution · {run.lifecycle}</h3>
        <button className="secondary" disabled={busy} onClick={refresh}>
          Refresh status
        </button>
      </div>
      {active && (
        <p role="status">
          {active === run.id
            ? "This Run is active. Closing the browser will not stop it."
            : `Another Run is active: ${active}. Wait for it to finish before starting.`}
        </p>
      )}
      {run.lifecycle === "running" && (
        <button disabled={busy} onClick={() => void act("stop")}>
          Stop after current attempt
        </button>
      )}
      {continuing && !review && (
        <button disabled={busy || !!active} onClick={() => setReview(true)}>
          Review continuation
        </button>
      )}
      {ready && (!continuing || review) && (
        <>
          <PlanSummary preview={run.plan.preview} frozen />
          {continuing && (
            <p>
              Existing results are retained. Uncertain attempts remain counted
              and will not be retried.
            </p>
          )}
          {live && !authorized && (
            <section className="live-review">
              <h3>Authorize bounded live execution</h3>
              {budget ? (
                <>
                  <p>{budget.label}</p>
                  <dl>
                    <dt>Task paid attempts used</dt>
                    <dd>{budget.used}</dd>
                    <dt>Current task allowance</dt>
                    <dd>{budget.cap}</dd>
                    <dt>Remaining allowance</dt>
                    <dd>{budget.remaining}</dd>
                    <dt>Proposed total task cap</dt>
                    <dd>{run.plan.preview.proposal.task_call_cap}</dd>
                    <dt>Invocation attempt cap</dt>
                    <dd>{run.plan.preview.invocation_cap}</dd>
                  </dl>
                  <p>
                    Authorization applies only to this frozen Run and
                    invocation. A call cap is not a guaranteed dollar cap.
                  </p>
                  <label className="approval-choice">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => setChecked(e.target.checked)}
                      disabled={busy}
                    />
                    <span>
                      I approve this task cap and bounded live invocation for
                      the frozen Run.
                    </span>
                  </label>
                  <button
                    disabled={!checked || busy || !!active}
                    onClick={() => void act("authorize")}
                  >
                    Authorize invocation
                  </button>
                </>
              ) : (
                <p role="alert">
                  {availability?.accounting_reason ??
                    "Task budget unavailable. Refresh status before authorizing."}
                </p>
              )}
            </section>
          )}
          {authorized && (
            <p role="status">Authorized. Start this invocation when ready.</p>
          )}
          {(!live || authorized) && (
            <button
              disabled={busy || !availability || !!active}
              onClick={() => void act(continuing ? "continue" : "start")}
            >
              {continuing ? "Continue Run" : "Start Run"}
            </button>
          )}
        </>
      )}
      {error && (
        <p role="alert">
          {error}{" "}
          <button
            disabled={busy}
            onClick={() => {
              command.current = null;
              setAuthorized(null);
              setChecked(false);
              setError("");
              refresh();
            }}
          >
            Refresh and review again
          </button>
        </p>
      )}
    </section>
  );
}
