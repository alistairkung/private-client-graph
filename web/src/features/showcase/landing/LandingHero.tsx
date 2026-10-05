import sourcePaper from "./assets/source-paper.png";
import "./hero.css";

export function LandingHero() {
  return (
    <section className="folio-hero folio-width" aria-labelledby="landing-title">
      <h1 id="landing-title">The story is<br />in the source.</h1>
      <SourceExcerpt />
      <EditorialRelationship />
      <div className="folio-invitation">
        <p>Follow a connection<br className="folio-desktop-break" /> back to the exact words<br className="folio-desktop-break" /> that support it.</p>
        <a className="folio-button" href="#case-01">
          Explore Case 01
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M4 12h16m-6-6 6 6-6 6" />
          </svg>
        </a>
      </div>
    </section>
  );
}

function SourceExcerpt() {
  return (
    <figure className="folio-source">
      <img className="folio-paper" src={sourcePaper} alt="" fetchPriority="high" />
      <figcaption>
        <span className="folio-source-title">Attendance note</span>
        <span>Case 01 · Synthetic source excerpt</span>
      </figcaption>
      <blockquote>
        <span className="folio-highlight">Alice Chen confirmed that Bob Chen is a beneficiary of the Evergreen Family Trust.</span>
      </blockquote>
      <div className="folio-source-lines" aria-hidden="true">
        <span /><span /><span /><span />
      </div>
    </figure>
  );
}

// Fixed editorial notation, independent of graph data and review controls.
function EditorialRelationship() {
  return (
    <figure className="folio-relationship" aria-label="Illustration: Bob Chen is a beneficiary of the Evergreen Family Trust">
      <div aria-hidden="true" className="folio-relationship-content">
        <span className="folio-annotation">Person</span>
        <span className="folio-person-stem" />
        <div className="folio-person">
          <svg viewBox="0 0 32 36" width="32" height="36">
            <circle cx="16" cy="10" r="6" />
            <path d="M5 31v-4a11 11 0 0 1 22 0v4Z" />
          </svg>
        </div>
        <span className="folio-person-name">Bob Chen</span>
        <div className="folio-role"><span>Beneficiary of</span></div>
        <div className="folio-trust">
          <svg viewBox="0 0 200 142" preserveAspectRatio="none">
            <path d="M100 2 198 140H2Z" />
          </svg>
          <span>Evergreen<br />Family Trust</span>
        </div>
        <span className="folio-annotation">Trust</span>
      </div>
    </figure>
  );
}
