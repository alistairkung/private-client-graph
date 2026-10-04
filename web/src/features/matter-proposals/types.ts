import type { CanonicalGraph } from "../../shared/canonical-graph";

export interface MatterProposalSummary {
  id: string;
  external_reference: string;
  matter_title: string;
}

export interface MatterProposalDetail extends MatterProposalSummary {
  authoritative_source: { title: string; text: string };
  proposed_graph: CanonicalGraph;
}

export interface ProposalInput {
  external_reference: string;
  matter_title: string;
  source_title: string;
  pdf: File;
  synthetic_confirmation: boolean;
}

export interface ExistingResource {
  resource_kind: "matter_proposal" | "matter";
  resource_id: string;
  location: string;
}

export interface ProposalError {
  code: string;
  message: string;
  retryable: boolean;
  outcome_unknown?: boolean;
  resets_at?: string | null;
  existing_resource?: ExistingResource;
}
