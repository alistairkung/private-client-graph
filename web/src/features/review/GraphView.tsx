import { useLocale } from "../../shared/locale";
import { NODE_WIDTH, TRUST_HEIGHT, type RelationshipRoute } from "./node-geometry";
import { useEffect, useMemo, useRef } from "react";
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
  const { setCenter, getZoom } = useReactFlow();
  const canvasWidth = useStore(state => state.width);
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
        onFocus={event => {
          if (canvasWidth <= 450 && event.currentTarget.matches(":focus-visible")) void setCenter(route.x, route.y, { zoom: Math.max(1, getZoom()) });
        }}
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
 const {t}=useLocale();
  return <div className="trust-node" aria-label={`${data.label} · ${t("Trust")}`}>
    <svg viewBox={`0 0 ${NODE_WIDTH} ${TRUST_HEIGHT}`} role="img" aria-label={t("Triangular Trust node")}>
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
  graph,
  selected,
  bounds,
  selectedRoute,
}: {
  graph: CanonicalGraph;
  selected: number | null;
  bounds: { x: number; y: number; width: number; height: number };
  selectedRoute?: RelationshipRoute;
}) {
  const { fitBounds, setCenter, getZoom, viewportInitialized } = useReactFlow();
  const width = useStore((state) => state.width);
  const height = useStore((state) => state.height);
  const focusRoute = width <= 450 ? selectedRoute : undefined;
  const focusIndex = width <= 450 ? selected : null;
  const previous = useRef<{ graph: CanonicalGraph; width: number; height: number; focusIndex: number | null } | null>(null);
  useEffect(() => {
    if (!viewportInitialized || !width || !height) return;
    const last = previous.current;
    // Translated label geometry must not reset a reviewer's chosen pan/zoom.
    if (last?.graph === graph && last.width === width && last.height === height && last.focusIndex === focusIndex) return;
    previous.current = { graph, width, height, focusIndex };
    if (width <= 450) {
      void setCenter(focusRoute?.x ?? bounds.x + bounds.width / 2,
        focusRoute?.y ?? bounds.y + bounds.height / 2,
        { zoom: Math.max(1, getZoom()) });
    } else {
      void fitBounds(bounds, { padding: 0.08 });
    }
  }, [viewportInitialized, graph, width, height, bounds, focusRoute, focusIndex, fitBounds, setCenter, getZoom]);
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
  const { t, locale } = useLocale();
  const view = useMemo(() => toGraphView(graph, locale), [graph, locale]);
  if (!graph.relationships.length)
    return (
      <div className="empty-graph">
        <h3>{t(emptyTitle)}</h3>
        <p>
          {t("The analysis produced no supported relationships. The source remains available for review.")}
        </p>
      </div>
    );
  const edges = view.edges.map((edge, index) => ({
    ...edge,
    selected: selected === index,
    style: {
      stroke: selected === index ? "#773b46" : "#607775",
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
    <>
    <label className="graph-selector">{t("Find a relationship")}
      <select value={selected ?? ""} onChange={event => onSelect(Number(event.target.value))}>
        <option value="" disabled>{t("Choose a relationship")}</option>
        {view.edges.map((edge, index) => <option key={edge.id} value={index}>{edge.ariaLabel}</option>)}
      </select>
    </label>
    <p className="graph-navigation-hint">{t("Drag to pan. Use + and \u2212 to zoom. Choose a relationship above to bring it into view.")}</p>
    <div className="graph-canvas" aria-label={t("Relationship graph")}>
      <ReactFlow
        ariaLabelConfig={{"controls.zoomIn.ariaLabel":t("Zoom in"), "controls.zoomOut.ariaLabel":t("Zoom out")}}
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
        <FitGraph graph={graph} selected={selected} bounds={view.bounds} selectedRoute={selected === null ? undefined : view.edges[selected]?.data?.route as RelationshipRoute} />
        <Controls showInteractive={false} showFitView={false} />
      </ReactFlow>
    </div>
    </>
  );
}
