import dagre from "@dagrejs/dagre";
import { Position, type Node, type Edge } from "@xyflow/react";
import type {
  CanonicalState,
  Graph,
  Relationship,
  ReviewRecord,
} from "../shared/contracts";
import type { Translate } from "../shared/locale";
export const relationshipLabels = {
  parent_of: "parent of",
  spouse_of: "spouse of",
  sibling_of: "sibling of",
  settlor_of: "settlor of",
  trustee_of: "trustee of",
  beneficiary_of: "beneficiary of",
} as const;
export function reviewState(record: ReviewRecord): CanonicalState {
  if (record.state) return record.state;
  const graph = record.current_graph ??
    record.proposed_graph ?? { entities: [], relationships: [], evidence: [] };
  const source = record.authoritative_source;
  return {
    ...graph,
    sources: source ? [{ id: "authoritative_source", ...source }] : [],
    evidence: graph.evidence.map((item) => ({
      ...item,
      source_id: "authoritative_source",
    })),
  };
}
export function relationshipStatement(
  graph: Graph,
  relationship: Relationship,
  t: Translate,
): string {
  const name = (id: string) =>
    graph.entities.find((entity) => entity.id === id)?.name ?? id;
  return (
    name(relationship.source) +
    " — " +
    t(relationshipLabels[relationship.type]) +
    " — " +
    name(relationship.target)
  );
}
export function exactSpan(
  text: string,
  quote: string,
): { start: number; end: number } | undefined {
  const start = text.indexOf(quote);
  return quote && start >= 0 ? { start, end: start + quote.length } : undefined;
}
export function graphDrawing(
  graph: Graph,
  t: Translate,
): { nodes: Node[]; edges: Edge[] } {
  const layout = new dagre.graphlib.Graph({ multigraph: true });
  layout.setGraph({
    rankdir: "TB",
    nodesep: 100,
    ranksep: 155,
    marginx: 40,
    marginy: 40,
  });
  layout.setDefaultEdgeLabel(() => ({}));
  graph.entities.forEach((entity) =>
    layout.setNode(entity.id, { width: 160, height: 72 }),
  );
  graph.relationships.forEach((edge, index) =>
    layout.setEdge(edge.source, edge.target, {}, String(index)),
  );
  dagre.layout(layout);
  const positions = new Map(
    graph.entities.map((entity) => [
      entity.id,
      { x: layout.node(entity.id).x, y: layout.node(entity.id).y },
    ]),
  );
  const trusts = graph.entities.filter((entity) => entity.type === "trust");
  if (trusts.length === 1) {
    const trust = trusts[0];
    positions.set(trust.id, { x: 250, y: 180 });
    const groups: string[][] = [[], [], [], []];
    graph.entities
      .filter((entity) => entity.type === "person")
      .forEach((entity) => {
        const roles = graph.relationships
          .filter(
            (edge) =>
              edge.source === entity.id &&
              edge.target === trust.id &&
              ["settlor_of", "trustee_of", "beneficiary_of"].includes(
                edge.type,
              ),
          )
          .map((edge) => edge.type);
        const group =
          roles.length > 1
            ? 3
            : roles[0] === "settlor_of"
              ? 0
              : roles[0] === "beneficiary_of"
                ? 1
                : roles[0] === "trustee_of"
                  ? 2
                  : 3;
        groups[group].push(entity.id);
      });
    groups.forEach((ids, group) =>
      ids.forEach((id, index) =>
        positions.set(
          id,
          group < 2
            ? {
                x: 250 + (index - (ids.length - 1) / 2) * 210,
                y: group === 0 ? 0 : 360,
              }
            : {
                x: group === 2 ? 500 : 0,
                y: 180 + (index - (ids.length - 1) / 2) * 130,
              },
        ),
      ),
    );
  }
  const nodes: Node[] = graph.entities.map((entity) => ({
    id: entity.id,
    type: "entity",
    position: {
      x: positions.get(entity.id)!.x - 80,
      y: positions.get(entity.id)!.y - 36,
    },
    data: {
      ...entity,
      kindLabel: t(entity.type === "trust" ? "Trust" : "Person"),
    },
    ariaLabel: entity.name,
    draggable: false,
    style: { width: 160, minHeight: 72 },
  }));
  const edges: Edge[] = graph.relationships.map((relationship, index) => {
    const source = positions.get(relationship.source)!;
    const target = positions.get(relationship.target)!;
    const dx = target.x - source.x,
      dy = target.y - source.y;
    const horizontal = Math.abs(dx) > Math.abs(dy);
    const sourceHandle = horizontal
      ? dx > 0
        ? "right"
        : "left"
      : dy > 0
        ? "bottom"
        : "top";
    const targetHandle = horizontal
      ? dx > 0
        ? "left"
        : "right"
      : dy > 0
        ? "top"
        : "bottom";
    const siblings = graph.relationships
      .map((edge, position) => ({ edge, position }))
      .filter(
        ({ edge }) =>
          [edge.source, edge.target].sort().join("|") ===
          [relationship.source, relationship.target].sort().join("|"),
      );
    const lane =
      siblings.findIndex((item) => item.position === index) -
      (siblings.length - 1) / 2;
    return {
      id: String(index),
      source: relationship.source,
      target: relationship.target,
      sourceHandle,
      targetHandle: "target-" + targetHandle,
      type: "relationship",
      label: t(relationshipLabels[relationship.type]),
      data: {
        // The renderer's perpendicular reverses with endpoint direction.
        lane: lane * (relationship.source < relationship.target ? 1 : -1),
        obstacles: graph.entities
          .filter(
            (entity) =>
              entity.id !== relationship.source &&
              entity.id !== relationship.target,
          )
          .map((entity) => {
            const position = positions.get(entity.id)!;
            const height = Math.max(
              72,
              Math.ceil(entity.name.length / 14) * 24 + 38,
            );
            return {
              left: position.x - 92,
              right: position.x + 92,
              top: position.y - 48,
              bottom: position.y - 36 + height + 12,
            };
          }),
        parent: relationship.type === "parent_of",
        trust:
          relationship.type.endsWith("_of") &&
          !["parent_of", "spouse_of", "sibling_of"].includes(relationship.type),
        statement: relationshipStatement(graph, relationship, t),
      },
      ariaLabel: relationshipStatement(graph, relationship, t),
      interactionWidth: 28,
    };
  });
  return { nodes, edges };
}
export const positions = {
  top: Position.Top,
  bottom: Position.Bottom,
  left: Position.Left,
  right: Position.Right,
};
