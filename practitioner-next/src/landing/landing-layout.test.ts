import { describe, expect, it } from "vitest";
import type { CanonicalState } from "../shared/contracts";
import { landingPositions, sourceContext } from "./landing-layout";
const graph: CanonicalState = {
  entities: [
    { id: "uuid-trust", name: "Trust", type: "trust" },
    { id: "uuid-carol", name: "Carol", type: "person" },
    { id: "uuid-alice", name: "Alice", type: "person" },
    { id: "uuid-bob", name: "Bob", type: "person" },
    { id: "uuid-david", name: "David", type: "person" },
  ],
  relationships: [
    {
      source: "uuid-alice",
      target: "uuid-trust",
      type: "settlor_of",
      evidence_ids: [],
    },
    {
      source: "uuid-alice",
      target: "uuid-david",
      type: "spouse_of",
      evidence_ids: [],
    },
    {
      source: "uuid-alice",
      target: "uuid-bob",
      type: "parent_of",
      evidence_ids: [],
    },
    {
      source: "uuid-david",
      target: "uuid-bob",
      type: "parent_of",
      evidence_ids: [],
    },
    {
      source: "uuid-bob",
      target: "uuid-trust",
      type: "beneficiary_of",
      evidence_ids: [],
    },
    {
      source: "uuid-carol",
      target: "uuid-trust",
      type: "beneficiary_of",
      evidence_ids: [],
    },
  ],
  sources: [],
  evidence: [],
};
describe("public drawing identity", () => {
  it("uses arbitrary canonical IDs consistently for every entity and all six nonzero connectors", () => {
    const points = landingPositions(graph);
    expect([...points.keys()]).toEqual(
      graph.entities.map((entity) => entity.id),
    );
    expect(
      new Set([...points.values()].map((point) => point.join(","))).size,
    ).toBe(5);
    graph.relationships.forEach((edge) => {
      const from = points.get(edge.source)!,
        to = points.get(edge.target)!;
      expect(Math.hypot(from[0] - to[0], from[1] - to[1])).toBeGreaterThan(10);
    });
    expect(points.get("uuid-alice")![1]).toBe(points.get("uuid-david")![1]);
    expect(points.get("uuid-trust")![1]).toBeGreaterThan(
      points.get("uuid-alice")![1],
    );
    expect(points.get("uuid-bob")![1]).toBeGreaterThan(
      points.get("uuid-trust")![1],
    );
  });
  it("gives every entity its own fallback coordinate without a Trust or known ID spelling", () => {
    const family = {
      ...graph,
      entities: graph.entities.filter((entity) => entity.type === "person"),
      relationships: graph.relationships.filter(
        (edge) => edge.type === "parent_of" || edge.type === "spouse_of",
      ),
    };
    const points = landingPositions(family);
    expect(
      new Set([...points.values()].map((point) => point.join(","))).size,
    ).toBe(family.entities.length);
    family.relationships.forEach((edge) =>
      expect(points.get(edge.source)).not.toEqual(points.get(edge.target)),
    );
  });
  it("bounds surrounding prose at word breaks and leaves the exact Evidence substring untouched", () => {
    const prefix = "Surrounding words ".repeat(15),
      quote = "The exact canonical quote.",
      suffix = " More surrounding words".repeat(15);
    const context = sourceContext(
      prefix + quote + suffix,
      prefix.length,
      quote.length,
    );
    expect(context.before).toMatch(/^… (Surrounding|words) /);
    expect(context.after).toMatch(/(More|surrounding|words) …$/);
    expect(
      (prefix + quote + suffix).slice(
        prefix.length,
        prefix.length + quote.length,
      ),
    ).toBe(quote);
  });
});
