import { useEffect, useMemo, useRef, useState } from "react";
import type {
  CanonicalState,
  RelationshipOutcome,
  RunObservation,
} from "../shared/contracts";
import { useLocale } from "../../src/shared/locale";
import { alignComparisonEntities, graphDrawing } from "../../src/features/review/graph-layout";
import { GraphDrawing } from "../../src/features/review/GraphDrawing";
import { edgeKey, graphEdgeKeys } from "./benchmarkEdges";
import { RelationshipEvidence } from "./RelationshipEvidence";
import { UnavailablePrediction } from "./UnavailablePrediction";
import "./condition-inspection.css";
import "./condition-workbench.css";

type Status = "correct" | "missing" | "unsupported" | "expected";
type Side = "expected" | "predicted";
type Relationship = [string, string, string];

function outcomesFor(
  graph: CanonicalState,
  side: Side,
  rows: ReadonlyMap<string, { edge: Relationship; status: Status }>,
  predictionAvailable: boolean,
) {
  return graphEdgeKeys(graph).map((key) => {
    if (!predictionAvailable) return "expected";
    const status = rows.get(key)?.status;
    if (!status || status === "expected") return undefined;
    if (side === "expected" && status === "unsupported") return undefined;
    if (side === "predicted" && status === "missing") return undefined;
    return status;
  });
}

function hideIsolatedEntities(state: CanonicalState | undefined) {
  if (!state) return undefined;
  const endpoints = new Set(
    state.relationships.flatMap(({ source, target }) => [source, target]),
  );
  const entities = state.entities.filter(({ id }) => endpoints.has(id));
  return entities.length === state.entities.length ? state : { ...state, entities };
}

function combineBounds(
  first: { x: number; y: number; width: number; height: number },
  second: { x: number; y: number; width: number; height: number },
) {
  const x = Math.min(first.x, second.x);
  const y = Math.min(first.y, second.y);
  const right = Math.max(first.x + first.width, second.x + second.width);
  const bottom = Math.max(first.y + first.height, second.y + second.height);
  return { x, y, width: right - x, height: bottom - y };
}

const presentation: Record<Status, { label: string; mark: string }> = {
  correct: { label: "Correct", mark: "✓" },
  missing: { label: "Missing", mark: "−" },
  unsupported: { label: "Unsupported", mark: "+" },
  expected: { label: "Expected", mark: "○" },
};

function outcomeStatus(outcome: RelationshipOutcome["outcome"]): Status {
  if (outcome === "missing") return "missing";
  if (outcome === "extra") return "unsupported";
  return "correct";
}

export function ConditionInspection({
  runId,
  observation,
  selectedEdgeKey: savedEdgeKey,
  onSelectedEdgeChange,
}: {
  runId: string;
  observation: RunObservation;
  selectedEdgeKey?: string | null;
  onSelectedEdgeChange?: (edgeKey: string | null) => void;
}) {
  const { t } = useLocale();
  const benchmark = observation.benchmark;
  const expected = benchmark?.expected;
  const prediction = observation.result?.state ?? undefined;
  const predictionAvailable = Boolean(
    prediction && benchmark?.outcome === "scored",
  );
  const comparison = predictionAvailable ? observation.relationships : [];
  const rows = useMemo(() => {
    if (predictionAvailable) {
      return comparison.map((relationship) => ({
        edge: relationship.edge as Relationship,
        status: outcomeStatus(relationship.outcome),
      }));
    }
    return (benchmark?.expected_relationships ?? []).map((relationship) => ({
      edge: relationship.edge as Relationship,
      status: "expected" as const,
    }));
  }, [benchmark?.expected_relationships, comparison, predictionAvailable]);
  const rowByKey = useMemo(
    () => new Map(rows.map((row) => [edgeKey(...row.edge), row])),
    [rows],
  );
  const [showIsolatedEntities, setShowIsolatedEntities] = useState(false);
  const connectedExpected = useMemo(() => hideIsolatedEntities(expected), [expected]);
  const connectedPrediction = useMemo(() => hideIsolatedEntities(prediction), [prediction]);
  const visibleExpected = showIsolatedEntities ? expected : connectedExpected;
  const visiblePrediction = showIsolatedEntities ? prediction : connectedPrediction;
  const comparisonLayout = useMemo(() => {
    if (!predictionAvailable || !expected || !prediction ||
      !visibleExpected?.entities.length || !visiblePrediction?.entities.length) {
      return undefined;
    }
    const expectedLayout = graphDrawing(
      visibleExpected,
      t,
      undefined,
      outcomesFor(visibleExpected, "expected", rowByKey, true),
    );
    const predictedOutcomes = outcomesFor(visiblePrediction, "predicted", rowByKey, true);
    const independentPrediction = graphDrawing(visiblePrediction, t, undefined, predictedOutcomes);
    const alignedPositions = alignComparisonEntities(
      expected,
      prediction,
      expectedLayout,
      independentPrediction,
    );
    if (!alignedPositions) {
      return {
        aligned: false,
        expected: expectedLayout,
        predicted: independentPrediction,
        bounds: undefined,
      };
    }
    const alignedPrediction = graphDrawing(visiblePrediction, t, alignedPositions, predictedOutcomes);
    return {
      aligned: true,
      expected: expectedLayout,
      predicted: alignedPrediction,
      bounds: combineBounds(expectedLayout.bounds, alignedPrediction.bounds),
    };
  }, [expected, prediction, predictionAvailable, rowByKey, t, visibleExpected, visiblePrediction]);
  const [localSelectedKey, setLocalSelectedKey] = useState<string | null>(null);
  const selectedKey = savedEdgeKey === undefined ? localSelectedKey : savedEdgeKey;
  const [filter, setFilter] = useState<"all" | Status>("all");
  const [view, setView] = useState<"graphs" | "relationships">("graphs");
  const relationshipList = useRef<HTMLElement>(null);
  const [side, setSide] = useState<Side>("expected");
  const [locateRequest, setLocateRequest] = useState<{
    side: Side;
    index: number;
    request: number;
  } | null>(null);
  const locateSequence = useRef(0);
  const invokingControl = useRef<HTMLButtonElement | null>(null);
  const sourceRegion = useRef<HTMLDivElement>(null);
  const expectedGraphRef = useRef<HTMLElement>(null);
  const predictedGraphRef = useRef<HTMLElement>(null);

  useEffect(() => {
    invokingControl.current = null;
    if (savedEdgeKey === undefined) setLocalSelectedKey(null);
    setFilter("all");
    setShowIsolatedEntities(false);
    setSide("expected");
    setView("graphs");
    setLocateRequest(null);
  }, [observation.id]);

  const selectedEdge = selectedKey ? rowByKey.get(selectedKey)?.edge : undefined;
  const counts = rows.reduce((total, row) => {
    total[row.status] += 1;
    return total;
  }, { correct: 0, missing: 0, unsupported: 0, expected: 0 });
  const expectedIsolated = (expected?.entities.length ?? 0) -
    (connectedExpected?.entities.length ?? 0);
  const predictedIsolated = predictionAvailable
    ? (prediction?.entities.length ?? 0) - (connectedPrediction?.entities.length ?? 0)
    : 0;
  const proofStates = useMemo(() => new Map(
    benchmark?.proof_targets.map((target) => [
      edgeKey(...target.edge),
      { complete: "Proof complete", incomplete: "Proof incomplete", missed: "Proof missed", without_graph: "No valid graph" }[target.status],
    ]),
  ), [benchmark?.proof_targets]);

  function focusRelationshipEvidence() {
    sourceRegion.current?.querySelector<HTMLElement>(".relationship-evidence")?.focus();
  }

  function inspectRelationships(nextFilter: "all" | Status, focusEvidence = false) {
    setFilter(nextFilter);
    setView("relationships");
    requestAnimationFrame(() => {
      if (focusEvidence) focusRelationshipEvidence();
      else relationshipList.current?.focus();
    });
  }

  function selectEdge(edge: Relationship, control?: HTMLButtonElement) {
    if (control) invokingControl.current = control;
    const key = edgeKey(...edge);
    setLocalSelectedKey(key);
    onSelectedEdgeChange?.(key);
  }

  function graphOutcomes(state: CanonicalState, graphSide: Side) {
    return outcomesFor(state, graphSide, rowByKey, predictionAvailable);
  }

  function graph(state: CanonicalState, graphSide: Side) {
    const keys = graphEdgeKeys(state);
    const selectedIndex = selectedKey ? keys.indexOf(selectedKey) : -1;
    const outcomes = graphOutcomes(state, graphSide);
    const view = showIsolatedEntities ? "all-entities" : "connected";
    const memoryKey = `benchmark:${runId}:${observation.id}:${graphSide}:${view}`;
    return (
      <section
        ref={graphSide === "expected" ? expectedGraphRef : predictedGraphRef}
        tabIndex={-1}
        className={`condition-graph condition-graph-${graphSide}`}
        aria-label={graphSide === "expected" ? "Expected graph" : "Predicted graph"}
        data-active={side === graphSide}
      >
        <h4>{graphSide === "expected" ? "Expected" : "Predicted"}</h4>
        {state.relationships.length === 0 && (
          <p className={state.entities.length === 0 ? "condition-valid-empty" : "layout-note"}>
            {graphSide === "expected" ? "0 expected relationships" : "Graph constructed · 0 relationships"}
          </p>
        )}
        {state.entities.length > 0 && (
          <GraphDrawing
            key={memoryKey}
            state={state}
            selected={selectedIndex < 0 ? null : selectedIndex}
            selectedEntity={null}
            memoryKey={memoryKey}
            outcomes={outcomes}
            modelOverride={graphSide === "expected"
              ? comparisonLayout?.expected
              : comparisonLayout?.predicted}
            comparisonBounds={comparisonLayout?.bounds}
            preserveManualViewOnResize
            locateRequest={locateRequest?.side === graphSide
              ? { index: locateRequest.index, request: locateRequest.request }
              : undefined}
            onSelect={(index, trigger) => {
              const row = rowByKey.get(keys[index]);
              if (row) {
                setSide(graphSide);
                selectEdge(row.edge, trigger);
                inspectRelationships("all", true);
              }
            }}
            onEntity={() => undefined}
          />
        )}

      </section>
    );
  }

  function locateRelationship(
    edge: Relationship,
    status: Status,
    control: HTMLButtonElement,
  ) {
    const targetSide: Side = status === "unsupported" ? "predicted" : "expected";
    const state = targetSide === "expected" ? expected : prediction;
    invokingControl.current = control;
    setSide(targetSide);
    setView("graphs");
    selectEdge(edge);
    if (!state) return;
    const index = graphEdgeKeys(state).indexOf(edgeKey(...edge));
    if (index < 0) return;
    setLocateRequest({ side: targetSide, index, request: ++locateSequence.current });
    const canvas = targetSide === "expected" ? expectedGraphRef.current : predictedGraphRef.current;
    requestAnimationFrame(() => canvas?.scrollIntoView?.({ block: "nearest", behavior: "instant" }));
  }

  if (!benchmark || !expected || !visibleExpected) {
    return <p role="status">Expected graph unavailable for this condition.</p>;
  }

  const filteredRows = rows.filter((row) => filter === "all" || row.status === filter);
  const inspectedEdge = filteredRows.some((row) => edgeKey(...row.edge) === selectedKey)
    ? selectedEdge
    : undefined;
  return (
    <section className="condition-inspection condition-graph-first" aria-label={`Environment Condition ${benchmark.condition} graph comparison`}>
      <div className="comparison-toolbar">
        <div className="comparison-views" role="group" aria-label="Comparison view">
          <button type="button" aria-pressed={view === "graphs"} onClick={() => setView("graphs")}>Graphs</button>
          <button type="button" aria-pressed={view === "relationships"} onClick={() => inspectRelationships("all")}>
            Relationships <span>{rows.length}</span>
          </button>
        </div>
        <div className="comparison-legend" role="group" aria-label="Relationship outcomes">
          {(predictionAvailable ? (["correct", "missing", "unsupported"] as const) : (["expected"] as const)).map((status) => (
            <button
              type="button"
              className={`outcome outcome-${status}`}
              key={status}
              aria-pressed={view === "relationships" && filter === status}
              onClick={() => inspectRelationships(status)}
            >
              <span aria-hidden="true">{presentation[status].mark}</span>
              {status === "expected" ? "Expected relationships" : presentation[status].label} <strong>{counts[status]}</strong>
            </button>
          ))}
        </div>
        {view === "graphs" && (
          <details className="comparison-options">
            <summary>Graph options</summary>
            {expectedIsolated + predictedIsolated > 0 && (
              <label className="isolated-entities-control">
                <input
                  type="checkbox"
                  checked={showIsolatedEntities}
                  onChange={(event) => setShowIsolatedEntities(event.target.checked)}
                />
                <span>Show isolated entities</span>
                <small>
                  Expected {expectedIsolated}{predictionAvailable && ` · Predicted ${predictedIsolated}`}
                </small>
              </label>
            )}
            {comparisonLayout && (
              <p className="layout-note">
                {comparisonLayout.aligned
                  ? "Shared entities are aligned between the graphs."
                  : "Graphs use independent layouts because shared entities are ambiguous or would overlap."}
              </p>
            )}
            <div className="comparison-rosters">
              {matterRoster(expected, "Expected")}
              {predictionAvailable && prediction && matterRoster(prediction, "Predicted")}
            </div>
          </details>
        )}
      </div>

      <div hidden={view !== "graphs"} className="comparison-graph-view">
        <div className="comparison-graph-settings">
          <div className="graph-side-tabs" role="group" aria-label="Graph side">
            <button aria-pressed={side === "expected"} onClick={() => setSide("expected")}>Expected</button>
            <button aria-pressed={side === "predicted"} disabled={!predictionAvailable} onClick={() => setSide("predicted")}>Predicted</button>
          </div>

          {comparisonLayout && !comparisonLayout.aligned && (
            <span className="layout-note">Independent layouts</span>
          )}
        </div>
        <div className="condition-graphs" data-side={side}>
          {graph(visibleExpected, "expected")}
          {predictionAvailable && visiblePrediction && graph(visiblePrediction, "predicted")}
          {!predictionAvailable && <UnavailablePrediction observation={observation} />}
        </div>
      </div>

      <div className="comparison-inspector" hidden={view !== "relationships"}>
        <section ref={relationshipList} tabIndex={-1} className="relationship-index" aria-label="Relationship list">
          <div className="inspector-list-heading">
            <h4>{filter === "all" ? "Relationships" : `${presentation[filter].label} relationships`}</h4>
            <span>{filteredRows.length} of {rows.length}</span>
          </div>
          <ul aria-label="Relationship outcomes">
            {filteredRows.map((row) => {
              const key = edgeKey(...row.edge);
              return (
                <li key={key}>
                  <button
                    type="button"
                    className="relationship-index-row"
                    aria-pressed={selectedKey === key}
                    onClick={(event) => {
                      setSide(row.status === "unsupported" ? "predicted" : "expected");
                      selectEdge(row.edge, event.currentTarget);
                      requestAnimationFrame(focusRelationshipEvidence);
                    }}
                  >
                    <span aria-hidden="true" className={`outcome-mark outcome-${row.status}`}>
                      {presentation[row.status].mark}
                    </span>
                    <span className="relationship-index-edge">
                      <strong>{row.edge[0]}</strong><span>{row.edge[1].replaceAll("_", " ")}</span><strong>{row.edge[2]}</strong>
                    </span>
                    <span className={`outcome-text outcome-${row.status}`}>{presentation[row.status].label}</span>
                    {proofStates.has(key) && <small className="relationship-row-proof">{proofStates.get(key)}</small>}
                  </button>
                  <button
                    type="button"
                    className="locate-relationship"
                    onClick={(event) => locateRelationship(row.edge, row.status, event.currentTarget)}
                    aria-label={`Locate ${row.edge.join(" ")} in graph`}
                    hidden={selectedKey !== key}
                  >Locate in graph</button>
                </li>
              );
            })}
          </ul>
          {!filteredRows.length && <p>No relationships match this outcome.</p>}
        </section>

        {inspectedEdge ? (
          <div ref={sourceRegion} className="selected-relationship-evidence">
            <RelationshipEvidence
              key={`${observation.id}-${selectedKey}`}
              observation={observation}
              edge={inspectedEdge}
              onBack={() => {
                const target = invokingControl.current?.isConnected &&
                  invokingControl.current.getClientRects().length > 0
                  ? invokingControl.current
                  : relationshipList.current?.querySelector<HTMLButtonElement>(
                      ".relationship-index-row[aria-pressed='true']",
                    );
                target?.focus();
              }}
            />
          </div>
        ) : (
          <section className="comparison-evidence-empty">
            <h4>Supporting evidence</h4>
            <p>Select a relationship to inspect its proof and Sources.</p>
          </section>
        )}
      </div>
    </section>
  );
}

function matterRoster(state: CanonicalState, side: "Expected" | "Predicted") {
  if (!state.entities.length) return null;
  return (
    <details className="condition-roster">
      <summary>{side} Matter roster · {state.entities.length}</summary>
      <ul aria-label={`${side} entities`}>
        {state.entities.map((entity) => <li key={entity.id}>{entity.name}</li>)}
      </ul>
    </details>
  );
}
