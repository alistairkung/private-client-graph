import type { CanonicalGraph } from "./types";

export interface MatterSummary {
  id: string;
  external_reference: string;
  title: string;
}

export async function getMatters(): Promise<MatterSummary[]> {
  const response = await fetch("/api/matters");
  if (!response.ok) throw new Error("Matters could not be loaded.");
  return response.json() as Promise<MatterSummary[]>;
}


export interface MatterDetail extends MatterSummary {
  authoritative_source: { title: string; text: string };
  current_graph: CanonicalGraph;
}

export async function getMatter(id: string): Promise<MatterDetail | null> {
  const response = await fetch(`/api/matters/${encodeURIComponent(id)}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Matter could not be loaded.");
  return response.json() as Promise<MatterDetail>;
}
