import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { BenchmarkRoster, Capabilities, Preview, RunDraft, WorkspaceDetail, WorkspaceHistoryItem } from "../shared/contracts";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { createWorkspace, freezeDraft, getCases, getRuns, getWorkspace, previewDraft, saveDraft } from "./api";
import { CasePicker } from "./CasePicker";
import { ReviewDialog } from "./ReviewDialog";
import { ReviewSummary } from "./ReviewSummary";
import { benchmarkExtractors, runPresetConfiguration, type RunPreset } from "./run-presets";

const newExperiment = "new";

type PendingRun = {
  preview: Preview;
  name: string;
  workspace?: WorkspaceDetail;
  savedDraft?: RunDraft;
  createId: string;
  saveId: string;
  freezeId: string;
};

async function freezeReviewedRun(review: PendingRun) {
  // Keep successful steps and command IDs so retrying a partial submission resumes it.
  const workspace = review.workspace ??= await createWorkspace({
    name: review.name,
    hypothesis: null,
    description: null,
    request_id: review.createId,
  });
  const draft = review.savedDraft ??= await saveDraft(workspace.id, {
    expected_revision: workspace.draft.revision,
    configuration: review.preview.proposal,
    request_id: review.saveId,
  });
  const run = await freezeDraft(workspace.id, {
    expected_revision: draft.revision,
    request_id: review.freezeId,
  });
  return { experimentId: workspace.id, runId: run.id };
}

export function NewRunHome({
  items, initialExperiment, benchmark, benchmarkLoading, capabilities, saving, frozen,
}: {
  items: WorkspaceHistoryItem[];
  initialExperiment: string | null;
  benchmark?: BenchmarkRoster | null;
  benchmarkLoading: boolean;
  capabilities: Capabilities;
  saving: (busy: boolean) => void;
  frozen: (experimentId: string, runId: string) => void;
}) {
  const writable = items.filter(item => item.integrity === "verified" && !item.read_only_import).reverse();
  const [experiment, setExperiment] = useState(
    writable.find(item => item.id === initialExperiment)?.id ?? writable[0]?.id ?? newExperiment,
  );
  const [name, setName] = useState("");
  const [createdWorkspace, setCreatedWorkspace] = useState<WorkspaceDetail>();
  const [preset, setPreset] = useState<RunPreset>();
  const [retainedId, setRetainedId] = useState("");
  const [limit, setLimit] = useState("");
  const [caseSelection, setCaseSelection] = useState<string[]>();
  const [review, setReview] = useState<PendingRun>();
  const [busy, setBusy] = useState<"preview" | "freeze">();
  const [error, setError] = useState("");
  const [freezeError, setFreezeError] = useState("");
  const lock = useRef(false);
  const mounted = useRef(false);
  const nameInput = useRef<HTMLInputElement>(null);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const headingId = useId();
  const noteId = useId();
  const creating = experiment === newExperiment;
  const canUseBenchmark = !!benchmark && capabilities.live_enabled;
  const mode = preset ?? (canUseBenchmark ? "extract" : "fixtures");
  const needsCases = mode === "fixtures" && (!benchmarkLoading || !capabilities.live_enabled || preset === "fixtures");
  const loadWorkspace = useCallback(
    (signal: AbortSignal) => experiment === newExperiment ? Promise.resolve(null) : getWorkspace(experiment, signal),
    [experiment],
  );
  const target = useRead(loadWorkspace);
  const workspace = target.data?.id === experiment ? target.data : undefined;
  const loadRuns = useCallback(
    (signal: AbortSignal) => canUseBenchmark && workspace?.run_ids.length
      ? getRuns(experiment, signal).then(runs => ({ experiment, runs }))
      : Promise.resolve(null),
    [canUseBenchmark, experiment, workspace],
  );
  const retained = useRead(loadRuns);
  const taskId = capabilities.live_task?.task_id;
  const extractors = taskId && retained.data?.experiment === experiment
    ? benchmarkExtractors(retained.data.runs, benchmark).filter(run =>
      run.plan.task_id === taskId && run.plan.preview.proposal.execution_mode === "live")
    : [];
  const origin = extractors.find(run => run.id === retainedId) ?? extractors.at(-1);
  const cases = useRead(useCallback(
    (signal: AbortSignal) => needsCases ? getCases(signal) : Promise.resolve(null),
    [needsCases],
  ));
  const caseIds = caseSelection ?? cases.data?.filter(item => item.kind === "benchmark").map(item => item.id) ?? [];
  const invocationLimit = limit === "" ? undefined : Number(limit);
  const configuration = runPresetConfiguration(mode, capabilities, caseIds, benchmark,
    mode === "resolve" ? origin : undefined, invocationLimit);
  const pendingBenchmark = benchmarkLoading && capabilities.live_enabled && preset === undefined;
  const canReview = !!configuration && !pendingBenchmark && (creating ? !!name.trim() : workspace?.read_only_import === false);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      saving(false);
    };
  }, [saving]);

  useEffect(() => {
    if (busy !== "freeze") return;
    function warn(event: BeforeUnloadEvent) { event.preventDefault(); }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [busy]);

  function chooseExperiment(id: string) {
    setExperiment(id);
    setRetainedId("");
    setError("");
    if (mode === "resolve") setPreset("extract");
    if (id === newExperiment) requestAnimationFrame(() => nameInput.current?.focus());
  }

  async function reviewRun() {
    if (lock.current || !canReview || !configuration) return;
    lock.current = true;
    setBusy("preview");
    setError("");
    try {
      const preview = await previewDraft(configuration);
      if (!mounted.current) return;
      setReview({
        preview,
        name: workspace?.name ?? name.trim(),
        workspace,
        createId: crypto.randomUUID(),
        saveId: crypto.randomUUID(),
        freezeId: crypto.randomUUID(),
      });
    } catch (reason) {
      if (mounted.current) setError((reason as Error).message);
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(undefined);
    }
  }

  function closeReview() {
    setReview(undefined);
    if (creating && review?.workspace) {
      setCreatedWorkspace(review.workspace);
      setExperiment(review.workspace.id);
    } else if (freezeError) {
      target.retry();
    }
    setFreezeError("");
    requestAnimationFrame(() => reviewButton.current?.focus());
  }

  async function freezeRun() {
    if (lock.current || !review) return;
    lock.current = true;
    setBusy("freeze");
    saving(true);
    setFreezeError("");
    try {
      const result = await freezeReviewedRun(review);
      if (mounted.current) frozen(result.experimentId, result.runId);
    } catch (reason) {
      if (mounted.current) setFreezeError((reason as Error).message);
    } finally {
      lock.current = false;
      if (mounted.current) {
        setBusy(undefined);
        saving(false);
      }
    }
  }

  function runLabel(id: string) {
    const number = workspace?.run_numbers?.[id] ?? (workspace?.run_ids.indexOf(id) ?? -1) + 1;
    return `Run ${number}`;
  }

  const description = pendingBenchmark ? "Checking available presets…"
    : mode === "fixtures" ? caseIds.length ? `${caseIds.length} benchmark inputs · Saved replay` : ""
    : mode === "resolve" && origin ? `${benchmark?.definition.input_count} frozen inputs · Uses verified extraction from ${runLabel(origin.id)}`
    : benchmark ? `${benchmark.definition.input_count} frozen inputs · Fresh extraction` : "";

  return (
    <div className="workbench-home-theme">
      <section className="new-run-home" aria-labelledby={headingId}>
        <h1 id={headingId}>New run</h1>
        <form className="new-run-form" aria-label="New run setup" aria-busy={!!busy}
          onSubmit={event => { event.preventDefault(); void reviewRun(); }}>
          <fieldset className="new-run-fields" disabled={!!busy}>
            <label>Experiment
              <select value={experiment} onChange={event => chooseExperiment(event.target.value)}>
                {writable.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                {createdWorkspace && !writable.some(item => item.id === createdWorkspace.id) && (
                  <option value={createdWorkspace.id}>{createdWorkspace.name}</option>
                )}
                <option value={newExperiment}>New experiment…</option>
              </select>
            </label>
            {creating && <label>Experiment name
              <input ref={nameInput} value={name} required maxLength={200} onChange={event => setName(event.target.value)} />
            </label>}
            <label>Run preset
              <select value={mode} aria-describedby={description ? noteId : undefined} onChange={event => {
                setPreset(event.target.value as RunPreset);
                setLimit("");
                setError("");
              }}>
                {canUseBenchmark && <option value="extract">Benchmark v4 · Extractor only</option>}
                {canUseBenchmark && <option value="resolve" disabled={!origin}>Benchmark v4 · Generative Resolver</option>}
                <option value="fixtures">Repository case fixtures</option>
              </select>
            </label>
            {mode === "resolve" && extractors.length > 1 && <label>Verified extraction
              <select value={origin?.id ?? ""} onChange={event => setRetainedId(event.target.value)}>
                {extractors.map(run => <option key={run.id} value={run.id}>{runLabel(run.id)}</option>)}
              </select>
            </label>}
            {description && <p className="new-run-note" id={noteId}>{description}</p>}
            <details className="new-run-settings">
              <summary>Advanced settings</summary>
              {mode === "fixtures" ? (
                cases.data ? <CasePicker cases={cases.data} selected={caseIds} update={setCaseSelection} disabled={!!busy} />
                  : <span>Reading benchmark cases…</span>
              ) : <label>Maximum provider calls for this invocation
                <input type="number" min={1} max={38} value={limit} placeholder="Use preset default"
                  onChange={event => setLimit(event.target.value)} />
              </label>}
            </details>
            {!creating && !workspace && !target.error && <p role="status">Reading experiment…</p>}
            {target.error && <ReadState error={target.error} retry={target.retry} />}
            {retained.error && <p role="status">Could not check for verified extractions.{" "}
              <button type="button" className="secondary" onClick={retained.retry}>Retry</button></p>}
            {mode === "fixtures" && cases.error && <ReadState error={cases.error} retry={cases.retry} />}
            {error && <p role="alert">{error}</p>}
          </fieldset>
          <div className="new-run-actions">
            <p>Review before confirming execution.</p>
            <button className="new-run-primary" type="submit" ref={reviewButton} disabled={!!busy || !canReview}>
              {busy === "preview" ? "Preparing review…" : "Review run"}
              <span className="new-run-arrow" aria-hidden="true" />
            </button>
          </div>
        </form>
      </section>
      {review && <ReviewDialog title="Review run" close={closeReview} busy={busy === "freeze"} actions={<>
        <button type="button" className="secondary" disabled={busy === "freeze"} onClick={closeReview}>Back to setup</button>
        <button type="button" disabled={busy === "freeze"} onClick={() => void freezeRun()}>
          {busy === "freeze" ? "Freezing…" : "Freeze Run"}
        </button>
      </>}>
        <p>Experiment · {review.name}</p>
        <p>Freezing saves the configuration. Start execution separately.</p>
        {freezeError && <p role="alert">{freezeError}</p>}
        <ReviewSummary preview={review.preview} />
      </ReviewDialog>}
    </div>
  );
}
