import { requestJson } from "../../shared/json-request";
import type { ShowcaseCase, ShowcaseCaseSummary } from "./types";

export const getShowcaseCases = () => requestJson<ShowcaseCaseSummary[]>("/api/showcase/cases");
export const getShowcaseCase = (caseId: string) =>
  requestJson<ShowcaseCase>(`/api/showcase/cases/${encodeURIComponent(caseId)}`);
