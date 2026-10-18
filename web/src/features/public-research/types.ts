import type { Entity, RelationshipType } from "../../shared/canonical-graph";
export type RunLabel = "A" | "A_prime" | "B";
export interface PublicSource {
  id: string;
  title: string;
  text: string;
}
export interface PublicEntity {
  id: string;
  type: Entity["type"];
  name: string;
}
export interface PublicRelationship {
  source: string;
  type: RelationshipType;
  target: string;
  evidence_ids: string[];
}
export interface PublicCall {
  attempt_id: string;
  run_id: string;
  case_id: string;
  stage: "extraction" | "resolution";
  model: string | null;
  status: string;
  input_tokens: number | null;
  output_tokens: number | null;
  cached_tokens: number | null;
  provider_seconds: number | null;
  cost: number | null;
  currency: string;
}
export interface PublicRun {
  label: RunLabel;
  run_id: string;
  git_commit: string;
  plan_digest: string;
  artifact_digest: string;
  metrics: {
    tp: number;
    fp: number;
    fn: number;
    micro_precision: number;
    micro_recall: number;
    micro_f1: number;
    macro_f1: number;
    quote_passed: number;
    quote_assessed: number;
    quote_accuracy: number;
    source_pair_passed: number;
    source_pair_assessed: number;
    source_pair_accuracy: number;
  };
  coverage: {
    planned: number;
    scored: number;
    pending: number;
    failed: number;
    uncertain: number;
    unavailable: number;
  };
  usage: {
    attempts: number;
    input_tokens: number | null;
    output_tokens: number | null;
    cached_tokens: number | null;
    total_tokens: number | null;
    provider_seconds: number | null;
    cost: number | null;
    currency: string;
    unpriced_attempts: number;
  };
  calls: PublicCall[];
}
export interface PublicQuote {
  id: string;
  source_id: string;
  text: string;
  occurrences: number[][];
}
export interface PublicOutcome {
  id: string;
  edge: string[];
  outcome:
    | "matched"
    | "missing"
    | "extra"
    | "provenance_failure"
    | "source_attribution_failure";
  expected: PublicQuote[];
  predicted: PublicQuote[];
}
export interface PublicObservation {
  relationships: PublicOutcome[];
  run_label: RunLabel;
  observation_id: string;
  sample_id: string;
  status: string;
  state: {
    sources: PublicSource[];
    entities: PublicEntity[];
    relationships: PublicRelationship[];
    evidence: {
      id: string;
      document: string;
      supporting_text: string;
      source_id: string;
    }[];
  };
  evaluation: {
    tp: number;
    fp: number;
    fn: number;
    precision: number;
    recall: number;
    f1: number;
    true_positive_edges: string[][];
    false_positive_edges: string[][];
    false_negative_edges: string[][];
    provenance_passed: number;
    provenance_failed: number;
    provenance_accuracy: number;
    provenance_passes: string[][];
    provenance_failures: string[][];
  };
  source_attribution: {
    version: number;
    assessed: number;
    passed: number;
    failed: number;
    accuracy: number;
    failures: {
      edge: string[];
      evidence_id: string;
      source_id: string;
      supporting_text: string;
    }[];
  };
  edits: {
    outcome_id: string;
    candidate_index: number;
    endpoint: "source_name" | "target_name";
    original_name: string;
    resolved_name: string;
    relationship_type: string;
    other_endpoint: string;
    source_id: string;
    supporting_text: string;
  }[];
}
export interface PublicCase {
  case_id: string;
  name: string;
  description: string;
  sources: PublicSource[];
  truth: {
    entities: PublicEntity[];
    relationships: {
      source: string;
      type: string;
      target: string;
      approved_evidence: string[];
    }[];
  };
  source_evidence: {
    schema_version: number;
    relationships: {
      source: string;
      type: string;
      target: string;
      approved_evidence: { source_id: string; supporting_text: string }[];
    }[];
  };
  observations: PublicObservation[];
}
export interface PublicResearchSnapshot {
  schema_version: number;
  snapshot_id: string;
  experiment_id: string;
  integrity: { algorithm: string; digest: string; scope: string };
  benchmark: {
    case_count: number;
    source_count: number;
    expected_relationships: number;
  };
  pairing: { control_equivalent: boolean; frozen_inputs_verified: boolean };
  runs: PublicRun[];
  cases: PublicCase[];
}
