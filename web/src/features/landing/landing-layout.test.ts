import { describe, expect, it } from "vitest";
import type { CanonicalState } from "../../shared/contracts";
import {
  landingPositions,
  sourceContext,
  sourceEntitySpans,
  canonicalSourceExcerpts,
} from "./landing-layout";
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

describe("source entity emphasis", () => {
  it("preserves exact source text, matches literal names and prefers the complete name", () => {
    const text = "A. Reed and A. Reed Jr have a trust (+).";
    const spans = sourceEntitySpans(text, [
      "A. Reed",
      "A. Reed Jr",
      "trust (+)",
      "",
      "A. Reed",
    ]);
    expect(spans.map((span) => span.text).join("")).toBe(text);
    expect(
      spans.filter((span) => span.entity).map((span) => span.text),
    ).toEqual(["A. Reed", "A. Reed Jr", "trust (+)"]);
    expect(sourceEntitySpans(text, [])).toEqual([{ text, entity: false }]);
  });
});

describe("canonical source excerpts", () => {
  it("deduplicates exact supported passages in source order and excludes different or missing sources", () => {
    const state = {
      ...graph,
      sources: [
        {
          id: "source-a",
          title: "Source",
          text: "First complete sentence. Second complete sentence.",
        },
      ],
      evidence: [
        {
          id: "e-2",
          document: "Source",
          source_id: "source-a",
          supporting_text: "Second complete sentence.",
        },
        {
          id: "e-1",
          document: "Source",
          source_id: "source-a",
          supporting_text: "First complete sentence.",
        },
        {
          id: "e-3",
          document: "Source",
          source_id: "source-a",
          supporting_text: "First complete sentence.",
        },
        {
          id: "e-4",
          document: "Other",
          source_id: "source-b",
          supporting_text: "Unrelated text.",
        },
        {
          id: "e-5",
          document: "Source",
          source_id: "source-a",
          supporting_text: "Unlocated text.",
        },
      ],
    };
    expect(canonicalSourceExcerpts(state, "source-a")).toEqual([
      "First complete sentence.",
      "Second complete sentence.",
    ]);
    expect(canonicalSourceExcerpts(state, "source-missing")).toEqual([]);
  });
});
