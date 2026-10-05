import { locateEvidence } from "../review/graph-view";
import type { ReviewSelection } from "../review/ReviewWorkspace";
import type { RelationshipType } from "../../shared/canonical-graph";
import type { CaseAnalysis } from "./types";

// Editorial attention targets, resolved against the returned graph, never source prose.
export const sampleMoments: { title: string; passages: {
  source: string; type: RelationshipType; target: string; explanation: string;
}[] }[] = [
  {
    title: "Alice’s connection to the Trust",
    passages: [{
      source: "Alice Chen", type: "settlor_of", target: "Evergreen Family Trust",
      explanation: "Alice confirms that she is the settlor of the Evergreen Family Trust. That statement supports her settlor relationship.",
    }],
  },
  {
    title: "The family relationships",
    passages: [
      {
        source: "Alice Chen", type: "spouse_of", target: "David Chen",
        explanation: "Alice confirms that she and David are spouses. The family passage supports their spouse relationship.",
      },
      {
        source: "Alice Chen", type: "parent_of", target: "Bob Chen",
        explanation: "The next statement identifies Alice and David as Bob’s parents. It supports Alice’s parent relationship to Bob…",
      },
      {
        source: "David Chen", type: "parent_of", target: "Bob Chen",
        explanation: "…and David’s parent relationship to Bob. The same Evidence supports both relationships. Neither establishes Bob’s beneficiary role.",
      },
    ],
  },
  {
    title: "Separate beneficiary roles",
    passages: [
      {
        source: "Bob Chen", type: "beneficiary_of", target: "Evergreen Family Trust",
        explanation: "A separate confirmation names Bob as a beneficiary of the Evergreen Family Trust. His beneficiary role comes from this passage, not from his family relationships.",
      },
      {
        source: "Carol Wong", type: "beneficiary_of", target: "Evergreen Family Trust",
        explanation: "Carol is also named as a beneficiary. That establishes her Trust role; it establishes no family connection to Alice, David or Bob.",
      },
    ],
  },
];

export interface SamplePassage extends ReviewSelection {
  quote: string;
}

export function resolveSamplePassages(analysis: CaseAnalysis, source: string): SamplePassage[] | undefined {
  if (analysis.execution.mode !== "sample") return;
  const { graph } = analysis;
  const targets = sampleMoments.flatMap((moment) => moment.passages);
  if (graph.relationships.length !== targets.length) return;
  const passages: SamplePassage[] = [];
  for (const target of targets) {
    const matches = graph.relationships.flatMap((relationship, relationshipIndex) => {
      const from = graph.entities.find((entity) => entity.id === relationship.source);
      const to = graph.entities.find((entity) => entity.id === relationship.target);
      return from?.name === target.source && from.type === "person"
        && to?.name === target.target && to.type === (target.target === "Evergreen Family Trust" ? "trust" : "person")
        && relationship.type === target.type ? [relationshipIndex] : [];
    });
    if (matches.length !== 1) return;
    const relationshipIndex = matches[0];
    const evidence = graph.evidence.find((item) => item.id === graph.relationships[relationshipIndex].evidence_ids[0]);
    if (!evidence) return;
    try {
      locateEvidence(source, evidence.supporting_text);
    } catch {
      return;
    }
    passages.push({ relationshipIndex, evidenceId: evidence.id, quote: evidence.supporting_text });
  }
  return passages;
}
