export const number = (value: number | null | undefined, places = 3) =>
  value == null ? "Unavailable" : value.toFixed(places);
export const mode = (kind: string | null) =>
  kind === "live_experiment"
    ? "Live experiment"
    : kind === "replay"
      ? "Saved replay"
      : kind === "demonstration"
        ? "Recorded demonstration"
        : kind === "task_b_pilot"
          ? "Development pilot"
          : kind === "task_a_diagnostic"
            ? "Development diagnostic"
            : "Unavailable";
export const configuration = (value: string) =>
  value === "noop"
    ? "Baseline · No resolution"
    : "Treatment · Generative resolution";

export function ReadState({
  error,
  retry,
}: {
  error?: string;
  retry: () => void;
}) {
  return error ? (
    <section role="alert">
      <h2>Unable to read research results</h2>
      <p>{error}</p>
      <button onClick={retry}>Retry read</button>
    </section>
  ) : (
    <p role="status">Reading retained research artifacts…</p>
  );
}
export function RecordedDetails({
  title,
  value,
}: {
  title: string;
  value: unknown;
}) {
  return (
    <details>
      <summary>{title}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
