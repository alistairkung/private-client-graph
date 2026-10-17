import { useEffect, useState } from "react";
import type { Capabilities, Preview, Proposal } from "../shared/contracts";
import { freeze, preview as requestPreview } from "./api";
import { PipelineFields } from "./Fields";
import { Pipeline } from "./Pipeline";
import { InputSelection } from "./InputSelection";
import { PlanSummary } from "./PlanSummary";
import "./configuration.css";

export function Configuration({
  capabilities,
  initial,
  onProposalChange,
}: {
  capabilities: Capabilities;
  initial?: Proposal;
  onProposalChange?: (proposal: Proposal) => void;
}) {
  const [proposal, setProposal] = useState<Proposal>(
    initial ?? {
      retained_experiment_id: null,
      retained_run_id: null,
      input_ids: capabilities.inputs.map((input) => input.id),
      input_mode: "saved",
      execution_mode: "replay",
      resolver: "none",
      extraction_samples: 1,
      resolver_repetitions: 1,
      invocation_cap: 0,
      temperature: null,
      timeout_seconds: 90,
      model: "deepseek-flash",
      task_call_cap: 0,
    },
  );
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setPreview(null);
    setError("");
    const timer = setTimeout(() => {
      requestPreview(proposal, controller.signal)
        .then((value) => {
          if (!controller.signal.aborted) setPreview(value);
        })
        .catch((error) => {
          if (!controller.signal.aborted) setError(error.message);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [proposal]);
  function update(changes: Partial<Proposal>) {
    const next = { ...proposal, ...changes };
    setProposal(next);
    onProposalChange?.(next);
  }
  async function review() {
    setBusy(true);
    setError("");
    try {
      const plan = await freeze(proposal);
      window.location.hash = `plan=${plan.id}`;
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <a href="#browse=1">Back to experiments</a>
      <h1>New experiment</h1>
      <p>
        Configure a finite experiment. Review the frozen plan before running it.
      </p>
      <form
        className="configuration-layout"
        onSubmit={(event) => {
          event.preventDefault();
          void review();
        }}
      >
        <InputSelection
          proposal={proposal}
          capabilities={capabilities}
          update={update}
          busy={busy}
        />
        <Pipeline
          proposal={proposal}
          capabilities={capabilities}
          update={update}
          busy={busy}
        />
        <div className="configuration-review execution-bench">
          <section className="run-status" aria-label="Draft execution status">
            <h2>Execution</h2>
            <p>
              {preview ? "Ready for plan review" : "Draft · Preview pending"}
            </p>
            <button type="submit" disabled={busy || !preview}>
              {busy ? "Freezing plan…" : "Review frozen plan"}
            </button>
            <p>Freezing does not start execution or authorize paid calls.</p>
          </section>
          <div className="execution-review">
            {proposal.resolver === "none" && (
              <details>
                <summary>Experiment settings and invocation limits</summary>
                <PipelineFields
                  proposal={proposal}
                  capabilities={capabilities}
                  update={update}
                  busy={busy}
                />
              </details>
            )}
            {preview ? (
              <PlanSummary preview={preview} />
            ) : (
              <p role="status">
                {error
                  ? "Preview unavailable. Check the configuration fields."
                  : "Updating server preview…"}
              </p>
            )}
            {error && <p role="alert">{error}</p>}
          </div>
        </div>
      </form>
      <section className="evaluation-empty">
        <h2>Evaluation</h2>
        <p>
          Completed observations will appear here for baseline and treatment
          comparison, then exact Evidence inspection.
        </p>
      </section>
    </>
  );
}
