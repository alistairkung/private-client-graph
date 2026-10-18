import { RunPerformanceChart, type PerformanceRun } from "../../src/shared/research/RunPerformanceChart";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
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
  const values: PerformanceRun[] = runs.map(run => ({
    id: run.id,
    lifecycle: run.lifecycle,
    resolver: run.plan.preview.proposal.resolver === "generative",
    inputMode: run.plan.preview.proposal.input_mode ?? null,
    model: run.plan.preview.proposal.model,
    recorded: run.plan.preview.proposal.execution_mode === "recorded",
    f1: run.evaluation.aggregate.f1,
    scoreState: run.evaluation.aggregate.state,
    coverage: run.evaluation.aggregate.coverage,
    cost: run.evaluation.cost,
    scopeIdentity: run.evaluation.scope?.identity ?? null,
    eligibility: run.evaluation.eligibility,
  }));
  return <RunPerformanceChart experiment={{ name: workspace.name, runIds: workspace.run_ids }} runs={values} selected={selected} select={select} />;
}
