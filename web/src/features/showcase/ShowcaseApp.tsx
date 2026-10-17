import { useLocale } from "../../shared/locale";
import { PublicHeader } from "../../shared/public/PublicHeader";
import { ResearchSummary } from "../public-research/ResearchSummary";
import "./showcase.css";
import { EvidenceChapter } from "./landing/EvidenceChapter";
import { LandingHero } from "./landing/LandingHero";
import { ShowcaseDemonstration } from "./landing/ShowcaseDemonstration";

export function ShowcaseApp() {
  const { t } = useLocale();
  return (
    <div className="showcase-shell">
      <a className="showcase-skip" href="#case-01">{t("Skip to synthetic demonstration")}</a>
      <PublicHeader />
      <main>
        <LandingHero />
        <EvidenceChapter />
        <ResearchSummary />
        <ShowcaseDemonstration />
      </main>
      <footer className="showcase-footer folio-width">
        <span>{t("Private Client Graph \u00b7 Synthetic research prototype")}</span>
        <a href="/app">{t("Practitioner application")}</a>
      </footer>
    </div>
  );
}
