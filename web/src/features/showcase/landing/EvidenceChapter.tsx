import { useLocale } from "../../../shared/locale";
import "./evidence-chapter.css";

export function EvidenceChapter() {
  const { t } = useLocale();
  return (
    <section id="approach" className="evidence-chapter" aria-labelledby="evidence-title">
      <div className="folio-width evidence-composition">
        <h2 id="evidence-title">{t("A relationship.")}<br />{t("Its exact Evidence.")}</h2>
        <span className="evidence-margin" aria-hidden="true">{t("Evidence")}</span>
        <blockquote>
          Alice Chen confirmed that <span className="folio-highlight">she and David Chen are spouses.</span>
        </blockquote>
        <p>{t("Follow the connection back to the words.")}</p>
      </div>
    </section>
  );
}
