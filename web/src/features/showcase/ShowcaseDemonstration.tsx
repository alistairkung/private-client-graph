import { useState } from "react";
import { AnalysisControls } from "./AnalysisControls";
import { ReviewWorkspace } from "../review/ReviewWorkspace";
import { SourcePanel } from "../review/SourcePanel";
import { useCaseAnalysis } from "./useCaseAnalysis";

export function ShowcaseDemonstration() {
  const [expanded, setExpanded] = useState(false);
  const { detail, sourceError, analysis, pending, error, lastMode, run } =
    useCaseAnalysis();
  return (
    <section
      id="demonstration"
      tabIndex={-1}
      className={`demonstration${expanded ? " demonstration-expanded" : ""}`}
      aria-labelledby="demonstration-title"
    >
      <div className="demonstration-heading">
        <div>
          <h2 id="demonstration-title">Choose a relationship. Read what supports it.</h2>
          <p>Load the Evergreen sample, then choose any relationship to follow its Evidence into the attendance note.</p>
          <p className="prototype-notice">Synthetic research prototype. Do not use real client information.</p>
        </div>
        <button aria-expanded={expanded} aria-controls="demonstration-review"
          onClick={() => setExpanded((value) => !value)}>
          {expanded ? "Collapse demonstration" : "Expand demonstration"}
        </button>
      </div>
      <div id="demonstration-review">
        {sourceError ? (
          <div className="load-state">
            <p role="alert">{sourceError}</p>
            <button onClick={() => window.location.reload()}>Reload case</button>
          </div>
        ) : !detail ? (
          <p role="status" className="load-state">Loading the synthetic case…</p>
        ) : (
          <>
            <AnalysisControls availability={detail.live_analysis} pending={pending}
              error={error} lastMode={lastMode} onRun={run} />
            <div className="workspace-bar">
              <span>
                {analysis ? "Review workspace" : "Start with the source"}
              </span>
              <span
                className={
                  analysis?.execution.mode === "sample" ? "mode sample" : "mode"
                }
              >
                {analysis
                  ? analysis.execution.mode === "live"
                    ? "Live analysis · Newly extracted"
                    : "Sample analysis · Demonstration fixture"
                  : "Load an analysis to reveal the relationships"}
              </span>
            </div>
            {analysis ? (
              <ReviewWorkspace
                embedded
                source={detail.source_text}
                graph={analysis.graph}
              />
            ) : (
              <div className="initial-source">
                <SourcePanel source={detail.source_text} />
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
