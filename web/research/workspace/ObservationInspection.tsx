import { useRef, useState } from "react";
import type { RunDetail } from "../shared/contracts";
import { EvidenceInspector } from "../results/EvidenceInspector";
import { metric } from "./RunChart";
import { GraphDrawing } from "../../src/features/review/GraphDrawing";
import type { CanonicalState } from "../shared/contracts";
import type { BenchmarkObservation } from "./benchmark-types";

const symmetric = new Set(["spouse_of", "sibling_of"]);
function edgeKey(source: string, type: string, target: string) {
  const [left, right] = symmetric.has(type) && source.localeCompare(target) > 0 ? [target, source] : [source, target];
  return JSON.stringify([left, type, right]);
}

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
  const [expectedEdge, setExpectedEdge] = useState<readonly [string, string, string] | null>(null);
  const observation =
    run.observations.find((item) => item.id === observationId) ??
    run.observations[0];
  const benchmarkObservation = observation as BenchmarkObservation | undefined;
  const relationship = observation?.relationships.find(
    (item) => item.id === relationshipId,
  );
  const expected = benchmarkObservation?.benchmark?.expected;
  const expectedEvidence = expectedEdge && benchmarkObservation?.benchmark?.expected_relationships.find(item => edgeKey(...item.edge) === edgeKey(...expectedEdge));
  const evidenceRelationship = relationship ?? (expectedEvidence ? {
    id: `expected:${expectedEvidence.edge.join(":")}`,
    edge: expectedEvidence.edge,
    outcome: "missing" as const,
    expected: expectedEvidence.quotes,
    predicted: [],
  } : undefined);
  const predicted = observation?.result?.state;
  const memberStatus = (sourceId: string, quote: string, edge: readonly [string, string, string]) => {
    if (!predicted?.sources.some(source => source.id === sourceId)) return "Source missing";
    const targetKey = edgeKey(...edge);
    const relation = predicted.relationships.find(item => edgeKey(
      predicted.entities.find(entity => entity.id === item.source)?.name ?? item.source,
      item.type,
      predicted.entities.find(entity => entity.id === item.target)?.name ?? item.target,
    ) === targetKey);
    if (!relation) return "Source present but relationship not attached";
    const evidence = predicted.evidence.filter(item => relation.evidence_ids.includes(item.id) && item.source_id === sourceId);
    return evidence.some(item => item.supporting_text === quote)
      ? "Attached to this relationship"
      : evidence.length ? "Wrong quotation on this relationship" : "Source present but relationship not attached";
  };
  const relationshipIndices = (state: CanonicalState | null | undefined) =>
    state?.relationships.flatMap((edge, index) => {
      const source = state.entities.find(entity => entity.id === edge.source)?.name ?? edge.source;
      const target = state.entities.find(entity => entity.id === edge.target)?.name ?? edge.target;
      const match = benchmarkObservation?.relationships.find((item) => edgeKey(...item.edge) === edgeKey(source, edge.type, target));
      return match ? [{ index, outcome: match.outcome, relationshipId: match.id }] : [];
    }) ?? [];
  const graph = (state: CanonicalState, label: string, side: "expected" | "predicted") => {
    const statuses = relationshipIndices(state);
    const selectedIndex = relationship
      ? statuses.find(item => item.relationshipId === relationship.id)?.index ?? null
      : expectedEdge ? state.relationships.findIndex(edge => edgeKey(
          state.entities.find(entity => entity.id === edge.source)?.name ?? edge.source,
          edge.type,
          state.entities.find(entity => entity.id === edge.target)?.name ?? edge.target,
        ) === edgeKey(...expectedEdge)) : null;
    return <section className="benchmark-graph graph-workspace" aria-label={label} key={side}>
      <h4>{label}</h4>
      <GraphDrawing state={state} selected={selectedIndex} selectedEntity={null} memoryKey={`benchmark:${observation?.id}:${side}`} onSelect={(index) => {
        const status = statuses.find(item => item.index === index);
        const item = status && observation?.relationships.find(value => value.id === status.relationshipId);
        if (item) { setRelationshipId(item.id); setExpectedEdge(null); }
        else {
          const edge = state.relationships[index];
          setExpectedEdge([
            state.entities.find(entity => entity.id === edge.source)?.name ?? edge.source,
            edge.type,
            state.entities.find(entity => entity.id === edge.target)?.name ?? edge.target,
          ]);
          setRelationshipId(null);
        }
      }} onEntity={() => undefined} />
    </section>;
  };
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
            {run.observations.map((raw) => {
              const item = raw as BenchmarkObservation;
              return <option key={item.id} value={item.id}>
                {item.benchmark ? `${item.benchmark.family} · ${item.benchmark.condition}${item.benchmark.role ? ` · ${item.benchmark.role}` : ""} · ${item.benchmark.outcome}` : `${item.metadata?.name ?? item.case_id} · ${item.metadata?.fixture_name ?? "Fixture name unavailable"} · ${item.sample_id} · repetition ${item.repetition} · ${item.status}`}
              </option>;
            })}
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
            {benchmarkObservation?.benchmark && <p><strong>{benchmarkObservation?.benchmark.family}</strong> · {benchmarkObservation?.benchmark.condition}{benchmarkObservation?.benchmark.role ? ` · ${benchmarkObservation?.benchmark.role}` : ""}{benchmarkObservation?.benchmark.contrast ? ` · ${benchmarkObservation?.benchmark.contrast}` : ""}</p>}
            {benchmarkObservation?.benchmark && <p>Outcome: {benchmarkObservation?.benchmark.outcome.replaceAll("_", " ")}{benchmarkObservation?.benchmark.failure_detail ? ` · ${benchmarkObservation?.benchmark.failure_detail}` : ""}</p>}
          </div>
          {benchmarkObservation?.benchmark && <div className="benchmark-inspection">
            <h3>Expected and predicted canonical graphs</h3>
            {!predicted && <p role="status">Predicted canonical graph unavailable · {benchmarkObservation?.benchmark.failure_detail ?? benchmarkObservation?.benchmark.outcome}</p>}
            {!predicted && Boolean(benchmarkObservation?.benchmark.parsed_prediction) && <details><summary>Retained parsed prediction</summary><pre>{JSON.stringify(benchmarkObservation?.benchmark.parsed_prediction, null, 2)}</pre></details>}
            <details><summary>Frozen Sources in order</summary><ol>{observation.sources?.map(source => <li key={source.id}><h4>{source.title} · {source.id}</h4><pre>{source.text}</pre></li>)}</ol></details>
            <div className="benchmark-graphs">{expected && graph(expected, "Expected graph", "expected")}{predicted && graph(predicted, predicted.relationships.length ? "Predicted graph" : "Predicted graph · valid empty graph", "predicted")}</div>
            <p>Matched · TP {benchmarkObservation?.benchmark.metrics.tp} · Extra · FP {benchmarkObservation?.benchmark.metrics.fp} · Missing · FN {benchmarkObservation?.benchmark.metrics.fn}</p>
            <p>Proof {benchmarkObservation?.benchmark.metrics.complete_proofs}/{benchmarkObservation?.benchmark.metrics.planned_proofs} · Joint {benchmarkObservation?.benchmark.metrics.complete_joint_proofs}/{benchmarkObservation?.benchmark.metrics.planned_joint_proofs}</p>
            <p>Quotation {ratio(benchmarkObservation?.benchmark.metrics.quote_passed, benchmarkObservation?.benchmark.metrics.quote_assessed)} · Source attribution {ratio(benchmarkObservation?.benchmark.metrics.attribution_passed, benchmarkObservation?.benchmark.metrics.attribution_assessed)}</p>
            <ul aria-label="Proof outcomes">{benchmarkObservation?.benchmark.proof_targets.map((target, index) => <li key={`${target.edge.join(":")}:${index}`}>{target.edge.join(" · ")} · {target.status.replaceAll("_", " ")}{target.alternatives.map((alternative, alternativeIndex) => <ul key={alternativeIndex} aria-label={`Evidence alternative ${alternativeIndex + 1}`}><li><strong>Alternative {alternativeIndex + 1}</strong></li>{alternative.members.map((member, memberIndex) => <li key={`${member.source_id}:${memberIndex}`}><code>{member.source_id}</code> · <q>{member.text}</q> · {member.attached ? "Attached to this relationship" : `Not attached · ${memberStatus(member.source_id, member.text, target.edge)}`}</li>)}</ul>)}</li>)}</ul>
          </div>}
          {observation.result?.evaluation && (
            <p>
              Precision {metric(observation.result.evaluation.precision)} ·
              Recall {metric(observation.result.evaluation.recall)} · F1{" "}
              {metric(observation.result.evaluation.f1)} · Provenance accuracy{" "}
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
                  {observation.result.source_attribution.failures.map((failure) => (
                    <li key={JSON.stringify([failure.edge, failure.evidence_id])}>
                      {failure.edge.join(" · ")} — {failure.source_id}:{" "}
                      <q>{failure.supporting_text}</q>
                    </li>
                  ))}
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
const ratio = (passed: number, eligible: number) => eligible ? `${passed}/${eligible} (${(passed / eligible * 100).toFixed(1)}%)` : "Unavailable (0 eligible)";
