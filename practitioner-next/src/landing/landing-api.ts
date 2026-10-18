import type { CanonicalState } from "../shared/contracts";
export interface PublicExample {
  id: string;
  title: string;
  notice: string;
  result_kind: "curated_ideal_fixture";
  state: CanonicalState;
}
export async function getPublicExample(
  signal: AbortSignal,
): Promise<PublicExample> {
  const response = await fetch("/api/showcase/cases/case-01", {
    signal,
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Example unavailable");
  const result: PublicExample = await response.json();
  if (
    result.result_kind !== "curated_ideal_fixture" ||
    !result.state ||
    ![
      result.state.entities,
      result.state.relationships,
      result.state.evidence,
      result.state.sources,
    ].every(Array.isArray)
  )
    throw new Error("Example unavailable");
  return result;
}
export function publicDestination(path: "/demo" | "/research-results") {
  return new URL(
    path,
    import.meta.env.VITE_PCG_SHOWCASE_URL ?? "https://localhost:8443/",
  ).href;
}
