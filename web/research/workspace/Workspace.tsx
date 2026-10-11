import { useEffect, useRef, useState } from "react";
import type {
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
  changed,
  saving,
}: {
  id: string;
  selected: string | null;
  select: (id: string) => void;
  capabilities: Capabilities | null;
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
  const copyCommand = useRef<string | null>(null);
  const copyLock = useRef(false);
  useEffect(() => () => saving(false), []);
  const refresh = () => setRetry((value) => value + 1);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
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
      } catch (error) {
        if (!controller.signal.aborted) setError((error as Error).message);
      }
      // Keep status current even when another Experiment is executing.
      if (!controller.signal.aborted) timer = setTimeout(load, 2000);
    }
    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [id, retry]);
  const run =
    runs.find((item) => item.id === selected) ??
    (selected ? undefined : runs.at(-1));
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
          {capabilities ? (
            <DraftEditor
              key={draftKey}
              id={id}
              draft={workspace.draft}
              cases={cases}
              capabilities={capabilities}
              saving={(busy) => {
                setDraftBusy(busy);
                saving(busy);
              }}
              saved={(draft) =>
                setWorkspace((value) => value && { ...value, draft })
              }
              frozen={(run) => {
                select(run);
                refresh();
                changed();
              }}
            />
          ) : (
            <p>
              This workspace is read-only. Retained Runs and Evidence remain
              available.
            </p>
          )}
          {availability?.active_run_id && (
            <p role="status">Active Run: {availability.active_run_id}</p>
          )}
          <RunChart
            workspace={workspace}
            runs={runs}
            selected={run?.id ?? null}
            select={select}
          />
          {failures.map((failure) => (
            <p role="alert" key={failure}>
              {failure} <button onClick={refresh}>Retry read</button>
            </p>
          ))}
          {selected && !run && !failures.length && (
            <p role="status">Loading selected Run…</p>
          )}
          {run && (
            <>
              {capabilities && (
                <RunExecution
                  key={`execution-${run.id}`}
                  run={run}
                  availability={availability}
                  refresh={refresh}
                />
              )}
              <RunInspection
                key={`inspection-${run.id}`}
                workspace={workspace}
                run={run}
                number={workspace.run_ids.indexOf(run.id) + 1}
                runs={runs}
                busy={copying || draftBusy}
                copy={
                  capabilities
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
            </>
          )}
        </>
      )}
    </>
  );
}
