import { describe, expect, it } from "vitest";
import { directionalTarget, relationshipLabelPoint } from "./story-geometry";
import type { LandingPoint } from "./landing-layout";
const from: LandingPoint = [100, 50];
const to: LandingPoint = [370, 210];
describe("visible directional connector endpoints", () => {
  it.each([
    { width: 660, height: 420, glyph: 38 },
    { width: 350, height: 230, glyph: 28 },
    { width: 1000, height: 300, glyph: 38 },
  ])(
    "keeps a three CSS pixel gap outside a person after aspect/viewport changes: %o",
    ({ width, height, glyph }) => {
      const end = directionalTarget(
        from,
        to,
        "person",
        { width, height },
        { width: glyph, height: glyph },
      );
      const dx = ((end[0] - to[0]) * width) / 660;
      const dy = ((end[1] - to[1]) * height) / 420;
      expect(Math.hypot(dx, dy)).toBeCloseTo((13 * glyph) / 48 + 3);
      const sourceDx = ((from[0] - to[0]) * width) / 660;
      const sourceDy = ((from[1] - to[1]) * height) / 420;
      expect(dx * sourceDy - dy * sourceDx).toBeCloseTo(0);
      expect(dx * sourceDx + dy * sourceDy).toBeGreaterThan(0);
    },
  );
  it("uses the actual triangle boundary rather than a circular trust approximation", () => {
    const drawing = { width: 660, height: 420 };
    const glyph = { width: 48, height: 48 };
    expect(directionalTarget([370, 0], to, "trust", drawing, glyph)).toEqual([
      370, 187,
    ]);
    expect(directionalTarget([370, 420], to, "trust", drawing, glyph)).toEqual([
      370, 231,
    ]);
    const left = directionalTarget([0, 210], to, "trust", drawing, glyph);
    expect(left[0]).toBeCloseTo(370 - (21 * 20) / 38 - 3);
    expect(left[1]).toBe(210);
  });
  it("handles an unmeasured drawing or coincident centers without inventing coordinates", () => {
    expect(
      directionalTarget(
        from,
        to,
        "person",
        { width: 0, height: 0 },
        { width: 38, height: 38 },
      ),
    ).toBe(to);
    expect(
      directionalTarget(
        to,
        to,
        "trust",
        { width: 660, height: 420 },
        { width: 48, height: 48 },
      ),
    ).toBe(to);
  });
});

describe("phone relationship captions", () => {
  it("moves only diagonal parent labels past the settlor label", () => {
    expect(
      relationshipLabelPoint(
        "parent_of",
        [370, 58],
        [155, 350],
        { width: 284, height: 290 },
        true,
        110,
        60,
      ),
    ).toEqual([284, 174.8]);
    expect(
      relationshipLabelPoint(
        "parent_of",
        [130, 58],
        [155, 350],
        { width: 284, height: 290 },
        true,
        110,
        60,
      ),
    ).toEqual([138.25, 154.36]);
    expect(
      relationshipLabelPoint(
        "parent_of",
        [370, 58],
        [155, 350],
        { width: 664, height: 540 },
        false,
        156,
        60,
      ),
    ).toEqual([299.05, 154.36]);
  });
  it.each([54, 60])(
    "separates both parent labels at 320px with %ipx font metrics",
    (labelWidth) => {
      const drawing = { width: 284, height: 290 };
      const diagonal = relationshipLabelPoint(
        "parent_of",
        [370, 58],
        [155, 350],
        drawing,
        true,
        110,
        labelWidth,
      );
      const vertical = relationshipLabelPoint(
        "parent_of",
        [130, 58],
        [155, 350],
        drawing,
        true,
        110,
        labelWidth,
      );
      const horizontalGap =
        ((diagonal[0] - vertical[0]) * drawing.width) / 660 - labelWidth;
      expect(horizontalGap).toBeGreaterThan(2);
    },
  );
  it("places beneficiary pills eight pixels outside the actual Trust caption on either side", () => {
    const drawing = { width: 284, height: 290 };
    const left = relationshipLabelPoint(
      "beneficiary_of",
      [155, 350],
      [370, 210],
      drawing,
      true,
      110,
      74,
    );
    const right = relationshipLabelPoint(
      "beneficiary_of",
      [545, 350],
      [370, 210],
      drawing,
      true,
      110,
      74,
    );
    expect(
      ((370 - left[0]) * drawing.width) / 660 - 74 / 2 - 110 / 2,
    ).toBeCloseTo(8);
    expect(
      ((right[0] - 370) * drawing.width) / 660 - 74 / 2 - 110 / 2,
    ).toBeCloseTo(8);
    expect(left[1]).toBe(280);
    expect(right[1]).toBe(280);
  });
});

it("places the settlor label clear of the source person's caption with a leader", () => {
  const drawing = { width: 284, height: 290 };
  const point = relationshipLabelPoint(
    "settlor_of",
    [370, 58],
    [370, 210],
    drawing,
    true,
    110,
    52,
  );
  expect(
    ((point[0] - 370) * drawing.width) / 660 - 110 / 2 - 52 / 2,
  ).toBeCloseTo(8);
  expect(point[1]).toBe(134);
});
