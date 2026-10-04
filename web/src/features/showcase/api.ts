import { JsonRequestError, requestJson } from "../../shared/json-request";
import type {
  AnalysisError,
  AnalysisMode,
  CaseAnalysis,
  CaseDetail,
} from "./types";

const connectionError: AnalysisError = {
  stage: "connection",
  message:
    "The application could not be reached. Check the local server and try again.",
  retryable: true,
};

export class RequestFailure extends Error {
  constructor(public error: AnalysisError) {
    super(error.message);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isAnalysisError(value: unknown): value is AnalysisError {
  return (
    isRecord(value) &&
    typeof value.stage === "string" &&
    typeof value.message === "string" &&
    typeof value.retryable === "boolean"
  );
}

function analysisErrorFrom(body: unknown): AnalysisError | undefined {
  if (!isRecord(body) || !isAnalysisError(body.error)) return undefined;
  return body.error;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    return await requestJson<T>(url, options);
  } catch (error) {
    if (error instanceof JsonRequestError && error.kind === "http") {
      const analysisError = analysisErrorFrom(error.body);
      if (analysisError) throw new RequestFailure(analysisError);
    }
    throw new RequestFailure(connectionError);
  }
}

export const getCase = () => request<CaseDetail>("/api/showcase/case-01");
export const analyseCase = (mode: AnalysisMode) =>
  request<CaseAnalysis>("/api/showcase/case-01/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
