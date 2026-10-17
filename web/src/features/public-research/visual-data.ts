import type { PipelineConfiguration } from "../../shared/research/AnalysisPipeline";
import type { PerformanceRun } from "../../shared/research/RunPerformanceChart";
import type { ResearchText } from "../../shared/research/presentation";
import type { PublicRun } from "./types";

// The v1 publication fixes A as fresh extraction and A′/B as its frozen replays.
// This adapter copies published measurements; it never reconstructs private Run records.
export function publishedPerformanceRuns(runs: PublicRun[]): PerformanceRun[] {
  const extractionModel = runs.find(run => run.label === "A")?.calls[0]?.model ?? null;
  return runs.map(run => ({
    id: run.run_id,
    lifecycle: null,
    resolver: run.label === "B",
    inputMode: run.label === "A" ? "fresh" : "saved",
    model: run.calls[0]?.model ?? extractionModel,
    recorded: false,
    f1: run.metrics.micro_f1,
    scoreState: run.coverage.scored === run.coverage.planned ? "complete" : "provisional",
    coverage: run.coverage,
    cost: { total: run.usage.cost, currency: run.usage.currency },
    scopeIdentity: null,
    eligibility: {
      f1_by_run: true,
      f1_vs_cost: run.usage.cost !== null,
      f1_reasons: [],
      cost_reasons: run.usage.cost === null ? ["Unpriced provider attempts; excluded from cost chart."] : [],
    },
  }));
}

export function publishedPipeline(run: PublicRun, runs: PublicRun[], t: ResearchText): PipelineConfiguration {
  const extraction = runs.find(value => value.label === "A");
  return {
    resolver: run.label === "B",
    input: t(run.label === "A" ? "Ordered Sources · One extraction per case" : "Frozen extractions · No new extraction"),
    model: run.calls[0]?.model ?? extraction?.calls[0]?.model ?? t("Unavailable"),
    repetitions: "1",
  };
}
