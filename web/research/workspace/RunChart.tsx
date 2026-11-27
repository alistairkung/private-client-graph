import {
  RunPerformanceChart,
  type PerformanceRun,
  type PerformanceMetricOptions,
} from "../../src/shared/research/RunPerformanceChart";
import type { BenchmarkStageUsage, RunDetail, WorkspaceDetail } from "../shared/contracts";
import { evidenceMetricLabels } from "./benchmark-metrics";
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
      experiment={{ name: workspace.name, runIds: workspace.run_ids, runNumbers: workspace.run_numbers }}
      runs={values}
      selected={selected}
      select={select}
      metrics={metricOptions(runs)}
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
  if (mixed) {
    const frozenCost = mixed.observation_origin === "live"
      ? verifiedFullPipelineCost(run.pipeline_usage?.full_pipeline)
      : null;
    const cost = run.reference_cost ?? frozenCost;
    const score = mixed.combined;
    const state = quality?.state ?? mixed.state;
    const complete = state === "complete";
    return {
      id: run.id,
      lifecycle: run.lifecycle,
      resolver: run.plan.preview.proposal.resolver === "generative",
      inputMode: run.plan.preview.proposal.input_mode,
      model: run.plan.preview.proposal.model,
      recorded: mixed.observation_origin === "offline_fixture",
      f1: score?.f1 ?? null,
      measures: quality ? qualityMeasures(quality) : undefined,
      metricLabel: "Benchmark v4 Graph F1 · mixed references",
      coverageLabel: "valid graphs / planned inputs",
      scoreState: state === "unmeasured" ? "unavailable" : state,
      coverage: { scored: score?.valid_graphs ?? 0, planned: run.observations.length },
      cost: cost ?? { total: null, currency: null },
      costBasis: run.reference_cost ? "reference_rate_estimate" : frozenCost ? "verified_provider_estimate" : undefined,
      fullPipelineCost: true,
      scopeIdentity: `${mixed.scope_sha256}:${mixed.scoring_sha256}:${mixed.observation_origin}`,
      eligibility: {
        f1_by_run: quality ? state !== "unmeasured" : complete,
        f1_vs_cost: complete && cost !== null,
        f1_reasons: complete ? [] : ["Benchmark v4 coverage is incomplete."],
        cost_reasons: !cost ? ["F1 vs Cost needs complete provider token usage and pricing for the full pipeline."]
          : complete ? [] : ["Cost points require a complete Run."],
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
    metricLabel: benchmark ? "All-condition Graph F1 · Protocol v1" : undefined,
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

function verifiedFullPipelineCost(usage: BenchmarkStageUsage | undefined) {
  if (
    !usage || usage.estimated_cost === null || !Number.isFinite(usage.estimated_cost) ||
    usage.estimated_cost < 0 || !usage.currency || usage.unpriced_attempts > 0 || usage.attempts === 0
  ) {
    return null;
  }
  return { total: usage.estimated_cost, currency: usage.currency };
}

const graphMetrics = ["qualified_graph", "combined_graph"] as const;
type GraphScope = typeof graphMetrics[number];
type RunQuality = NonNullable<RunDetail["quality"]>;

function qualityScope(quality: RunQuality, key: GraphScope) {
  if (key === "qualified_graph") return `${quality.qualified_inputs} qualified Conditions`;
  return quality.planned_inputs === quality.qualified_inputs
    ? `${quality.planned_inputs} evaluation inputs`
    : `${quality.planned_inputs} evaluation inputs · mixed references`;
}

function metricOptions(runs: RunDetail[]): PerformanceMetricOptions | undefined {
  const reports = runs.flatMap((run) => run.quality ? [run.quality] : []);
  if (!reports.length) return undefined;
  return Object.fromEntries(graphMetrics.map((key) => {
    const scopes = new Set(reports.map((quality) => qualityScope(quality, key)));
    return [key, {
      label: evidenceMetricLabels[key],
      scope: scopes.size === 1 ? [...scopes][0] : "Scope varies by Run",
    }];
  }));
}

function qualityMeasures(quality: RunQuality): PerformanceRun["measures"] {
  const coverage = {
    combined_graph: { scored: quality.observed_inputs, planned: quality.planned_inputs },
    qualified_graph: { scored: quality.observed_qualified_inputs, planned: quality.qualified_inputs },
  };
  const coverageLabels = {
    combined_graph: "observed evaluation inputs",
    qualified_graph: "observed qualified Conditions",
  };
  return Object.fromEntries(graphMetrics.map((key) => [key, {
    value: quality[key]?.f1 ?? null,
    label: `${evidenceMetricLabels[key]} · ${qualityScope(quality, key)}`,
    coverage: coverage[key],
    coverageLabel: coverageLabels[key],
  }]));
}
