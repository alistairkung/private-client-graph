import "./showcase.css";
import { LandingOpening } from "./LandingOpening";
import { ShowcaseDemonstration } from "./ShowcaseDemonstration";
import { EvaluationChapter } from "./EvaluationChapter";
import { ProfessionalJudgment } from "./ProfessionalJudgment";

export function ShowcaseApp() {
  return (
    <div className="showcase-shell">
      <div className="showcase-width">
        <header className="showcase-masthead">
          <a href="/" className="showcase-brand">Private Client Graph</a>
          <nav className="showcase-navigation" aria-label="Public navigation">
            <a href="#demonstration">Demonstration</a>
            <a href="#evaluation">Evaluation</a>
            <a href="/app">Practitioner application</a>
          </nav>
        </header>
        <main>
          <LandingOpening />
          <ShowcaseDemonstration />
          <ProfessionalJudgment />
          <EvaluationChapter />
        </main>
        <footer className="showcase-closing">
          <div>
            <h2>Follow the source for yourself.</h2>
            <div className="closing-routes">
              <a className="showcase-action" href="#demonstration">Explore the demonstration</a>
              <a href="/app">Open practitioner prototype</a>
            </div>
            <p className="prototype-notice">Synthetic research prototype. Do not use real client information.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
