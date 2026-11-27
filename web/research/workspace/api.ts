import type {
  CaseMetadata,
  BenchmarkRoster,
  RunObservation,
  Command,
  CopyRunDraft,
  CreateExperiment,
  DraftUpdate,
  ExecutionAvailability,
  FreezeRun,
  FrozenPlan,
  LiveApproval,
  Preview,
  RunAuthorization,
  RunComparison,
  RunConfiguration,
  RunDetail,
  RunDraft,
  RunStatus,
  SemanticComparison,
  SemanticEvidenceReport,
  WorkspaceDetail,
  WorkspaceHistory,
} from "../shared/contracts";

export async function request<T>(
  path: string,
  body?: unknown,
  method = "POST",
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(
    `/api/research/v2${path}`,
    body === undefined
      ? { signal }
      : {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal,
        },
  );
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    const detail = result?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg: string }) => item.msg).join("; ")
          : `Research request failed (${response.status}). Retry the request.`,
    );
  }
  return response.json() as Promise<T>;
}
const workspacePath = (id: string) => `/experiments/${encodeURIComponent(id)}`;
export const runPath = (experiment: string, run: string) =>
  `${workspacePath(experiment)}/runs/${encodeURIComponent(run)}`;
export const listWorkspaces = (signal?: AbortSignal) =>
  request<WorkspaceHistory>("/experiments", undefined, undefined, signal);
export const getWorkspace = (id: string, signal?: AbortSignal) =>
  request<WorkspaceDetail>(workspacePath(id), undefined, undefined, signal);
export const getRuns = (id: string, signal?: AbortSignal) =>
  request<RunDetail[]>(
    `${workspacePath(id)}/runs`,
    undefined,
    undefined,
    signal,
  );
export const getRun = (id: string, run: string, signal?: AbortSignal) =>
  request<RunDetail>(runPath(id, run), undefined, undefined, signal);
export const getCases = (signal?: AbortSignal) =>
  request<CaseMetadata[]>("/cases", undefined, undefined, signal);
export const getAvailability = (signal?: AbortSignal) =>
  request<ExecutionAvailability>("/status", undefined, undefined, signal);
export const createWorkspace = (body: CreateExperiment) =>
  request<WorkspaceDetail>("/experiments", body);
export const saveDraft = (id: string, body: DraftUpdate) =>
  request<RunDraft>(`${workspacePath(id)}/draft`, body, "PUT");
export const copyDraft = (id: string, body: CopyRunDraft) =>
  request<RunDraft>(`${workspacePath(id)}/draft/copy`, body);
export const previewDraft = (body: RunConfiguration, signal?: AbortSignal) =>
  request<Preview>("/preview", body, "POST", signal);
export const freezeDraft = (id: string, body: FreezeRun) =>
  request<FrozenPlan>(`${workspacePath(id)}/runs`, body);
export const authorizeRun = (id: string, run: string, body: LiveApproval) =>
  request<RunAuthorization>(`${runPath(id, run)}/authorize`, body);
export const archiveRun = (id: string, run: string) =>
  request<WorkspaceDetail>(`${runPath(id, run)}/archive`, {});
export const controlRun = (
  id: string,
  run: string,
  action: "start" | "stop" | "continue",
  body: Command,
) => request<RunStatus>(`${runPath(id, run)}/${action}`, body);
export const compareRuns = (
  id: string,
  left: string,
  right: string,
  signal?: AbortSignal,
) =>
  request<RunComparison>(
    `${workspacePath(id)}/comparison?${new URLSearchParams({ left, right })}`,
    undefined,
    undefined,
    signal,
  );


export async function benchmarkV4Roster(signal: AbortSignal) {
  const response = await fetch("/api/research/v2/benchmark-v4", { signal });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Benchmark v4 roster is unavailable.");
  return (await response.json()) as BenchmarkRoster;
}

export const benchmarkV4Input = (id: string, signal: AbortSignal) =>
  request<RunObservation>(`/benchmark-v4/inputs/${encodeURIComponent(id)}`, undefined, undefined, signal);

export const getEvaluation = (run: string, signal?: AbortSignal) =>
  request<SemanticEvidenceReport>(
    `/semantic-evidence/runs/${encodeURIComponent(run)}`, undefined, undefined, signal,
  );
export const compareEvaluations = (left: string, right: string, signal?: AbortSignal) =>
  request<SemanticComparison>(
    `/semantic-evidence/comparison?${new URLSearchParams({ left, right })}`, undefined, undefined, signal,
  );
