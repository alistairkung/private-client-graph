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
