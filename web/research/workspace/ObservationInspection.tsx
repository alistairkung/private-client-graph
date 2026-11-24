import { useRef, useState } from "react";
import type { RunDetail } from "../shared/contracts";
import { EvidenceInspector } from "../results/EvidenceInspector";
import { metric } from "./RunChart";
import { GraphDrawing } from "../../src/features/review/GraphDrawing";
import type { CanonicalState } from "../shared/contracts";
import { BenchmarkProofs, edgeKey, graphEdgeKeys } from "./BenchmarkProofs";

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
  const [expectedEdge, setExpectedEdge] = useState<
    readonly [string, string, string] | null
  >(null);
  const observation =
    run.observations.find((item) => item.id === observationId) ??
    run.observations[0];
  const relationship = observation?.relationships.find(
    (item) => item.id === relationshipId,
  );
  const expected = observation?.benchmark?.expected;
  const expectedEvidence =
    expectedEdge &&
    observation?.benchmark?.expected_relationships.find(
      (item) => edgeKey(...item.edge) === edgeKey(...expectedEdge),
    );
  const evidenceRelationship =
    relationship ??
    (expectedEvidence
      ? {
          id: `expected:${expectedEvidence.edge.join(":")}`,
          edge: expectedEvidence.edge,
          outcome: "missing" as const,
          expected: expectedEvidence.quotes,
          predicted: [],
        }
      : undefined);
  const predicted = observation?.result?.state;
  const comparisonEdges = new Map(
    observation?.relationships.map((row) => [edgeKey(...row.edge), row]),
  );
  function graph(
    state: CanonicalState,
    label: string,
    side: "expected" | "predicted",
  ) {
    const keys = graphEdgeKeys(state);
    const selectedEdge = relationship?.edge ?? expectedEdge;
    const index = selectedEdge ? keys.indexOf(edgeKey(...selectedEdge)) : -1;
    return (
      <section
        className="benchmark-graph graph-workspace"
        aria-label={label}
        key={side}
      >
        <h4>{label}</h4>
        {state.relationships.length === 0 && <p>Valid empty graph</p>}
        {state.entities.length > 0 && (
          <GraphDrawing
            key={`${observation?.id}:${side}`}
            state={state}
            selected={index < 0 ? null : index}
            selectedEntity={null}
            memoryKey={`benchmark:${run.id}:${observation?.id}:${side}`}
            outcomes={keys.map((key) => comparisonEdges.get(key)?.outcome)}
            onSelect={(edgeIndex) => {
              const selected = comparisonEdges.get(keys[edgeIndex]);
              setRelationshipId(selected?.id ?? null);
              const expected =
                observation?.benchmark?.expected_relationships.find(
                  (row) => edgeKey(...row.edge) === keys[edgeIndex],
                );
              setExpectedEdge(selected ? null : (expected?.edge ?? null));
            }}
            onEntity={() => undefined}
          />
        )}
      </section>
    );
  }
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
            setExpectedEdge(null);
            setOutcome("all");
          }}
        >
          {run.benchmark
            ? Object.keys(run.benchmark.families).map((family) => (
                <optgroup key={family} label={`Family ${family}`}>
                  {run.observations
                    .filter((item) => item.benchmark?.family === family)
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.benchmark?.condition} · {item.benchmark?.role} ·{" "}
                        {item.status.replaceAll("_", " ")}
                      </option>
                    ))}
                </optgroup>
              ))
            : run.observations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.metadata?.name ?? item.case_id} ·{" "}
                  {item.metadata?.fixture_name ?? "Fixture name unavailable"} ·{" "}
                  {item.sample_id} · repetition {item.repetition} ·{" "}
                  {item.status}
                </option>
              ))}
        </select>
      </label>
      {observation && (
        <>
          <div className="observation-metadata">
            {observation.benchmark ? (
              <>
                <strong>
                  Family {observation.benchmark.family} · Condition{" "}
                  {observation.benchmark.condition}
                </strong>
                <p>
                  {observation.benchmark.role}
                  {observation.benchmark.contrast &&
                    ` · ${observation.benchmark.contrast}`}
                </p>
                <p>
                  Outcome: {observation.benchmark.outcome.replaceAll("_", " ")}
                </p>
              </>
            ) : (
              <>
                <strong>
                  {observation.metadata?.name ??
                    `Case ${observation.case_id} (name unavailable)`}
                </strong>
                <p>
                  {observation.metadata?.description ??
                    "Case description unavailable"}
                </p>
                <p>
                  {observation.metadata?.fixture_name ??
                    "Fixture name unavailable"}{" "}
                  —{" "}
                  {observation.metadata?.fixture_description ??
                    "Fixture description unavailable"}
                </p>
                <small>
                  {observation.case_id} · {observation.sample_id} · repetition{" "}
                  {observation.repetition} · {observation.status}
                </small>
                {observation.reason && <p>{observation.reason}</p>}
              </>
            )}
          </div>
          {observation?.benchmark && (
            <div className="benchmark-inspection">
              <h3>Expected and predicted canonical graphs</h3>
              {!predicted && (
                <p role="status">
                  Predicted canonical graph unavailable ·{" "}
                  {observation?.benchmark.failure_detail ??
                    observation?.benchmark.outcome}
                </p>
              )}
              {!predicted &&
                Boolean(observation?.benchmark.parsed_prediction) && (
                  <details>
                    <summary>Retained parsed prediction</summary>
                    <pre>
                      {JSON.stringify(
                        observation?.benchmark.parsed_prediction,
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                )}
              <details>
                <summary>Frozen Sources in order</summary>
                <ol>
                  {observation.sources?.map((source) => (
                    <li key={source.id}>
                      <h4>
                        {source.title} · {source.id}
                      </h4>
                      <pre>{source.text}</pre>
                    </li>
                  ))}
                </ol>
              </details>
              <div className="benchmark-graphs">
                {expected && graph(expected, "Expected graph", "expected")}
                {predicted &&
                  graph(
                    predicted,
                    predicted.relationships.length
                      ? "Predicted graph"
                      : "Predicted graph · valid empty graph",
                    "predicted",
                  )}
              </div>
              {predicted && (
                <p className="muted">
                  Green relationships matched. Red relationships were missing or
                  extra.
                </p>
              )}
              <p>
                Matched · TP {observation?.benchmark.metrics.tp} · Extra · FP{" "}
                {observation?.benchmark.metrics.fp} · Missing · FN{" "}
                {observation?.benchmark.metrics.fn}
              </p>
              <p>
                Proof {observation?.benchmark.metrics.complete_proofs}/
                {observation?.benchmark.metrics.planned_proofs} · Joint{" "}
                {observation?.benchmark.metrics.complete_joint_proofs}/
                {observation?.benchmark.metrics.planned_joint_proofs}
              </p>
              <p>
                Quotation{" "}
                {ratio(
                  observation?.benchmark.metrics.quote_passed,
                  observation?.benchmark.metrics.quote_assessed,
                )}{" "}
                · Source attribution{" "}
                {ratio(
                  observation?.benchmark.metrics.attribution_passed,
                  observation?.benchmark.metrics.attribution_assessed,
                )}
              </p>
              <BenchmarkProofs
                targets={observation.benchmark.proof_targets}
                predicted={predicted}
                sources={observation.sources ?? []}
              />
            </div>
          )}
          {observation.result?.evaluation && (
            <p>
              {observation.benchmark && "Valid graph · "}Precision {metric(observation.result.evaluation.precision)} ·
              Recall {metric(observation.result.evaluation.recall)} · F1{" "}
              {metric(observation.result.evaluation.f1)} · {observation.benchmark && "Legacy "}Provenance accuracy{" "}
              {metric(observation.result.evaluation.provenance_accuracy)}
            </p>
          )}
          {observation.result?.source_attribution && (
            <div>
              <p>
                Approved Source/quote associations on matched relationships:{" "}
                {observation.result.source_attribution.passed} /{" "}
                {observation.result.source_attribution.assessed}
              </p>
              {observation.result.source_attribution.failures.length > 0 && (
                <ul aria-label="Unapproved Source/quote associations">
                  {observation.result.source_attribution.failures.map(
                    (failure) => (
                      <li
                        key={JSON.stringify([
                          failure.edge,
                          failure.evidence_id,
                        ])}
                      >
                        {failure.edge.join(" · ")} — {failure.source_id}:{" "}
                        <q>{failure.supporting_text}</q>
                      </li>
                    ),
                  )}
                </ul>
              )}
            </div>
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
                    setExpectedEdge(null);
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
                key={`${observation.id}-${evidenceRelationship?.id ?? ""}`}
                relationship={evidenceRelationship}
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
const ratio = (passed: number, eligible: number) =>
  eligible
    ? `${passed}/${eligible} (${((passed / eligible) * 100).toFixed(1)}%)`
    : "Unavailable (0 eligible)";
