export type AnalysisMode = "live" | "sample";
export type RelationshipType =
  | "parent_of"
  | "spouse_of"
  | "sibling_of"
  | "settlor_of"
  | "trustee_of"
  | "beneficiary_of";
export interface Entity {
  id: string;
  type: "person" | "trust";
  name: string;
}
export interface Relationship {
  source: string;
  type: RelationshipType;
  target: string;
  evidence_ids: string[];
}
export interface Evidence {
  id: string;
  document: string;
  supporting_text: string;
}
export interface CanonicalGraph {
  entities: Entity[];
  relationships: Relationship[];
  evidence: Evidence[];
}
export interface CaseDetail {
  title: string;
  notice: string;
  source_text: string;
}
export interface CaseAnalysis {
  execution: { mode: AnalysisMode; run_artifact_id: string | null };
  graph: CanonicalGraph;
}
export interface AnalysisError {
  stage: string;
  message: string;
  retryable: boolean;
  run_artifact_id?: string | null;
}
