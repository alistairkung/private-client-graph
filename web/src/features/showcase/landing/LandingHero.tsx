import { useLocale } from "../../../shared/locale";
import sourcePaper from "./assets/source-paper.png";
import "./hero.css";

export function LandingHero() {
  const { t } = useLocale();
  return (
    <section className="folio-hero folio-width" aria-labelledby="landing-title">
      <h1 id="landing-title">{t("The story is")}<br />{t("in the source.")}</h1>
      <SourceExcerpt />
      <EditorialRelationship />
      <div className="folio-invitation">
        <p>{t("Follow a connection")}<br className="folio-desktop-break" />{t("back to the exact words")}<br className="folio-desktop-break" />{t("that support it.")}</p>
        <a className="folio-button" href="#case-01">
          {t("Explore cases")}
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M4 12h16m-6-6 6 6-6 6" />
          </svg>
        </a>
      </div>
    </section>
  );
}

function SourceExcerpt() {
  const { t } = useLocale();
  return (
    <figure className="folio-source">
      <img className="folio-paper" src={sourcePaper} alt="" fetchPriority="high" />
      <figcaption>
        <span className="folio-source-title">{t("Attendance note")}</span>
        <span>{t("Case 01 · Synthetic source excerpt")}</span>
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
  const { t } = useLocale();
  return (
    <figure className="folio-relationship" aria-label={t("Illustration: Bob Chen is a beneficiary of the Evergreen Family Trust")}>
      <div aria-hidden="true" className="folio-relationship-content">
        <span className="folio-annotation">{t("Person")}</span>
        <span className="folio-person-stem" />
        <div className="folio-person">
          <svg viewBox="0 0 32 36" width="32" height="36">
            <circle cx="16" cy="10" r="6" />
            <path d="M5 31v-4a11 11 0 0 1 22 0v4Z" />
          </svg>
        </div>
        <span className="folio-person-name">Bob Chen</span>
        <div className="folio-role"><span>{t("Beneficiary of")}</span></div>
        <div className="folio-trust">
          <svg viewBox="0 0 200 142" preserveAspectRatio="none">
            <path d="M100 2 198 140H2Z" />
          </svg>
          <span>Evergreen<br />Family Trust</span>
        </div>
        <span className="folio-annotation">{t("Trust")}</span>
      </div>
    </figure>
  );
}
