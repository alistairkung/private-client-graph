import type { AnalysisError, AnalysisMode } from "./types";

export function AnalysisControls({
  pending,
  error,
  lastMode,
  onRun,
}: {
  pending?: AnalysisMode;
  error?: AnalysisError;
  lastMode?: AnalysisMode;
  onRun: (mode: AnalysisMode) => void;
}) {
  const retryLive = error?.retryable && lastMode === "live";
  return (
    <div className="analysis-controls">
      <div className="actions">
        <button
          className="primary"
          disabled={
            !!pending || (lastMode === "live" && !!error && !error.retryable)
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
