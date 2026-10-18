import { describe, expect, it } from "vitest";
import { nodeBoundary, nodeFootprint, nodeRectangle, PERSON_HEIGHT, TRUST_HEIGHT, TRUST_LABEL_HEIGHT } from "./node-geometry";

describe("visible node footprints", () => {
  it("reserves the Trust caption without moving connector endpoints", () => {
    const center = { x: 100, y: 100 };
    const shape = nodeRectangle(center, TRUST_HEIGHT, 8);
    expect(nodeFootprint(center, TRUST_HEIGHT, 8)).toEqual({ ...shape, bottom: shape.bottom + TRUST_LABEL_HEIGHT });
    expect(nodeBoundary(center, { x: 100, y: 300 }, true)).toEqual({ x: 100, y: 148 });
  });
  it("keeps Person captions within rectangular nodes", () => {
    expect(nodeFootprint({ x: 0, y: 0 }, PERSON_HEIGHT)).toEqual(nodeRectangle({ x: 0, y: 0 }, PERSON_HEIGHT));
  });
});
