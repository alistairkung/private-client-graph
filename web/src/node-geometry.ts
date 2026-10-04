export type Point = { x: number; y: number };
export const NODE_WIDTH = 170;
export const PERSON_HEIGHT = 56;
export const TRUST_HEIGHT = 96;

export function nodeBoundary(from: Point, toward: Point, triangle: boolean): Point {
  const dx = toward.x - from.x;
  const dy = toward.y - from.y;
  // Intersect a ray with the triangle's three sides or the ordinary node box.
  const scale = triangle
    ? 1 / Math.max(dy / (TRUST_HEIGHT / 2), (Math.abs(dx) / (NODE_WIDTH / 2) - dy / TRUST_HEIGHT) * 2)
    : 1 / Math.max(Math.abs(dx) / (NODE_WIDTH / 2), Math.abs(dy) / (PERSON_HEIGHT / 2));
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}
