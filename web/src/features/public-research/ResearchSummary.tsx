import { useLocale } from "../../shared/locale";
import { usePublicResearchSnapshot } from "./api";
import { percent } from "./RunComparison";
import "./research-summary.css";

export function ResearchSummary() {
  const { t } = useLocale();
  const { snapshot, status } = usePublicResearchSnapshot();
  const baseline = snapshot?.runs.find(run => run.label === "A");
  const resolver = snapshot?.runs.find(run => run.label === "B");
  const ready = status === "ready" && snapshot && baseline && resolver;
  return <section id="research-summary" className="research-summary" aria-labelledby="research-summary-title">
    <div className="folio-width">
      <header className="research-summary-opening">
        <h2 id="research-summary-title">{t("We didn’t just build it. We measured it.")}</h2>
        <p>{t("From extraction to a measured graph.")}</p>
      </header>
      {ready ? <>
        <dl className="research-summary-metrics">
          <div><dt>{t("Naive full-context baseline")}</dt><dd>{percent(baseline.metrics.micro_f1)}<span aria-label={t("See benchmark limitations")}>*</span></dd><p>{t("Relationship micro-F1")} · A</p></div>
          <div><dt>{t("With generative entity resolution")}</dt><dd>{percent(resolver.metrics.micro_f1)}<span aria-label={t("See benchmark limitations")}>*</span></dd><p>{t("Relationship micro-F1")} · B</p></div>
        </dl>
        <div className="research-summary-conclusion">
          <p className="research-summary-insight">{t("Two canonical-name corrections. No observed relationship regressions.")}</p>
          <div className="research-summary-reading">
            <p>{t("{cases} held-out cases · {relationships} expected relationships", { cases: snapshot.benchmark.case_count, relationships: snapshot.benchmark.expected_relationships })}</p>
            <p className="research-summary-caveat">{t("* Small internal development benchmark. The resolver comparison was post-hoc and exploratory; two name corrections in one case accounted for the entire improvement.")}</p>
            <p>{t("Evaluated on ten project-authored, held-out synthetic cases created for this research project. No real client data was used. These results do not establish production accuracy or reliability.")}</p>
            <p>{t("Review used separate AI validators within the project’s internal development process, not independent human or institutional validation.")}</p>
          </div>
        </div>
      </> : <p role="status">{status === "loading" ? t("Loading published research results…") : t("Published research results are unavailable. Open the results page to try again.")}</p>}
      <a className="research-summary-link" href="/research-results">{t("Explore the research →")}</a>
    </div>
  </section>;
}
