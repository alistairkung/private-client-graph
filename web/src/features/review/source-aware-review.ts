import type { CanonicalState, SourcedEvidence } from "../../shared/canonical-state";
import { locateEvidence } from "./graph-view";

export function evidenceSource(state: CanonicalState, evidence: SourcedEvidence) {
  const source = state.sources.find(item => item.id === evidence.source_id);
  if (!source) throw new Error("The Evidence Source could not be found. Reload the case.");
  return { source, span: locateEvidence(source.text, evidence.supporting_text) };
}
