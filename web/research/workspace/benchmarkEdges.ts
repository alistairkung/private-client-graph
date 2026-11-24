import type { CanonicalState } from "../shared/contracts";

const symmetric = new Set(["spouse_of", "sibling_of"]);

export function edgeKey(source: string, type: string, target: string) {
  const endpoints = symmetric.has(type)
    ? [source, target].sort()
    : [source, target];
  return JSON.stringify([endpoints[0], type, endpoints[1]]);
}

export function graphEdgeKeys(state: CanonicalState) {
  const names = new Map(state.entities.map((item) => [item.id, item.name]));
  return state.relationships.map((edge) =>
    edgeKey(
      names.get(edge.source) ?? edge.source,
      edge.type,
      names.get(edge.target) ?? edge.target,
    ),
  );
}
