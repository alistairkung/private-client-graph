import { useLocale } from "../../shared/locale";
import { analysisFailureMessage } from "./error-presentation";
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
  const { t, locale } = useLocale();
  const available = availability.state === "available";
  const retryLive = available && error?.retryable && lastMode === "live";
  return (
    <div className="analysis-controls">
      <div className="actions">
        <button
          className="secondary"
          disabled={!!pending}
          onClick={() => onRun("sample")}
        >
          {t("Load sample analysis")}
        </button>
        <button
          className="primary"
          disabled={
            !available || !!pending || (lastMode === "live" && !!error && !error.retryable)
          }
          onClick={() => onRun("live")}
        >
          {retryLive ? t("Retry live analysis") : t("Run live analysis")}
          <span aria-hidden="true"> ↗</span>
        </button>
      </div>
      {!available && (
        <p className="live-availability">
          {availability.state === "disabled"
            ? t("Live analysis is currently disabled. Sample analysis remains available.")
            : availability.state === "exhausted"
              ? t("Live analysis is unavailable for now. Sample analysis remains available.")
              : t("Live analysis is temporarily unavailable. Sample analysis remains available.")}
          {availability.resets_at && <> {t("Try live analysis again after")} <time dateTime={availability.resets_at}>
            {new Date(availability.resets_at).toLocaleString(locale, { timeZoneName: "short" })}
          </time>. {t("Reload the page to check availability.")}</>}
        </p>
      )}
      {pending && (
        <p role="status" className="progress">
          {pending === "live"
            ? t("Running live analysis. This may take a moment…")
            : t("Loading sample analysis…")}
        </p>
      )}
      {error && (
        <div role="alert" className="error-message">
          <strong>
            {error.stage === "graph"
              ? t("Relationship validation failed")
              : t("Analysis unavailable")}
          </strong>
          <p>{t(analysisFailureMessage(error))}</p>
          {!error.retryable && (
            <p>
              {t("You can explicitly load the sample analysis to continue the demonstration.")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
