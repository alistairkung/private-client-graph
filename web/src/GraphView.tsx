import { useCallback, useEffect, useMemo } from "react";
import {
  Background,
  BaseEdge,
  Controls,
  ReactFlow,
  useReactFlow,
  useStore,
  type EdgeChange,
  type EdgeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toGraphView } from "./graph-view";
import type { CanonicalGraph } from "./types";

function RoutedEdge({
  id,
  data,
  label,
  markerEnd,
  style,
  labelStyle,
  labelBgStyle,
}: EdgeProps) {
  const route = data?.route as {
    points: { x: number; y: number }[];
    x: number;
    y: number;
  };
  const path = route.points
    .map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`)
    .join(" ");
  return (
    <BaseEdge
      id={id}
      path={path}
      label={label}
      labelX={route.x}
      labelY={route.y}
      markerEnd={markerEnd}
      style={style}
      labelStyle={labelStyle}
      labelBgStyle={labelBgStyle}
      interactionWidth={20}
    />
  );
}

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
}: {
  graph: CanonicalGraph;
  selected: number | null;
  onSelect: (index: number) => void;
}) {
  const view = useMemo(() => toGraphView(graph), [graph]);
  const selectEdge = useCallback(
    (changes: EdgeChange[]) => {
      const selection = changes.find(
        (change) => change.type === "select" && change.selected,
      );
      if (selection?.type === "select") onSelect(Number(selection.id));
    },
    [onSelect],
  );
  if (!graph.relationships.length)
    return (
      <div className="empty-graph">
        <h3>No relationships found</h3>
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
    labelStyle: {
      fill: selected === index ? "#92421b" : "#29423f",
      fontWeight: selected === index ? 700 : 500,
    },
    labelBgStyle: { fill: selected === index ? "#fff0cf" : "#fafbf7" },
  }));
  return (
    <div className="graph-canvas" aria-label="Relationship graph">
      <ReactFlow
        edgeTypes={edgeTypes}
        nodes={view.nodes}
        edges={edges}
        minZoom={0.25}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
        nodesFocusable={false}
        edgesReconnectable={false}
        deleteKeyCode={null}
        onEdgeClick={(_, edge) => onSelect(Number(edge.id))}
        onEdgesChange={selectEdge}
      >
        <FitGraph bounds={view.bounds} />
        <Background color="#cbd5cc" gap={22} size={1} />
        <Controls showInteractive={false} showFitView={false} />
      </ReactFlow>
    </div>
  );
}
