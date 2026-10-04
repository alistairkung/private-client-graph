import type { CanonicalGraph, RelationshipType } from "../../shared/canonical-graph";

import {
  NODE_WIDTH,
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  nodeBoundary,
  relationshipRoute,
  type Point,
  type Rectangle,
  type RelationshipRoute,
} from "./node-geometry";

const HORIZONTAL_GAP = 96;
const LEVEL_GAP = 150;
const MARGIN = 48;

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
  const clearance = 8;
  return graph.entities.map(entity => {
    const center = positions.get(entity.id)!;
    const height = entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT;
    return {
      left: center.x - NODE_WIDTH / 2 - clearance,
      top: center.y - height / 2 - clearance,
      right: center.x + NODE_WIDTH / 2 + clearance,
      bottom: center.y + height / 2 + clearance,
    };
  });
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
    .sort((first, second) =>
      `${first.relationship.source}:${first.relationship.type}:${first.relationship.target}`
        .localeCompare(`${second.relationship.source}:${second.relationship.type}:${second.relationship.target}`));
  const trustLanes = new Map(trustRelationships.map(({ index }, lane) =>
    [index, (lane - (trustRelationships.length - 1) / 2) * 34]));
  const personGroups = new Map<string, number[]>();
  graph.relationships.forEach((edge, index) => {
    if (edge.source === trusts[0].id || edge.target === trusts[0].id) return;
    const key = [edge.source, edge.target].sort().join(":");
    personGroups.set(key, [...(personGroups.get(key) ?? []), index]);
  });
  const obstacles = entityObstacles(graph, positions);
  const routes: RelationshipRoute[] = [];
  graph.relationships.forEach((edge, index) => {
    const source = positions.get(edge.source)!;
    const target = positions.get(edge.target)!;
    let route: RelationshipRoute;
    if (edge.source === trusts[0].id || edge.target === trusts[0].id) {
      const approach = {
        x: center.x + trustLanes.get(index)!,
        y: center.y - TRUST_HEIGHT / 2 - 30,
      };
      const personId = edge.source === trusts[0].id ? edge.target : edge.source;
      const person = positions.get(personId)!;
      const blocked = graph.entities.some(entity => entity.id !== personId
        && entity.id !== trusts[0].id
        && crossesNode(person, approach, positions.get(entity.id)!,
          entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT));
      let personToTrust: Point[];
      if (blocked) {
        const corridorX = person.x <= center.x ? MARGIN / 2 : width - MARGIN / 2;
        const exit = { x: corridorX, y: person.y + PERSON_HEIGHT / 2 + 28 };
        personToTrust = [
          nodeBoundary(person, exit, false),
          exit,
          { x: corridorX, y: approach.y },
          approach,
          nodeBoundary(center, approach, true),
        ];
      } else {
        personToTrust = [
          nodeBoundary(person, approach, false),
          approach,
          nodeBoundary(center, approach, true),
        ];
      }
      const points = edge.source === trusts[0].id ? personToTrust.reverse() : personToTrust;
      route = relationshipRoute(points, labels[edge.type], { awayFrom: center, obstacles });
    } else {
      const group = personGroups.get([edge.source, edge.target].sort().join(":"))!;
      let lane = (group.indexOf(index) - (group.length - 1) / 2) * 46;
      const blocked = graph.entities.some(entity => entity.id !== edge.source
        && entity.id !== edge.target
        && crossesNode(source, target, positions.get(entity.id)!,
          entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT));
      if (blocked && Math.abs(lane) < 80) lane = (index % 2 ? 1 : -1) * 80;
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
      route = relationshipRoute(points, labels[edge.type], { obstacles });
    }
    routes.push(route);
    obstacles.push(route.labelBounds);
  });
  return {
    positions,
    routes,
    bounds: { x: 0, y: 0, width, height: center.y + TRUST_HEIGHT / 2 + MARGIN },
  };
}
