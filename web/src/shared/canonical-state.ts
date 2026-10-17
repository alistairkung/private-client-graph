import type { Entity, Evidence, Relationship } from "./canonical-graph";

export interface Source {
  id: string;
  title: string;
  text: string;
}

export interface SourcedEvidence extends Evidence {
  source_id: string;
}

export interface CanonicalState {
  sources: Source[];
  entities: Entity[];
  relationships: Relationship[];
  evidence: SourcedEvidence[];
}
