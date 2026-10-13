import type { ExperimentDetail } from "../shared/contracts";
import { number } from "../shared/presentation";

function recordedNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function UsageSummary({ data }: { data: ExperimentDetail }) {
  const operations = data.operations;
  const latency = record(operations.provider_latency);
  const tokens = record(operations.tokens);
  const pricing = record(data.configuration.pricing);
  return (
    <div className="usage-summary">
      <dl>
        <div>
          <dt>Input tokens</dt>
          <dd>
            {number(recordedNumber(record(tokens.input_tokens).known_sum), 0)}
          </dd>
        </div>
        <div>
          <dt>Output tokens</dt>
          <dd>
            {number(recordedNumber(record(tokens.output_tokens).known_sum), 0)}
          </dd>
        </div>
        <div>
          <dt>Mean provider latency</dt>
          <dd>{number(recordedNumber(latency.mean))} seconds</dd>
        </div>
        <div>
          <dt>Estimated spend</dt>
          <dd>
            {number(recordedNumber(operations.estimated_spend), 6)}{" "}
            {typeof pricing.currency === "string" ? pricing.currency : ""}
          </dd>
        </div>
      </dl>
      <p className="muted">
        Latency: {number(recordedNumber(latency.n), 0)} measured,{" "}
        {number(recordedNumber(latency.missing), 0)} missing. Unpriced attempts:{" "}
        {number(recordedNumber(operations.unpriced_attempts), 0)}. Estimates use
        recorded pricing; they are not provider invoices. Token totals include
        known usage only.
      </p>
    </div>
  );
}
