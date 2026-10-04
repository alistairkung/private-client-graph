import type {
  AnalysisError,
  AnalysisMode,
  CaseAnalysis,
  CaseDetail,
} from "./types";

export class RequestFailure extends Error {
  constructor(public error: AnalysisError) {
    super(error.message);
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options);
    const body = await response.json();
    if (!response.ok) throw new RequestFailure(body.error);
    return body as T;
  } catch (error) {
    if (error instanceof RequestFailure) throw error;
    throw new RequestFailure({
      stage: "connection",
      message:
        "The application could not be reached. Check the local server and try again.",
      retryable: true,
    });
  }
}

export const getCase = () => request<CaseDetail>("/api/showcase/case-01");
export const analyseCase = (mode: AnalysisMode) =>
  request<CaseAnalysis>("/api/showcase/case-01/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
