import { expect, test } from "vitest";
import { toGraphView, locateEvidence } from "./graph-view";
import type { CanonicalGraph } from "../../shared/canonical-graph";

export const graph: CanonicalGraph = {
  entities: [
    { id: "a", name: "Alice", type: "person" },
    { id: "b", name: "Bob", type: "person" },
    { id: "t", name: "Trust", type: "trust" },
  ],
  relationships: [
    { source: "a", target: "b", type: "spouse_of", evidence_ids: ["e1", "e2"] },
    { source: "b", target: "t", type: "beneficiary_of", evidence_ids: ["e2"] },
  ],
  evidence: [
    {
      id: "e1",
      document: "source.txt",
      supporting_text: "Alice and Bob are spouses.",
    },
    {
      id: "e2",
      document: "source.txt",
      supporting_text: "Bob benefits from Trust.",
    },
  ],
};

const caseGraph: CanonicalGraph = {
  entities: [
    { id: "alice", name: "Alice Chen", type: "person" },
    { id: "bob", name: "Bob Chen", type: "person" },
    { id: "carol", name: "Carol Wong", type: "person" },
    { id: "david", name: "David Chen", type: "person" },
    { id: "trust", name: "Evergreen Family Trust", type: "trust" },
  ],
  relationships: [
    { source: "alice", target: "bob", type: "parent_of", evidence_ids: [] },
    { source: "alice", target: "trust", type: "settlor_of", evidence_ids: [] },
    { source: "alice", target: "david", type: "spouse_of", evidence_ids: [] },
    { source: "bob", target: "trust", type: "beneficiary_of", evidence_ids: [] },
    { source: "carol", target: "trust", type: "beneficiary_of", evidence_ids: [] },
    { source: "david", target: "bob", type: "parent_of", evidence_ids: [] },
  ],
  evidence: [],
};

function nodeBounds(view: ReturnType<typeof toGraphView>, id: string) {
  const node = view.nodes.find(candidate => candidate.id === id)!;
  return {
    left: node.position.x,
    top: node.position.y,
    right: node.position.x + Number(node.style!.width),
    bottom: node.position.y + Number(node.style!.height),
  };
}

function boxesOverlap(
  first: { left: number; top: number; right: number; bottom: number },
  second: { left: number; top: number; right: number; bottom: number },
) {
  return first.left < second.right && first.right > second.left
    && first.top < second.bottom && first.bottom > second.top;
}

function expectGeneralLayout(view: ReturnType<typeof toGraphView>) {
  const centers = view.nodes.map(node => ({
    x: node.position.x + Number(node.style!.width) / 2,
    y: node.position.y + Number(node.style!.height) / 2,
  }));
  expect(new Set(centers.map(center => center.x))).toHaveLength(1);
  expect(centers.map(center => center.y)).toEqual(
    [...centers.map(center => center.y)].sort((a, b) => a - b),
  );
}

test("presentation preserves canonical endpoints and shows direction only for directed edges", () => {
  const view = toGraphView(graph);
  expect(view.edges).toHaveLength(2);
  expect(view.edges[0]).toMatchObject({
    source: "a",
    target: "b",
    label: "Spouse of",
  });
  expect(view.edges[0].markerEnd).toBeUndefined();
  expect(view.edges[1]).toMatchObject({
    source: "b",
    target: "t",
    label: "Beneficiary of",
  });
  expect(view.edges[1].markerEnd).toBeDefined();
  expect(view.nodes.find((node) => node.id === "t")?.data.kind).toBe("trust");
  expect(
    new Set(view.nodes.map((node) => JSON.stringify(node.position))).size,
  ).toBe(3);
  expect(toGraphView(graph)).toEqual(view);
});

test("evidence location preserves exact text and reports a contract error for missing quotes", () => {
  expect(locateEvidence("Before. Exact quote. After.", "Exact quote.")).toEqual(
    { start: 8, end: 20 },
  );
  expect(locateEvidence("Same. Same.", "Same.")).toEqual({ start: 0, end: 5 });
  expect(() => locateEvidence("Actual text.", "actual text.")).toThrow(
    "source",
  );
  expect(() => locateEvidence("Actual text.", "")).toThrow("source");
});

test.each([
  ["parent_of", "Parent of", true],
  ["spouse_of", "Spouse of", false],
  ["sibling_of", "Sibling of", false],
  ["settlor_of", "Settlor of", true],
  ["trustee_of", "Trustee of", true],
  ["beneficiary_of", "Beneficiary of", true],
] as const)(
  "%s has readable presentation without changing direction",
  (type, label, directed) => {
    const view = toGraphView({
      ...graph,
      relationships: [{ ...graph.relationships[0], type }],
    });
    expect(view.edges[0].label).toBe(label);
    expect(!!view.edges[0].markerEnd).toBe(directed);
    expect(view.edges[0].source).toBe("a");
    expect(view.edges[0].target).toBe("b");
  },
);

test("presentation anchors the single Trust below people and preserves graph semantics", () => {
  const original = structuredClone(graph);
  const view = toGraphView(graph);
  const trust = view.nodes.find(node => node.id === "t")!;
  const people = view.nodes.filter(node => node.id !== "t");
  const personCenters = people.map(node => node.position.x + Number(node.style!.width) / 2);
  expect(trust.type).toBe("trust");
  expect(trust.position.x + Number(trust.style!.width) / 2)
    .toBe((Math.min(...personCenters) + Math.max(...personCenters)) / 2);
  expect(trust.position.y).toBeGreaterThan(Math.max(...view.nodes
    .filter(node => node.id !== "t")
    .map(node => node.position.y + Number(node.style!.height))));
  expect(view.nodes.filter(node => node.id !== "t").every(node => node.type !== "trust")).toBe(true);
  expect(view.edges.map(({ source, target, markerEnd }) => ({ source, target, directed: !!markerEnd })))
    .toEqual([{ source: "a", target: "b", directed: false }, { source: "b", target: "t", directed: true }]);
  expect(toGraphView(graph)).toEqual(view);
  expect(graph).toEqual(original);
});

test("single-Trust presentation keeps family claims local and Trust approaches separate", () => {
  const view = toGraphView(caseGraph);
  const routes = view.edges.map(edge => edge.data!.route as {
    points: { x: number; y: number }[];
  });
  const familyRoutes = caseGraph.relationships
    .map((relationship, index) => ({ relationship, route: routes[index] }))
    .filter(({ relationship }) => relationship.target !== "trust");
  for (const { relationship, route } of familyRoutes) {
    const source = nodeBounds(view, relationship.source);
    const target = nodeBounds(view, relationship.target);
    const corridor = {
      left: Math.min(source.left, target.left) - 32,
      top: Math.min(source.top, target.top) - 32,
      right: Math.max(source.right, target.right) + 32,
      bottom: Math.max(source.bottom, target.bottom) + 32,
    };
    expect(route.points.every(point =>
      point.x >= corridor.left && point.x <= corridor.right
      && point.y >= corridor.top && point.y <= corridor.bottom,
    )).toBe(true);
    expect(route.points.length).toBeLessThanOrEqual(4);
  }
  const trustEntries = caseGraph.relationships
    .map((relationship, index) => ({ relationship, route: routes[index] }))
    .filter(({ relationship }) => relationship.target === "trust")
    .map(({ route }) => route.points.at(-1));
  expect(new Set(trustEntries.map(point => JSON.stringify(point))).size).toBe(trustEntries.length);
  expect(toGraphView(caseGraph)).toEqual(view);
});

test("relationship label geometry clears every entity", () => {
  const view = toGraphView(caseGraph);
  for (const [index, edge] of view.edges.entries()) {
    const route = edge.data!.route as {
      labelBounds: { left: number; top: number; right: number; bottom: number };
      labelOffset: { x: number; y: number };
    };
    expect(Math.hypot(route.labelOffset.x, route.labelOffset.y)).toBeGreaterThanOrEqual(20);
    expect(Math.hypot(route.labelOffset.x, route.labelOffset.y)).toBeLessThanOrEqual(24);
    for (const entity of caseGraph.entities) {
      expect(boxesOverlap(route.labelBounds, nodeBounds(view, entity.id)),
        `${caseGraph.relationships[index].type} label overlaps ${entity.name}`).toBe(false);
    }
  }
  const beneficiary = view.edges.find(edge => edge.label === "Beneficiary of")!;
  const labelBounds = (beneficiary.data!.route as {
    labelBounds: { left: number; right: number };
  }).labelBounds;
  expect(labelBounds.right - labelBounds.left).toBeGreaterThanOrEqual(100);
  const labelBoxes = view.edges.map(edge => (edge.data!.route as {
    labelBounds: { left: number; top: number; right: number; bottom: number };
  }).labelBounds);
  labelBoxes.forEach((labelBox, index) => labelBoxes.slice(index + 1).forEach(other =>
    expect(boxesOverlap(labelBox, other)).toBe(false)));
});

test("Person relationships use separate lanes around intervening entities", () => {
  const laneGraph: CanonicalGraph = {
    entities: [
      { id: "a", name: "Alice", type: "person" },
      { id: "b", name: "Bob", type: "person" },
      { id: "c", name: "Carol", type: "person" },
      { id: "t", name: "Trust", type: "trust" },
    ],
    relationships: [
      { source: "a", target: "c", type: "spouse_of", evidence_ids: [] },
      { source: "a", target: "c", type: "sibling_of", evidence_ids: [] },
      { source: "b", target: "t", type: "beneficiary_of", evidence_ids: [] },
    ],
    evidence: [],
  };
  const view = toGraphView(laneGraph);
  const routes = view.edges.slice(0, 2).map(edge => edge.data!.route as {
    points: { x: number; y: number }[];
    labelBounds: { left: number; top: number; right: number; bottom: number };
  });
  expect(routes[0].points).not.toEqual(routes[1].points);
  expect(boxesOverlap(routes[0].labelBounds, routes[1].labelBounds)).toBe(false);
  const bob = nodeBounds(view, "b");
  for (const route of routes) {
    for (const [index, end] of route.points.slice(1).entries()) {
      const start = route.points[index];
      const samples = Array.from({ length: 21 }, (_, sample) => ({
        x: start.x + (end.x - start.x) * sample / 20,
        y: start.y + (end.y - start.y) * sample / 20,
      }));
      expect(samples.some(point => point.x > bob.left && point.x < bob.right
        && point.y > bob.top && point.y < bob.bottom)).toBe(false);
    }
    expect(route.points.every(point => point.x >= view.bounds.x
      && point.x <= view.bounds.x + view.bounds.width
      && point.y >= view.bounds.y
      && point.y <= view.bounds.y + view.bounds.height)).toBe(true);
    expect(route.labelBounds.left).toBeGreaterThanOrEqual(view.bounds.x);
    expect(route.labelBounds.right).toBeLessThanOrEqual(view.bounds.x + view.bounds.width);
    expect(route.labelBounds.top).toBeGreaterThanOrEqual(view.bounds.y);
    expect(route.labelBounds.bottom).toBeLessThanOrEqual(view.bounds.y + view.bounds.height);
  }
});

test("equivalent relationship order retains geometry for each semantic claim", () => {
  const original = toGraphView(caseGraph);
  const reordered = toGraphView({ ...caseGraph, relationships: [...caseGraph.relationships].reverse() });
  const geometry = (view: ReturnType<typeof toGraphView>) => new Map(view.edges.map(edge => [
    `${edge.source}:${edge.label}:${edge.target}`,
    edge.data!.route,
  ]));
  expect(geometry(reordered)).toEqual(geometry(original));
});

test("central Trust layout is independent of entity input order and has distinct node positions", () => {
  const view = toGraphView(graph);
  const reordered = toGraphView({ ...graph, entities: [...graph.entities].reverse() });
  for (const node of view.nodes) {
    expect(reordered.nodes.find(other => other.id === node.id)?.position).toEqual(node.position);
  }
  expect(new Set(view.nodes.map(node => JSON.stringify(node.position))).size).toBe(graph.entities.length);
});

test("graphs without a single Trust retain the general layout", () => {
  const people = { ...graph, entities: graph.entities.map(entity => ({ ...entity, type: "person" as const })) };
  const view = toGraphView(people);
  expect(view.nodes.every(node => node.type !== "trust")).toBe(true);
  expectGeneralLayout(view);
});

test("multiple Trusts remain triangles with routes meeting their visible boundary", () => {
  const multiple = { ...graph, entities: graph.entities.map(entity => entity.id === "b" ? { ...entity, type: "trust" as const } : entity) };
  const view = toGraphView(multiple);
  const trust = view.nodes.find(node => node.id === "t")!;
  expect(view.nodes.filter(node => node.type === "trust")).toHaveLength(2);
  expectGeneralLayout(view);
  const route = view.edges[1].data!.route as { points: { x: number; y: number }[] };
  const end = route.points.at(-1)!;
  // A directed arrow touches one of the triangle's three sides, not its interior.
  const x = (end.x - trust.position.x) / Number(trust.style!.width);
  const y = (end.y - trust.position.y) / Number(trust.style!.height);
  expect(Math.min(Math.abs(y - 1), Math.abs(x - y / 2 - 0.5), Math.abs(x + y / 2 - 0.5))).toBeLessThan(0.001);
  expect(toGraphView(multiple)).toEqual(view);
});

test("general fallback geometry is stable for equivalent input order", () => {
  const multiple: CanonicalGraph = {
    entities: [
      { id: "a", name: "Alice", type: "person" },
      { id: "b", name: "Bob", type: "person" },
      { id: "t", name: "First Trust", type: "trust" },
      { id: "u", name: "Second Trust", type: "trust" },
    ],
    relationships: [
      { source: "a", target: "t", type: "settlor_of", evidence_ids: [] },
      { source: "a", target: "u", type: "trustee_of", evidence_ids: [] },
      { source: "b", target: "t", type: "beneficiary_of", evidence_ids: [] },
      { source: "b", target: "u", type: "beneficiary_of", evidence_ids: [] },
    ],
    evidence: [],
  };
  const original = toGraphView(multiple);
  const reordered = toGraphView({
    ...multiple,
    entities: [...multiple.entities].reverse(),
    relationships: [...multiple.relationships].reverse(),
  });
  const positions = (view: ReturnType<typeof toGraphView>) => new Map(
    view.nodes.map(node => [node.id, node.position]),
  );
  const routes = (view: ReturnType<typeof toGraphView>) => new Map(
    view.edges.map(edge => [`${edge.source}:${edge.label}:${edge.target}`, edge.data!.route]),
  );
  expect(positions(reordered)).toEqual(positions(original));
  expect(routes(reordered)).toEqual(routes(original));
});
