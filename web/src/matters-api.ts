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
