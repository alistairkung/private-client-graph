import { useState } from "react";
import type { RunObservation } from "../shared/contracts";

export function UnavailablePrediction({
  observation,
}: {
  observation: RunObservation;
}) {
  const condition = observation.benchmark;
  const resolving = observation.configuration === "generative_full_source";
  const candidates = condition?.parsed_prediction?.relationships;
  const sources = observation.sources ?? [];
  const [sourceIndex, setSourceIndex] = useState(0);
  const source = sources[sourceIndex];
  if (condition?.outcome === "scored") {
    return (
      <p role="alert">
        The scored prediction could not be read. Reload this Run to retry
        inspection.
      </p>
    );
  }
  return (
    <section
      className="prediction-unavailable"
      aria-label="Unavailable prediction"
    >
      <strong>{condition?.outcome === "not_attempted" ? resolving ? "Awaiting resolution" : "Awaiting extraction" : "Prediction unavailable"}</strong>
      <p>
        {condition?.failure_detail ??
          observation.reason ??
          (condition?.outcome === "not_attempted" ? resolving ? "No resolution is recorded for this input." : "No extraction is recorded for this input." : condition?.outcome.replaceAll("_", " "))}
      </p>
      {candidates && (
        <details>
          <summary>Retained candidates · {candidates.length}</summary>
          {candidates.length ? (
            <ol className="failure-records" aria-label="Parsed candidates">
              {candidates.map((row, index) => (
                <li key={index}>
                  <strong>
                    {row.source_name} ·{" "}
                    {row.relationship_type.replaceAll("_", " ")} ·{" "}
                    {row.target_name}
                  </strong>
                  <p>
                    {row.source_id} · <q>{row.supporting_text}</q>
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <p>The parsed result contained no candidates.</p>
          )}
        </details>
      )}
      {source && (
        <details>
          <summary>Frozen Sources · {sources.length}</summary>
          <label>
            Source in retained order
            <select
              value={sourceIndex}
              onChange={(event) => setSourceIndex(Number(event.target.value))}
            >
              {sources.map((item, index) => (
                <option key={item.id} value={index}>
                  {index + 1}. {item.title} · {item.id}
                </option>
              ))}
            </select>
          </label>
          <div
            className="failure-records"
            tabIndex={0}
            role="region"
            aria-label="Full frozen Source"
          >
            {source.text}
          </div>
        </details>
      )}
    </section>
  );
}
