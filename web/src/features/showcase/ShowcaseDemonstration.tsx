import { useState } from "react";
import { AnalysisControls } from "./AnalysisControls";
import { SourcePanel } from "../review/SourcePanel";
import { useCaseAnalysis } from "./useCaseAnalysis";
import { SampleStory, SampleWalkthrough } from "./SampleWalkthrough";

export function ShowcaseDemonstration() {
  const [expanded, setExpanded] = useState(false);
  const [skipRequested, setSkipRequested] = useState(false);
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
          <h2 id="demonstration-title">Follow the source.</h2>
          <p>A guided Case 01 sample walkthrough: follow the settlor, family and beneficiary passages through the complete Evergreen graph.</p>
          <p>Load sample analysis to follow the supplied Evidence. Choose a relationship at any time to take control.</p>
          <a href="#interactive-demonstration" onClick={() => setSkipRequested(true)}>Skip to interactive demonstration</a>
          <p className="prototype-notice">Synthetic research prototype. Do not use real client information.</p>
        </div>
        <button aria-expanded={expanded} aria-controls="demonstration-review"
          onClick={() => setExpanded((value) => !value)}>
          {expanded ? "Collapse demonstration" : "Expand demonstration"}
        </button>
      </div>
      <div id="demonstration-review">
        {/* Keep the skip target mounted so source loading does not discard keyboard focus. */}
        <div id={analysis ? undefined : "interactive-demonstration"}
          tabIndex={analysis ? undefined : -1}>
          {sourceError ? (
            <div className="load-state">
              <p role="alert">{sourceError}</p>
              <button onClick={() => window.location.reload()}>Reload case</button>
            </div>
          ) : !detail ? (
            <p role="status" className="load-state">Loading the synthetic case…</p>
          ) : (
            <AnalysisControls availability={detail.live_analysis} pending={pending}
              error={error} lastMode={lastMode} onRun={run} />
          )}
        </div>
        {!analysis && <SampleStory />}
        {detail && !sourceError && (
          <>
            {analysis ? (
              <SampleWalkthrough source={detail.source_text} analysis={analysis}
                expanded={expanded} skipRequested={skipRequested} />
            ) : (
              <div className="initial-source">
                <SourcePanel source={detail.source_text} scrollWithinPanel />
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
