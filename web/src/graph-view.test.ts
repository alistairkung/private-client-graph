import { expect, test } from "vitest";
import { toGraphView, locateEvidence } from "./graph-view";
import type { CanonicalGraph } from "./types";

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

test("presentation centers the single Trust and preserves graph semantics", () => {
  const original = structuredClone(graph);
  const view = toGraphView(graph);
  const trust = view.nodes.find(node => node.id === "t")!;
  expect(trust.type).toBe("trust");
  expect(trust.position.x + Number(trust.style!.width) / 2).toBe(view.bounds.width / 2);
  expect(trust.position.y + Number(trust.style!.height) / 2).toBe(view.bounds.height / 2);
  expect(view.nodes.filter(node => node.id !== "t").every(node => node.type !== "trust")).toBe(true);
  expect(view.edges.map(({ source, target, markerEnd }) => ({ source, target, directed: !!markerEnd })))
    .toEqual([{ source: "a", target: "b", directed: false }, { source: "b", target: "t", directed: true }]);
  expect(toGraphView(graph)).toEqual(view);
  expect(graph).toEqual(original);
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
  const centers = view.nodes.map(node => ({
    x: node.position.x + Number(node.style!.width) / 2,
    y: node.position.y + Number(node.style!.height) / 2,
  }));
  expect(view.nodes.every(node => node.type !== "trust")).toBe(true);
  expect(new Set(centers.map(center => center.x))).toHaveLength(1);
  expect(centers.map(center => center.y)).toEqual(
    [...centers.map(center => center.y)].sort((a, b) => a - b),
  );
});

test("multiple Trusts remain triangles with routes meeting their visible boundary", () => {
  const multiple = { ...graph, entities: graph.entities.map(entity => entity.id === "b" ? { ...entity, type: "trust" as const } : entity) };
  const view = toGraphView(multiple);
  const trust = view.nodes.find(node => node.id === "t")!;
  const centers = view.nodes.map(node => ({
    x: node.position.x + Number(node.style!.width) / 2,
    y: node.position.y + Number(node.style!.height) / 2,
  }));
  expect(view.nodes.filter(node => node.type === "trust")).toHaveLength(2);
  expect(new Set(centers.map(center => center.x))).toHaveLength(1);
  expect(centers.map(center => center.y)).toEqual(
    [...centers.map(center => center.y)].sort((a, b) => a - b),
  );
  const route = view.edges[1].data!.route as { points: { x: number; y: number }[] };
  const end = route.points.at(-1)!;
  // A directed arrow touches one of the triangle's three sides, not its interior.
  const x = (end.x - trust.position.x) / Number(trust.style!.width);
  const y = (end.y - trust.position.y) / Number(trust.style!.height);
  expect(Math.min(Math.abs(y - 1), Math.abs(x - y / 2 - 0.5), Math.abs(x + y / 2 - 0.5))).toBeLessThan(0.001);
  expect(toGraphView(multiple)).toEqual(view);
});
