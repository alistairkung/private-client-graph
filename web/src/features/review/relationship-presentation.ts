import type { CanonicalGraph, RelationshipType } from "../../shared/canonical-graph";

export type TrustRole = "settlor" | "beneficiary" | "trustee";

type ConnectorPresentation = {
  label: string;
  role?: TrustRole;
  arrow: boolean;
};

const connectors: Record<RelationshipType, ConnectorPresentation> = {
  parent_of: { label: "Parent of", arrow: true },
  spouse_of: { label: "Spouse of", arrow: false },
  sibling_of: { label: "Sibling of", arrow: false },
  settlor_of: { label: "Settlor", role: "settlor", arrow: false },
  beneficiary_of: { label: "Beneficiary", role: "beneficiary", arrow: false },
  trustee_of: { label: "Trustee", role: "trustee", arrow: false },
};

// Presentation annotations never replace the canonical claim or its selection index.
export function presentRelationships(graph: CanonicalGraph) {
  const names = new Map(graph.entities.map(entity => [entity.id, entity.name]));
  const relationships = graph.relationships.map((relationship, index) => {
    const connector = connectors[relationship.type];
    return {
      ...relationship,
      index,
      ...connector,
      kind: connector.role ? "trust-role" : "family",
      description: `${names.get(relationship.source)} — ${connector.label}${connector.role ? " of" : ""} — ${names.get(relationship.target)}`,
    };
  });
  return {
    entities: graph.entities.map(entity => ({
      ...entity,
      roles: [...new Set(relationships.filter(relationship => relationship.source === entity.id)
        .flatMap(relationship => relationship.role ? [relationship.role] : []))].sort(),
    })),
    relationships,
  };
}

export type RelationshipPresentation = ReturnType<typeof presentRelationships>;
