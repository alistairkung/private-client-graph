import type { CanonicalGraph } from "./types";

type Point = { x: number; y: number };

// A single Trust is an anchor, not a new legal ordering of the other entities.
// Multiple-Trust positioning remains on the existing general graph layout.
export function centralTrustLayout(graph: CanonicalGraph) {
  const trusts = graph.entities.filter(entity => entity.type === "trust");
  if (trusts.length !== 1) return null;
  const others = graph.entities.filter(entity => entity.id !== trusts[0].id)
    .sort((a, b) => a.id.localeCompare(b.id));
  const radius = Math.max(220, others.length * 55);
  const center = { x: radius + 160, y: radius + 120 };
  const positions = new Map<string, Point>([[trusts[0].id, center]]);
  const angles = new Map<string, number>();
  others.forEach((entity, index) => {
    const angle = -Math.PI / 2 + index * 2 * Math.PI / others.length;
    angles.set(entity.id, angle);
    positions.set(entity.id, {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle),
    });
  });
  const routes = graph.relationships.map(edge => {
    const source = positions.get(edge.source)!;
    const target = positions.get(edge.target)!;
    let points: Point[];
    let label: Point;
    if (edge.source === trusts[0].id || edge.target === trusts[0].id) {
      // End at the node boundary, preserving the canonical direction.
      const start = boundary(source, target, edge.source === trusts[0].id);
      const end = boundary(target, source, edge.target === trusts[0].id);
      points = [start, end];
      label = { x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 };
    } else {
      // Route person-to-person links around the anchor instead of through it.
      const startAngle = angles.get(edge.source)!;
      let delta = angles.get(edge.target)! - startAngle;
      if (delta > Math.PI) delta -= 2 * Math.PI;
      if (delta < -Math.PI) delta += 2 * Math.PI;
      const arcRadius = radius + 75;
      const arc = Array.from({ length: 17 }, (_, index) => {
        const angle = startAngle + delta * index / 16;
        return { x: center.x + arcRadius * Math.cos(angle), y: center.y + arcRadius * Math.sin(angle) };
      });
      points = [boundary(source, arc[0], false), ...arc, boundary(target, arc[16], false)];
      label = arc[8];
    }
    return { points, ...label };
  });
  return { positions, routes, bounds: { x: 0, y: 0, width: center.x * 2, height: center.y * 2 } };
}

function boundary(from: Point, toward: Point, trust: boolean): Point {
  const dx = toward.x - from.x;
  const dy = toward.y - from.y;
  // Trust triangle vertices relative to its center: (0,-48), (-85,48), (85,48).
  const scale = trust
    ? 1 / Math.max(dy / 48, (Math.abs(dx) / 85 - dy / 96) * 2)
    : 1 / Math.max(Math.abs(dx) / 85, Math.abs(dy) / 28);
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}
