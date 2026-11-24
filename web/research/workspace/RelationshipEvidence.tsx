import { EvidenceInspector } from "../results/EvidenceInspector";
import type { RunObservation } from "../shared/contracts";
import { edgeKey } from "./benchmarkEdges";

export function RelationshipEvidence({ observation, edge, onBack }: {
  observation: RunObservation;
  edge: [string, string, string];
  onBack: () => void;
}) {
  const key = edgeKey(...edge);
  const relationship = observation.relationships.find(row => edgeKey(...row.edge) === key);
  return <EvidenceInspector relationship={relationship} sources={observation.sources}
    source={observation.source} onBack={onBack} />;
}
