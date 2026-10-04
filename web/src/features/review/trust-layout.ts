import type { CanonicalGraph, RelationshipType } from "../../shared/canonical-graph";

import {
  NODE_WIDTH,
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  nodeBoundary,
  nodeRectangle,
  relationshipRoute,
  type Point,
  type Rectangle,
  type RelationshipRoute,
} from "./node-geometry";

const HORIZONTAL_GAP = 96;
const LEVEL_GAP = 150;
const MARGIN = 48;
type Relationship = CanonicalGraph["relationships"][number];

const relationshipKey = (relationship: Relationship) =>
  `${relationship.source}:${relationship.type}:${relationship.target}`;
const personPairKey = (relationship: Relationship) =>
  [relationship.source, relationship.target].sort().join(":");

function personLevels(graph: CanonicalGraph, personIds: Set<string>) {
  const parents = new Map<string, string[]>();
  graph.relationships
    .filter(relationship => relationship.type === "parent_of"
      && personIds.has(relationship.source) && personIds.has(relationship.target))
    .forEach(relationship => {
      parents.set(relationship.target, [...(parents.get(relationship.target) ?? []), relationship.source]);
    });
  const visiting = new Set<string>();
  const resolved = new Map<string, number>();
  const level = (id: string): number => {
    if (resolved.has(id)) return resolved.get(id)!;
    if (visiting.has(id)) return 0;
    visiting.add(id);
    const value = Math.max(0, ...(parents.get(id) ?? []).map(parent => level(parent) + 1));
    visiting.delete(id);
    resolved.set(id, value);
    return value;
  };
  personIds.forEach(level);
  const familyIds = new Set(graph.relationships
    .filter(relationship => relationship.type === "parent_of"
      || relationship.type === "spouse_of" || relationship.type === "sibling_of")
    .flatMap(relationship => [relationship.source, relationship.target]));
  const familyMaximum = Math.max(0, ...[...personIds]
    .filter(id => familyIds.has(id)).map(id => resolved.get(id)!));
  personIds.forEach(id => {
    if (!familyIds.has(id)) resolved.set(id, familyMaximum);
  });
  return resolved;
}

function crossesNode(
  start: Point,
  end: Point,
  center: Point,
  height: number,
) {
  const clearance = 10;
  return Array.from({ length: 19 }, (_, index) => (index + 1) / 20).some(progress => {
    const point = {
      x: start.x + (end.x - start.x) * progress,
      y: start.y + (end.y - start.y) * progress,
    };
    return point.x > center.x - NODE_WIDTH / 2 - clearance
      && point.x < center.x + NODE_WIDTH / 2 + clearance
      && point.y > center.y - height / 2 - clearance
      && point.y < center.y + height / 2 + clearance;
  });
}

function positionPeople(graph: CanonicalGraph) {
  const people = graph.entities.filter(entity => entity.type === "person");
  const levels = personLevels(graph, new Set(people.map(person => person.id)));
  const rows = new Map<number, typeof people>();
  people.sort((first, second) => first.id.localeCompare(second.id)).forEach(person => {
    const personLevel = levels.get(person.id)!;
    rows.set(personLevel, [...(rows.get(personLevel) ?? []), person]);
  });
  const rowWidth = (count: number) => count * NODE_WIDTH + Math.max(0, count - 1) * HORIZONTAL_GAP;
  const width = Math.max(420, ...[...rows.values()].map(row => rowWidth(row.length))) + MARGIN * 2;
  const positions = new Map<string, Point>();
  for (const [level, row] of [...rows].sort(([first], [second]) => first - second)) {
    const left = (width - rowWidth(row.length)) / 2 + NODE_WIDTH / 2;
    row.forEach((person, index) => positions.set(person.id, {
      x: left + index * (NODE_WIDTH + HORIZONTAL_GAP),
      y: MARGIN + PERSON_HEIGHT / 2 + level * LEVEL_GAP,
    }));
  }
  return { levels, positions, width };
}

function entityObstacles(graph: CanonicalGraph, positions: Map<string, Point>): Rectangle[] {
  return graph.entities.map(entity => nodeRectangle(
    positions.get(entity.id)!,
    entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
    8,
  ));
}

type RoutingContext = {
  graph: CanonicalGraph;
  labels: Record<RelationshipType, string>;
  positions: Map<string, Point>;
  trustId: string;
  center: Point;
  width: number;
  trustLanes: Map<number, number>;
  personGroups: Map<string, number[]>;
  obstacles: Rectangle[];
};

function routeTrustRelationship(
  edge: Relationship,
  index: number,
  context: RoutingContext,
) {
  const approach = {
    x: context.center.x + context.trustLanes.get(index)!,
    y: context.center.y - TRUST_HEIGHT / 2 - 30,
  };
  const personId = edge.source === context.trustId ? edge.target : edge.source;
  const person = context.positions.get(personId)!;
  const blocked = context.graph.entities.some(entity => entity.id !== personId
    && entity.id !== context.trustId
    && crossesNode(person, approach, context.positions.get(entity.id)!,
      entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT));
  let personToTrust: Point[];
  if (blocked) {
    const corridorX = person.x <= context.center.x ? MARGIN / 2 : context.width - MARGIN / 2;
    const exit = { x: corridorX, y: person.y + PERSON_HEIGHT / 2 + 28 };
    personToTrust = [
      nodeBoundary(person, exit, false),
      exit,
      { x: corridorX, y: approach.y },
      approach,
      nodeBoundary(context.center, approach, true),
    ];
  } else {
    personToTrust = [
      nodeBoundary(person, approach, false),
      approach,
      nodeBoundary(context.center, approach, true),
    ];
  }
  const points = edge.source === context.trustId ? personToTrust.reverse() : personToTrust;
  return relationshipRoute(points, context.labels[edge.type], {
    awayFrom: context.center,
    obstacles: context.obstacles,
  });
}

function routePersonRelationship(
  edge: Relationship,
  index: number,
  context: RoutingContext,
) {
  const source = context.positions.get(edge.source)!;
  const target = context.positions.get(edge.target)!;
  const group = context.personGroups.get(personPairKey(edge))!;
  let lane = (group.indexOf(index) - (group.length - 1) / 2) * 46;
  const blocked = context.graph.entities.some(entity => entity.id !== edge.source
    && entity.id !== edge.target
    && crossesNode(source, target, context.positions.get(entity.id)!,
      entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT));
  if (blocked && Math.abs(lane) < 80) lane = lane > 0 ? 80 : -80;
  let points: Point[];
  if (lane) {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const length = Math.hypot(dx, dy) || 1;
    const waypoint = {
      x: (source.x + target.x) / 2 - dy / length * lane,
      y: (source.y + target.y) / 2 + dx / length * lane,
    };
    points = [nodeBoundary(source, waypoint, false), waypoint,
      nodeBoundary(target, waypoint, false)];
  } else {
    points = [nodeBoundary(source, target, false), nodeBoundary(target, source, false)];
  }
  return relationshipRoute(points, context.labels[edge.type], { obstacles: context.obstacles });
}

function meaningfulBounds(
  graph: CanonicalGraph,
  positions: Map<string, Point>,
  routes: RelationshipRoute[],
) {
  const nodeBounds = graph.entities.map(entity => nodeRectangle(
    positions.get(entity.id)!,
    entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
  ));
  const xValues = [
    ...nodeBounds.flatMap(bounds => [bounds.left, bounds.right]),
    ...routes.flatMap(route => route.points.map(point => point.x)),
    ...routes.flatMap(route => [route.labelBounds.left, route.labelBounds.right]),
  ];
  const yValues = [
    ...nodeBounds.flatMap(bounds => [bounds.top, bounds.bottom]),
    ...routes.flatMap(route => route.points.map(point => point.y)),
    ...routes.flatMap(route => [route.labelBounds.top, route.labelBounds.bottom]),
  ];
  const padding = 24;
  const x = Math.min(...xValues) - padding;
  const y = Math.min(...yValues) - padding;
  return {
    x,
    y,
    width: Math.max(...xValues) - x + padding,
    height: Math.max(...yValues) - y + padding,
  };
}

// A single Trust is an anchor, not a new legal ordering of the other entities.
// Multiple-Trust positioning remains on the existing general graph layout.
export function centralTrustLayout(
  graph: CanonicalGraph,
  labels: Record<RelationshipType, string>,
) {
  const trusts = graph.entities.filter(entity => entity.type === "trust");
  if (trusts.length !== 1) return null;
  const { levels, positions, width } = positionPeople(graph);
  const maximumLevel = Math.max(0, ...levels.values());
  const center = {
    x: width / 2,
    y: MARGIN + PERSON_HEIGHT / 2 + maximumLevel * LEVEL_GAP + 190,
  };
  positions.set(trusts[0].id, center);
  const trustRelationships = graph.relationships
    .map((relationship, index) => ({ relationship, index }))
    .filter(({ relationship }) => relationship.source === trusts[0].id || relationship.target === trusts[0].id)
    .sort((first, second) => relationshipKey(first.relationship)
      .localeCompare(relationshipKey(second.relationship)));
  const trustLanes = new Map(trustRelationships.map(({ index }, lane) =>
    [index, (lane - (trustRelationships.length - 1) / 2) * 34]));
  const personGroups = new Map<string, number[]>();
  const orderedRelationships = graph.relationships.map((edge, index) => ({ edge, index }))
    .sort((first, second) => relationshipKey(first.edge).localeCompare(relationshipKey(second.edge)));
  orderedRelationships.forEach(({ edge, index }) => {
    if (edge.source === trusts[0].id || edge.target === trusts[0].id) return;
    const key = personPairKey(edge);
    personGroups.set(key, [...(personGroups.get(key) ?? []), index]);
  });
  const obstacles = entityObstacles(graph, positions);
  const routes: RelationshipRoute[] = [];
  const context: RoutingContext = {
    graph, labels, positions, trustId: trusts[0].id, center, width,
    trustLanes, personGroups, obstacles,
  };
  orderedRelationships.forEach(({ edge, index }) => {
    const route = edge.source === context.trustId || edge.target === context.trustId
      ? routeTrustRelationship(edge, index, context)
      : routePersonRelationship(edge, index, context);
    routes[index] = route;
    obstacles.push(route.labelBounds);
  });
  return {
    positions,
    routes,
    bounds: meaningfulBounds(graph, positions, routes),
  };
}
