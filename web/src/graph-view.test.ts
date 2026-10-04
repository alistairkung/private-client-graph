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
