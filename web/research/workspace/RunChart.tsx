import {
  RunPerformanceChart,
  type PerformanceRun,
} from "../../src/shared/research/RunPerformanceChart";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
export { metric } from "../../src/shared/research/RunPerformanceChart";
export const money = (value: number | null, currency: string | null) =>
  value === null
    ? "Unavailable"
    : `${currency ?? "Currency unavailable"} ${value.toFixed(4)}`;

export function RunChart({
  workspace,
  runs,
  selected,
  select,
}: {
  workspace: WorkspaceDetail;
  runs: RunDetail[];
  selected: string | null;
  select: (id: string) => void;
}) {
  const values = runs.map(performanceRun);
  return (
    <RunPerformanceChart
      experiment={{ name: workspace.name, runIds: workspace.run_ids }}
      runs={values}
      selected={selected}
      select={select}
      metricSelector={runs.some((run) => !!run.quality)}
    />
  );
}

function verifiedBenchmarkCost(run: RunDetail) {
  const cost = run.evaluation?.cost;
  if (
    run.benchmark?.scope.observation_origin !== "live" ||
    !cost ||
    !Number.isFinite(run.benchmark.cohort.all_condition_micro_f1) ||
    cost.total === null ||
    !Number.isFinite(cost.total) ||
    cost.total < 0 ||
    !cost.currency ||
    cost.unpriced_attempts !== 0 ||
    cost.reasons.length
  ) {
    return null;
  }
  // The imported projection is verified on read. RunCost.total is the
  // complete estimate for incurred attempts, excluding full-pipeline costs.
  return { total: cost.total, currency: cost.currency };
}

function performanceRun(run: RunDetail): PerformanceRun {
  const { benchmark, benchmark_v4: mixed, evaluation, quality } = run;
  const measures = quality ? qualityMeasures(quality, !!mixed) : undefined;
  if (mixed) {
    const pipeline = run.pipeline_usage?.full_pipeline;
    const cost = mixed.observation_origin === "live" && pipeline?.estimated_cost != null &&
      pipeline.unpriced_attempts === 0 && pipeline.attempts > 0 && pipeline.currency
      ? { total: pipeline.estimated_cost, currency: pipeline.currency }
      : null;
    const score = mixed.combined;
    return {
      id: run.id,
      lifecycle: run.lifecycle,
      resolver: run.plan.preview.proposal.resolver === "generative",
      inputMode: run.plan.preview.proposal.input_mode,
      model: run.plan.preview.proposal.model,
      recorded: mixed.observation_origin === "offline_fixture",
      f1: score?.f1 ?? null,
      measures,
      costLabel: "Estimated full pipeline cost · {currency} {amount}",
      metricLabel: "Benchmark v4 graph micro-F1 · mixed references",
      coverageLabel: "valid graphs / planned inputs",
      scoreState: mixed.state === "unmeasured" ? "unavailable" : mixed.state,
      coverage: { scored: score?.valid_graphs ?? 0, planned: run.observations.length },
      cost: cost ?? { total: null, currency: null },
      costBasis: cost ? "verified_provider_estimate" : undefined,
      scopeIdentity: `${mixed.scope_sha256}:${mixed.scoring_sha256}:${mixed.observation_origin}`,
      eligibility: {
        f1_by_run: quality ? quality.graph !== null : mixed.state === "complete",
        f1_vs_cost: mixed.state === "complete" && cost !== null,
        f1_reasons: mixed.state === "complete" ? [] : ["Benchmark v4 coverage is incomplete."],
        cost_reasons: !cost ? ["Verified provider cost is unavailable."]
          : mixed.state !== "complete" ? ["Cost points require a complete Run."] : [],
      },
    };
  }
  const verifiedCost = verifiedBenchmarkCost(run);
  const costReasons = evaluation?.cost.reasons ?? [];
  return {
    id: run.id,
    lifecycle: run.lifecycle,
    resolver: run.plan?.preview.proposal.resolver === "generative",
    inputMode: run.plan?.preview.proposal.input_mode ?? null,
    model: run.plan?.preview.proposal.model ?? null,
    recorded: run.plan?.preview.proposal.execution_mode === "recorded",
    f1: benchmark
      ? benchmark.cohort.all_condition_micro_f1
      : (evaluation?.aggregate.f1 ?? null),
    measures,
    metricLabel: benchmark ? "All-condition micro-F1 · Protocol v1" : undefined,
    coverageLabel: benchmark ? "valid graphs / planned Conditions" : undefined,
    scoreState: benchmark
      ? benchmark.cohort.outcomes.not_attempted
        ? "provisional"
        : "complete"
      : (evaluation?.aggregate.state ?? "unavailable"),
    coverage: benchmark
      ? {
          scored: benchmark.cohort.valid_graphs,
          planned: benchmark.cohort.planned_conditions,
        }
      : (evaluation?.aggregate.coverage ?? { scored: 0, planned: 0 }),
    cost: (benchmark ? verifiedCost : evaluation?.cost) ?? {
      total: null,
      currency: null,
    },
    costBasis: verifiedCost ? "verified_provider_estimate" : undefined,
    scopeIdentity: benchmark
      ? benchmark.scope_identity
      : (evaluation?.scope?.identity ?? null),
    eligibility: benchmark
      ? {
          f1_by_run: true,
          f1_vs_cost: verifiedCost !== null,
          f1_reasons: [],
          cost_reasons: verifiedCost
            ? []
            : costReasons.length
              ? costReasons
              : ["Verified provider cost is unavailable."],
        }
      : (evaluation?.eligibility ?? {
          f1_by_run: false,
          f1_vs_cost: false,
          f1_reasons: ["Evaluation unavailable"],
          cost_reasons: ["Evaluation unavailable"],
        }),
  };
}

function qualityMeasures(quality: NonNullable<RunDetail["quality"]>, mixed: boolean): PerformanceRun["measures"] {
  const scope = `${quality.qualified_inputs} qualified Conditions`;
  const qualified = { scored: quality.observed_qualified_inputs, planned: quality.qualified_inputs };
  return {
    graph: {
      value: quality.graph?.f1 ?? null,
      label: mixed ? `Graph micro-F1 · ${quality.planned_inputs} inputs · mixed references` : `Graph micro-F1 · ${scope}`,
      coverage: { scored: quality.observed_inputs, planned: quality.planned_inputs },
      coverageLabel: "observed / planned inputs",
    },
    grounded: {
      value: quality.grounded?.f1 ?? null,
      label: `Evidence-Grounded micro-F1 · ${scope}`,
      coverage: qualified,
      coverageLabel: "observed / planned Conditions",
    },
    proof: {
      value: quality.complete_proof.rate,
      label: `Complete Proof Rate · ${scope}`,
      coverage: { scored: quality.complete_proof.complete, planned: quality.complete_proof.targets },
      coverageLabel: "complete / observed proof targets",
    },
  };
}
