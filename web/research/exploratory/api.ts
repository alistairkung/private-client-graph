import type { Source } from "../shared/contracts";

export interface ExploratoryManifest {
  workload_id: string;
  workload_kind: "exploratory_scale";
  qualification: "unqualified";
  read_only: true;
  scored: false;
  source_count: 65;
  source_file_sha256: string;
}

interface ExploratoryWorkload {
  manifest: ExploratoryManifest;
  sources: Source[];
}

const path = "/api/research/v1/exploratory-workload";

export async function exploratoryManifest(signal: AbortSignal) {
  const response = await fetch(path, { signal });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("The exploratory workload is unavailable.");
  return (await response.json()) as ExploratoryManifest;
}

export async function exploratorySources(signal: AbortSignal) {
  const response = await fetch(`${path}/sources`, { signal });
  if (!response.ok)
    throw new Error("The released exploratory Sources could not be loaded.");
  return (await response.json()) as ExploratoryWorkload;
}

export interface ConsensusRelationship {
  source: string;
  predicate: string;
  target: string;
  counts: { support: number; reject: number; uncertain: number; omitted: number };
  evidence_decision: "supported" | "unresolved" | "below_majority";
  evidence_reason: string | null;
  routes: { approved: boolean; members: { source_id: string; quote: string }[] }[];
}

export interface ConsensusReference {
  cutoff: string;
  reviewer_count: 10;
  majority: 6;
  relationships: ConsensusRelationship[];
  limitations: string[];
  reviewer_open_questions: string[];
}

export async function exploratoryReference(signal: AbortSignal) {
  const response = await fetch(`${path}/reference`, { signal });
  if (response.status === 404) return null;
  if (!response.ok)
    throw new Error("The frozen exploratory consensus reference could not be verified.");
  return (await response.json()) as ConsensusReference;
}
