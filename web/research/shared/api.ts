import type { Comparison, ExperimentDetail, HistoryPage } from "./contracts";
const prefix = "/api/research/v1";

export async function read<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${prefix}${path}`, { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : `Research read failed (${response.status}).`,
    );
  }
  return response.json() as Promise<T>;
}
export const history = (params: URLSearchParams, signal: AbortSignal) =>
  read<HistoryPage>(`/experiments?${params}`, signal);
export const experiment = (id: string, signal: AbortSignal) =>
  read<ExperimentDetail>(`/experiments/${encodeURIComponent(id)}`, signal);
export const comparison = (left: string, right: string, signal: AbortSignal) =>
  read<Comparison>(
    `/comparison?${new URLSearchParams({ left, right })}`,
    signal,
  );
