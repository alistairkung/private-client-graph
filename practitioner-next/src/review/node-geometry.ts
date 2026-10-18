export type Point = { x: number; y: number };
export type Rectangle = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};
export type RelationshipRoute = {
  points: Point[];
  anchor: Point;
  x: number;
  y: number;
  labelOffset: Point;
  labelBounds: Rectangle;
};
export const NODE_WIDTH = 170;
export const PERSON_HEIGHT = 56;
export const TRUST_HEIGHT = 96;
export const TRUST_LABEL_HEIGHT = 60;
const LABEL_HEIGHT = 32;

type RouteOptions = {
  obstacles?: Rectangle[];
  routes?: Point[][];
};

export function nodeBoundary(
  from: Point,
  toward: Point,
  triangle: boolean,
): Point {
  const dx = toward.x - from.x;
  const dy = toward.y - from.y;
  // Intersect a ray with the triangle's three sides or the ordinary node box.
  const scale = triangle
    ? 1 /
      Math.max(
        dy / (TRUST_HEIGHT / 2),
        (Math.abs(dx) / (NODE_WIDTH / 2) - dy / TRUST_HEIGHT) * 2,
      )
    : 1 /
      Math.max(
        Math.abs(dx) / (NODE_WIDTH / 2),
        Math.abs(dy) / (PERSON_HEIGHT / 2),
      );
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}

export function nodeRectangle(
  center: Point,
  height: number,
  clearance = 0,
): Rectangle {
  return {
    left: center.x - NODE_WIDTH / 2 - clearance,
    top: center.y - height / 2 - clearance,
    right: center.x + NODE_WIDTH / 2 + clearance,
    bottom: center.y + height / 2 + clearance,
  };
}

// Labels beneath Trust triangles occupy real layout space without changing connectors.
export function nodeFootprint(
  center: Point,
  height: number,
  clearance = 0,
): Rectangle {
  const rectangle = nodeRectangle(center, height, clearance);
  if (height === TRUST_HEIGHT) rectangle.bottom += TRUST_LABEL_HEIGHT;
  return rectangle;
}

function routeAnchor(points: Point[], fraction: number) {
  const lengths = points
    .slice(1)
    .map((point, index) =>
      Math.hypot(point.x - points[index].x, point.y - points[index].y),
    );
  const distance =
    lengths.reduce((total, length) => total + length, 0) * fraction;
  let travelled = 0,
    segment = 0;
  while (
    segment < lengths.length - 1 &&
    travelled + lengths[segment] < distance
  ) {
    travelled += lengths[segment];
    segment++;
  }
  const start = points[segment],
    end = points[segment + 1];
  const length = lengths[segment] || 1;
  const progress = (distance - travelled) / length;
  return {
    anchor: {
      x: start.x + (end.x - start.x) * progress,
      y: start.y + (end.y - start.y) * progress,
    },
    normal: { x: -(end.y - start.y) / length, y: (end.x - start.x) / length },
  };
}

export function relationshipRoute(
  points: Point[],
  label: string,
  options: RouteOptions = {},
): RelationshipRoute {
  const width = Math.max(
    120,
    [...label].reduce(
      (total, character) => total + (character.charCodeAt(0) > 255 ? 14 : 7.2),
      0,
    ) + 24,
  );
  const anchors = [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9].map(
    (fraction) => routeAnchor(points, fraction),
  );
  const placements = [26, 44, 62, 80, 100, 124, 156, 196].flatMap((distance) =>
    anchors.flatMap(({ anchor, normal }) =>
      [1, -1].map((direction) => {
        const labelOffset = {
          x: normal.x * distance * direction,
          y: normal.y * distance * direction,
        };
        const x = anchor.x + labelOffset.x,
          y = anchor.y + labelOffset.y;
        return {
          anchor,
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
      }),
    ),
  );
  function collisions(candidate: (typeof placements)[number]) {
    const box = candidate.labelBounds;
    const nodeCollisions = (options.obstacles ?? []).filter(
      (obstacle) =>
        box.left < obstacle.right &&
        box.right > obstacle.left &&
        box.top < obstacle.bottom &&
        box.bottom > obstacle.top,
    ).length;
    const lineBox = {
      left: box.left - 4,
      right: box.right + 4,
      top: box.top - 4,
      bottom: box.bottom + 4,
    };
    const lineCollisions = (options.routes ?? []).filter((route) =>
      route
        .slice(1)
        .some((end, index) => segmentCrossesBounds(route[index], end, lineBox)),
    ).length;
    return nodeCollisions + lineCollisions;
  }
  const selected =
    placements.find((candidate) => collisions(candidate) === 0) ??
    [...placements].sort((a, b) => collisions(a) - collisions(b))[0];
  return { points, ...selected };
}

export function segmentCrossesBounds(
  start: Point,
  end: Point,
  bounds: Rectangle,
): boolean {
  let enter = 0;
  let leave = 1;
  for (const [origin, delta, minimum, maximum] of [
    [start.x, end.x - start.x, bounds.left, bounds.right],
    [start.y, end.y - start.y, bounds.top, bounds.bottom],
  ]) {
    if (!delta) {
      if (origin < minimum || origin > maximum) return false;
      continue;
    }
    const first = (minimum - origin) / delta;
    const second = (maximum - origin) / delta;
    enter = Math.max(enter, Math.min(first, second));
    leave = Math.min(leave, Math.max(first, second));
    if (enter > leave) return false;
  }
  return true;
}
