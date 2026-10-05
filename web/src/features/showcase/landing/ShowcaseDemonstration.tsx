import { ReviewWorkspace } from "../../review/ReviewWorkspace";
import { SourcePanel } from "../../review/SourcePanel";
import { AnalysisControls } from "../AnalysisControls";
import { useCaseAnalysis } from "../useCaseAnalysis";
import "./demonstration.css";

export function ShowcaseDemonstration() {
  const { detail, sourceError, analysis, pending, error, lastMode, run } = useCaseAnalysis();

  return (
    <section id="case-01" tabIndex={-1} className="demonstration folio-width" aria-labelledby="demonstration-title">
      <div className="demonstration-caption">
        <h2 id="demonstration-title">See it in context.</h2>
        <p className="demonstration-case">{detail?.title ?? "Case 01 · Evergreen Family Trust"}</p>
        <p>Explore the relationship, read the source, and see the exact Evidence that supports it.</p>
        <span className="synthetic-badge">SYNTHETIC CASE</span>
        {detail && <AnalysisControls
          availability={detail.live_analysis}
          pending={pending}
          error={error}
          lastMode={lastMode}
          onRun={run}
        />}
      </div>
      <div className="demonstration-stage">
        <div className="demonstration-frame" aria-busy={!!pending}>
          {sourceError ? (
            <div className="demonstration-load">
              <p role="alert">{sourceError}</p>
              <button onClick={() => window.location.reload()}>Reload case</button>
            </div>
          ) : !detail ? (
            <p role="status" className="demonstration-load">Loading the synthetic case…</p>
          ) : analysis ? (
            <ReviewWorkspace source={detail.source_text} graph={analysis.graph} />
          ) : (
            <SourcePanel source={detail.source_text} />
          )}
        </div>
        <p className="demonstration-mode">
          {analysis
            ? analysis.execution.mode === "live"
              ? "Live analysis · Newly extracted"
              : "Sample analysis · Demonstration fixture"
            : "Read-only synthetic source · Choose an analysis to reveal the relationships"}
        </p>
      </div>
    </section>
  );
}
