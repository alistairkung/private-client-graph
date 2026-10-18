import type { Entity, RelationshipType } from "../shared/contracts";
import type { LandingPoint } from "./landing-layout";
export interface GlyphSize {
  width: number;
  height: number;
}
export interface DrawingSize {
  width: number;
  height: number;
}

/** End a directed connector outside the actual glyph, even in a stretched viewBox. */
export function directionalTarget(
  from: LandingPoint,
  to: LandingPoint,
  type: Entity["type"],
  drawing: DrawingSize,
  glyph: GlyphSize,
  gap = 3,
): LandingPoint {
  if (!drawing.width || !drawing.height || !glyph.width || !glyph.height)
    return to;
  const dx = ((from[0] - to[0]) * drawing.width) / 660;
  const dy = ((from[1] - to[1]) * drawing.height) / 420;
  const length = Math.hypot(dx, dy);
  if (!length) return to;
  const ux = dx / length;
  const uy = dy / length;
  let radius: number;
  if (type === "person") {
    const rx = (13 * glyph.width) / 48;
    const ry = (13 * glyph.height) / 48;
    radius = 1 / Math.hypot(ux / rx, uy / ry);
  } else {
    // These vertices are the rendered trust path, relative to its (24,24) anchor.
    const vertices = [
      [0, (-20 * glyph.height) / 48],
      [(21 * glyph.width) / 48, (18 * glyph.height) / 48],
      [(-21 * glyph.width) / 48, (18 * glyph.height) / 48],
    ];
    radius = Infinity;
    for (let index = 0; index < vertices.length; index++) {
      const a = vertices[index];
      const b = vertices[(index + 1) % vertices.length];
      const ex = b[0] - a[0];
      const ey = b[1] - a[1];
      const cross = ux * ey - uy * ex;
      if (Math.abs(cross) < 1e-9) continue;
      const distance = (a[0] * ey - a[1] * ex) / cross;
      const segment = (a[0] * uy - a[1] * ux) / cross;
      if (distance >= 0 && segment >= 0 && segment <= 1)
        radius = Math.min(radius, distance);
    }
  }
  const inset = Math.min(length, radius + gap);
  return [
    to[0] + (ux * inset * 660) / drawing.width,
    to[1] + (uy * inset * 420) / drawing.height,
  ];
}

/** Phone labels clear entity captions without changing the graph itself. */
export function relationshipLabelPoint(
  type: RelationshipType,
  from: LandingPoint,
  to: LandingPoint,
  drawing: DrawingSize,
  mobile: boolean,
  captionWidth: number,
  labelWidth: number,
): LandingPoint {
  const diagonal = Math.abs(from[0] - to[0]) > Math.abs(from[1] - to[1]) * 0.25;
  const fraction =
    type === "parent_of" ? (mobile && diagonal ? 0.52 : 0.33) : 0.5;
  const point: LandingPoint = [
    from[0] + (to[0] - from[0]) * fraction,
    from[1] + (to[1] - from[1]) * fraction,
  ];
  if (
    !mobile ||
    !["beneficiary_of", "settlor_of"].includes(type) ||
    !drawing.width
  )
    return point;
  const side = type === "settlor_of" ? 1 : from[0] < to[0] ? -1 : 1;
  return [
    to[0] +
      (side * (captionWidth / 2 + 8 + labelWidth / 2) * 660) / drawing.width,
    point[1],
  ];
}
