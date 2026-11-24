import dagre from "@dagrejs/dagre";
import { Position, type Edge, type Node } from "@xyflow/react";
import type { Graph } from "../../shared/contracts";
import type { Translate } from "../../shared/locale";
import { relationshipStatement } from "./presentation";
import { presentRelationships } from "./relationship-presentation";
import { centralTrustLayout } from "./trust-layout";
import {
  NODE_WIDTH,
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  nodeBoundary,
  nodeFootprint,
  relationshipRoute,
  type Point,
  type RelationshipRoute,
} from "./node-geometry";

const COMPARISON_DETACHED_GAP = 110;

export interface DrawingBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}
export interface GraphDrawingModel {
  nodes: Node[];
  edges: Edge[];
  bounds: DrawingBounds;
}

export function alignComparisonEntities(
  reference: Graph,
  candidate: Graph,
  referenceModel: GraphDrawingModel,
  candidateModel: GraphDrawingModel,
): Readonly<Record<string, Point>> | undefined {
  const referenceEntities = new Map<string, (typeof reference.entities)[number]>();
  for (const entity of reference.entities) {
    if (referenceEntities.has(entity.name)) return undefined;
    referenceEntities.set(entity.name, entity);
  }
  const candidateEntities = new Map<string, (typeof candidate.entities)[number]>();
  for (const entity of candidate.entities) {
    if (candidateEntities.has(entity.name)) return undefined;
    candidateEntities.set(entity.name, entity);
  }
  const referenceNodes = new Map(referenceModel.nodes.map((node) => [node.id, node]));
  const candidateNodes = new Map(candidateModel.nodes.map((node) => [node.id, node]));
  const candidateById = new Map(candidate.entities.map((entity) => [entity.id, entity]));
  const height = (type: string) => type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT;
  const referenceEndpoints = new Set(reference.relationships.flatMap(({ source, target }) => [source, target]));
  const candidateEndpoints = new Set(candidate.relationships.flatMap(({ source, target }) => [source, target]));
  const aligned = new Map<string, Point>();
  const commonNames = new Set<string>();
  for (const entity of candidate.entities) {
    const match = referenceEntities.get(entity.name);
    if (!match || match.type !== entity.type ||
      !referenceEndpoints.has(match.id) || !candidateEndpoints.has(entity.id)) continue;
    const position = referenceNodes.get(match.id)?.position;
    if (!position) continue;
    aligned.set(entity.id, {
      x: position.x + NODE_WIDTH / 2,
      y: position.y + height(entity.type) / 2,
    });
    commonNames.add(entity.name);
  }
  if (aligned.size < 2) return undefined;

  for (const entity of candidate.entities) {
    if (commonNames.has(entity.name)) continue;
    const node = candidateNodes.get(entity.id);
    if (!node) continue;
    const candidateCenter = {
      x: node.position.x + NODE_WIDTH / 2,
      y: node.position.y + height(entity.type) / 2,
    };
    for (const alignedId of aligned.keys()) {
      const alignedEntity = candidateById.get(alignedId)!;
      const position = aligned.get(alignedId)!;
      const overlaps =
        Math.abs(candidateCenter.x - position.x) < NODE_WIDTH + 24 &&
        Math.abs(candidateCenter.y - position.y) <
          (height(entity.type) + height(alignedEntity.type)) / 2 + 24;
      if (overlaps) return undefined;
    }
  }
  return Object.fromEntries(aligned);
}

function completeBounds(
  graph: Graph,
  positions: Map<string, Point>,
  routes: RelationshipRoute[],
): DrawingBounds {
  const boxes = [
    ...graph.entities.map((entity) =>
      nodeFootprint(
        positions.get(entity.id)!,
        entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
      ),
    ),
    ...routes.map((route) => route.labelBounds),
    ...routes.flatMap((route) =>
      route.points.map((point) => ({
        left: point.x,
        right: point.x,
        top: point.y,
        bottom: point.y,
      })),
    ),
  ];
  if (!boxes.length) return { x: 0, y: 0, width: 1, height: 1 };
  const x = Math.min(...boxes.map((box) => box.left)) - 24;
  const y = Math.min(...boxes.map((box) => box.top)) - 24;
  return {
    x,
    y,
    width: Math.max(...boxes.map((box) => box.right)) - x + 24,
    height: Math.max(...boxes.map((box) => box.bottom)) - y + 24,
  };
}

export function graphDrawing(
  graph: Graph,
  t: Translate,
  alignedPositions?: Readonly<Record<string, Point>>,
  outcomes?: ReadonlyArray<string | undefined>,
): GraphDrawingModel {
  const presentation = presentRelationships(graph, t);
  const comparisonLabels: Record<string, string> = {
    correct: "✓ Correct",
    missing: "− Missing",
    unsupported: "+ Unsupported",
    expected: "Expected",
  };
  const relationships = presentation.relationships.map((edge, index) => {
    const outcome = outcomes?.[index];
    const status = outcome ? comparisonLabels[outcome] : undefined;
    return {
      ...edge,
      label: status ? `${status} · ${edge.label}` : edge.label,
      outcome,
    };
  });
  const layout = new dagre.graphlib.Graph({ multigraph: true });
  layout.setGraph({
    rankdir: "TB",
    nodesep: 70,
    ranksep: 80,
    marginx: 32,
    marginy: 32,
  });
  layout.setDefaultEdgeLabel(() => ({}));
  const height = (id: string) =>
    graph.entities.find((entity) => entity.id === id)?.type === "trust"
      ? TRUST_HEIGHT
      : PERSON_HEIGHT;
  const orderedEdges = relationships
    .map((edge, index) => ({ edge, index }))
    .sort((a, b) =>
      (a.edge.source + ":" + a.edge.type + ":" + a.edge.target).localeCompare(
        b.edge.source + ":" + b.edge.type + ":" + b.edge.target,
      ),
    );
  [...graph.entities]
    .sort((a, b) => a.id.localeCompare(b.id))
    .forEach((entity) =>
      layout.setNode(entity.id, {
        width: NODE_WIDTH,
        height: height(entity.id),
      }),
    );
  orderedEdges.forEach(({ edge, index }) =>
    layout.setEdge(
      edge.source,
      edge.target,
      { width: 120, height: 32 },
      String(index),
    ),
  );
  dagre.layout(layout);
  const anchored = centralTrustLayout(
    presentation,
    outcomes ? COMPARISON_DETACHED_GAP : undefined,
  );
  const layoutPositions =
    anchored?.positions ??
    new Map(
      graph.entities.map((entity) => [
        entity.id,
        { x: layout.node(entity.id).x, y: layout.node(entity.id).y },
      ]),
    );
  const positions = new Map(
    graph.entities.map((entity) => [
      entity.id,
      alignedPositions?.[entity.id] ?? layoutPositions.get(entity.id)!,
    ]),
  );
  const paths: Point[][] = anchored?.routes ?? [];
  if (!anchored) {
    orderedEdges.forEach(({ edge, index }) => {
      const points: Point[] = layout
        .edge({ v: edge.source, w: edge.target, name: String(index) })
        .points.map((point: Point) => ({ ...point }));
      points[0] = nodeBoundary(
        positions.get(edge.source)!,
        points[1],
        height(edge.source) === TRUST_HEIGHT,
      );
      points[points.length - 1] = nodeBoundary(
        positions.get(edge.target)!,
        points[points.length - 2],
        height(edge.target) === TRUST_HEIGHT,
      );
      paths[index] = points;
    });
  }
  // Place labels only after every claim's path exists. A later route must not disappear beneath an earlier label.
  const obstacles = graph.entities.map((entity) =>
    nodeFootprint(positions.get(entity.id)!, height(entity.id), 8),
  );
  const routes: RelationshipRoute[] = [];
  orderedEdges.forEach(({ edge, index }) => {
    const route = relationshipRoute(paths[index], edge.label, {
      obstacles,
      routes: paths,
    });
    routes[index] = route;
    obstacles.push(route.labelBounds);
  });
  return {
    bounds: completeBounds(graph, positions, routes),
    nodes: graph.entities.map((entity) => ({
      id: entity.id,
      type: "entity",
      // Fixed diagram footprints also define XYFlow's endpoint contract. Controlled
      // visual updates must not discard DOM-measured handle bounds between pointer events.
      width: NODE_WIDTH,
      height: height(entity.id),
      handles: [
        {
          type: "target",
          position: Position.Top,
          x: NODE_WIDTH / 2,
          y: 0,
          width: 1,
          height: 1,
        },
        {
          type: "source",
          position: Position.Bottom,
          x: NODE_WIDTH / 2,
          y: height(entity.id),
          width: 1,
          height: 1,
        },
      ],
      position: {
        x: positions.get(entity.id)!.x - NODE_WIDTH / 2,
        y: positions.get(entity.id)!.y - height(entity.id) / 2,
      },
      data: {
        ...entity,
        kindLabel: t(entity.type === "trust" ? "Trust" : "Person"),
      },
      ariaLabel: entity.name,
      draggable: false,
      style: { width: NODE_WIDTH, height: height(entity.id) },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    })),
    edges: relationships.map((edge, index) => ({
      id: String(index),
      source: edge.source,
      target: edge.target,
      type: "relationship",
      label: edge.label,
      ariaLabel: relationshipStatement(graph, graph.relationships[index], t),
      data: {
        route: routes[index],
        parent: edge.arrow,
        trust: edge.kind === "trust-role",
        comparison: Boolean(outcomes),
        outcome: edge.outcome,
        statement: relationshipStatement(graph, graph.relationships[index], t),
      },
      interactionWidth: 28,
    })),
  };
}
