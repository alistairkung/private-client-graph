import { useEffect, useMemo, useRef } from "react";
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
import { graphDrawing, type DrawingBounds } from "./graph-layout";
import {
  NODE_WIDTH,
  TRUST_HEIGHT,
  type RelationshipRoute,
} from "./node-geometry";
import type { CanonicalState } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import "@xyflow/react/dist/style.css";

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
  const color = selected ? "#2358BA" : data?.trust ? "#425c78" : "#708297";
  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        interactionWidth={28}
        style={{
          stroke: color,
          strokeWidth: selected ? 2.8 : 1.6,
          strokeDasharray: data?.trust ? undefined : "5 5",
        }}
        markerEnd={data?.parent ? "url(#parent-arrow)" : undefined}
      />
      <EdgeLabelRenderer>
        <button
          type="button"
          className={"edge-label nodrag nopan " + (selected ? "selected" : "")}
          data-edge-id={id}
          aria-label={String(data?.statement)}
          aria-pressed={Boolean(selected)}
          onClick={() => (data?.onSelect as () => void)()}
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
}: {
  graph: CanonicalState;
  bounds: DrawingBounds;
}) {
  const { fitBounds, viewportInitialized } = useReactFlow();
  const width = useStore((state) => state.width);
  const height = useStore((state) => state.height);
  const previous = useRef<{
    graph: CanonicalState;
    width: number;
    height: number;
  } | null>(null);
  useEffect(() => {
    if (!viewportInitialized || !width || !height) return;
    const last = previous.current;
    if (last?.graph === graph && last.width === width && last.height === height)
      return;
    previous.current = { graph, width, height };
    void fitBounds(bounds, { padding: 0.05 });
  }, [graph, bounds, viewportInitialized, width, height, fitBounds]);
  return null;
}
interface DrawingProps {
  state: CanonicalState;
  selected: number | null;
  selectedEntity: string | null;
  onSelect: (index: number) => void;
  onEntity: (id: string) => void;
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
}: DrawingProps) {
  const { t, locale } = useLocale();
  const flow = useReactFlow();
  // Reserve the widest supported label in the initial bounds. Locale changes preserve the camera.
  const model = useMemo(() => graphDrawing(state, t), [state, locale]);
  const nodes = model.nodes.map((node) => ({
    ...node,
    selected: node.id === selectedEntity,
  }));
  const edges = model.edges.map((edge, index) => ({
    ...edge,
    selected: selected === index,
    data: { ...edge.data, onSelect: () => onSelect(index) },
  }));
  return (
    <section className="graph-workspace" aria-label={t("Relationship graph")}>
      <p className="graph-navigation-hint">
        {t(
          "Drag to pan. Use the controls to zoom, or select a connector label to inspect Evidence.",
        )}
      </p>
      <div className="graph-container">
        <svg width="0" height="0" className="graph-defs">
          <defs>
            <marker
              id="parent-arrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <path d="m0 0 8 4-8 4" fill="none" stroke="#536579" />
            </marker>
          </defs>
        </svg>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          minZoom={0.15}
          maxZoom={2.5}
          zoomOnScroll={false}
          onEdgeClick={(_, edge) => onSelect(Number(edge.id))}
          onNodeClick={(_, node) => onEntity(node.id)}
          nodesDraggable={false}
          nodesConnectable={false}
          nodesFocusable
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
          <FitDrawing graph={state} bounds={model.bounds} />
        </ReactFlow>
        <div className="graph-tools" aria-label={t("Graph controls")}>
          <button onClick={() => flow.zoomOut()} aria-label={t("Zoom out")}>
            −
          </button>
          <button onClick={() => flow.zoomIn()} aria-label={t("Zoom in")}>
            +
          </button>
          <button
            onClick={() => flow.fitBounds(model.bounds, { padding: 0.05 })}
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
