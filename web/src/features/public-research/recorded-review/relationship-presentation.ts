import type { Locale } from "../../../shared/locale";
import type { CanonicalGraph, RelationshipType } from "../../../shared/canonical-graph";

export type TrustRole = "settlor" | "beneficiary" | "trustee";

type ConnectorPresentation = {
  label: string;
  role?: TrustRole;
  arrow: boolean;
};

const chineseLabels: Record<RelationshipType, string> = {
  parent_of: "父母", spouse_of: "配偶", sibling_of: "兄弟姐妹",
  settlor_of: "信托设立人", beneficiary_of: "受益人", trustee_of: "受托人",
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
export function presentRelationships(graph: CanonicalGraph, locale: Locale = "en") {
  const names = new Map(graph.entities.map(entity => [entity.id, entity.name]));
  const relationships = graph.relationships.map((relationship, index) => {
    const original = connectors[relationship.type];
    const connector = {...original, label: locale === "zh-CN" ? chineseLabels[relationship.type] : original.label};
    return {
      ...relationship,
      index,
      ...connector,
      kind: connector.role ? "trust-role" : "family",
      description: `${names.get(relationship.source)} — ${connector.label}${connector.role && locale === "en" ? " of" : ""} — ${names.get(relationship.target)}`,
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
