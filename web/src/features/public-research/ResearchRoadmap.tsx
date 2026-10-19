import { useLocale } from "../../shared/locale";
import "./research-roadmap.css";

const directions = [
  {
    title: "Names and uncertain claims",
    question: "Test aliases, ambiguous roles, indirect descriptions, negation, pronouns and incomplete information.",
    decision: "Decide when constrained resolution earns a place in intake, and how unresolved claims should appear in review. The current practitioner application uses baseline extraction.",
  },
  {
    title: "Evidence across richer documents",
    question: "Test longer Sources, different document genres, larger graphs, multiple Trusts and overlapping quotations. Assess relationship accuracy and Source attribution separately.",
    decision: "Guide Evidence navigation, document acquisition requirements and the limits of supported input.",
  },
  {
    title: "Change and disagreement",
    question: "Test contradictory Sources and historical versus current relationships. One recorded trustee-replacement example does not establish a general temporal model.",
    decision: "Define the semantics and review workflow needed for incremental Matter updates, corrections and historical state before adding them.",
  },
  {
    title: "Practitioner usefulness and safe scope",
    question: "Observe practitioners finding missing claims, checking Evidence and deciding whether to accept a proposal.",
    decision: "Improve the workspace and Trust layout around observed needs. Real client material requires a complete authorization, tenancy, ownership, security, privacy and data-handling design first.",
  },
];

export function ResearchRoadmap() {
  const { t } = useLocale();
  return (
    <section id="roadmap" className="research-section research-chapter research-roadmap">
      <h2>{t("How research guides the next version")}</h2>
      <p>{t("The folio proposes a staged twenty-scenario research programme alongside practitioner testing. Five development scenarios have authored cases; fifteen remain planned. These are research directions, not delivery commitments.")}</p>
      <div className="research-roadmap-directions">
        {directions.map(direction => (
          <section key={direction.title}>
            <h3>{t(direction.title)}</h3>
            <div>
              <p>{t(direction.question)}</p>
              <p><strong>{t("Application decision")}</strong> {t(direction.decision)}</p>
            </div>
          </section>
        ))}
      </div>
      <p className="research-caption">{t("Further evaluation needs newly unseen cases, richer documents and repeated runs. The published held-out set is now visible. New entity types, including corporate trustees, remain proposed scope requiring an explicit semantic design decision.")}</p>
      <p className="research-caption">{t("Based on the folio’s product direction and research roadmap, English pages 18–19 / Chinese pages 38–39. The recorded comparison evaluates one baseline-plus-resolver slice of that programme.")}</p>
    </section>
  );
}
