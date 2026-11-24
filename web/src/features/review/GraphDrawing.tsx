import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  useStore,
  type EdgeProps,
  type NodeProps,
} from "@xyflow/react";
import {
  graphDrawing,
  type DrawingBounds,
  type GraphDrawingModel,
} from "./graph-layout";
import {
  NODE_WIDTH,
  TRUST_HEIGHT,
  type RelationshipRoute,
} from "./node-geometry";
import { useSessionState } from "../../shared/session-state";
import type { CanonicalState } from "../../shared/contracts";
import { useLocale } from "../../shared/locale";
import "@xyflow/react/dist/style.css";
import "./graph-drawing.css";

const nodeTypes = { entity: EntityNode };
const edgeTypes = { relationship: RelationshipEdge };

function EntityNode({ data, selected }: NodeProps) {
  const trust = data.type === "trust";
  return (
    <div
      title={String(data.name)}
      className={
        "entity-node " +
        (trust ? "trust-entity" : "person-entity") +
        (selected ? " selected" : "")
      }
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      {trust ? (
        <>
          <svg
            viewBox={"0 0 " + NODE_WIDTH + " " + TRUST_HEIGHT}
            aria-hidden="true"
          >
            <polygon
              points={
                NODE_WIDTH / 2 +
                ",0 " +
                NODE_WIDTH +
                "," +
                TRUST_HEIGHT +
                " 0," +
                TRUST_HEIGHT
              }
            />
          </svg>
          <strong>{String(data.name)}</strong>
        </>
      ) : (
        <>
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <circle cx="10" cy="10" r="7" />
          </svg>
          <strong>{String(data.name)}</strong>
        </>
      )}
    </div>
  );
}
function RelationshipEdge({ id, selected, data, label }: EdgeProps) {
  const route = data?.route as RelationshipRoute;
  const path = route.points
    .map((point, index) => (index ? "L " : "M ") + point.x + " " + point.y)
    .join(" ");
  const emphasized = selected || Boolean(data?.emphasized);
  const outcome = data?.outcome as string | undefined;
  const comparisonColors: Record<string, string> = {
    correct: "var(--benchmark-correct)",
    missing: "var(--benchmark-missing)",
    unsupported: "var(--benchmark-unsupported)",
    expected: "var(--graph-line)",
  };
  const markerPrefix = String(data?.markerPrefix ?? "review");
  const markerId = data?.comparison
    ? selected
      ? `${markerPrefix}-parent-arrow-selected`
      : outcome && comparisonColors[outcome]
        ? `${markerPrefix}-parent-arrow-${outcome}`
        : `${markerPrefix}-parent-arrow`
    : `${markerPrefix}-parent-arrow`;
  const color = emphasized
    ? "var(--accent)"
    : data?.comparison && outcome
      ? comparisonColors[outcome] ?? "var(--graph-line)"
      : outcome === "missing" || outcome === "extra"
        ? "#ab382c"
        : outcome === "matched" || outcome === "provenance_failure"
          ? "#29725c"
          : data?.trust
            ? "var(--graph-line)"
            : "var(--graph-family-line)";
  return (
    <>
      <path
        className="edge-label-leader"
        d={
          "M " +
          route.anchor.x +
          " " +
          route.anchor.y +
          " L " +
          route.x +
          " " +
          route.y
        }
        fill="none"
        stroke={emphasized ? "var(--accent)" : "var(--graph-leader)"}
        strokeWidth={1}
        pointerEvents="none"
      />
      {emphasized && (
        <path
          d={path}
          fill="none"
          stroke="var(--graph-canvas)"
          strokeWidth={7}
          pointerEvents="none"
        />
      )}
      <BaseEdge
        id={id}
        path={path}
        interactionWidth={28}
        style={{
          stroke: color,
          strokeWidth: emphasized ? 2.8 : 1.6,
          strokeDasharray: data?.trust ? undefined : "5 5",
        }}
      markerEnd={data?.parent || data?.showDirection ? `url(#${markerId})` : undefined}
      />
      <EdgeLabelRenderer>
        <button
          type="button"
          className={
            "edge-label nodrag nopan " +
            (selected ? "selected " : "") +
            (emphasized ? "emphasized " : "") +
            (data?.comparison && outcome ? `comparison-${outcome}` : "")
          }
          data-edge-id={id}
          aria-label={outcome ? `${String(data?.statement)} · ${outcome.replaceAll("_", " ")}` : String(data?.statement)}
          aria-pressed={Boolean(selected)}
          onClick={(event) => {
            const select = data?.onSelect as
              | ((trigger?: HTMLButtonElement) => void)
              | undefined;
            if (data?.comparison) select?.(event.currentTarget);
            else select?.();
          }}
          onPointerEnter={() =>
            (data?.onEmphasis as (active: boolean) => void)(true)
          }
          onPointerLeave={() =>
            (data?.onEmphasis as (active: boolean) => void)(false)
          }
          onFocus={() => (data?.onEmphasis as (active: boolean) => void)(true)}
          onBlur={() => (data?.onEmphasis as (active: boolean) => void)(false)}
          style={{
            transform:
              "translate(-50%, -50%) translate(" +
              route.x +
              "px," +
              route.y +
              "px)",
            width: route.labelBounds.right - route.labelBounds.left,
          }}
        >
          {String(label)}
        </button>
      </EdgeLabelRenderer>
    </>
  );
}
function FitDrawing({
  graph,
  bounds,
  restored,
  onFitScaleChange,
  sharedBounds,
  manualView,
}: {
  graph: CanonicalState;
  bounds: DrawingBounds;
  restored: boolean;
  onFitScaleChange?: (scale: number) => void;
  sharedBounds?: DrawingBounds;
  manualView?: { current: boolean };
}) {
  const { fitBounds, getViewport, setViewport, viewportInitialized } = useReactFlow();
  const width = useStore((state) => state.width);
  const height = useStore((state) => state.height);
  const fittedBounds = sharedBounds ?? bounds;
  const fitScale = Math.min(width / fittedBounds.width, height / fittedBounds.height) * 0.9;
  const previous = useRef<{
    graph: CanonicalState;
    width: number;
    height: number;
  } | null>(null);
  useEffect(() => {
    if (!viewportInitialized || !width || !height) return;
    onFitScaleChange?.(fitScale);
    const last = previous.current;
    const sameLayout = last?.graph === graph;
    if (sameLayout && last.width === width && last.height === height) return;
    previous.current = { graph, width, height };
    if (!last && restored) return;
    if (sameLayout && manualView?.current) {
      // Hold the same point at the center of the resized canvas.
      const { x, y, zoom } = getViewport();
      void setViewport({
        x: x + (width - last.width) / 2,
        y: y + (height - last.height) / 2,
        zoom,
      });
      return;
    }
    if (manualView) manualView.current = false;
    void fitBounds(fittedBounds, { padding: 0.05 });
  }, [graph, fittedBounds, viewportInitialized, width, height, fitBounds,
    restored, fitScale, onFitScaleChange, manualView, getViewport, setViewport]);
  return null;
}
interface DrawingProps {
  state: CanonicalState;
  selected: number | null;
  selectedEntity: string | null;
  onSelect: (index: number, trigger?: HTMLButtonElement) => void;
  onEntity: (id: string) => void;
  memoryKey?: string;
  outcomes?: Array<string | undefined>;
  modelOverride?: GraphDrawingModel;
  onFitScaleChange?: (scale: number) => void;
  comparisonBounds?: DrawingBounds;
  preserveManualViewOnResize?: boolean;
  locateRequest?: { index: number; request: number };
}
export function GraphDrawing(props: DrawingProps) {
  return (
    <ReactFlowProvider>
      <Drawing {...props} />
    </ReactFlowProvider>
  );
}
function Drawing({
  state,
  selected,
  selectedEntity,
  onSelect,
  onEntity,
  memoryKey = "review:graph",
  outcomes,
  modelOverride,
  onFitScaleChange,
  comparisonBounds,
  preserveManualViewOnResize = false,
  locateRequest,
}: DrawingProps) {
  const { t } = useLocale();
  const flow = useReactFlow();
  const markerPrefix = useId().replaceAll(":", "");
  const [viewport, setViewport] = useSessionState<
    import("@xyflow/react").Viewport | undefined
  >(memoryKey + ":camera", undefined);
  const restored = useRef(Boolean(viewport)).current;
  const manualView = useRef(restored);
  const [emphasis, setEmphasis] = useState<number | null>(null);
  // Reserve the widest supported label in the initial bounds. Locale changes preserve the camera.
  const model = useMemo(
    () => modelOverride ?? graphDrawing(state, t, undefined, outcomes),
    [state, t, outcomes, modelOverride],
  );
  const lastLocatedRequest = useRef<number | null>(null);
  const flowWidth = useStore((store) => store.width);
  const flowHeight = useStore((store) => store.height);
  useEffect(() => {
    if (!locateRequest || !flowWidth || !flowHeight ||
      lastLocatedRequest.current === locateRequest.request) return;
    const route = model.edges[locateRequest.index]?.data?.route as
      | RelationshipRoute
      | undefined;
    if (!route) return;
    lastLocatedRequest.current = locateRequest.request;
    manualView.current = true;
    void flow.setCenter(route.x, route.y, { zoom: flow.getZoom(), duration: 0 }).then(() => {
      requestAnimationFrame(() => {
        document.querySelector<HTMLButtonElement>(
          `[data-graph-memory-key="${CSS.escape(memoryKey)}"] [data-edge-id="${locateRequest.index}"]`,
        )?.focus({ preventScroll: true });
      });
    });
  }, [locateRequest, flowWidth, flowHeight, model, flow, memoryKey]);
  const select = useRef(onSelect);
  select.current = onSelect;
  const handlers = useMemo(
    () =>
      model.edges.map((_, index) => ({
        onSelect: (trigger?: HTMLButtonElement) => {
          if (outcomes) select.current(index, trigger);
          else select.current(index);
        },
        onEmphasis: (active: boolean) =>
          setEmphasis((current) =>
            active ? index : current === index ? null : current,
          ),
      })),
    [model, outcomes],
  );
  const nodes = useMemo(() => {
    const activeEndpoints = [selected, emphasis].flatMap((index) =>
      index === null
        ? []
        : [
            state.relationships[index].source,
            state.relationships[index].target,
          ],
    );
    return model.nodes.map((node) => ({
      ...node,
      selected: node.id === selectedEntity || activeEndpoints.includes(node.id),
    }));
  }, [model, state, selected, selectedEntity, emphasis]);
  const edges = useMemo(
    () =>
      model.edges.map((edge, index) => ({
        ...edge,
        selected: selected === index,
        data: {
          ...edge.data,
          ...handlers[index],
          emphasized: emphasis === index,
          outcome: outcomes?.[index],
          comparison: Boolean(outcomes),
          markerPrefix,
          showDirection: Boolean(outcomes) && !["sibling_of", "spouse_of"].includes(state.relationships[index].type),
        },
      })),
    [model, handlers, selected, emphasis, outcomes, state],
  );
  return (
    <section className="graph-workspace" aria-label={t("Relationship graph")}>
      <p className="graph-navigation-hint">
        {t(
          "Drag to pan. Use the controls to zoom, or select a connector label to inspect Evidence.",
        )}
      </p>
      <div className="graph-container" data-graph-memory-key={memoryKey}>
        <svg width="0" height="0" className="graph-defs">
          <defs>
            <marker id={`${markerPrefix}-parent-arrow`} markerWidth="8" markerHeight="8"
              refX="7" refY="4" orient="auto">
              <path d="m0 0 8 4-8 4" fill="none" stroke="var(--muted)" />
            </marker>
            {Object.entries({
              correct: "var(--benchmark-correct)",
              missing: "var(--benchmark-missing)",
              unsupported: "var(--benchmark-unsupported)",
            }).map(([outcome, color]) => (
              <marker key={outcome} id={`${markerPrefix}-parent-arrow-${outcome}`}
                markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <path d="m0 0 8 4-8 4" fill="none" stroke={color} />
              </marker>
            ))}
            <marker id={`${markerPrefix}-parent-arrow-selected`} markerWidth="8" markerHeight="8"
              refX="7" refY="4" orient="auto">
              <path d="m0 0 8 4-8 4" fill="none" stroke="var(--accent)" />
            </marker>
          </defs>
        </svg>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          defaultViewport={viewport}
          onMoveStart={(event) => {
            if (event) manualView.current = true;
          }}
          onMoveEnd={(_, value) => setViewport(value)}
          onEdgeMouseEnter={(_, edge) => setEmphasis(Number(edge.id))}
          onEdgeMouseLeave={() => setEmphasis(null)}
          minZoom={0.15}
          maxZoom={2.5}
          zoomOnScroll={false}
          onEdgeClick={(_, edge) => onSelect(Number(edge.id))}
          onNodeClick={(_, node) => onEntity(node.id)}
          nodesDraggable={false}
          nodesConnectable={false}
          nodesFocusable
          autoPanOnNodeFocus={false}
          edgesFocusable={false}
          elementsSelectable
          deleteKeyCode={null}
          proOptions={{ hideAttribution: true }}
          ariaLabelConfig={{
            "node.a11yDescription.default": t(
              "Select an entity to explore its relationships.",
            ),
            "node.a11yDescription.keyboardDisabled": t(
              "Select an entity to explore its relationships.",
            ),
          }}
        >
          <FitDrawing
            graph={state}
            bounds={model.bounds}
            restored={restored}
            onFitScaleChange={onFitScaleChange}
            sharedBounds={comparisonBounds}
            manualView={preserveManualViewOnResize ? manualView : undefined}
          />
        </ReactFlow>
        <div className="graph-tools" aria-label={t("Graph controls")}>
          <button onClick={() => {
            manualView.current = true;
            void flow.zoomOut();
          }} aria-label={t("Zoom out")}>
            −
          </button>
          <button onClick={() => {
            manualView.current = true;
            void flow.zoomIn();
          }} aria-label={t("Zoom in")}>
            +
          </button>
          <button
            onClick={() => {
              manualView.current = false;
              void flow.fitBounds(comparisonBounds ?? model.bounds, { padding: 0.05 });
            }}
          >
            {t("Fit graph")}
          </button>
        </div>
      </div>
      <div className="graph-key" aria-label={t("Graph legend")}>
        <span>
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <circle cx="10" cy="10" r="6" />
          </svg>
          {t("Person")}
        </span>
        <span>
          <svg viewBox="0 0 24 20" aria-hidden="true">
            <path d="M12 2 22 18H2Z" />
          </svg>
          {t("Trust")}
        </span>
        <span>
          <svg viewBox="0 0 32 20" aria-hidden="true">
            <path d="M2 10h28" />
          </svg>
          {t("Trust role")}
        </span>
        <span>
          <svg viewBox="0 0 32 20" aria-hidden="true">
            <path d="M2 10h26m-5-4 5 4-5 4" strokeDasharray="4 3" />
          </svg>
          {t("Parent to child")}
        </span>
        <span>
          <svg viewBox="0 0 32 20" aria-hidden="true">
            <path d="M2 10h28" strokeDasharray="4 3" />
          </svg>
          {t("Spouse or sibling")}
        </span>
      </div>
    </section>
  );
}
