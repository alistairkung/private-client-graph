import { useEffect, useRef, useState } from "react";
import type {
  BenchmarkRoster,
  Capabilities,
  CaseMetadata,
  ExecutionAvailability,
  RunDetail,
  WorkspaceDetail,
} from "../shared/contracts";
import {
  copyDraft,
  getAvailability,
  getCases,
  getRun,
  getWorkspace,
} from "./api";
import { DraftEditor } from "./DraftEditor";
import { RunChart } from "./RunChart";
import { RunInspection } from "./RunInspection";
import { RunExecution } from "./RunExecution";

export function Workspace({
  id,
  selected,
  select,
  capabilities,
  benchmark,
  changed,
  saving,
}: {
  id: string;
  selected: string | null;
  select: (id: string) => void;
  capabilities: Capabilities | null;
  benchmark?: BenchmarkRoster | null;
  changed: () => void;
  saving: (busy: boolean) => void;
}) {
  const [workspace, setWorkspace] = useState<WorkspaceDetail>();
  const [runs, setRuns] = useState<RunDetail[]>([]);
  const [cases, setCases] = useState<CaseMetadata[]>([]);
  const [availability, setAvailability] =
    useState<ExecutionAvailability | null>(null);
  const [failures, setFailures] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [draftKey, setDraftKey] = useState(0);
  const [draftBusy, setDraftBusy] = useState(true);
  const [copying, setCopying] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const evaluation = useRef<HTMLDivElement>(null);
  const focusRun = useRef<string | null>(null);
  const [selectionRevision, setSelectionRevision] = useState(0);
  const copyCommand = useRef<string | null>(null);
  const copyLock = useRef(false);
  useEffect(() => () => saving(false), []);
  const refresh = () => setRetry((value) => value + 1);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      let shouldPoll = true;
      try {
        const [detail, catalog, status] = await Promise.all([
          getWorkspace(id, controller.signal),
          getCases(controller.signal),
          getAvailability(controller.signal),
        ]);
        const results = await Promise.allSettled(
          detail.run_ids.map((run) => getRun(id, run, controller.signal)),
        );
        if (controller.signal.aborted) return;
        setWorkspace((previous) =>
          previous ? { ...detail, draft: previous.draft } : detail,
        );
        setCases(catalog);
        setAvailability(status);
        setError("");
        setRuns(
          results.flatMap((result) =>
            result.status === "fulfilled" ? [result.value] : [],
          ),
        );
        setFailures(
          results.flatMap((result, index) =>
            result.status === "rejected"
              ? [
                  `Run ${detail.run_ids[index]}: ${result.reason.message}. Retry inspection.`,
                ]
              : [],
          ),
        );
        // Imported Runs are immutable and are verified again on each explicit read.
        shouldPoll = !detail.read_only_import;
      } catch (error) {
        if (!controller.signal.aborted) setError((error as Error).message);
      }
      if (shouldPoll && !controller.signal.aborted)
        timer = setTimeout(load, 2000);
    }
    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [id, retry]);
  const editCapabilities = workspace?.read_only_import ? null : capabilities;
  const run =
    runs.find((item) => item.id === selected) ??
    (selected ? undefined : runs.at(-1));
  const executionRun = runs.find((item) => item.id === executionId) ?? run;
  useEffect(() => {
    if (!run || focusRun.current !== run.id) return;
    focusRun.current = null;
    const target = evaluation.current;
    target?.focus({ preventScroll: true });
    target?.scrollIntoView({
      block: "start",
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  }, [run?.id, selectionRevision]);
  function selectEvaluation(id: string) {
    focusRun.current = id;
    setSelectionRevision((value) => value + 1);
    setExecutionId(null);
    select(id);
  }
  const runChart = workspace && (
    <RunChart workspace={workspace} runs={runs} selected={run?.id ?? null} select={selectEvaluation} />
  );
  return (
    <>
      {error && (
        <p role="alert">
          {error} <button onClick={refresh}>Retry workspace</button>
        </p>
      )}
      {!workspace ? (
        <p role="status">Loading experiment…</p>
      ) : (
        <>
          <header className="workspace-heading">
            <h1>{workspace.name}</h1>
            <p>{workspace.run_ids.length} Runs</p>
            {(workspace.hypothesis || workspace.description) && (
              <details>
                <summary>About this experiment</summary>
                <p>{workspace.hypothesis}</p>
                <p>{workspace.description}</p>
                <small>{workspace.id}</small>
              </details>
            )}
          </header>
          {editCapabilities ? (
            <DraftEditor
              key={draftKey}
              id={id}
              disabled={copying}
              draft={workspace.draft}
              runIds={workspace.run_ids}
              extractorRuns={runs.filter((item) => item.benchmark_v4?.state === "complete"
                && item.plan.preview.proposal.input_mode === "fresh"
                && item.plan.preview.proposal.resolver === "none")}
              benchmark={benchmark}
              cases={cases}
              capabilities={editCapabilities}
              saving={(busy) => {
                setDraftBusy(busy);
                saving(busy);
              }}
              saved={(draft) =>
                setWorkspace((value) => value && { ...value, draft })
              }
              frozen={(id) => {
                select(run?.id ?? id);
                setExecutionId(id);
                refresh();
                changed();
              }}
            />
          ) : workspace.read_only_import ? null : (
            <p>
              This workspace is read-only. Retained Runs and Evidence remain
              available.
            </p>
          )}
          {availability?.active_run_id && (
            <p role="status">Active Run: {availability.active_run_id}</p>
          )}
          {workspace.read_only_import && run?.benchmark ? (
            <details className="imported-run-history">
              <summary>Run history and selection</summary>
              {runChart}
            </details>
          ) : runChart}
          {failures.map((failure) => (
            <p role="alert" key={failure}>
              {failure} <button onClick={refresh}>Retry read</button>
            </p>
          ))}
          {selected && !run && !failures.length && (
            <p role="status">Loading selected Run…</p>
          )}
          {executionRun && editCapabilities && (
            <RunExecution
              key={`execution-${executionRun.id}`}
              run={executionRun}
              number={workspace.run_ids.indexOf(executionRun.id) + 1}
              reviewRequested={executionId === executionRun.id}
              availability={availability}
              refresh={refresh}
            />
          )}
          {run && (
            <div
              ref={evaluation}
              tabIndex={-1}
              className="selected-evaluation"
              role="region"
              aria-label="Selected Run evaluation"
            >
              <RunInspection
                key={`inspection-${run.id}`}
                workspace={workspace}
                run={run}
                number={workspace.run_ids.indexOf(run.id) + 1}
                runs={runs}
                busy={copying || draftBusy}
                copy={
                  editCapabilities
                    ? async () => {
                        if (copyLock.current) return;
                        copyLock.current = true;
                        setCopying(true);
                        setError("");
                        copyCommand.current ??= crypto.randomUUID();
                        try {
                          const draft = await copyDraft(id, {
                            request_id: copyCommand.current,
                            expected_revision: workspace.draft.revision,
                            run_id: run.id,
                          });
                          setWorkspace((value) => value && { ...value, draft });
                          setDraftKey((value) => value + 1);
                          copyCommand.current = null;
                        } catch (error) {
                          setError((error as Error).message);
                        } finally {
                          copyLock.current = false;
                          setCopying(false);
                        }
                      }
                    : undefined
                }
              />
            </div>
          )}
        </>
      )}
    </>
  );
}
