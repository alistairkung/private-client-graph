import { useEffect, useMemo, useState } from "react";

type CollectionResult<T> =
  | { status: "loading" }
  | { status: "ready"; records: T[] }
  | { status: "error"; error: unknown };

export interface RecordCollection<T> {
  result: CollectionResult<T>;
  retry: () => void;
}

export function useRecordCollection<T>(
  read: () => Promise<T[]>,
  path?: string,
): RecordCollection<T> {
  const [attempt, setAttempt] = useState(0);
  const request = useMemo(() => ({ read, path, attempt }), [read, path, attempt]);
  const [resolved, setResolved] = useState<{
    request: typeof request;
    result: CollectionResult<T>;
  }>();

  // A route change rechecks shared state after intake or a proposal decision.
  useEffect(() => {
    let active = true;
    request.read().then(
      (records) => {
        if (active) setResolved({ request, result: { status: "ready", records } });
      },
      (error) => {
        if (active) setResolved({ request, result: { status: "error", error } });
      },
    );
    return () => { active = false; };
  }, [request]);

  return {
    result: resolved?.request === request
      ? resolved.result
      : { status: "loading" },
    retry: () => setAttempt((value) => value + 1),
  };
}
