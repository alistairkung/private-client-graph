import { Fragment, useEffect, useMemo, useRef } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type EdgeProps,
  type NodeProps,
} from "@xyflow/react";
import { connectorGeometry, type Obstacle } from "./connectors";
import { graphDrawing, positions } from "./presentation";
import type { CanonicalState } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import "@xyflow/react/dist/style.css";

const nodeTypes = { entity: EntityNode };
const edgeTypes = { relationship: RelationshipEdge };
function EntityNode({ data, selected }: NodeProps) {
  return (
    <div className={"entity-node " + (selected ? "selected" : "")}>
      {Object.entries(positions).map(([key, position]) => (
        <Fragment key={key}>
          <Handle type="source" id={key} position={position} />
          <Handle type="target" id={"target-" + key} position={position} />
        </Fragment>
      ))}
      <svg viewBox="0 0 40 40" aria-hidden="true">
        {data.type === "trust" ? (
          <path d="M20 5 36 34H4Z" />
        ) : (
          <circle cx="20" cy="20" r="11" />
        )}
      </svg>
      <div>
        <strong>{String(data.name)}</strong>
        <span>{String(data.kindLabel)}</span>
      </div>
    </div>
  );
}
function RelationshipEdge(props: EdgeProps) {
  const { sourceX, sourceY, targetX, targetY, selected, data, label } = props;
  const geometry = connectorGeometry(
    { sourceX, sourceY, targetX, targetY },
    Number(data?.lane ?? 0),
    data?.obstacles as Obstacle[] | undefined,
  );
  const color = selected ? "#2358BA" : data?.trust ? "#536579" : "#8A9AAA";
  return (
    <>
      <BaseEdge
        id={props.id}
        path={geometry.path}
        interactionWidth={28}
        style={{
          stroke: color,
          strokeWidth: selected ? 3 : data?.trust ? 1.8 : 1.4,
        }}
        markerEnd={data?.parent ? "url(#parent-arrow)" : undefined}
      />
      <EdgeLabelRenderer>
        <div
          className={"edge-label nodrag nopan " + (selected ? "selected" : "")}
          style={{
            transform:
              "translate(-50%, -50%) translate(" +
              geometry.label.x +
              "px," +
              geometry.label.y +
              "px)",
          }}
        >
          {String(label)}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
export function GraphDrawing(props: {
  state: CanonicalState;
  selected: number | null;
  selectedEntity: string | null;
  onSelect: (index: number) => void;
  onEntity: (id: string) => void;
}) {
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
}: {
  state: CanonicalState;
  selected: number | null;
  selectedEntity: string | null;
  onSelect: (index: number) => void;
  onEntity: (id: string) => void;
}) {
  const { t, locale } = useLocale();
  const flow = useReactFlow();
  const drawing = useMemo(() => graphDrawing(state, t), [state, locale]);
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      void flow.fitView({ padding: 0.06, minZoom: 0.8, maxZoom: 1.1 });
    });
    observer.observe(container.current);
    return () => observer.disconnect();
  }, [flow.fitView]);
  const nodes = drawing.nodes.map((node) => ({
    ...node,
    selected: selectedEntity === node.id,
  }));
  const edges = drawing.edges.map((edge) => ({
    ...edge,
    selected: String(selected) === edge.id,
  }));
  return (
    <div
      className="graph-container"
      ref={container}
      aria-label={t("Relationship graph")}
    >
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
        fitView
        fitViewOptions={{ padding: 0.06, minZoom: 0.8, maxZoom: 1.1 }}
        minZoom={0.15}
        maxZoom={2.5}
        onEdgeClick={(_, edge) => onSelect(Number(edge.id))}
        onNodeClick={(_, node) => onEntity(node.id)}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        edgesFocusable
        nodesFocusable
        deleteKeyCode={null}
        onNodeDrag={undefined}
        onInit={(instance) =>
          instance.fitView({ padding: 0.06, minZoom: 0.8, maxZoom: 1.1 })
        }
        proOptions={{ hideAttribution: true }}
        ariaLabelConfig={{
          "edge.a11yDescription.default": t(
            "Select a relationship to inspect its Evidence.",
          ),
          "node.a11yDescription.default": t(
            "Select an entity to explore its relationships.",
          ),
        }}
      />
      <div className="graph-tools" aria-label={t("Graph controls")}>
        <button onClick={() => flow.zoomOut()} aria-label={t("Zoom out")}>
          −
        </button>
        <button onClick={() => flow.zoomIn()} aria-label={t("Zoom in")}>
          +
        </button>
        <button onClick={() => flow.fitView({ padding: 0.06, maxZoom: 1.1 })}>
          {t("Fit graph")}
        </button>
      </div>
      <div className="graph-key">
        <span className="key-person" />
        {t("Person")}
        <span className="key-trust" />
        {t("Trust")}
      </div>
    </div>
  );
}
