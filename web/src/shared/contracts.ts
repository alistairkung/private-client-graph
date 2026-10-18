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
  source_id?: string;
}
export interface Source {
  id: string;
  title: string;
  text: string;
}
export interface Graph {
  entities: Entity[];
  relationships: Relationship[];
  evidence: Evidence[];
}
export interface CanonicalState extends Graph {
  sources: Source[];
}
export interface MatterSummary {
  id: string;
  external_reference: string;
  title: string;
}
export interface ProposalSummary {
  id: string;
  external_reference: string;
  matter_title: string;
}
export interface ReviewRecord {
  id: string;
  external_reference: string;
  title?: string;
  matter_title?: string;
  authoritative_source: { title: string; text: string } | null;
  state?: CanonicalState;
  current_graph?: Graph;
  proposed_graph?: Graph;
}
export interface ExistingResource {
  resource_kind: "matter" | "matter_proposal";
  resource_id: string;
  location: string;
}
export interface ServiceError {
  code: string;
  message: string;
  retryable: boolean;
  outcome_unknown?: boolean;
  resets_at?: string | null;
  existing_resource?: ExistingResource;
}
export interface SourceUpload {
  id: string;
  title: string;
  pdf: File;
}
export interface IntakeInput {
  external_reference: string;
  matter_title: string;
  synthetic_confirmation: boolean;
  sources: SourceUpload[];
}
