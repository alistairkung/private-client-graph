import { useEffect, useRef, useState } from "react";
import type { ExecutionAvailability, RunDetail } from "../shared/contracts";
import { authorizeRun, controlRun } from "./api";
import { ReviewDialog } from "./ReviewDialog";
import { ReviewSummary } from "./ReviewSummary";
import { ArchiveRun } from "./ArchiveRun";

export function RunExecution({
  run,
  availability,
  refresh,
  reviewRequested = false,
  number,
  copy,
  archived,
}: {
  run: RunDetail;
  availability: ExecutionAvailability | null;
  refresh: () => void;
  reviewRequested?: boolean;
  number: number;
  copy?: () => void;
  archived?: () => void;
}) {
  const [pending, setPending] = useState<"authorize" | "start" | "continue" | "stop" | null>(null);
  const busy = pending !== null;
  const [error, setError] = useState("");
  const [review, setReview] = useState(reviewRequested);
  useEffect(() => {
    if (reviewRequested) setReview(true);
  }, [reviewRequested]);
  const [checked, setChecked] = useState(false);
  const [authorized, setAuthorized] = useState<string | null>(null);
  const command = useRef<string | null>(null);
  const lock = useRef(false);
  const plan = run.plan;
  if (!plan || (run.benchmark && !run.benchmark_v4)) return null;
  const live = plan.preview.proposal.execution_mode === "live";
  const continuing = ["stopped", "interrupted", "failed"].includes(
    run.lifecycle,
  );
  const active = availability?.active_run_id;
  const ready = run.lifecycle === "frozen" || continuing;
  const budget = availability?.task_budget;
  const proposedCap = plan.preview.proposal.task_call_cap;
  const capBlocked = live && !!budget && (proposedCap < budget.cap || proposedCap <= budget.used);
  const act = async (action: "authorize" | "start" | "continue" | "stop") => {
    if (lock.current) return;
    lock.current = true;
    setPending(action);
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
          plan_digest: plan.digest,
          approved: true,
          continuation: continuing,
          task_id: budget.task_id,
          expected_task_usage: budget.used,
          expected_task_cap: budget.cap,
          task_cap: plan.preview.proposal.task_call_cap,
        });
        setAuthorized(approval.invocation_id);
      } else {
        await controlRun(run.experiment_id, run.id, action, {
          request_id,
          plan_digest: plan.digest,
        });
        command.current = null;
        setAuthorized(null);
        setReview(false);
        setChecked(false);
      }
      refresh();
    } catch (error) {
      setError((error as Error).message);
      setReview(false);
      refresh();
    } finally {
      lock.current = false;
      setPending(null);
    }
  };
  const title = continuing
    ? `Review continuation for Run ${number}`
    : live && !authorized
      ? `Authorize Run ${number}`
      : `Ready to start Run ${number}`;
  const failure = error && (
    <p role="alert">
      {error}{" "}
      {ready && live && <button
        disabled={busy}
        onClick={() => {
          command.current = null;
          setAuthorized(null);
          setChecked(false);
          setError("");
          refresh();
          setReview(true);
        }}
      >
        Review a new authorization
      </button>}
    </p>
  );
  return (
    <section className="run-execution" aria-label="Run execution">
      <div className="section-heading">
        <h3>
          Run {number} · Execution · {run.lifecycle}
        </h3>
        <div className="run-actions">
          {ready && (
            <button disabled={busy} onClick={() => setReview(true)}>
              {continuing ? "Review continuation" : error
                ? live && !authorized ? "Review authorization" : "Review and retry start"
                : "Review frozen Run"}
            </button>
          )}
          {ready && copy && (
            <button className="secondary" disabled={busy} onClick={copy}>Use configuration in draft</button>
          )}
          {run.lifecycle === "running" && (
            <button disabled={busy} onClick={() => void act("stop")}>
              Stop after current attempt
            </button>
          )}
          <button className="secondary" disabled={busy} onClick={refresh}>
            Refresh status
          </button>
          {run.can_archive && archived && (
            <ArchiveRun run={run} number={number} disabled={busy || active === run.id} archived={archived} />
          )}
        </div>
      </div>
      {active && (
        <p role="status">
          {active === run.id
            ? "This Run is active. Closing the browser will not stop it."
            : `Another Run is active: ${active}. Wait for it to finish before starting.`}
        </p>
      )}
      {continuing && run.execution_message && <p role="status">{run.execution_message}</p>}
      {capBlocked && ready && (
        <p role="status">This frozen task cap cannot cover more attempts. Use the configuration in the draft and review a new total task cap.</p>
      )}
      {!review && failure}
      {ready && review && (
        <ReviewDialog
          title={title}
          close={() => setReview(false)}
          busy={busy}
          actions={
            <>
              <small>
                {live && !authorized
                  ? "Authorization applies only to this frozen Run and invocation."
                  : "Execution begins only when you start this invocation."}
              </small>
              {live && !authorized ? (
                <button
                  disabled={!checked || !budget || capBlocked || busy || !!active}
                  onClick={() => void act("authorize")}
                >
                  {pending === "authorize" ? "Authorizing…" : "Authorize invocation"}
                </button>
              ) : (
                <button
                  disabled={busy || !availability || capBlocked || !!active}
                  onClick={() => void act(continuing ? "continue" : "start")}
                >
                  {pending ? "Submitting…" : continuing ? "Continue Run" : "Start Run"}
                </button>
              )}
            </>
          }
        >
          <p className="frozen-notice">Configuration frozen · Run {number}</p>
          <ReviewSummary preview={plan.preview} frozen />
          {continuing && (
            <p>
              Existing results are retained. Uncertain attempts remain counted
              and will not be retried.
            </p>
          )}
          {live && !authorized && (
            <section className="live-review">
              {budget ? (
                <>
                  <h3>Task allowance</h3>
                  <p>{budget.label}</p>
                  <dl className="review-summary">
                    <dt>Paid attempts used / current cap</dt>
                    <dd>
                      {budget.used} / {budget.cap}
                    </dd>
                    <dt>Remaining allowance</dt>
                    <dd>{budget.remaining}</dd>
                    <dt>Proposed total task cap</dt>
                    <dd>{plan.preview.proposal.task_call_cap}</dd>
                  </dl>
                  <p>A call cap is not a guaranteed dollar cap.</p>
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
          <button className="secondary" disabled={busy} onClick={refresh}>
            Refresh task status
          </button>
          {capBlocked && <p role="status">Close this review and use the configuration in the draft to propose a new total task cap.</p>}
        </ReviewDialog>
      )}
    </section>
  );
}
