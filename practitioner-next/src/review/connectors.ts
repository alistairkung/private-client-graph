export interface Point {
  x: number;
  y: number;
}
export interface Obstacle {
  left: number;
  right: number;
  top: number;
  bottom: number;
}
interface Endpoints {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
}

function segmentCrosses(start: Point, end: Point, box: Obstacle): boolean {
  let enter = 0,
    leave = 1;
  for (const [origin, delta, minimum, maximum] of [
    [start.x, end.x - start.x, box.left, box.right],
    [start.y, end.y - start.y, box.top, box.bottom],
  ]) {
    if (!delta) {
      if (origin < minimum || origin > maximum) return false;
      continue;
    }
    const first = (minimum - origin) / delta,
      second = (maximum - origin) / delta;
    enter = Math.max(enter, Math.min(first, second));
    leave = Math.min(leave, Math.max(first, second));
    if (enter > leave) return false;
  }
  return true;
}
function curvePoint(
  start: Point,
  control: Point,
  end: Point,
  t: number,
): Point {
  return {
    x: (1 - t) ** 2 * start.x + 2 * (1 - t) * t * control.x + t * t * end.x,
    y: (1 - t) ** 2 * start.y + 2 * (1 - t) * t * control.y + t * t * end.y,
  };
}
function clearCurve(
  start: Point,
  control: Point,
  end: Point,
  obstacles: Obstacle[],
): boolean {
  const label = curvePoint(start, control, end, 0.5);
  if (
    obstacles.some(
      (box) =>
        label.x + 78 > box.left &&
        label.x - 78 < box.right &&
        label.y + 20 > box.top &&
        label.y - 20 < box.bottom,
    )
  )
    return false;
  let previous = start;
  for (let step = 1; step <= 40; step++) {
    const next = curvePoint(start, control, end, step / 40);
    if (obstacles.some((box) => segmentCrosses(previous, next, box)))
      return false;
    previous = next;
  }
  return true;
}

export function connectorGeometry(
  endpoints: Endpoints,
  lane: number,
  obstacles: Obstacle[] = [],
) {
  const start = { x: endpoints.sourceX, y: endpoints.sourceY };
  const end = { x: endpoints.targetX, y: endpoints.targetY };
  const dx = end.x - start.x,
    dy = end.y - start.y;
  const length = Math.hypot(dx, dy) || 1;
  const offset = lane * 85;
  const direction = Math.sign(offset) || 1;
  const controlAt = (distance: number) => ({
    x: (start.x + end.x) / 2 - (dy / length) * distance,
    y: (start.y + end.y) / 2 + (dx / length) * distance,
  });
  const candidates = [
    offset,
    ...[180, 300, 480, 720].flatMap((distance) => [
      offset + direction * distance,
      offset - direction * distance,
    ]),
  ];
  const control =
    candidates
      .map(controlAt)
      .find((control) => clearCurve(start, control, end, obstacles)) ??
    controlAt(offset + direction * 720);
  return {
    path:
      "M " +
      start.x +
      " " +
      start.y +
      " Q " +
      control.x +
      " " +
      control.y +
      " " +
      end.x +
      " " +
      end.y,
    control,
    label: curvePoint(start, control, end, 0.5),
  };
}
