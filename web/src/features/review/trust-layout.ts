import type { RelationshipPresentation } from "./relationship-presentation";

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
const LEVEL_GAP = 210;
const MARGIN = 48;
type Relationship = RelationshipPresentation["relationships"][number];

const relationshipKey = (relationship: Relationship) =>
  `${relationship.source}:${relationship.type}:${relationship.target}`;
const personPairKey = (relationship: Relationship) =>
  [relationship.source, relationship.target].sort().join(":");

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

function positionPeople(graph: RelationshipPresentation) {
  const people = graph.entities.filter(entity => entity.type === "person")
    .sort((first, second) => first.id.localeCompare(second.id));
  const settlors = people.filter(person => person.roles.length === 1 && person.roles[0] === "settlor");
  const beneficiaries = people.filter(person => person.roles.length === 1 && person.roles[0] === "beneficiary");
  const trustees = people.filter(person => person.roles.length === 1 && person.roles[0] === "trustee");
  const rowWidth = (count: number) => count * NODE_WIDTH + Math.max(0, count - 1) * HORIZONTAL_GAP;
  const width = Math.max(420, rowWidth(Math.max(settlors.length, beneficiaries.length))) + MARGIN * 2;
  const center = { x: width / 2, y: MARGIN + PERSON_HEIGHT / 2 + LEVEL_GAP };
  const positions = new Map<string, Point>();
  const placeRow = (row: typeof people, y: number) => row.forEach((person, index) =>
    positions.set(person.id, {
      x: center.x - rowWidth(row.length) / 2 + NODE_WIDTH / 2 + index * (NODE_WIDTH + HORIZONTAL_GAP),
      y,
    }));
  placeRow(settlors, center.y - LEVEL_GAP);
  placeRow(beneficiaries, center.y + LEVEL_GAP);
  trustees.forEach((person, index) => positions.set(person.id, {
    x: width + HORIZONTAL_GAP,
    y: center.y + index * LEVEL_GAP,
  }));
  people.filter(person => person.roles.length > 1).forEach((person, index) =>
    positions.set(person.id, { x: -HORIZONTAL_GAP, y: center.y + index * LEVEL_GAP }));
  placeFamilyContext(graph, people.map(person => person.id), positions, center);
  return { positions, width, center };
}

function placeFamilyContext(
  graph: RelationshipPresentation,
  people: string[],
  positions: Map<string, Point>,
  center: Point,
) {
  const neighbours = new Map(people.map(id => [id, [] as string[]]));
  graph.relationships.filter(relationship => relationship.kind === "family")
    .forEach(relationship => {
      neighbours.get(relationship.source)?.push(relationship.target);
      neighbours.get(relationship.target)?.push(relationship.source);
    });
  neighbours.forEach(ids => ids.sort());
  const contextX = Math.min(center.x - NODE_WIDTH / 2, ...[...positions.values()].map(point => point.x))
    - NODE_WIDTH - HORIZONTAL_GAP;
  const queue = people.filter(id => positions.has(id));
  const contextRows: number[] = [];
  // Breadth-first placement keeps direct relatives closest to their represented role holder.
  for (let index = 0; index < queue.length; index++) {
    const relative = positions.get(queue[index])!;
    for (const id of neighbours.get(queue[index]) ?? []) {
      if (positions.has(id)) continue;
      let y = relative.y;
      while (contextRows.some(row => Math.abs(row - y) < PERSON_HEIGHT + 40)) y += LEVEL_GAP;
      positions.set(id, { x: contextX, y });
      contextRows.push(y);
      queue.push(id);
    }
  }
  let disconnectedY = Math.max(center.y + TRUST_HEIGHT / 2,
    ...[...positions.values()].map(point => point.y + PERSON_HEIGHT / 2)) + LEVEL_GAP;
  for (const id of people) {
    if (positions.has(id)) continue;
    const group = [id];
    positions.set(id, { x: center.x, y: disconnectedY });
    for (let index = 0; index < group.length; index++) {
      for (const neighbour of neighbours.get(group[index]) ?? []) {
        if (positions.has(neighbour)) continue;
        positions.set(neighbour, { x: center.x + group.length * (NODE_WIDTH + HORIZONTAL_GAP), y: disconnectedY });
        group.push(neighbour);
      }
    }
    disconnectedY += LEVEL_GAP;
  }
}

function entityObstacles(graph: RelationshipPresentation, positions: Map<string, Point>): Rectangle[] {
  return graph.entities.map(entity => nodeRectangle(
    positions.get(entity.id)!,
    entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
    8,
  ));
}

type RoutingContext = {
  graph: RelationshipPresentation;
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
  const personId = edge.source === context.trustId ? edge.target : edge.source;
  const person = context.positions.get(personId)!;
  const lane = context.trustLanes.get(index)!;
  const approach = Math.abs(person.y - context.center.y) > PERSON_HEIGHT
    ? { x: context.center.x + lane,
        y: context.center.y + Math.sign(person.y - context.center.y) * (TRUST_HEIGHT / 2 + 30) }
    : { x: context.center.x + Math.sign(person.x - context.center.x) * (NODE_WIDTH / 2 + 30),
        y: context.center.y + lane };
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
  return relationshipRoute(points, edge.label, {
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
  const lane = (group.indexOf(index) - (group.length - 1) / 2) * 46;
  const obstacles = context.graph.entities.filter(entity => entity.id !== edge.source && entity.id !== edge.target);
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const length = Math.hypot(dx, dy) || 1;
  const routes = [lane, ...[80, 160, 240, 320].flatMap(offset => [offset + lane, -offset + lane])]
    .map(offset => {
      if (!offset) return [nodeBoundary(source, target, false), nodeBoundary(target, source, false)];
      const waypoint = {
        x: (source.x + target.x) / 2 - dy / length * offset,
        y: (source.y + target.y) / 2 + dx / length * offset,
      };
      return [nodeBoundary(source, waypoint, false), waypoint, nodeBoundary(target, waypoint, false)];
    });
  const points = routes.find(route => route.slice(1).every((end, segment) =>
    obstacles.every(entity => !crossesNode(route[segment], end, context.positions.get(entity.id)!,
      entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT)))) ?? routes[0];
  return relationshipRoute(points, edge.label, { obstacles: context.obstacles });
}

function meaningfulBounds(
  graph: RelationshipPresentation,
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

// Role positions are presentation preferences, not additional legal meaning.
// Multiple-Trust positioning remains on the existing general graph layout.
export function centralTrustLayout(
  graph: RelationshipPresentation,
) {
  const trusts = graph.entities.filter(entity => entity.type === "trust");
  if (trusts.length !== 1) return null;
  const { positions, width, center } = positionPeople(graph);
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
    graph, positions, trustId: trusts[0].id, center, width,
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
