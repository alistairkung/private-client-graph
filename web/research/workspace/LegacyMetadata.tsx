import { useCallback } from "react";
import type { LegacyStudyDetail } from "../shared/contracts";
import { useRead } from "../shared/useRead";
import { ReadState } from "../shared/presentation";
import { request } from "./api";
export function LegacyMetadata({ id }: { id: string }) {
  const load = useCallback(
    (signal: AbortSignal) =>
      request<LegacyStudyDetail>(
        `/legacy/experiments/${encodeURIComponent(id)}`,
        undefined,
        undefined,
        signal,
      ),
    [id],
  );
  const { data, error, retry } = useRead(load);
  if (!data) return <ReadState error={error} retry={retry} />;
  return (
    <details className="legacy-metadata">
      <summary>{data.metadata.name}</summary>
      <p>{data.metadata.reason}</p>
      <p>
        {data.metadata.hypothesis ??
          "Hypothesis unavailable in this historical record"}
      </p>
      {data.cases.map((item) => (
        <p key={item.input_id}>
          {item.name} · {item.fixture_name}
          <small>
            {item.description ?? "Description unavailable"} · {item.case_id} ·{" "}
            {item.input_id}
          </small>
        </p>
      ))}
    </details>
  );
}
