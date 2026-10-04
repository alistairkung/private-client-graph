import { AnalysisControls } from "./AnalysisControls";
import { ReviewWorkspace } from "./ReviewWorkspace";
import { SourcePanel } from "./SourcePanel";
import { useCaseAnalysis } from "./useCaseAnalysis";

export function ShowcaseApp() {
  const { detail, sourceError, analysis, pending, error, lastMode, run } =
    useCaseAnalysis();
  return (
    <main>
      <header className="masthead">
        <a href="/" className="brand">
          <span className="brand-symbol" aria-hidden="true">
            ⌘
          </span>{" "}
          Private Client Graph
        </a>
        <div className="showcase-navigation">
          <span className="masthead-note">PUBLIC SYNTHETIC SHOWCASE</span>
          <a href="/app">Practitioner application</a>
        </div>
      </header>
      {sourceError ? (
        <section className="load-state">
          <p role="alert">{sourceError}</p>
          <button onClick={() => window.location.reload()}>Reload case</button>
        </section>
      ) : !detail ? (
        <p role="status" className="load-state">
          Loading the synthetic case…
        </p>
      ) : (
        <>
          <section className="case-heading">
            <div>
              <p className="eyebrow">CASE 01 / FAMILY & TRUST RELATIONSHIPS</p>
              <h1>
                Every relationship.
                <br />
                <em>Back to its source.</em>
              </h1>
              <p className="intro">
                Review the people and trust connections in an attendance note,
                with the original evidence always in view.
              </p>
            </div>
            <div className="case-summary">
              <span className="synthetic-badge">SYNTHETIC CASE</span>
              <h2>{detail.title}</h2>
              <p>{detail.notice}</p>
              <AnalysisControls
                pending={pending}
                error={error}
                lastMode={lastMode}
                onRun={run}
              />
            </div>
          </section>
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
                : "Choose an analysis above to reveal the relationships"}
            </span>
          </div>
          {analysis ? (
            <ReviewWorkspace
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
      <footer>
        Private Client Graph{" "}
        <span>Read-only review · Synthetic material only</span>
      </footer>
    </main>
  );
}
