import { useEffect, useRef, useState } from "react";
import type {
  Capabilities,
  CaseMetadata,
  Preview,
  RunDraft,
  RunConfiguration,
} from "../shared/contracts";
import { Pipeline } from "../configuration/Pipeline";
import { PipelineFields } from "../configuration/Fields";
import { ReviewDialog } from "./ReviewDialog";
import { ReviewSummary } from "./ReviewSummary";
import { CasePicker } from "./CasePicker";
import { freezeDraft, getRun, previewDraft, saveDraft } from "./api";
import "../configuration/configuration.css";

export function DraftEditor({
  id,
  draft,
  cases,
  capabilities,
  saved,
  frozen,
  saving,
  disabled = false,
  runIds = [],
}: {
  id: string;
  draft: RunDraft;
  cases: CaseMetadata[];
  capabilities: Capabilities;
  saved: (draft: RunDraft) => void;
  frozen: (id: string) => void;
  saving: (busy: boolean) => void;
  disabled?: boolean;
  runIds?: string[];
}) {
  const [configuration, setConfiguration] = useState<RunConfiguration>(
    draft.configuration,
  );
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState("");
  const [freezing, setBusy] = useState(false);
  const busy = freezing || disabled;
  const [review, setReview] = useState(false);
  const [state, setState] = useState("Saved");
  const revision = useRef(draft.revision);
  const persisted = useRef(draft);
  const generation = useRef(0);
  const pending = useRef<Promise<void>>(Promise.resolve());
  const lock = useRef(false);
  const freezeId = useRef(crypto.randomUUID());
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const sequence = ++generation.current;
    const controller = new AbortController();
    setPreview(null);
    setError("");
    setState("Checking draft…");
    saving(true);
    const timer = setTimeout(() => {
      pending.current = pending.current
        .catch(() => {})
        .then(async () => {
          if (controller.signal.aborted) return;
          try {
            const value = await previewDraft(configuration, controller.signal);
            if (controller.signal.aborted) return;
            // Serialize writes: a previous request may have committed after its read was aborted.
            const updated =
              JSON.stringify(configuration) ===
              JSON.stringify(persisted.current.configuration)
                ? persisted.current
                : await saveDraft(id, {
                    request_id: crypto.randomUUID(),
                    expected_revision: revision.current,
                    configuration,
                  });
            persisted.current = updated;
            revision.current = updated.revision;
            if (sequence === generation.current) {
              setPreview(value);
              setState("Saved");
              saving(false);
              saved(updated);
            }
          } catch (error) {
            if (!controller.signal.aborted) {
              setError((error as Error).message);
              setState("Draft not saved");
            }
          }
        });
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [configuration, id, retry]); // saved is a notification, not an input to persistence.
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (state !== "Saved") {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [state]);
  function update(changes: Partial<RunConfiguration>) {
    setReview(false);
    setPreview(null);
    setConfiguration((value) => ({ ...value, ...changes }));
    freezeId.current = crypto.randomUUID();
  }
  async function selectInputOrigin(runId: string) {
    if (!runId) {
      update({
        retained_experiment_id: null,
        retained_run_id: null,
        input_ids: cases
          .filter((item) => item.kind === "benchmark")
          .map((item) => item.id),
      });
      return;
    }
    setBusy(true);
    setError("");
    try {
      const run = await getRun(id, runId);
      if (
        run.lifecycle !== "complete" ||
        run.plan.preview.proposal.input_mode !== "fresh" ||
        run.plan.preview.proposal.resolver !== "none"
      ) {
        throw new Error("Select a completed fresh no-resolution Run.");
      }
      update({
        retained_experiment_id: id,
        retained_run_id: runId,
        input_ids: run.observations.map((item) => item.sample_id),
        input_mode: "saved",
        extraction_samples: 1,
        resolver: "none",
        execution_mode: "replay",
        invocation_cap: 0,
        task_call_cap: 0,
      });
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="next-run" aria-label="Next Run Draft">
      <div className="section-heading">
        <div>
          <h2>Next run</h2>
          <small role="status">{state}</small>
        </div>
        <button disabled={!preview || busy} onClick={() => setReview(true)}>
          Run
        </button>
      </div>
      <label>
        Input origin
        <select
          aria-label="Input origin"
          disabled={busy}
          value={configuration.retained_run_id ?? ""}
          onChange={(event) => void selectInputOrigin(event.target.value)}
        >
          <option value="">Repository case fixtures</option>
          {runIds.map((runId) => (
            <option key={runId} value={runId}>Retained extraction — {runId}</option>
          ))}
        </select>
      </label>
      {configuration.retained_run_id ? (
        <p>
          Using all {configuration.input_ids.length} retained extractions from Run {configuration.retained_run_id}.
          Source order, evidence and original provider outputs are verified before freezing.
        </p>
      ) : (
        <CasePicker
          cases={cases}
          selected={configuration.input_ids}
          update={(input_ids) => update({ input_ids })}
          disabled={busy}
        />
      )}
      <Pipeline
        persistent
        proposal={configuration}
        capabilities={capabilities}
        update={update}
        busy={busy}
      />
      {configuration.resolver === "none" && (
        <details className="draft-options">
          <summary>Run settings and invocation limits</summary>
          <PipelineFields
            proposal={configuration}
            capabilities={capabilities}
            update={update}
            busy={busy}
          />
        </details>
      )}
      {error && (
        <p role="alert">
          {error}{" "}
          <button onClick={() => setRetry((value) => value + 1)}>
            Retry draft save
          </button>
          <button onClick={() => window.location.reload()}>
            Reload saved draft
          </button>
        </p>
      )}
      {review && preview && (
        <ReviewDialog
          title="Review next Run"
          close={() => setReview(false)}
          busy={busy}
          actions={
            <>
              <small>
                Freezing preserves this configuration. It does not start
                execution.
              </small>
              <button
                disabled={busy}
                onClick={async () => {
                  if (lock.current) return;
                  lock.current = true;
                  setBusy(true);
                  setError("");
                  try {
                    const result = await freezeDraft(id, {
                      request_id: freezeId.current,
                      expected_revision: revision.current,
                    });
                    freezeId.current = crypto.randomUUID();
                    setReview(false);
                    frozen(result.id);
                  } catch (error) {
                    setError((error as Error).message);
                  } finally {
                    lock.current = false;
                    setBusy(false);
                  }
                }}
              >
                {busy ? "Freezing…" : "Freeze Run"}
              </button>
            </>
          }
        >
          <ReviewSummary preview={preview} />
          {error && <p role="alert">{error}</p>}
        </ReviewDialog>
      )}
    </section>
  );
}
