import { describe, expect, it } from "vitest";
import { exactSpan, relationshipStatement, reviewState } from "./presentation";
import { graphDrawing } from "./graph-layout";
import type { CanonicalState, ReviewRecord } from "../shared/contracts";
const state: CanonicalState = {
  sources: [
    { id: "source-a", title: "Same title", text: "Exact quote. Exact quote." },
    { id: "source-b", title: "Same title", text: "Other exact quote." },
  ],
  entities: [
    { id: "person", type: "person", name: "Full canonical name" },
    { id: "trust", type: "trust", name: "Synthetic Trust" },
  ],
  relationships: [
    {
      source: "person",
      type: "settlor_of",
      target: "trust",
      evidence_ids: ["evidence-b", "evidence-a"],
    },
    {
      source: "person",
      type: "trustee_of",
      target: "trust",
      evidence_ids: ["evidence-a"],
    },
  ],
  evidence: [
    {
      id: "evidence-a",
      source_id: "source-a",
      document: "Same title",
      supporting_text: "Exact quote.",
    },
    {
      id: "evidence-b",
      source_id: "source-b",
      document: "Same title",
      supporting_text: "Other exact quote.",
    },
  ],
};
describe("authoritative review presentation", () => {
  it("uses complete CanonicalState without remapping Evidence/source identity", () => {
    const record: ReviewRecord = {
      id: "p",
      external_reference: "SYN-1",
      authoritative_source: null,
      state,
    };
    expect(reviewState(record)).toBe(state);
    expect(state.relationships[0].evidence_ids).toEqual([
      "evidence-b",
      "evidence-a",
    ]);
  });
  it("adapts the legacy single source without changing graph labels or quotes", () => {
    const record: ReviewRecord = {
      id: "p",
      external_reference: "SYN-1",
      authoritative_source: { title: "Original", text: "Exact." },
      proposed_graph: {
        ...state,
        evidence: [
          { id: "e", document: "Original", supporting_text: "Exact." },
        ],
      },
    };
    const result = reviewState(record);
    expect(result.sources[0].text).toBe("Exact.");
    expect(result.evidence[0]).toEqual({
      id: "e",
      document: "Original",
      supporting_text: "Exact.",
      source_id: result.sources[0].id,
    });
  });
  it("locates exactly one first occurrence without normalizing or approximating", () => {
    expect(exactSpan("Exact quote. Exact quote.", "Exact quote.")).toEqual({
      start: 0,
      end: 12,
    });
    expect(exactSpan("Exact quote.", "exact quote.")).toBeUndefined();
    expect(exactSpan("Exact quote.", "")).toBeUndefined();
  });
  it("renders one node per canonical entity and separate role connectors", () => {
    const drawing = graphDrawing(state, (key) => key);
    expect(drawing.nodes.map((node) => node.id)).toEqual(["person", "trust"]);
    expect(drawing.edges).toHaveLength(2);
    expect(drawing.edges[0].data?.route).not.toEqual(
      drawing.edges[1].data?.route,
    );
    expect(drawing.edges.every((edge) => edge.data?.parent === false)).toBe(
      true,
    );
  });
  it("preserves relationship direction and full endpoint names in textual alternatives", () => {
    expect(
      relationshipStatement(state, state.relationships[0], (key) => key),
    ).toBe("Full canonical name — settlor of — Synthetic Trust");
    const parent = graphDrawing(
      {
        ...state,
        relationships: [{ ...state.relationships[0], type: "parent_of" }],
      },
      (key) => key,
    );
    expect(parent.edges[0].data?.parent).toBe(true);
    expect(parent.edges[0].source).toBe("person");
  });
});
