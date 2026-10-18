export type Point = { x: number; y: number };
export type Rectangle = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};
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
export const TRUST_LABEL_HEIGHT = 60;
const LABEL_HEIGHT = 32;
const LABEL_OFFSET = 26;

type RouteOptions = {
  awayFrom?: Point;
  obstacles?: Rectangle[];
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

export function relationshipRoute(
  points: Point[],
  label: string,
  options: RouteOptions = {},
): RelationshipRoute {
  const lengths = points
    .slice(1)
    .map((point, index) =>
      Math.hypot(point.x - points[index].x, point.y - points[index].y),
    );
  const routeLength = lengths.reduce((total, length) => total + length, 0);
  // Reserve the complete English/Chinese label footprint so language changes do not move routes.
  const width = Math.max(
    120,
    [...label].reduce(
      (total, character) => total + (character.charCodeAt(0) > 255 ? 14 : 7.2),
      0,
    ) + 24,
  );
  const placements = [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8].flatMap((fraction) => {
    const targetDistance = routeLength * fraction;
    let travelled = 0;
    let segment = 0;
    while (
      segment < lengths.length - 1 &&
      travelled + lengths[segment] < targetDistance
    ) {
      travelled += lengths[segment];
      segment += 1;
    }
    const start = points[segment];
    const end = points[segment + 1];
    const length = lengths[segment] || 1;
    const progress = (targetDistance - travelled) / length;
    const anchor = {
      x: start.x + (end.x - start.x) * progress,
      y: start.y + (end.y - start.y) * progress,
    };
    const normal = {
      x: -(end.y - start.y) / length,
      y: (end.x - start.x) / length,
    };
    const positiveNormalOffset = {
      x: normal.x * LABEL_OFFSET,
      y: normal.y * LABEL_OFFSET,
    };
    const negativeNormalOffset = {
      x: -positiveNormalOffset.x,
      y: -positiveNormalOffset.y,
    };
    const distance = (offset: Point) =>
      options.awayFrom
        ? Math.hypot(
            anchor.x + offset.x - options.awayFrom.x,
            anchor.y + offset.y - options.awayFrom.y,
          )
        : 0;
    const offsets =
      options.awayFrom &&
      distance(negativeNormalOffset) > distance(positiveNormalOffset)
        ? [negativeNormalOffset, positiveNormalOffset]
        : [positiveNormalOffset, negativeNormalOffset];
    return [1, 1.8, 2.6, 3.4].flatMap((distance) =>
      offsets.map((baseOffset) => {
        const labelOffset = {
          x: baseOffset.x * distance,
          y: baseOffset.y * distance,
        };
        const x = anchor.x + labelOffset.x;
        const y = anchor.y + labelOffset.y;
        return {
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
    );
  });
  const selected =
    placements.find(
      (candidate) =>
        !(options.obstacles ?? []).some(
          (obstacle) =>
            candidate.labelBounds.left < obstacle.right &&
            candidate.labelBounds.right > obstacle.left &&
            candidate.labelBounds.top < obstacle.bottom &&
            candidate.labelBounds.bottom > obstacle.top,
        ),
    ) ?? placements[0];
  return {
    points,
    ...selected,
  };
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
