import { read } from "../shared/api";
import type {
  Capabilities,
  LiveApproval,
  Command,
  FrozenPlan,
  Preview,
  Proposal,
  RunStatus,
} from "../shared/contracts";

export async function command<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api/research/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    throw new Error(
      typeof result?.detail === "string"
        ? result.detail
        : `Command rejected (${response.status}). Check the configuration.`,
    );
  }
  return response.json() as Promise<T>;
}
export async function capabilities(
  signal?: AbortSignal,
): Promise<Capabilities | null> {
  const response = await fetch("/api/research/v1/capabilities", { signal });
  if (response.status === 404) return null;
  if (!response.ok)
    throw new Error("Execution capabilities unavailable. Retry the read.");
  return response.json() as Promise<Capabilities>;
}
export const preview = (proposal: Proposal, signal?: AbortSignal) =>
  command<Preview>("/preview", proposal, signal);
export const freeze = (proposal: Proposal) =>
  command<FrozenPlan>("/plans", proposal);
export const progress = (id: string, signal?: AbortSignal) =>
  read<RunStatus>(`/plans/${id}`, signal);
export const control = (
  id: string,
  action: "start" | "stop" | "continue",
  body: Command,
) => command<RunStatus>(`/plans/${id}/${action}`, body);

export const authorize = (id: string, body: LiveApproval) =>
  command<RunStatus>(`/plans/${id}/authorize`, body);
