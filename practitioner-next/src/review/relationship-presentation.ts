import type { Graph, RelationshipType } from "../shared/contracts";
import type { Translate } from "../shared/locale";
export type TrustRole = "settlor" | "beneficiary" | "trustee";
const connectors: Record<
  RelationshipType,
  { label: string; role?: TrustRole; arrow: boolean }
> = {
  parent_of: { label: "Parent of", arrow: true },
  spouse_of: { label: "Spouse of", arrow: false },
  sibling_of: { label: "Sibling of", arrow: false },
  settlor_of: { label: "Settlor", role: "settlor", arrow: false },
  trustee_of: { label: "Trustee", role: "trustee", arrow: false },
  beneficiary_of: { label: "Beneficiary", role: "beneficiary", arrow: false },
};
export function presentRelationships(graph: Graph, t: Translate) {
  const relationships = graph.relationships.map((relationship, index) => ({
    ...relationship,
    ...connectors[relationship.type],
    index,
    label: t(connectors[relationship.type].label),
    kind: connectors[relationship.type].role ? "trust-role" : "family",
  }));
  return {
    entities: graph.entities.map((entity) => ({
      ...entity,
      roles: [
        ...new Set(
          relationships
            .filter((edge) => edge.source === entity.id)
            .flatMap((edge) => (edge.role ? [edge.role] : [])),
        ),
      ].sort(),
    })),
    relationships,
  };
}
export type RelationshipPresentation = ReturnType<typeof presentRelationships>;
