import type { CanonicalGraph } from "../../shared/canonical-graph";

export type AnalysisMode = "live" | "sample";

export interface LiveAvailability {
  state: "disabled" | "available" | "exhausted" | "unavailable";
  resets_at: string | null;
}

export interface CaseDetail {
  live_analysis: LiveAvailability;
  title: string;
  notice: string;
  source_text: string;
}

export interface CaseAnalysis {
  execution: { mode: AnalysisMode; run_artifact_id: string | null };
  graph: CanonicalGraph;
}

export interface AnalysisError {
  live_analysis?: LiveAvailability | null;
  stage: string;
  message: string;
  retryable: boolean;
  run_artifact_id?: string | null;
}
