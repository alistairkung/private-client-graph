import { useLocale } from "../../shared/locale";
import { usePublicResearchSnapshot } from "./api";
import "./research-summary.css";

export function ResearchSummary() {
  const { t, locale } = useLocale();
  const { snapshot, status } = usePublicResearchSnapshot();
  const baseline = snapshot?.runs.find(run => run.label === "A_prime");
  const resolver = snapshot?.runs.find(run => run.label === "B");
  const ready = status === "ready" && snapshot && baseline && resolver;
  const format = (value: number) => new Intl.NumberFormat(locale, {
    style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value);

  return <section id="research-summary" className="research-summary" aria-labelledby="research-summary-title">
    <div className="folio-width research-summary-layout">
      <h2 id="research-summary-title">{t("Measured against a controlled synthetic benchmark.")}</h2>
      <div className="research-summary-reading">
        {ready ? <>
          <dl className="research-summary-metrics">
            <div><dt>{t("Baseline · relationship micro-F1")}</dt><dd>{format(baseline.metrics.micro_f1)}<span aria-label={t("See benchmark limitations")}>*</span></dd></div>
            <div><dt>{t("With resolver · relationship micro-F1")}</dt><dd>{format(resolver.metrics.micro_f1)}<span aria-label={t("See benchmark limitations")}>*</span></dd></div>
          </dl>
          <p className="research-summary-caveat">{t("* Small internal development benchmark. The resolver comparison was post-hoc and exploratory; two name corrections in one case accounted for the entire improvement.")}</p>
          <p>{t("Evaluated on ten project-authored, held-out synthetic cases used as an internal development benchmark. No real client data was used. These results do not establish production accuracy or reliability.")}</p>
          <p>{t("{cases} cases · {relationships} expected relationships. The comparison reused the same frozen extractions; no relationship regressions were observed.", {
            cases: snapshot.benchmark.case_count, relationships: snapshot.benchmark.expected_relationships,
          })}</p>
        </> : <p role="status">{status === "loading" ? t("Loading published research results…") : t("Published research results are unavailable. Open the results page to try again.")}</p>}
        <a className="research-summary-link" href="/research-results">{t("Explore the research results →")}</a>
      </div>
    </div>
  </section>;
}
