import type { Preview } from "../shared/contracts";
import { PlanSummary } from "../configuration/PlanSummary";

export function ReviewSummary({
  preview,
  frozen = false,
}: {
  preview: Preview;
  frozen?: boolean;
}) {
  const configuration = preview.proposal;
  return (
    <>
      <p>
        {configuration.execution_mode === "live"
          ? "Live provider execution · Authorization required"
          : configuration.execution_mode === "recorded"
            ? "Recorded demonstration · Not live quality"
            : "Provider-free replay"}
      </p>
      {configuration.benchmark_v4_sha256 && <p>Benchmark v4 · Mixed reference methodologies</p>}
      <dl className="review-summary">
        <dt>Pipeline</dt>
        <dd>
          {configuration.resolver === "generative"
            ? "Generative Resolver → Build graph"
            : configuration.benchmark_v4_sha256 ? "Extractor only → Build graph" : "Build graph · No resolver"}
        </dd>
        <dt>Inputs</dt>
        <dd>
          {configuration.input_mode === "saved"
            ? configuration.benchmark_v4_sha256 ? "Verified candidates inherited from the selected Run" : "Saved extractions"
            : "Fresh extraction"}{" "}
          · {configuration.input_ids.length} inputs
        </dd>
        {configuration.benchmark_v4_sha256 && <>
          <dt>Provider attempt maxima</dt>
          <dd>{preview.extraction_call_maximum} extraction · {preview.resolution_call_maximum} resolver</dd>
          {preview.eligible_resolution_inputs != null && <>
            <dt>Inputs eligible for resolution</dt>
            <dd>{preview.eligible_resolution_inputs} / {preview.planned_observations}</dd>
          </>}
        </>}
        <dt>Observations</dt>
        <dd>{preview.planned_observations} planned</dd>
        <dt>Model</dt>
        <dd>{configuration.model}</dd>
        <dt>Invocation limit</dt>
        <dd>{preview.invocation_cap} new attempts maximum</dd>
      </dl>
      <p className="muted">{preview.cost_reason}</p>
      <details>
        <summary>Inputs, limits &amp; provenance</summary>
        <PlanSummary preview={preview} frozen={frozen} />
      </details>
    </>
  );
}
