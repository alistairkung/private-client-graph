import { NODE_WIDTH, TRUST_HEIGHT, type RelationshipRoute } from "./node-geometry";
import { useEffect, useMemo } from "react";
import {
  Handle,
  Position,
  type NodeProps,
  BaseEdge,
  EdgeLabelRenderer,
  Controls,
  ReactFlow,
  useReactFlow,
  useStore,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toGraphView } from "./graph-view";
import type { CanonicalGraph } from "../../shared/canonical-graph";

type ReviewEdge = Edge<{
  route: RelationshipRoute;
  description: string;
  connectorClass: string;
  onSelect: () => void;
}>;

function RoutedEdge({ id, data, label, markerEnd, style, selected }: EdgeProps<ReviewEdge>) {
  const { route, description, connectorClass, onSelect } = data!;
  const path = route.points
    .map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`)
    .join(" ");
  return <>
    <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} interactionWidth={20} />
    <EdgeLabelRenderer>
      <button
        type="button"
        className={`relationship-label nodrag nopan ${connectorClass}${selected ? " selected" : ""}`}
        data-edge-id={id}
        aria-label={description}
        aria-pressed={!!selected}
        onClick={onSelect}
        style={{
          transform: `translate(-50%, -50%) translate(${route.x}px, ${route.y}px)`,
          width: route.labelBounds.right - route.labelBounds.left,
        }}
      >{label}</button>
    </EdgeLabelRenderer>
  </>;
}

function TrustNode({ data }: NodeProps) {
  return <div className="trust-node" aria-label={`${data.label} · Trust`}>
    <svg viewBox={`0 0 ${NODE_WIDTH} ${TRUST_HEIGHT}`} role="img" aria-label="Triangular Trust node">
      <polygon points={`${NODE_WIDTH / 2},0 ${NODE_WIDTH},${TRUST_HEIGHT} 0,${TRUST_HEIGHT}`} />
    </svg>
    <span>{String(data.label)}</span>
    <Handle type="target" position={Position.Top} />
    <Handle type="source" position={Position.Bottom} />
  </div>;
}

const nodeTypes = { trust: TrustNode };
const edgeTypes = { routed: RoutedEdge };

function FitGraph({
  bounds,
}: {
  bounds: { x: number; y: number; width: number; height: number };
}) {
  const { fitBounds, viewportInitialized } = useReactFlow();
  const width = useStore((state) => state.width);
  const height = useStore((state) => state.height);
  useEffect(() => {
    if (viewportInitialized && width && height)
      void fitBounds(bounds, { padding: 0.08 });
  }, [viewportInitialized, width, height, bounds, fitBounds]);
  return null;
}

export function GraphView({
  graph,
  selected,
  onSelect,
  emptyTitle = "No relationships found",
}: {
  emptyTitle?: string;
  graph: CanonicalGraph;
  selected: number | null;
  onSelect: (index: number) => void;
}) {
  const view = useMemo(() => toGraphView(graph), [graph]);
  if (!graph.relationships.length)
    return (
      <div className="empty-graph">
        <h3>{emptyTitle}</h3>
        <p>
          The analysis produced no supported relationships. The source remains
          available for review.
        </p>
      </div>
    );
  const edges = view.edges.map((edge, index) => ({
    ...edge,
    selected: selected === index,
    style: {
      stroke: selected === index ? "#b15a27" : "#607775",
      strokeWidth: selected === index ? 3 : 1.5,
    },
    data: {
      ...edge.data,
      description: edge.ariaLabel,
      connectorClass: edge.className,
      onSelect: () => onSelect(index),
    },
  }));
  return (
    <div className="graph-canvas" aria-label="Relationship graph">
      <ReactFlow
        edgeTypes={edgeTypes}
        nodeTypes={nodeTypes}
        nodes={view.nodes}
        edges={edges}
        minZoom={0.25}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
        nodesFocusable={false}
        edgesReconnectable={false}
        edgesFocusable={false}
        deleteKeyCode={null}
        onEdgeClick={(_, edge) => onSelect(Number(edge.id))}
      >
        <FitGraph bounds={view.bounds} />
        <Controls showInteractive={false} showFitView={false} />
      </ReactFlow>
    </div>
  );
}
