import type { AnalysisError, AnalysisMode, LiveAvailability } from "./types";

export function AnalysisControls({
  availability,
  pending,
  error,
  lastMode,
  onRun,
}: {
  availability: LiveAvailability;
  pending?: AnalysisMode;
  error?: AnalysisError;
  lastMode?: AnalysisMode;
  onRun: (mode: AnalysisMode) => void;
}) {
  const available = availability.state === "available";
  const retryLive = available && error?.retryable && lastMode === "live";
  return (
    <div className="analysis-controls">
      <div className="actions">
        <button
          className="primary"
          disabled={
            !available || !!pending || (lastMode === "live" && !!error && !error.retryable)
          }
          onClick={() => onRun("live")}
        >
          {retryLive ? "Retry live analysis" : "Run live analysis"}
          <span aria-hidden="true"> ↗</span>
        </button>
        <button
          className="secondary"
          disabled={!!pending}
          onClick={() => onRun("sample")}
        >
          Load sample analysis
        </button>
      </div>
      {!available && (
        <p className="live-availability">
          {availability.state === "disabled"
            ? "Live analysis is currently disabled. Sample analysis remains available."
            : availability.state === "exhausted"
              ? "Live analysis is unavailable for now. Sample analysis remains available."
              : "Live analysis is temporarily unavailable. Sample analysis remains available."}
          {availability.resets_at && <> Try live analysis again after <time dateTime={availability.resets_at}>
            {new Date(availability.resets_at).toLocaleString(undefined, { timeZoneName: "short" })}
          </time>. Reload the page to check availability.</>}
        </p>
      )}
      {pending && (
        <p role="status" className="progress">
          {pending === "live"
            ? "Running live analysis. This may take a moment…"
            : "Loading sample analysis…"}
        </p>
      )}
      {error && (
        <div role="alert" className="error-message">
          <strong>
            {error.stage === "graph"
              ? "Relationship validation failed"
              : "Analysis unavailable"}
          </strong>
          <p>{error.message}</p>
          {!error.retryable && (
            <p>
              You can explicitly load the sample analysis to continue the
              demonstration.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
