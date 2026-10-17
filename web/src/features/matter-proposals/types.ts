import type { CanonicalGraph } from "../../shared/canonical-graph";
import type { CanonicalState } from "../../shared/canonical-state";

export interface MatterProposalSummary {
  id: string;
  external_reference: string;
  matter_title: string;
}

export interface MatterProposalDetail extends MatterProposalSummary {
  authoritative_source: { title: string; text: string } | null;
  state?: CanonicalState;
  proposed_graph: CanonicalGraph;
}

interface ProposalIdentity {
  external_reference: string;
  matter_title: string;
  synthetic_confirmation: boolean;
}

export interface PdfSourceInput {
  id: string;
  title: string;
  pdf: File;
}

export type ProposalInput = ProposalIdentity & (
  | { source_title: string; pdf: File; sources?: never }
  | { sources: PdfSourceInput[]; source_title?: never; pdf?: never }
);

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
