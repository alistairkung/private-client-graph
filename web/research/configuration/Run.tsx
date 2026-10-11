import { useEffect, useRef, useState } from "react";
import type { Proposal, RunStatus } from "../shared/contracts";
import { control, progress, authorize } from "./api";
import { LiveReview } from "./LiveReview";
import { PlanSummary } from "./PlanSummary";
import "./configuration.css";

import { Pipeline } from "./Pipeline";
import { Results } from "../results/Results";

export function Run({
  id,
  edit,
  params,
}: {
  id: string;
  params: URLSearchParams;
  edit: (proposal: Proposal) => void;
}) {
  const [data, setData] = useState<RunStatus | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [retry, setRetry] = useState(0);
  const requestIds = useRef<Partial<Record<string, string>>>({});
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const status = await progress(id, controller.signal);
        if (controller.signal.aborted) return;
        setData(status);
        setError("");
        if (
          status.state === "running" ||
          status.state === "stopping" ||
          status.active_plan_id
        )
          timer = setTimeout(load, 1000);
      } catch (error) {
        if (!controller.signal.aborted) setError((error as Error).message);
      }
    };
    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [id, retry]);
  async function act(action: "start" | "stop" | "continue") {
    if (!data) return;
    setBusy(true);
    setError("");
    const requestId = requestIds.current[action] ?? crypto.randomUUID();
    requestIds.current[action] = requestId;
    try {
      const result = await control(id, action, {
        request_id: requestId,
        plan_digest: data.plan.digest,
      });
      setData(result);
      delete requestIds.current[action];
      setReviewing(false);
      setRetry((value) => value + 1);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function approveLive() {
    if (!data?.task_budget) return;
    setBusy(true);
    setError("");
    const requestId = requestIds.current.approve ?? crypto.randomUUID();
    requestIds.current.approve = requestId;
    try {
      const result = await authorize(id, {
        request_id: requestId,
        plan_digest: data.plan.digest,
        approved: true,
        task_id: data.task_budget.task_id,
        expected_task_usage: data.task_budget.used,
        expected_task_cap: data.task_budget.cap,
        task_cap: data.plan.preview.proposal.task_call_cap,
        continuation: data.state !== "frozen",
      });
      setData(result);
      delete requestIds.current.approve;
      setReviewing(false);
      setRetry((value) => value + 1);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <>
        <a href="#browse=1">Back to experiments</a>
        <h1>Frozen experiment</h1>
        {error ? <p role="alert">{error}</p> : <p>Loading plan…</p>}
        <button onClick={() => setRetry((value) => value + 1)}>
          Retry read
        </button>
      </>
    );
  const live = data.plan.preview.proposal.execution_mode === "live";
  const another = data.active_plan_id && data.active_plan_id !== id;
  return (
    <>
      <a href="#browse=1">Back to experiments</a>
      <h1>Frozen experiment</h1>
      <Pipeline proposal={data.plan.preview.proposal} />
      <div className="execution-bench">
        <section className="run-status" aria-label="Execution status">
          <h2>Execution · {data.state}</h2>
          <progress
            aria-label="Recorded observations"
            max={Math.max(1, data.planned_observations)}
            value={data.completed_observations}
          />
          <p role="status">{data.message}</p>
          <p>Current work: {data.current_work ?? "Unavailable"}</p>
          <p>{data.remaining_attempts} remaining attempts</p>
          <p>
            {data.completed_observations} / {data.planned_observations}{" "}
            observations recorded · {data.attempts} provider attempts ·{" "}
            {data.uncertain_attempts} uncertain
          </p>
          {(data.state === "running" || data.state === "stopping") && (
            <p>Browser closure does not stop this experiment.</p>
          )}
          {another && (
            <p>
              Another experiment is active.{" "}
              <a href={`#plan=${data.active_plan_id}`}>
                Open active experiment
              </a>
            </p>
          )}
          {error && !(live && (data.state === "frozen" || reviewing)) && (
            <p role="alert">
              {error}{" "}
              <button onClick={() => setRetry((value) => value + 1)}>
                Refresh status
              </button>
            </p>
          )}
          <div className="run-actions">
            {data.state === "running" && (
              <button disabled={busy} onClick={() => act("stop")}>
                Stop after current attempt
              </button>
            )}
            {["stopped", "interrupted", "failed"].includes(data.state) &&
              !reviewing && (
                <button
                  disabled={busy || !!another}
                  onClick={() => setReviewing(true)}
                >
                  Review continuation
                </button>
              )}
            <a href={`#experiment=${data.result_id}`}>
              Inspect persisted results
            </a>
          </div>
        </section>
        <div className="execution-review">
          {reviewing && (
            <section className="continuation">
              <h2>Review remaining execution</h2>
              <p>
                Provider attempts remaining: {data.remaining_attempts}.
                Invocation cap: {data.plan.preview.invocation_cap}. Uncertain
                attempts stay counted and will not be resubmitted.
              </p>
              <p>
                {live
                  ? "Review the task budget and explicitly approve continuation after the frozen configuration."
                  : "No paid calls are authorized. Existing results are retained."}
              </p>
              {!live && (
                <button
                  disabled={busy || !!another}
                  onClick={() => act("continue")}
                >
                  Continue offline execution
                </button>
              )}
            </section>
          )}
          <div className="frozen-layout">
            <PlanSummary preview={data.plan.preview} frozen />
            <details>
              <summary>Frozen configuration</summary>
              <dl>
                <dt>Input mode</dt>
                <dd>
                  {data.plan.preview.proposal.input_mode === "saved"
                    ? "Saved extraction snapshots"
                    : "Fresh extraction samples"}
                </dd>
                <dt>Resolver</dt>
                <dd>
                  {data.plan.preview.proposal.resolver === "none"
                    ? "No resolution"
                    : "Generative · Full Source"}
                </dd>
                <dt>Extraction samples</dt>
                <dd>{data.plan.preview.proposal.extraction_samples}</dd>
                <dt>Resolver repetitions</dt>
                <dd>{data.plan.preview.proposal.resolver_repetitions}</dd>
                <dt>Model</dt>
                <dd>{data.plan.preview.proposal.model}</dd>
                <dt>Temperature</dt>
                <dd>
                  {data.plan.preview.proposal.temperature ?? "Provider default"}
                </dd>
                <dt>Timeout (seconds)</dt>
                <dd>{data.plan.preview.proposal.timeout_seconds}</dd>
              </dl>
              <details>
                <summary>Plan identity and digest</summary>
                <dl>
                  <dt>Plan identity</dt>
                  <dd>{data.plan.id}</dd>
                  <dt>Task identity</dt>
                  <dd>{data.plan.task_id}</dd>
                  <dt>Plan digest</dt>
                  <dd>{data.plan.digest}</dd>
                </dl>
              </details>
            </details>
          </div>
          {live && (data.state === "frozen" || reviewing) && (
            <LiveReview
              key={`${data.task_budget?.used}-${data.task_budget?.cap}`}
              data={data}
              busy={busy}
              error={error}
              continuing={data.state !== "frozen"}
              approve={() => void approveLive()}
              refresh={() => {
                delete requestIds.current.approve;
                setRetry((value) => value + 1);
              }}
            />
          )}
          <div className="frozen-actions">
            <div className="run-actions">
              {data.state === "frozen" && !live && (
                <button
                  disabled={busy || !!another}
                  onClick={() => act("start")}
                >
                  {data.plan.preview.proposal.execution_mode === "replay"
                    ? "Run replay"
                    : "Run recorded demonstration"}
                </button>
              )}
              <button
                disabled={busy}
                onClick={() => edit(data.plan.preview.proposal)}
              >
                Edit configuration
              </button>
            </div>
            <p className="muted">
              Editing creates a new proposal requiring a new frozen plan. This
              plan and its results remain unchanged.
            </p>
          </div>
        </div>
      </div>
      <Results
        id={data.result_id}
        params={params}
        historyLink="#browse=1"
        embedded
        refresh={data.completed_observations + data.attempts + retry}
      />
    </>
  );
}
