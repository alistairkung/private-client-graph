import { useCallback } from "react";
import {
  RunPerformanceChart,
  type PerformanceRun,
  type PerformanceMetricOptions,
} from "../../src/shared/research/RunPerformanceChart";
import type { BenchmarkStageUsage, RunDetail, SemanticRunSummary, WorkspaceDetail } from "../shared/contracts";
import { useRead } from "../shared/useRead";
import { getEvaluationSummary } from "./api";
import { evidenceMetricLabels } from "./benchmark-metrics";
export { metric } from "../../src/shared/research/RunPerformanceChart";
export const money = (value: number | null, currency: string | null) =>
  value === null
    ? "Unavailable"
    : `${currency ?? "Currency unavailable"} ${value.toFixed(4)}`;

const supportingMetrics = [
  {
    key: "evidence_support",
    label: evidenceMetricLabels.evidence_support,
    description: "Formal targets with at least one required evidence member matched",
  },
  {
    key: "complete_proof",
    label: evidenceMetricLabels.complete_proof,
    description: "Formal targets with every required member of an approved proof matched",
  },
  {
    key: "joint_only_coverage",
    label: evidenceMetricLabels.joint_only_coverage,
    description: "Average share of required members matched across multi-source targets, using the best approved proof for each target",
  },
] as const;
const targetEquivalents = new Intl.NumberFormat("en", { maximumFractionDigits: 3 });

type RunChartProps = {
  workspace: WorkspaceDetail;
  runs: RunDetail[];
  selected: string | null;
  select: (id: string) => void;
  selectInPlace?: (id: string) => void;
};

export function RunChart(props: RunChartProps) {
  const { workspace, runs, selected, select } = props;
  const experiment = { name: workspace.name, runIds: workspace.run_ids, runNumbers: workspace.run_numbers };
  const metrics = metricOptions(runs);
  return metrics
    ? <BenchmarkPerformance {...props} metrics={metrics} />
    : <RunPerformanceChart experiment={experiment} runs={runs.map(run => performanceRun(run))} selected={selected} select={select} />;
}

function BenchmarkPerformance({ workspace, runs, selected, select, selectInPlace, metrics }: RunChartProps & {
  metrics: PerformanceMetricOptions;
}) {
  // Run details poll while the workspace is open. Read retained assessments only
  // when the set of completed Runs changes or the reader refreshes the scores.
  const completed = runs.filter(run => run.benchmark_v4?.state === "complete").map(run => run.id).join(" ");
  const load = useCallback(async (signal: AbortSignal) => {
    const ids = completed ? completed.split(" ") : [];
    const reports = await Promise.allSettled(ids.map(id => getEvaluationSummary(id, signal)));
    return new Map(ids.map((id, index) => {
      const report = reports[index];
      return [id, report.status === "fulfilled" && report.value.run_id === id ? report.value : null];
    }));
  }, [completed]);
  const { data, retry } = useRead(load);
  const scores = runs.map(run => performanceRun(run, data?.get(run.id)));
  const needsRefresh = data && [...data.values()].some(report => report?.state !== "complete");
  return (
    <RunPerformanceChart
      experiment={{ name: workspace.name, runIds: workspace.run_ids, runNumbers: workspace.run_numbers }}
      runs={scores}
      selected={selected}
      select={selectInPlace ?? select}
      comparison={{
        metrics,
        adjusted: {
          key: "evidence_adjusted",
          label: evidenceMetricLabels.evidence_adjusted,
          description: "Relationship correctness with a penalty for incomplete proof",
        },
        supporting: supportingMetrics,
        loadingEvidence: !!completed && !data,
        refreshEvidence: needsRefresh ? retry : undefined,
      }}
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

function performanceRun(run: RunDetail, assessment?: SemanticRunSummary | null): PerformanceRun {
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
      measures: quality ? {
        ...qualityMeasures(quality),
        ...assessmentMeasures(assessment),
      } : undefined,
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

const graphMetrics = ["combined_graph", "qualified_graph"] as const;
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

function assessmentMeasures(assessment?: SemanticRunSummary | null): PerformanceRun["measures"] {
  if (!assessment) return undefined;
  const { graph_f1: graph, evidence_adjusted_f1: adjusted, target_summary: targets } = assessment;
  const qualifier = {
    exact_only: "Exact-only",
    pending: "Exact-only · Evaluation pending",
    complete: "Exact and equivalent",
    complete_with_failures: "Combined evaluation finished with failures",
  }[assessment.state];
  const support = targets.evidence_support;
  const completion = targets.proof_completion;
  const coverage = targets.multi_source_evidence_coverage;
  return {
    ...(graph && adjusted && {
      evidence_adjusted: {
        value: adjusted.f1,
        label: `${evidenceMetricLabels.evidence_adjusted} · ${graph.inputs} qualified Conditions`,
        coverage: { scored: graph.valid_graphs, planned: graph.inputs },
        coverageLabel: "valid graphs",
        qualifier,
      },
    }),
    evidence_support: {
      value: support.rate,
      label: evidenceMetricLabels.evidence_support,
      basis: `${support.count} of ${support.targets} formal targets`,
      qualifier,
    },
    complete_proof: {
      value: completion.rate,
      label: evidenceMetricLabels.complete_proof,
      basis: `${completion.count} of ${completion.targets} formal targets`,
      qualifier,
    },
    joint_only_coverage: {
      value: coverage.mean,
      label: evidenceMetricLabels.joint_only_coverage,
      basis: `${targetEquivalents.format(coverage.matched_target_equivalents)} of ${coverage.targets} target-equivalents`,
      qualifier,
    },
  };
}
