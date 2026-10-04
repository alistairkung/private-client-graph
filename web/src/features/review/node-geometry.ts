export type Point = { x: number; y: number };
export type Rectangle = { left: number; top: number; right: number; bottom: number };
export type RelationshipRoute = {
  points: Point[];
  x: number;
  y: number;
  labelOffset: Point;
  labelBounds: Rectangle;
};
export const NODE_WIDTH = 170;
export const PERSON_HEIGHT = 56;
export const TRUST_HEIGHT = 96;
const LABEL_HEIGHT = 24;
const LABEL_OFFSET = 22;

export function nodeBoundary(from: Point, toward: Point, triangle: boolean): Point {
  const dx = toward.x - from.x;
  const dy = toward.y - from.y;
  // Intersect a ray with the triangle's three sides or the ordinary node box.
  const scale = triangle
    ? 1 / Math.max(dy / (TRUST_HEIGHT / 2), (Math.abs(dx) / (NODE_WIDTH / 2) - dy / TRUST_HEIGHT) * 2)
    : 1 / Math.max(Math.abs(dx) / (NODE_WIDTH / 2), Math.abs(dy) / (PERSON_HEIGHT / 2));
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}

export function relationshipRoute(
  points: Point[],
  label: string,
  awayFrom?: Point,
): RelationshipRoute {
  const lengths = points.slice(1).map((point, index) =>
    Math.hypot(point.x - points[index].x, point.y - points[index].y));
  const halfway = lengths.reduce((total, length) => total + length, 0) / 2;
  let travelled = 0;
  let segment = 0;
  while (segment < lengths.length - 1 && travelled + lengths[segment] < halfway) {
    travelled += lengths[segment];
    segment += 1;
  }
  const start = points[segment];
  const end = points[segment + 1];
  const length = lengths[segment] || 1;
  const progress = (halfway - travelled) / length;
  const anchor = {
    x: start.x + (end.x - start.x) * progress,
    y: start.y + (end.y - start.y) * progress,
  };
  const normal = { x: -(end.y - start.y) / length, y: (end.x - start.x) / length };
  const first = { x: normal.x * LABEL_OFFSET, y: normal.y * LABEL_OFFSET };
  const second = { x: -first.x, y: -first.y };
  const distance = (offset: Point) => awayFrom
    ? Math.hypot(anchor.x + offset.x - awayFrom.x, anchor.y + offset.y - awayFrom.y)
    : 0;
  const labelOffset = awayFrom && distance(second) > distance(first) ? second : first;
  const x = anchor.x + labelOffset.x;
  const y = anchor.y + labelOffset.y;
  const width = Math.max(56, label.length * 6.6 + 14);
  return {
    points,
    x,
    y,
    labelOffset,
    labelBounds: {
      left: x - width / 2,
      top: y - LABEL_HEIGHT / 2,
      right: x + width / 2,
      bottom: y + LABEL_HEIGHT / 2,
    },
  };
}
