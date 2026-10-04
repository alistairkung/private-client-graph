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

test("presentation preserves canonical endpoints without implying flow through Trust roles", () => {
  const view = toGraphView(graph);
  expect(view.edges).toHaveLength(2);
  expect(view.edges[0]).toMatchObject({
    source: "a",
    target: "b",
    label: "Spouse of",
  });
  expect(view.edges[0].markerEnd).toBeUndefined();
  expect(view.edges[0].className).toContain("relationship-family");
  expect(view.edges[1]).toMatchObject({
    source: "b",
    target: "t",
    label: "Beneficiary",
  });
  expect(view.edges[1].markerEnd).toBeUndefined();
  expect(view.edges[1].className).toContain("relationship-trust-role");
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
  ["settlor_of", "Settlor", false],
  ["trustee_of", "Trustee", false],
  ["beneficiary_of", "Beneficiary", false],
] as const)(
  "%s has readable presentation without changing direction",
  (type, label, directed) => {
    const target = ["settlor_of", "trustee_of", "beneficiary_of"].includes(type) ? "t" : "b";
    const view = toGraphView({
      ...graph,
      relationships: [{ ...graph.relationships[0], type, target }],
    });
    expect(view.edges[0].label).toBe(label);
    expect(!!view.edges[0].markerEnd).toBe(directed);
    expect(view.edges[0].source).toBe("a");
    expect(view.edges[0].target).toBe(target);
  },
);

test("single-Trust presentation places explicit roles around the anchor without changing the graph", () => {
  const roles: CanonicalGraph = {
    ...caseGraph,
    entities: [...caseGraph.entities, { id: "trustee", name: "Taylor", type: "person" }],
    relationships: [...caseGraph.relationships,
      { source: "trustee", target: "trust", type: "trustee_of", evidence_ids: [] }],
  };
  const original = structuredClone(roles);
  const view = toGraphView(roles);
  const trust = nodeBounds(view, "trust");
  expect(nodeBounds(view, "alice").bottom).toBeLessThan(trust.top);
  expect(nodeBounds(view, "bob").top).toBeGreaterThan(trust.bottom);
  expect(nodeBounds(view, "carol").top).toBeGreaterThan(trust.bottom);
  const trustee = nodeBounds(view, "trustee");
  expect((trustee.top + trustee.bottom) / 2).toBe((trust.top + trust.bottom) / 2);
  expect(trustee.left).toBeGreaterThan(trust.right);
  expect(view.nodes.filter(node => node.type === "trust").map(node => node.id)).toEqual(["trust"]);
  expect(view.nodes.map(node => node.id)).toEqual(roles.entities.map(entity => entity.id));
  expect(view.edges.map(edge => [edge.source, edge.target])).toEqual(
    roles.relationships.map(relationship => [relationship.source, relationship.target]),
  );
  expect(toGraphView(roles)).toEqual(view);
  expect(roles).toEqual(original);
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
  const beneficiary = view.edges.find(edge => edge.label === "Beneficiary")!;
  const labelBounds = (beneficiary.data!.route as {
    labelBounds: { left: number; right: number };
  }).labelBounds;
  expect(labelBounds.right - labelBounds.left).toBeGreaterThanOrEqual(80);
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

test("graphs without a Trust retain the general layout", () => {
  const people: CanonicalGraph = {
    ...graph,
    entities: graph.entities.map(entity => ({ ...entity, type: "person" as const })),
    relationships: [
      { source: "a", target: "b", type: "parent_of", evidence_ids: [] },
      { source: "b", target: "t", type: "parent_of", evidence_ids: [] },
    ],
  };
  const view = toGraphView(people);
  expect(view.nodes.every(node => node.type !== "trust")).toBe(true);
  expectGeneralLayout(view);
});

test("multiple Trusts keep canonical role connectors and triangle boundary routes in the general layout", () => {
  const multiple: CanonicalGraph = {
    entities: [graph.entities[0], graph.entities[2], { id: "u", name: "Other Trust", type: "trust" }],
    relationships: [
      { source: "a", target: "t", type: "settlor_of", evidence_ids: [] },
      { source: "a", target: "u", type: "beneficiary_of", evidence_ids: [] },
    ],
    evidence: [],
  };
  const original = structuredClone(multiple);
  const view = toGraphView(multiple);
  expect(view.nodes.filter(node => node.type === "trust")).toHaveLength(2);
  expect(view.nodes.filter(node => node.id === "a")).toHaveLength(1);
  expect(view.edges.map(edge => edge.label)).toEqual(["Settlor", "Beneficiary"]);
  expect(view.edges.every(edge => !edge.markerEnd)).toBe(true);
  for (const edge of view.edges) {
    const trust = view.nodes.find(node => node.id === edge.target)!;
    // Generic canonical topology leaves even a beneficiary above its target Trust.
    expect(nodeBounds(view, "a").bottom).toBeLessThan(trust.position.y);
    const route = edge.data!.route as { points: { x: number; y: number }[] };
    const end = route.points.at(-1)!;
    const x = (end.x - trust.position.x) / Number(trust.style!.width);
    const y = (end.y - trust.position.y) / Number(trust.style!.height);
    expect(Math.min(Math.abs(y - 1), Math.abs(x - y / 2 - 0.5), Math.abs(x + y / 2 - 0.5))).toBeLessThan(0.001);
  }
  expect(multiple).toEqual(original);
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

test("a multiple-role person appears once outside single-role groups with separately mapped connectors", () => {
  const multipleRoles: CanonicalGraph = {
    ...caseGraph,
    entities: [...caseGraph.entities, { id: "m", name: "Morgan", type: "person" }],
    relationships: [...caseGraph.relationships,
      { source: "m", target: "trust", type: "settlor_of", evidence_ids: ["settlement"] },
      { source: "m", target: "trust", type: "beneficiary_of", evidence_ids: ["benefit"] },
      { source: "m", target: "trust", type: "trustee_of", evidence_ids: ["appointment"] }],
    evidence: [
      { id: "settlement", document: "source", supporting_text: "Morgan settled the Trust." },
      { id: "benefit", document: "source", supporting_text: "Morgan is a beneficiary." },
      { id: "appointment", document: "source", supporting_text: "Morgan is a trustee." },
    ],
  };
  const view = toGraphView(multipleRoles);
  expect(view.nodes.filter(node => node.id === "m")).toHaveLength(1);
  const person = nodeBounds(view, "m");
  expect(person.right).toBeLessThan(nodeBounds(view, "alice").left);
  expect(person.right).toBeLessThan(nodeBounds(view, "bob").left);
  const roles = view.edges.filter(edge => edge.source === "m");
  expect(roles.map(edge => edge.label)).toEqual(["Settlor", "Beneficiary", "Trustee"]);
  expect(roles.map(edge => multipleRoles.relationships[Number(edge.id)].evidence_ids))
    .toEqual([["settlement"], ["benefit"], ["appointment"]]);
  expect(new Set(roles.map(edge => JSON.stringify(edge.data!.route))).size).toBe(3);
  expect(roles.every(edge => edge.target === "trust" && !edge.markerEnd)).toBe(true);
  const labels = roles.map(edge => (edge.data!.route as {
    labelBounds: { left: number; top: number; right: number; bottom: number };
  }).labelBounds);
  labels.forEach((label, index) => labels.slice(index + 1).forEach(other =>
    expect(boxesOverlap(label, other)).toBe(false)));

});

test("family-only relatives stay near connected role holders and disconnected families occupy a separate area", () => {
  const families: CanonicalGraph = {
    ...caseGraph,
    entities: [...caseGraph.entities,
      { id: "ann", name: "Ann", type: "person" },
      { id: "alex", name: "Alex", type: "person" },
      { id: "x", name: "Xavier", type: "person" },
      { id: "y", name: "Yvonne", type: "person" }],
    relationships: [...caseGraph.relationships,
      { source: "ann", target: "bob", type: "spouse_of", evidence_ids: [] },
      { source: "alex", target: "ann", type: "parent_of", evidence_ids: [] },
      { source: "x", target: "y", type: "parent_of", evidence_ids: [] }],
  };
  const original = structuredClone(families);
  const view = toGraphView(families);
  const bob = nodeBounds(view, "bob");
  const ann = nodeBounds(view, "ann");
  expect(ann.right).toBeLessThan(bob.left);
  expect(ann.top).toBe(bob.top);
  expect(nodeBounds(view, "david").top).toBe(nodeBounds(view, "alice").top);
  const connectedBottom = Math.max(...["alice", "bob", "carol", "david", "ann", "alex", "trust"]
    .map(id => nodeBounds(view, id).bottom));
  expect(nodeBounds(view, "x").top).toBeGreaterThan(connectedBottom);
  expect(nodeBounds(view, "y").top).toBeGreaterThan(connectedBottom);
  view.nodes.forEach((node, index) => view.nodes.slice(index + 1).forEach(other =>
    expect(boxesOverlap(nodeBounds(view, node.id), nodeBounds(view, other.id))).toBe(false)));
  expect(view.edges).toHaveLength(families.relationships.length);
  expect(families).toEqual(original);
});

test("family connectors do not pass through the Trust or unrelated people", () => {
  const view = toGraphView(caseGraph);
  for (const edge of view.edges.filter(edge => edge.className?.includes("relationship-family"))) {
    const points = (edge.data!.route as { points: { x: number; y: number }[] }).points;
    const obstacles = view.nodes.filter(node => node.id !== edge.source && node.id !== edge.target);
    for (let index = 1; index < points.length; index++) {
      const start = points[index - 1];
      const end = points[index];
      for (const node of obstacles) {
        const bounds = nodeBounds(view, node.id);
        const crosses = Array.from({ length: 101 }, (_, sample) => ({
          x: start.x + (end.x - start.x) * sample / 100,
          y: start.y + (end.y - start.y) * sample / 100,
        })).some(point => point.x > bounds.left && point.x < bounds.right
          && point.y > bounds.top && point.y < bounds.bottom);
        expect(crosses, `${edge.ariaLabel} crosses ${node.data.label}`).toBe(false);
      }
    }
  }
});
