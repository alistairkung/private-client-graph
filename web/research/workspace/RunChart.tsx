import { RunPerformanceChart, type PerformanceRun } from "../../src/shared/research/RunPerformanceChart";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
import type { BenchmarkRunDetail } from "./benchmark-types";
export { metric } from "../../src/shared/research/RunPerformanceChart";
export const money = (value: number | null, currency: string | null) =>
  value === null
    ? "Unavailable"
    : `${currency ?? "Currency unavailable"} ${value.toFixed(4)}`;


export function RunChart({ workspace, runs, selected, select }: {
  workspace: WorkspaceDetail;
  runs: RunDetail[];
  selected: string | null;
  select: (id: string) => void;
}) {
  const values: PerformanceRun[] = runs.map(item => {
    const run = item as BenchmarkRunDetail;
    return ({
    id: run.id,
    lifecycle: run.lifecycle,
    resolver: run.plan?.preview.proposal.resolver === "generative",
    inputMode: run.plan?.preview.proposal.input_mode ?? null,
    model: run.plan?.preview.proposal.model ?? null,
    recorded: run.plan?.preview.proposal.execution_mode === "recorded",
    f1: run.benchmark?.cohort.all_condition_micro_f1 ?? run.evaluation?.aggregate.f1 ?? null,
    metricLabel: run.benchmark ? "All-condition micro-F1 · Protocol v1" : undefined,
    coverageLabel: run.benchmark ? "valid graphs / planned Conditions" : undefined,
    scoreState: run.benchmark ? "complete" : run.evaluation?.aggregate.state ?? "unavailable",
    coverage: run.benchmark ? { scored: run.benchmark.cohort.valid_graphs, planned: run.benchmark.cohort.planned_conditions } : run.evaluation?.aggregate.coverage ?? { scored: 0, planned: 0 },
    cost: run.evaluation?.cost ?? { total: null, currency: null },
    scopeIdentity: run.benchmark ? `${run.benchmark.scope.benchmark_sha256}:${run.benchmark.scope.protocol_version}` : run.evaluation?.scope?.identity ?? null,
    eligibility: run.benchmark ? { f1_by_run: true, f1_vs_cost: false, f1_reasons: [], cost_reasons: ["Protocol comparison has no provider cost basis"] } : run.evaluation?.eligibility ?? { f1_by_run: false, f1_vs_cost: false, f1_reasons: ["Evaluation unavailable"], cost_reasons: ["Evaluation unavailable"] },
    });
  });
  return <RunPerformanceChart experiment={{ name: workspace.name, runIds: workspace.run_ids }} runs={values} selected={selected} select={select} />;
}
