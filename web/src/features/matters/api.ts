import { JsonRequestError, requestJson } from "../../shared/json-request";
import type { MatterDetail, MatterSummary } from "./types";

export async function getMatters(): Promise<MatterSummary[]> {
  try {
    return await requestJson<MatterSummary[]>("/api/matters");
  } catch {
    throw new Error("Matters could not be loaded.");
  }
}
export async function getMatter(id: string): Promise<MatterDetail | null> {
  try {
    return await requestJson<MatterDetail>(
      `/api/matters/${encodeURIComponent(id)}`,
    );
  } catch (error) {
    if (error instanceof JsonRequestError && error.status === 404) return null;
    throw new Error("Matter could not be loaded.");
  }
}
