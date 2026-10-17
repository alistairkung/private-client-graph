import { useRef, useState } from "react";
import type { RunDetail } from "../shared/contracts";
import { EvidenceInspector } from "../results/EvidenceInspector";
import { metric } from "./RunChart";

export function ObservationInspection({ run }: { run: RunDetail }) {
  const evidence = useRef<HTMLDivElement>(null);
  const selectedControl = useRef<HTMLButtonElement | null>(null);
  function showEvidence(button: HTMLButtonElement, id: string) {
    selectedControl.current = button;
    setRelationshipId(id);
    if (matchMedia("(width < 760px)").matches)
      requestAnimationFrame(() => {
        evidence.current?.focus({ preventScroll: true });
        evidence.current?.scrollIntoView({
          block: "start",
          behavior: "instant",
        });
      });
  }
  const [observationId, setObservationId] = useState(run.observations[0]?.id);
  const [outcome, setOutcome] = useState("all");
  const [relationshipId, setRelationshipId] = useState<string | null>(null);
  const observation =
    run.observations.find((item) => item.id === observationId) ??
    run.observations[0];
  const relationship = observation?.relationships.find(
    (item) => item.id === relationshipId,
  );
  return (
    <details className="observation-inspection">
      <summary>Observations &amp; Evidence</summary>
      <label>
        Observation
        <select
          value={observation?.id ?? ""}
          onChange={(e) => {
            setObservationId(e.target.value);
            setRelationshipId(null);
            setOutcome("all");
          }}
        >
          {run.observations.map((item) => (
            <option key={item.id} value={item.id}>
              {item.metadata?.name ?? item.case_id} ·{" "}
              {item.metadata?.fixture_name ?? "Fixture name unavailable"} ·{" "}
              {item.sample_id} · repetition {item.repetition} · {item.status}
            </option>
          ))}
        </select>
      </label>
      {observation && (
        <>
          <div className="observation-metadata">
            <strong>
              {observation.metadata?.name ??
                `Case ${observation.case_id} (name unavailable)`}
            </strong>
            <p>
              {observation.metadata?.description ??
                "Case description unavailable"}
            </p>
            <p>
              {observation.metadata?.fixture_name ?? "Fixture name unavailable"}{" "}
              —{" "}
              {observation.metadata?.fixture_description ??
                "Fixture description unavailable"}
            </p>
            <small>
              {observation.case_id} · {observation.sample_id} · repetition{" "}
              {observation.repetition} · {observation.status}
            </small>
            {observation.reason && <p>{observation.reason}</p>}
          </div>
          {observation.result?.evaluation && (
            <p>
              Precision {metric(observation.result.evaluation.precision)} ·
              Recall {metric(observation.result.evaluation.recall)} · F1{" "}
              {metric(observation.result.evaluation.f1)} · Provenance accuracy{" "}
              {metric(observation.result.evaluation.provenance_accuracy)}
            </p>
          )}
          <div className="observation-bench">
            <section id="relationships" tabIndex={-1}>
              <label>
                Relationship outcome
                <select
                  value={outcome}
                  onChange={(e) => {
                    setOutcome(e.target.value);
                    setRelationshipId(null);
                  }}
                >
                  <option value="all">All relationships</option>
                  <option value="matched">Matched · TP</option>
                  <option value="extra">Extra · FP</option>
                  <option value="missing">Missing · FN</option>
                  <option value="provenance_failure">
                    Provenance failures
                  </option>
                </select>
              </label>
              <div className="relationship-list">
                {observation.relationships
                  .filter(
                    (item) => outcome === "all" || item.outcome === outcome,
                  )
                  .map((item) => (
                    <button
                      className="secondary"
                      key={item.id}
                      aria-pressed={relationshipId === item.id}
                      onClick={(event) =>
                        showEvidence(event.currentTarget, item.id)
                      }
                    >
                      {item.edge[0]}
                      <small>{item.edge[1].replaceAll("_", " ")}</small>
                      {item.edge[2]}
                      <small>{item.outcome.replaceAll("_", " ")}</small>
                    </button>
                  ))}
              </div>
              {!observation.relationships.length && (
                <p>No scored relationships available for this observation.</p>
              )}
            </section>
            <div
              ref={evidence}
              tabIndex={-1}
              className="selected-evidence"
              role="region"
              aria-label="Selected relationship Evidence"
            >
              <EvidenceInspector
                onBack={() => {
                  const target = selectedControl.current?.isConnected
                    ? selectedControl.current
                    : document.getElementById("relationships");
                  target?.focus({ preventScroll: true });
                  target?.scrollIntoView({
                    block: "center",
                    behavior: "instant",
                  });
                }}
                key={`${observation.id}-${relationship?.id ?? ""}`}
                relationship={relationship}
                source={observation.source}
                sources={observation.sources}
              />
            </div>
          </div>
        </>
      )}
    </details>
  );
}
