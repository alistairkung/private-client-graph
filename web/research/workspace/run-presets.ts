import type { BenchmarkRoster, Capabilities, RunConfiguration, RunDetail } from "../shared/contracts";

export type RunPreset = "extract" | "resolve" | "fixtures";

export function benchmarkExtractors(runs: RunDetail[], roster?: BenchmarkRoster | null) {
  return runs.filter(({ benchmark_v4, plan }) =>
    benchmark_v4?.state === "complete" &&
    (!roster || plan.preview.proposal.benchmark_v4_sha256 === roster.sha256) &&
    plan.preview.proposal.input_mode === "fresh" &&
    plan.preview.proposal.resolver === "none",
  );
}

export function runPresetConfiguration(
  preset: RunPreset,
  capabilities: Capabilities,
  caseIds: string[],
  roster?: BenchmarkRoster | null,
  origin?: RunDetail,
  invocationLimit?: number,
): RunConfiguration | null {
  const configuration: RunConfiguration = {
    input_ids: caseIds,
    benchmark_v4_sha256: null,
    retained_experiment_id: null,
    retained_run_id: null,
    input_mode: "saved",
    execution_mode: "replay",
    resolver: "none",
    extraction_samples: 1,
    resolver_repetitions: 1,
    invocation_cap: 0,
    task_call_cap: 0,
    temperature: null,
    timeout_seconds: 90,
    model: "deepseek-flash",
  };
  if (preset === "fixtures") return caseIds.length ? configuration : null;
  if (!roster || !capabilities.live_enabled || (preset === "resolve" && !origin)) return null;

  const count = roster.definition.input_count;
  const model = origin?.plan.preview.proposal;
  return {
    ...configuration,
    input_ids: roster.inputs.map(({ sample_id }) => sample_id),
    benchmark_v4_sha256: roster.sha256,
    retained_experiment_id: origin?.experiment_id ?? null,
    retained_run_id: origin?.id ?? null,
    input_mode: origin ? "saved" : "fresh",
    resolver: origin ? "generative" : "none",
    execution_mode: "live",
    invocation_cap: invocationLimit ?? count,
    task_call_cap: Math.max(count, capabilities.live_task?.cap ?? 0),
    temperature: model?.temperature ?? configuration.temperature,
    timeout_seconds: model?.timeout_seconds ?? configuration.timeout_seconds,
    model: model?.model ?? configuration.model,
  };
}
