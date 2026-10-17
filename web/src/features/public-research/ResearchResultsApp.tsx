import { useLocale } from "../../shared/locale";
import { PublicHeader } from "../../shared/public/PublicHeader";
import { PUBLIC_RESEARCH_DOWNLOAD, usePublicResearchSnapshot } from "./api";
import { ResearchStory } from "./ResearchStory";
import "./public-research.css";
export function ResearchResultsApp() {
  const { t } = useLocale();
  const { snapshot, status } = usePublicResearchSnapshot();
  const baseline = snapshot?.runs.find((run) => run.label === "A_prime");
  const treatment = snapshot?.runs.find((run) => run.label === "B");
  return (
    <div className="showcase-shell research-shell">
      <a className="showcase-skip" href="#research-main">
        {t("Skip to research results")}
      </a>
      <PublicHeader />
      <main id="research-main" className="research-main">
        <header className="research-opening">
          <h1>{t("Research results")}</h1>
          <p>
            {t(
              "A full-context baseline. The same frozen extractions, with entity resolution. A narrow improvement we can trace to the original words.",
            )}
          </p>
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
            <p className="research-disclosure">
              {t(
                "Evaluated on ten project-authored, held-out synthetic cases used as an internal development benchmark. No real client data was used. These results do not establish production accuracy or reliability.",
              )}
            </p>
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
              <a href="#reproducibility">{t("Reproducibility")}</a>
              <a href={PUBLIC_RESEARCH_DOWNLOAD} download>
                {t("Download results")}
              </a>
            </nav>
            <p>
              {t(
                "{cases} cases · {sources} Sources · {relationships} expected relationships",
                {
                  cases: snapshot.benchmark.case_count,
                  sources: snapshot.benchmark.source_count,
                  relationships: snapshot.benchmark.expected_relationships,
                },
              )}
            </p>
            <ResearchStory snapshot={snapshot} />
          </>
        )}
      </main>
      <footer className="research-footer folio-width">
        <a href="/">{t("Back to Private Client Graph")}</a>
      </footer>
    </div>
  );
}
