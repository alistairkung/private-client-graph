import { describe, expect, it } from "vitest";
import { connectorGeometry } from "./connectors";
import { graphDrawing } from "./presentation";
import type { Graph } from "../shared/contracts";

const people = [
  { id: "a", name: "Fictional A", type: "person" as const },
  { id: "b", name: "Fictional B", type: "person" as const },
];
const forward = { sourceX: 0, sourceY: 0, targetX: 200, targetY: 100 };
const reverse = { sourceX: 200, sourceY: 100, targetX: 0, targetY: 0 };

describe("distinct and inspectable relationship routing", () => {
  it("separates reciprocal parent paths and labels while preserving their directions", () => {
    const graph: Graph = {
      entities: people,
      evidence: [],
      relationships: [
        { source: "a", target: "b", type: "parent_of", evidence_ids: ["one"] },
        { source: "b", target: "a", type: "parent_of", evidence_ids: ["two"] },
      ],
    };
    const drawing = graphDrawing(graph, (key) => key);
    const first = connectorGeometry(
      forward,
      Number(drawing.edges[0].data?.lane),
    );
    const second = connectorGeometry(
      reverse,
      Number(drawing.edges[1].data?.lane),
    );
    expect(first.control).not.toEqual(second.control);
    expect(first.label).not.toEqual(second.label);
    expect(
      drawing.edges.map((edge) => [
        edge.source,
        edge.target,
        edge.data?.parent,
      ]),
    ).toEqual([
      ["a", "b", true],
      ["b", "a", true],
    ]);
  });

  it("keeps each same-direction role connector distinct without dropping canonical relationships", () => {
    const graph: Graph = {
      entities: [
        people[0],
        { id: "b", name: "Fictional Trust", type: "trust" },
      ],
      evidence: [],
      relationships: [
        { source: "a", target: "b", type: "settlor_of", evidence_ids: ["one"] },
        { source: "a", target: "b", type: "trustee_of", evidence_ids: ["two"] },
        {
          source: "a",
          target: "b",
          type: "beneficiary_of",
          evidence_ids: ["three"],
        },
      ],
    };
    const drawing = graphDrawing(graph, (key) => key);
    const labels = drawing.edges.map(
      (edge) => connectorGeometry(forward, Number(edge.data?.lane)).label,
    );
    expect(new Set(labels.map((label) => JSON.stringify(label))).size).toBe(3);
    expect(drawing.edges.map((edge) => edge.label)).toEqual([
      "settlor of",
      "trustee of",
      "beneficiary of",
    ]);
    expect(drawing.edges.every((edge) => edge.data?.parent === false)).toBe(
      true,
    );
  });

  it("bends family connectors and their labels clear of a nonendpoint Trust", () => {
    const obstacle = { left: 70, right: 130, top: 20, bottom: 80 };
    const geometry = connectorGeometry(forward, 0, [obstacle]);
    expect(geometry.control).not.toEqual({ x: 100, y: 50 });
    expect(
      geometry.label.y + 20 <= obstacle.top ||
        geometry.label.y - 20 >= obstacle.bottom ||
        geometry.label.x + 78 <= obstacle.left ||
        geometry.label.x - 78 >= obstacle.right,
    ).toBe(true);
    for (let step = 0; step <= 100; step++) {
      const t = step / 100;
      const x = 2 * (1 - t) * t * geometry.control.x + t * t * forward.targetX;
      const y = 2 * (1 - t) * t * geometry.control.y + t * t * forward.targetY;
      expect(
        x > obstacle.left &&
          x < obstacle.right &&
          y > obstacle.top &&
          y < obstacle.bottom,
      ).toBe(false);
    }
  });

  it("provides each connector with only nonendpoint node obstacles", () => {
    const graph: Graph = {
      entities: [
        ...people,
        { id: "trust", type: "trust", name: "Fictional Trust" },
      ],
      evidence: [],
      relationships: [
        { source: "a", target: "b", type: "parent_of", evidence_ids: [] },
      ],
    };
    const edge = graphDrawing(graph, (key) => key).edges[0];
    expect(edge.data?.obstacles).toEqual([
      expect.objectContaining({ left: 158, right: 342 }),
    ]);
  });
});
