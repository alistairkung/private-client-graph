import dagre from "@dagrejs/dagre";
import { MarkerType, Position, type Edge, type Node } from "@xyflow/react";
import type { CanonicalGraph, RelationshipType } from "./types";

const labels: Record<RelationshipType, string> = {
  parent_of: "Parent of",
  spouse_of: "Spouse of",
  sibling_of: "Sibling of",
  settlor_of: "Settlor of",
  trustee_of: "Trustee of",
  beneficiary_of: "Beneficiary of",
};

export function toGraphView(graph: CanonicalGraph): {
  nodes: Node[];
  edges: Edge[];
  bounds: { x: number; y: number; width: number; height: number };
} {
  const layout = new dagre.graphlib.Graph({ multigraph: true });
  layout.setGraph({
    rankdir: "TB",
    nodesep: 35,
    ranksep: 35,
    marginx: 30,
    marginy: 30,
  });
  layout.setDefaultEdgeLabel(() => ({}));
  graph.entities.forEach((entity) =>
    layout.setNode(entity.id, { width: 170, height: 56 }),
  );
  graph.relationships.forEach((edge, index) =>
    layout.setEdge(
      edge.source,
      edge.target,
      { width: 105, height: 24 },
      String(index),
    ),
  );
  dagre.layout(layout);
  return {
    bounds: {
      x: 0,
      y: 0,
      width: layout.graph().width!,
      height: layout.graph().height!,
    },
    nodes: graph.entities.map((entity) => ({
      id: entity.id,
      position: {
        x: layout.node(entity.id).x - 85,
        y: layout.node(entity.id).y - 28,
      },
      data: { label: entity.name, kind: entity.type },
      className: `entity-${entity.type}`,
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      style: { width: 170, height: 56 },
    })),
    edges: graph.relationships.map((edge, index) => ({
      id: String(index),
      source: edge.source,
      target: edge.target,
      label: labels[edge.type],
      type: "routed",
      ariaRole: "button",
      data: {
        route: layout.edge({
          v: edge.source,
          w: edge.target,
          name: String(index),
        }),
      },
      markerEnd:
        edge.type === "spouse_of" || edge.type === "sibling_of"
          ? undefined
          : { type: MarkerType.ArrowClosed, color: "#607775" },
      ariaLabel: `${graph.entities.find((entity) => entity.id === edge.source)?.name} — ${labels[edge.type]} — ${graph.entities.find((entity) => entity.id === edge.target)?.name}`,
    })),
  };
}

export function locateEvidence(
  source: string,
  quote: string,
): { start: number; end: number } {
  const start = source.indexOf(quote);
  if (!quote || start < 0)
    throw new Error(
      "The selected evidence could not be located in the source. Reload the case to restore the review.",
    );
  return { start, end: start + quote.length };
}
