import { useEffect, useState } from "react";
import type { Capabilities, Preview, Proposal } from "../shared/contracts";
import { freeze, preview as requestPreview } from "./api";
import { InputFields, PipelineFields } from "./Fields";
import { PlanSummary } from "./PlanSummary";
import "./configuration.css";

export function Configuration({
  capabilities,
  initial,
}: {
  capabilities: Capabilities;
  initial?: Proposal;
}) {
  const [proposal, setProposal] = useState<Proposal>(
    initial ?? {
      input_ids: ["case_03_fixture"],
      input_mode: "saved",
      execution_mode: "replay",
      resolver: "none",
      extraction_samples: 1,
      resolver_repetitions: 1,
      invocation_cap: 0,
      temperature: null,
      timeout_seconds: 90,
      model: "deepseek-flash",
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
    setProposal((current) => ({ ...current, ...changes }));
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
      <a href="#">Back to experiments</a>
      <h1>New experiment</h1>
      <p>
        Configure a finite offline experiment. Review the frozen plan before
        running it.
      </p>
      <form
        className="configuration-layout"
        onSubmit={(event) => {
          event.preventDefault();
          void review();
        }}
      >
        <div className="configuration-fields">
          <InputFields
            proposal={proposal}
            capabilities={capabilities}
            update={update}
            busy={busy}
          />
          <PipelineFields
            proposal={proposal}
            capabilities={capabilities}
            update={update}
            busy={busy}
          />
        </div>
        <div className="configuration-review">
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
          <button type="submit" disabled={busy || !preview}>
            {busy ? "Freezing plan…" : "Review frozen plan"}
          </button>
          <p className="muted">
            Freezing does not start execution or authorize paid calls.
          </p>
        </div>
      </form>
    </>
  );
}
