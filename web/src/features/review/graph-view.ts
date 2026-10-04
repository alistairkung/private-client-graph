import {
  NODE_WIDTH,
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  nodeBoundary,
  nodeRectangle,
  relationshipRoute,
  type Rectangle,
  type RelationshipRoute,
} from "./node-geometry";
import { centralTrustLayout } from "./trust-layout";
import dagre from "@dagrejs/dagre";
import { MarkerType, Position, type Edge, type Node } from "@xyflow/react";
import type { CanonicalGraph, RelationshipType } from "../../shared/canonical-graph";

const labels: Record<RelationshipType, string> = {
  parent_of: "Parent of",
  spouse_of: "Spouse of",
  sibling_of: "Sibling of",
  settlor_of: "Settlor of",
  trustee_of: "Trustee of",
  beneficiary_of: "Beneficiary of",
};

const relationshipKey = (relationship: CanonicalGraph["relationships"][number]) =>
  `${relationship.source}:${relationship.type}:${relationship.target}`;

export function toGraphView(graph: CanonicalGraph): {
  nodes: Node[];
  edges: Edge[];
  bounds: { x: number; y: number; width: number; height: number };
} {
  const isTrust = (id: string) => graph.entities.some(entity => entity.id === id && entity.type === "trust");
  const nodeHeight = (id: string) => isTrust(id) ? TRUST_HEIGHT : PERSON_HEIGHT;
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
    layout.setNode(entity.id, { width: NODE_WIDTH, height: nodeHeight(entity.id) }),
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
  const anchored = centralTrustLayout(graph, labels);
  if (!anchored) {
    graph.relationships.forEach((edge, index) => {
      const route = layout.edge({ v: edge.source, w: edge.target, name: String(index) });
      if (isTrust(edge.source)) route.points[0] = nodeBoundary(layout.node(edge.source), route.points[1], true);
      if (isTrust(edge.target)) route.points[route.points.length - 1] = nodeBoundary(
        layout.node(edge.target), route.points[route.points.length - 2], true,
      );
    });
  }
  const labelObstacles: Rectangle[] = anchored ? [] : graph.entities.map(entity =>
    nodeRectangle(layout.node(entity.id), nodeHeight(entity.id), 8));
  const generalRoutes: RelationshipRoute[] = new Array(graph.relationships.length);
  const orderedRelationships = graph.relationships.map((edge, index) => ({ edge, index }))
    .sort((first, second) => relationshipKey(first.edge).localeCompare(relationshipKey(second.edge)));
  if (!anchored) orderedRelationships.forEach(({ edge, index }) => {
    const route = relationshipRoute(
      layout.edge({ v: edge.source, w: edge.target, name: String(index) }).points,
      labels[edge.type],
      { obstacles: labelObstacles },
    );
    labelObstacles.push(route.labelBounds);
    generalRoutes[index] = route;
  });
  return {
    bounds: anchored?.bounds ?? {
      x: 0,
      y: 0,
      width: layout.graph().width!,
      height: layout.graph().height!,
    },
    nodes: graph.entities.map((entity) => ({
      id: entity.id,
      type: isTrust(entity.id) ? "trust" : undefined,
      position: {
        x: (anchored?.positions.get(entity.id)?.x ?? layout.node(entity.id).x) - NODE_WIDTH / 2,
        y: (anchored?.positions.get(entity.id)?.y ?? layout.node(entity.id).y) - nodeHeight(entity.id) / 2,
      },
      data: { label: entity.name, kind: entity.type },
      className: `entity-${entity.type}`,
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      style: { width: NODE_WIDTH, height: nodeHeight(entity.id) },
    })),
    edges: graph.relationships.map((edge, index) => ({
      id: String(index),
      source: edge.source,
      target: edge.target,
      label: labels[edge.type],
      type: "routed",
      ariaRole: "button",
      data: {
        route: anchored?.routes[index] ?? generalRoutes[index],
      },
      markerEnd:
        edge.type === "spouse_of" || edge.type === "sibling_of"
          ? undefined
          : { type: MarkerType.ArrowClosed, color: "#607775", width: 18, height: 18 },
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
