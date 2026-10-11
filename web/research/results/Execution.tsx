import type { ExperimentDetail } from "../shared/contracts";
import { number, RecordedDetails } from "../shared/presentation";

export function Execution({ data }: { data: ExperimentDetail }) {
  const operations = data.operations;
  const spend =
    typeof operations.estimated_spend === "number"
      ? operations.estimated_spend
      : null;
  const pricing = data.configuration.pricing as { currency?: string } | null;
  return (
    <section>
      <h2>Execution & artifacts</h2>
      <p>
        Historical imports are read-only. Recorded authorizations and ledger
        paths cannot authorize execution here.
      </p>
      <dl>
        <dt>Recorded provider attempts</dt>
        <dd>{String(operations.attempted ?? "Unavailable")}</dd>
        <dt>Uncertain attempts</dt>
        <dd>{String(operations.uncertain_attempts ?? "Unavailable")}</dd>
        <dt>Estimated experiment spend</dt>
        <dd>
          {number(spend, 9)} {pricing?.currency ?? ""}
          {spend === null && " — sufficient pricing or usage was not recorded."}
        </dd>
        <dt>Unpriced attempts</dt>
        <dd>{String(operations.unpriced_attempts ?? "Unavailable")}</dd>
      </dl>
      <RecordedDetails
        title="Provider attempts, failures, usage and latency (seconds)"
        value={operations}
      />
      <RecordedDetails
        title="Lifecycle checkpoints and stop reasons"
        value={data.sessions}
      />
      <RecordedDetails
        title="Configuration, pricing model/date and provenance"
        value={data.configuration}
      />
      <RecordedDetails
        title="Code, dependencies and prompts"
        value={data.provenance}
      />
      <h3>Observation execution detail</h3>
      {data.samples.map((sample) => (
        <RecordedDetails
          key={sample.id}
          title={sample.id}
          value={sample.observations.map((row) => ({
            configuration: row.configuration,
            repetition: row.repetition,
            status: row.status,
            stage: row.stage,
            ...row.execution,
          }))}
        />
      ))}
    </section>
  );
}
