import { useEffect } from "react";
import { MotionConfig } from "motion/react";
import { useLocale } from "../../shared/locale";
import { PublicHeader } from "../../shared/public/PublicHeader";
import { PUBLIC_RESEARCH_DOWNLOAD, usePublicResearchSnapshot } from "./api";
import { ResearchStory } from "./ResearchStory";
import { ResearchOverview } from "./ResearchOverview";
import "../../styles/global.css";
import "../../shared/public/showcase-foundations.css";
import "./public-research.css";
export function ResearchResultsApp() {
  const { t } = useLocale();
  useEffect(() => {
    document.title = `${t("Research results")} · Private Client Graph`;
  }, [t]);
  const { snapshot, status } = usePublicResearchSnapshot();
  const baseline = snapshot?.runs.find((run) => run.label === "A_prime");
  const treatment = snapshot?.runs.find((run) => run.label === "B");
  return (
    <MotionConfig reducedMotion="user"><div className="showcase-shell research-shell">
      <a className="showcase-skip" href="#research-main">
        {t("Skip to research results")}
      </a>
      <PublicHeader currentPage="research" />
      <main id="research-main" className="research-main">
        <header className="research-opening">
          <h1>{t("Research results")}</h1>
          <p>{t("What changes when the extraction stays fixed?")}</p>
        </header>
        {status === "loading" && (
          <p role="status">{t("Loading published research results…")}</p>
        )}
        {status === "unavailable" && (
          <section role="alert" className="research-unavailable">
            <h2>{t("Published results are unavailable")}</h2>
            <p>
              {t(
                "The verified publication could not be loaded. Reload this page to try again.",
              )}
            </p>
          </section>
        )}
        {snapshot && baseline && treatment && (
          <>
            <ResearchOverview snapshot={snapshot} />
            <nav
              className="research-contents"
              aria-label={t("Results sections")}
            >
              <a href="#question">{t("Research question")}</a>
              <a href="#architecture">{t("Architecture")}</a>
              <a href="#comparison">{t("Experimental results")}</a>
              <a href="#failure-analysis">{t("Failure analysis")}</a>
              <a href="#cases">{t("Cases and Evidence")}</a>
              <a href="#limitations">{t("Limitations and trade-offs")}</a>
              <a href="#usage">{t("Usage")}</a>
              <a href="#roadmap">{t("Research roadmap")}</a>
              <a href="#reproducibility">{t("Reproducibility")}</a>
            </nav>
            <ResearchStory snapshot={snapshot} />
          </>
        )}
      </main>
      <footer className="research-footer folio-width">
        <a href="/">{t("Back to Private Client Graph")}</a>
        <a href={PUBLIC_RESEARCH_DOWNLOAD} download>{t("Download results")}</a>
      </footer>
    </div></MotionConfig>
  );
}
