import "./showcase.css";
import { EvidenceChapter } from "./landing/EvidenceChapter";
import { LandingHero } from "./landing/LandingHero";
import { ShowcaseDemonstration } from "./landing/ShowcaseDemonstration";
import { BrandMark } from "../../shared/brand/BrandMark";

export function ShowcaseApp() {
  return (
    <div className="showcase-shell">
      <a className="showcase-skip" href="#case-01">Skip to Case 01 demonstration</a>
      <header className="showcase-header folio-width">
        <a className="showcase-brand" href="/"><BrandMark />Private Client Graph</a>
        <nav aria-label="Public showcase">
          <a href="#approach">The approach</a>
          <a href="#case-01">Explore Case 01</a>
        </nav>
        <span className="showcase-notice">Synthetic research prototype</span>
      </header>
      <main>
        <LandingHero />
        <EvidenceChapter />
        <ShowcaseDemonstration />
      </main>
      <footer className="showcase-footer folio-width">
        <span>Private Client Graph · Synthetic research prototype</span>
        <a href="/app">Practitioner application</a>
      </footer>
    </div>
  );
}
