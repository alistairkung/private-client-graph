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
      <dl className="review-summary">
        <dt>Pipeline</dt>
        <dd>
          {configuration.resolver === "generative"
            ? "Generative resolver → Build graph"
            : "Build graph · No resolver"}
        </dd>
        <dt>Inputs</dt>
        <dd>
          {configuration.input_mode === "saved"
            ? "Saved extractions"
            : "Fresh extraction"}{" "}
          · {configuration.input_ids.length} inputs
        </dd>
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
