import type { RelationshipPresentation } from "./relationship-presentation";

import {
  NODE_WIDTH,
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  nodeBoundary,
  nodeFootprint,
  relationshipRoute,
  segmentCrossesBounds,
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

function crossesNode(start: Point, end: Point, center: Point, height: number) {
  return segmentCrossesBounds(start, end, nodeFootprint(center, height, 10));
}

function positionPeople(graph: RelationshipPresentation) {
  const people = graph.entities
    .filter((entity) => entity.type === "person")
    .sort((first, second) => first.id.localeCompare(second.id));
  const settlors = people.filter(
    (person) => person.roles.length === 1 && person.roles[0] === "settlor",
  );
  const beneficiaries = people.filter(
    (person) => person.roles.length === 1 && person.roles[0] === "beneficiary",
  );
  const trustees = people.filter(
    (person) => person.roles.length === 1 && person.roles[0] === "trustee",
  );
  const rowWidth = (count: number) =>
    count * NODE_WIDTH + Math.max(0, count - 1) * HORIZONTAL_GAP;
  const width =
    Math.max(420, rowWidth(Math.max(settlors.length, beneficiaries.length))) +
    MARGIN * 2;
  const center = { x: width / 2, y: MARGIN + PERSON_HEIGHT / 2 + LEVEL_GAP };
  const positions = new Map<string, Point>();
  const placeRow = (row: typeof people, y: number) =>
    row.forEach((person, index) =>
      positions.set(person.id, {
        x:
          center.x -
          rowWidth(row.length) / 2 +
          NODE_WIDTH / 2 +
          index * (NODE_WIDTH + HORIZONTAL_GAP),
        y,
      }),
    );
  placeRow(settlors, center.y - LEVEL_GAP);
  placeRow(beneficiaries, center.y + LEVEL_GAP);
  trustees.forEach((person, index) =>
    positions.set(person.id, {
      x: width + HORIZONTAL_GAP,
      y: center.y + index * LEVEL_GAP,
    }),
  );
  people
    .filter((person) => person.roles.length > 1)
    .forEach((person, index) =>
      positions.set(person.id, {
        x: -HORIZONTAL_GAP,
        y: center.y + index * LEVEL_GAP,
      }),
    );
  placeFamilyContext(
    graph,
    people.map((person) => person.id),
    positions,
    center,
  );
  return { positions, width, center };
}

function placeFamilyContext(
  graph: RelationshipPresentation,
  people: string[],
  positions: Map<string, Point>,
  center: Point,
) {
  const neighbours = new Map(people.map((id) => [id, [] as string[]]));
  graph.relationships
    .filter((relationship) => relationship.kind === "family")
    .forEach((relationship) => {
      neighbours.get(relationship.source)?.push(relationship.target);
      neighbours.get(relationship.target)?.push(relationship.source);
    });
  neighbours.forEach((ids) => ids.sort());
  const contextX =
    Math.min(
      center.x - NODE_WIDTH / 2,
      ...[...positions.values()].map((point) => point.x),
    ) -
    NODE_WIDTH -
    HORIZONTAL_GAP;
  const queue = people.filter((id) => positions.has(id));
  const contextRows: number[] = [];
  // Breadth-first placement keeps direct relatives closest to their represented role holder.
  for (let index = 0; index < queue.length; index++) {
    const relative = positions.get(queue[index])!;
    for (const id of neighbours.get(queue[index]) ?? []) {
      if (positions.has(id)) continue;
      let y = relative.y;
      while (contextRows.some((row) => Math.abs(row - y) < PERSON_HEIGHT + 40))
        y += LEVEL_GAP;
      positions.set(id, { x: contextX, y });
      contextRows.push(y);
      queue.push(id);
    }
  }
  let disconnectedY =
    Math.max(
      center.y + TRUST_HEIGHT / 2,
      ...[...positions.values()].map((point) => point.y + PERSON_HEIGHT / 2),
    ) + LEVEL_GAP;
  for (const id of people) {
    if (positions.has(id)) continue;
    const group = [id];
    positions.set(id, { x: center.x, y: disconnectedY });
    for (let index = 0; index < group.length; index++) {
      for (const neighbour of neighbours.get(group[index]) ?? []) {
        if (positions.has(neighbour)) continue;
        positions.set(neighbour, {
          x: center.x + group.length * (NODE_WIDTH + HORIZONTAL_GAP),
          y: disconnectedY,
        });
        group.push(neighbour);
      }
    }
    disconnectedY += LEVEL_GAP;
  }
}

function entityObstacles(
  graph: RelationshipPresentation,
  positions: Map<string, Point>,
): Rectangle[] {
  return graph.entities.map((entity) =>
    nodeFootprint(
      positions.get(entity.id)!,
      entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
      8,
    ),
  );
}

type RoutingContext = {
  graph: RelationshipPresentation;
  positions: Map<string, Point>;
  trustId: string;
  center: Point;
  trustApproaches: Map<number, Point>;
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
  const approach = context.trustApproaches.get(index)!;
  const obstacles = context.graph.entities.filter(
    (entity) => entity.id !== personId && entity.id !== context.trustId,
  );
  const trustBoundary = nodeBoundary(context.center, approach, true);
  const direct = [
    nodeBoundary(person, approach, false),
    approach,
    trustBoundary,
  ];
  const corridorXs = [
    (person.x + approach.x) / 2,
    ...obstacles.flatMap((entity) => {
      const bounds = nodeFootprint(
        context.positions.get(entity.id)!,
        entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
        24,
      );
      return [bounds.left, bounds.right];
    }),
  ]
    .filter((x) => x !== person.x)
    .sort(
      (first, second) =>
        Math.abs(first - person.x) - Math.abs(second - person.x) ||
        first - second,
    );
  const routes = [
    direct,
    ...corridorXs.map((x) => {
      const exit = { x, y: person.y };
      return [
        nodeBoundary(person, exit, false),
        exit,
        { x, y: approach.y },
        approach,
        trustBoundary,
      ];
    }),
  ];
  const caption = nodeFootprint(context.center, TRUST_HEIGHT, 4);
  caption.top = context.center.y + TRUST_HEIGHT / 2 + 4;
  const personToTrust =
    routes.find((route) =>
      route
        .slice(1)
        .every(
          (end, segment) =>
            !segmentCrossesBounds(route[segment], end, caption) &&
            obstacles.every(
              (entity) =>
                !crossesNode(
                  route[segment],
                  end,
                  context.positions.get(entity.id)!,
                  entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
                ),
            ),
        ),
    ) ?? direct;
  const points =
    edge.source === context.trustId ? personToTrust.reverse() : personToTrust;
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
  const orientation = edge.source < edge.target ? 1 : -1;
  const lane =
    (group.indexOf(index) - (group.length - 1) / 2) * 58 * orientation;
  const obstacles = context.graph.entities.filter(
    (entity) => entity.id !== edge.source && entity.id !== edge.target,
  );
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const length = Math.hypot(dx, dy) || 1;
  const routes = [
    lane,
    ...[80, 160, 240, 320].flatMap((offset) => [
      offset * (Math.sign(lane) || orientation) + lane,
      -offset * (Math.sign(lane) || orientation) + lane,
    ]),
  ].map((offset) => {
    if (!offset)
      return [
        nodeBoundary(source, target, false),
        nodeBoundary(target, source, false),
      ];
    const waypoint = {
      x: (source.x + target.x) / 2 - (dy / length) * offset,
      y: (source.y + target.y) / 2 + (dx / length) * offset,
    };
    return [
      nodeBoundary(source, waypoint, false),
      waypoint,
      nodeBoundary(target, waypoint, false),
    ];
  });
  const points =
    routes.find((route) =>
      route
        .slice(1)
        .every((end, segment) =>
          obstacles.every(
            (entity) =>
              !crossesNode(
                route[segment],
                end,
                context.positions.get(entity.id)!,
                entity.type === "trust" ? TRUST_HEIGHT : PERSON_HEIGHT,
              ),
          ),
        ),
    ) ?? routes[0];
  return relationshipRoute(points, edge.label, {
    obstacles: context.obstacles,
  });
}

// Role positions are presentation preferences, not additional legal meaning.
// Multiple-Trust positioning remains on the existing general graph layout.
export function centralTrustLayout(graph: RelationshipPresentation) {
  const trusts = graph.entities.filter((entity) => entity.type === "trust");
  if (trusts.length !== 1) return null;
  const { positions, center } = positionPeople(graph);
  positions.set(trusts[0].id, center);
  const trustRelationships = graph.relationships
    .map((relationship, index) => ({ relationship, index }))
    .filter(
      ({ relationship }) =>
        relationship.source === trusts[0].id ||
        relationship.target === trusts[0].id,
    )
    .sort((first, second) =>
      relationshipKey(first.relationship).localeCompare(
        relationshipKey(second.relationship),
      ),
    );
  const trustApproaches = new Map<number, Point>();
  const sideGroups = new Map<string, typeof trustRelationships>();
  trustRelationships.forEach((item) => {
    const personId =
      item.relationship.source === trusts[0].id
        ? item.relationship.target
        : item.relationship.source;
    const person = graph.entities.find((entity) => entity.id === personId)!;
    const side =
      person.roles.length > 1
        ? "left"
        : person.roles[0] === "settlor"
          ? "top"
          : person.roles[0] === "beneficiary"
            ? "bottom"
            : "right";
    sideGroups.set(side, [...(sideGroups.get(side) ?? []), item]);
  });
  sideGroups.forEach((group, side) =>
    group.forEach(({ index }, lane) => {
      const vertical = side === "top" || side === "bottom";
      const span = (vertical ? NODE_WIDTH : TRUST_HEIGHT) * 0.65;
      const offset =
        (lane - (group.length - 1) / 2) *
        Math.min(34, span / Math.max(1, group.length - 1));
      if (side === "bottom") {
        const edge = graph.relationships[index];
        const personId =
          edge.source === trusts[0].id ? edge.target : edge.source;
        const person = positions.get(personId)!;
        const direction =
          person.x < center.x ? -1 : person.x > center.x ? 1 : -1;
        // Enter at a lower side of the triangle; the caption is a real obstacle below it.
        trustApproaches.set(index, {
          x:
            center.x +
            direction * (NODE_WIDTH / 2 + 32 + Math.floor(lane / 2) * 22),
          y: center.y + TRUST_HEIGHT / 2 - 10 - (lane % 2) * 12,
        });
        return;
      }
      trustApproaches.set(
        index,
        vertical
          ? {
              x: center.x + offset,
              y: center.y + (side === "top" ? -1 : 1) * (TRUST_HEIGHT / 2 + 30),
            }
          : {
              x: center.x + (side === "left" ? -1 : 1) * (NODE_WIDTH / 2 + 30),
              y: center.y + offset,
            },
      );
    }),
  );
  const personGroups = new Map<string, number[]>();
  const orderedRelationships = graph.relationships
    .map((edge, index) => ({ edge, index }))
    .sort((first, second) =>
      relationshipKey(first.edge).localeCompare(relationshipKey(second.edge)),
    );
  orderedRelationships.forEach(({ edge, index }) => {
    if (edge.source === trusts[0].id || edge.target === trusts[0].id) return;
    const key = personPairKey(edge);
    personGroups.set(key, [...(personGroups.get(key) ?? []), index]);
  });
  const obstacles = entityObstacles(graph, positions);
  const routes: RelationshipRoute[] = [];
  const context: RoutingContext = {
    graph,
    positions,
    trustId: trusts[0].id,
    center,
    trustApproaches,
    personGroups,
    obstacles,
  };
  orderedRelationships.forEach(({ edge, index }) => {
    const route =
      edge.source === context.trustId || edge.target === context.trustId
        ? routeTrustRelationship(edge, index, context)
        : routePersonRelationship(edge, index, context);
    routes[index] = route;
    obstacles.push(route.labelBounds);
  });
  return {
    positions,
    routes,
  };
}
