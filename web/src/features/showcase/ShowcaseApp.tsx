import { useLocale } from "../../shared/locale";
import { LanguageControl } from "../../shared/LanguageControl";
import "./showcase.css";
import { EvidenceChapter } from "./landing/EvidenceChapter";
import { LandingHero } from "./landing/LandingHero";
import { ShowcaseDemonstration } from "./landing/ShowcaseDemonstration";
import { BrandMark } from "../../shared/brand/BrandMark";

export function ShowcaseApp() {
 const {t}=useLocale();
  return (
    <div className="showcase-shell">
      <a className="showcase-skip" href="#case-01">{t("Skip to synthetic demonstration")}</a>
      <header className="showcase-header folio-width">
        <a className="showcase-brand" href="/"><BrandMark />Private Client Graph</a>
        <nav aria-label={t("Public showcase")}>
          <a href="#approach">{t("The approach")}</a>
          <a href="#case-01">{t("Explore cases")}</a>
        <a href="/demo">{t("Demo application")}</a>
        </nav>
        <LanguageControl />
        <span className="showcase-notice">{t("Synthetic research prototype")}</span>
      </header>
      <main>
        <LandingHero />
        <EvidenceChapter />
        <ShowcaseDemonstration />
      </main>
      <footer className="showcase-footer folio-width">
        <span>{t("Private Client Graph \u00b7 Synthetic research prototype")}</span>
        <a href="/app">{t("Practitioner application")}</a>
      </footer>
    </div>
  );
}
