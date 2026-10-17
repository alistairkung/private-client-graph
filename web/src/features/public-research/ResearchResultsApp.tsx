import { useLocale } from "../../shared/locale";
import { PublicHeader } from "../../shared/public/PublicHeader";
import { PUBLIC_RESEARCH_DOWNLOAD, usePublicResearchSnapshot } from "./api";
import { CaseWorkspace } from "./CaseWorkspace";
import { Publication } from "./Publication";
import { percent, Provenance, RunComparison } from "./RunComparison";
import { Usage } from "./Usage";
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
      <main id="research-main" className="folio-width">
        <header className="research-opening">
          <h1>{t("Research results")}</h1>
          <p>
            {t(
              "A controlled comparison of constrained alias resolution on a small synthetic development benchmark.",
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
            <div className="research-headline">
              <div>
                <p>{t("Baseline replay A′ · relationship micro-F1")}</p>
                <strong>{percent(baseline.metrics.micro_f1)}*</strong>
              </div>
              <div>
                <p>{t("With resolver B · relationship micro-F1")}</p>
                <strong>{percent(treatment.metrics.micro_f1)}*</strong>
              </div>
            </div>
            <p className="research-caveat">
              {t(
                "* Small internal development benchmark. The resolver comparison was post-hoc and exploratory; two name corrections in one case accounted for the entire improvement.",
              )}
            </p>
            <p className="research-disclosure">
              {t(
                "Evaluated on ten project-authored, held-out synthetic cases used as an internal development benchmark. No real client data was used. These results do not establish production accuracy or reliability.",
              )}
            </p>
            <nav
              className="research-contents"
              aria-label={t("Results sections")}
            >
              <a href="#cases">{t("Cases and Evidence")}</a>
              <a href="#provenance">{t("Provenance")}</a>
              <a href="#usage">{t("Usage")}</a>
              <a href="#methodology">{t("Methodology and limitations")}</a>
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
            <RunComparison runs={snapshot.runs} />
            <CaseWorkspace cases={snapshot.cases} />
            <Provenance runs={snapshot.runs} />
            <Usage runs={snapshot.runs} />
            <Publication snapshot={snapshot} />
          </>
        )}
      </main>
      <footer className="research-footer folio-width">
        <a href="/">{t("Back to Private Client Graph")}</a>
      </footer>
    </div>
  );
}
