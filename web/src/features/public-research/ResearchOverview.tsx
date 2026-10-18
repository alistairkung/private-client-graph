import { useLocale } from "../../shared/locale";
import { percent } from "./RunComparison";
import type { PublicResearchSnapshot } from "./types";

export function ResearchOverview({ snapshot }: { snapshot: PublicResearchSnapshot }) {
  const { t } = useLocale();
  const baseline = snapshot.runs.find(run => run.label === "A_prime")!;
  const resolved = snapshot.runs.find(run => run.label === "B")!;
  return <section className="research-overview" aria-labelledby="research-finding">
    <div className="research-overview-story">
      <h2 id="research-finding">{t("Two corrections explain the entire gain.")}</h2>
      <p>{t("A controlled comparison of the same frozen extractions with and without generative entity resolution. One alias mapping, repeated at two endpoints in Case 03, accounts for the entire improvement.")}</p>
      <p className="research-caption">{t("The practitioner application uses baseline extraction. The resolver is evaluated here as a research comparison.")}</p>
      <a className="research-primary-link" href="#failure-analysis">{t("Follow the two corrections")}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5" /></svg></a>
    </div>
    <div className="research-overview-record">
      <a className="research-score-link" href="#comparison">
        <span>{t("Relationship micro-F1")}</span>
        <strong>{percent(baseline.metrics.micro_f1)} <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5" /></svg> {percent(resolved.metrics.micro_f1)}<sup>*</sup></strong>
        <span>{t("Frozen baseline A′ to resolution B")}</span>
      </a>
      <p className="research-disclosure">{t("* Small, project-authored synthetic benchmark. Post-hoc and exploratory; no repeated trials or uncertainty estimates. These results do not establish production reliability.")}</p>
      <p>{t("{cases} cases · {sources} Sources · {relationships} expected relationships", { cases: snapshot.benchmark.case_count, sources: snapshot.benchmark.source_count, relationships: snapshot.benchmark.expected_relationships })}</p>
    </div>
  </section>;
}
