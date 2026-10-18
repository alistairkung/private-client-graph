import { useEffect, useState } from "react";
import { requestJson } from "../../shared/json-request";
import type { PublicResearchSnapshot } from "./types";
export const PUBLIC_RESEARCH_DOWNLOAD = "/api/research-results/download";
export async function getPublicResearchSnapshot(): Promise<PublicResearchSnapshot> {
  const snapshot = await requestJson<PublicResearchSnapshot>(
    "/api/research-results",
  );
  if (
    snapshot?.schema_version !== 1 ||
    !Array.isArray(snapshot.runs) ||
    !Array.isArray(snapshot.cases)
  ) {
    throw new Error("Unsupported published research artifact");
  }
  return snapshot;
}
export function usePublicResearchSnapshot() {
  const [snapshot, setSnapshot] = useState<PublicResearchSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "unavailable">(
    "loading",
  );
  useEffect(() => {
    let active = true;
    getPublicResearchSnapshot()
      .then((value) => {
        if (active) {
          setSnapshot(value);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (active) setStatus("unavailable");
      });
    return () => {
      active = false;
    };
  }, []);
  return { snapshot, status };
}
