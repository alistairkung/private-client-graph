import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  const [side, setSide] = useState<Side>("expected");
  const [locateRequest, setLocateRequest] = useState<{
    side: Side;
    index: number;
    request: number;
  } | null>(null);
  const locateSequence = useRef(0);
  const [fitScales, setFitScales] = useState<Record<Side, number | null>>({
    expected: null,
    predicted: null,
  });
  const invokingControl = useRef<HTMLButtonElement | null>(null);
  const sourceRegion = useRef<HTMLElement>(null);
  const expectedGraphRef = useRef<HTMLElement>(null);
  const predictedGraphRef = useRef<HTMLElement>(null);
  const reportExpectedFitScale = useCallback((scale: number) => {
    setFitScales((current) => current.expected === scale
      ? current
      : { ...current, expected: scale });
  }, []);
  const reportPredictedFitScale = useCallback((scale: number) => {
    setFitScales((current) => current.predicted === scale
      ? current
      : { ...current, predicted: scale });
  }, []);

  useEffect(() => {
    invokingControl.current = null;
    if (savedEdgeKey === undefined) setLocalSelectedKey(null);
    setFilter("all");
    setShowIsolatedEntities(false);
    setSide("expected");
    setFitScales({ expected: null, predicted: null });
    setLocateRequest(null);
  }, [observation.id]);

  const selectedEdge = selectedKey ? rowByKey.get(selectedKey)?.edge : undefined;
  const counts = useMemo(
    () => rows.reduce((count, row) => ({ ...count, [row.status]: count[row.status] + 1 }), {
      correct: 0, missing: 0, unsupported: 0, expected: 0,
    }),
    [rows],
  );
  const expectedIsolated = (expected?.entities.length ?? 0) -
    (connectedExpected?.entities.length ?? 0);
  const predictedIsolated = predictionAvailable
    ? (prediction?.entities.length ?? 0) - (connectedPrediction?.entities.length ?? 0)
    : 0;
  const graphIsDense = rows.length >= 12 ||
    Math.max(visibleExpected?.entities.length ?? 0, visiblePrediction?.entities.length ?? 0) >= 20;
  const measuredFitScales = Object.values(fitScales).filter(
    (scale): scale is number => scale !== null,
  );
  const indexOpensByFit =
    measuredFitScales.length > 0 && Math.min(...measuredFitScales) < 0.75;
  function selectEdge(edge: Relationship, control?: HTMLButtonElement) {
    if (control) invokingControl.current = control;
    const key = edgeKey(...edge);
    setLocalSelectedKey(key);
    onSelectedEdgeChange?.(key);
  }

  function graphOutcomes(state: CanonicalState, graphSide: Side) {
    return outcomesFor(state, graphSide, rowByKey, predictionAvailable);
  }

  function graph(state: CanonicalState, roster: CanonicalState, graphSide: Side) {
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
            onFitScaleChange={graphSide === "expected" ? reportExpectedFitScale : reportPredictedFitScale}
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
              }
            }}
            onEntity={() => undefined}
          />
        )}
        {roster.entities.length > 0 && (
          <details className="condition-roster">
            <summary>Full Matter roster · {roster.entities.length}</summary>
            <ul aria-label={graphSide === "expected" ? "Expected entities" : "Predicted entities"}>
              {roster.entities.map((entity) => <li key={entity.id}>{entity.name}</li>)}
            </ul>
          </details>
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
    selectEdge(edge);
    if (!state) return;
    const index = graphEdgeKeys(state).indexOf(edgeKey(...edge));
    if (index < 0) return;
    setLocateRequest({ side: targetSide, index, request: ++locateSequence.current });
    const canvas = targetSide === "expected" ? expectedGraphRef.current : predictedGraphRef.current;
    canvas?.scrollIntoView?.({ block: "center", behavior: "instant" });
  }

  if (!benchmark || !expected || !visibleExpected) {
    return <p role="status">Expected graph unavailable for this condition.</p>;
  }

  const filteredRows = rows.filter((row) => filter === "all" || row.status === filter);
  return (
    <section className="condition-inspection" aria-label={`Environment Condition ${benchmark.condition} graph comparison`}>
      <div className="comparison-legend" role="group" aria-label="Relationship outcomes">
        {predictionAvailable ? (Object.keys(counts) as Status[]).filter((status) => status !== "expected").map((status) => (
          <span className={`outcome outcome-${status}`} key={status}>
            <span aria-hidden="true">{presentation[status].mark}</span>
            {presentation[status].label} <strong>{counts[status]}</strong>
          </span>
        )) : (
          <span className="outcome outcome-expected">Expected relationships <strong>{counts.expected}</strong></span>
        )}
      </div>

      {!predictionAvailable && <UnavailablePrediction observation={observation} />}

      {predictionAvailable && prediction && comparisonLayout && (
        <p className="layout-note" role="status">
          {comparisonLayout.aligned
            ? "Shared entities are aligned between the graphs."
            : "The graphs are placed independently because shared entities are ambiguous or would overlap."}
        </p>
      )}

      {expectedIsolated + predictedIsolated > 0 && (
        <label className="isolated-entities-control">
          <input
            type="checkbox"
            checked={showIsolatedEntities}
            onChange={(event) => setShowIsolatedEntities(event.target.checked)}
          />
          <span>Show isolated entities</span>
          <small>
            Expected {expectedIsolated}
            {predictionAvailable && ` · Predicted ${predictedIsolated}`}
          </small>
        </label>
      )}
      <div className="graph-side-tabs" role="group" aria-label="Graph side">
        <button aria-pressed={side === "expected"} onClick={() => setSide("expected")}>Expected</button>
        <button aria-pressed={side === "predicted"} disabled={!predictionAvailable} onClick={() => setSide("predicted")}>Predicted</button>
      </div>
      <div className="condition-graphs" data-side={side}>
        {graph(visibleExpected, expected, "expected")}
        {predictionAvailable && prediction && visiblePrediction &&
          graph(visiblePrediction, prediction, "predicted")}
      </div>

      {selectedEdge && <button className="secondary jump-to-evidence" onClick={() => sourceRegion.current?.focus()}>Jump to evidence</button>}
      <details className="relationship-index" open={graphIsDense || indexOpensByFit}>
        <summary>Relationships <span>{rows.length}</span></summary>
        <div className="relationship-index-controls">
          <label htmlFor={`relationship-filter-${observation.id}`}>Show</label>
          <select
            id={`relationship-filter-${observation.id}`}
            aria-label="Filter relationships"
            value={filter}
            onChange={(event) => setFilter(event.target.value as "all" | Status)}
          >
            <option value="all">All relationships</option>
            <option value="correct" disabled={!predictionAvailable}>Correct</option>
            <option value="missing" disabled={!predictionAvailable}>Missing</option>
            <option value="unsupported" disabled={!predictionAvailable}>Unsupported</option>
          </select>
        </div>
        <ul aria-label="Relationship outcomes">
          {filteredRows.map((row) => {
            const key = edgeKey(...row.edge);
            return (
              <li key={key}>
                <button
                  type="button"
                  className="relationship-index-row"
                  data-relationship-key={key}
                  aria-pressed={selectedKey === key}
                  onClick={(event) => {
                    setSide(row.status === "unsupported" ? "predicted" : "expected");
                    selectEdge(row.edge, event.currentTarget);
                  }}
                >
                  <span aria-hidden="true" className={`outcome-mark outcome-${row.status}`}>
                    {presentation[row.status].mark}
                  </span>
                  <span className="relationship-index-edge">
                    <strong>{row.edge[0]}</strong><span>{row.edge[1].replaceAll("_", " ")}</span><strong>{row.edge[2]}</strong>
                  </span>
                  <span className={`outcome-text outcome-${row.status}`}>{presentation[row.status].label}</span>
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
        {!filteredRows.length && <p>No relationships match this filter.</p>}
      </details>

      {selectedEdge && (
        <section
          ref={sourceRegion}
          tabIndex={-1}
          className="selected-relationship-evidence"
          role="region"
          aria-label="Selected relationship evidence"
        >
          <RelationshipEvidence
            key={`${observation.id}-${selectedKey}`}
            observation={observation}
            edge={selectedEdge}
          onBack={() => {
              const target = invokingControl.current?.isConnected &&
                invokingControl.current.getClientRects().length > 0
                ? invokingControl.current
                : selectedKey
                  ? document.querySelector<HTMLButtonElement>(
                      `[data-relationship-key="${CSS.escape(selectedKey)}"]`,
                    )
                  : null;
              if (target) {
                const index = target.closest("details");
                if (index) index.open = true;
                target.focus();
              } else {
                expectedGraphRef.current?.focus();
              }
            }}
          />
        </section>
      )}
    </section>
  );
}
