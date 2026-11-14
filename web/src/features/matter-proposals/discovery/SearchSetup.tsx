import { useState } from "react";
import { useLocale } from "../../../shared/locale";

export function SearchSetup({
  folder,
  label,
  start,
}: {
  folder: string;
  label: string;
  start: (terms: string, first: string, last: string) => void;
}) {
  const { t } = useLocale();
  const [terms, setTerms] = useState("Alder Trust");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  return (
    <form
      className="discovery-panel discovery-setup"
      onSubmit={(e) => {
        e.preventDefault();
        start(terms, first, last);
      }}
    >
      <h2 className="discovery-title">{t("Search Workspace")}</h2>
      <dl className="discovery-scope">
        <div>
          <dt>{t("Drive folder")}</dt>
          <dd>{folder}</dd>
        </div>
        <div>
          <dt>{t("Gmail label")}</dt>
          <dd>{label}</dd>
        </div>
      </dl>
      <label>
        {t("Initial search terms")}
        <input
          required
          value={terms}
          maxLength={160}
          onChange={(e) => setTerms(e.target.value)}
        />
      </label>
      <details>
        <summary>{t("Gmail date range (optional)")}</summary>
        <div className="discovery-dates">
          <label>
            {t("Gmail from (UTC)")}
            <input
              type="date"
              value={first}
              max={last || undefined}
              onChange={(e) => setFirst(e.target.value)}
            />
          </label>
          <label>
            {t("Gmail through (UTC)")}
            <input
              type="date"
              value={last}
              min={first || undefined}
              onChange={(e) => setLast(e.target.value)}
            />
          </label>
        </div>
      </details>
      <p>
        {t(
          "Starting discovery authorizes private inspection of matching synthetic content in the selected scope. Review and publication require separate approval.",
        )}
      </p>
      <button
        className="button primary"
        disabled={!terms.trim() || Boolean(first && last && first > last)}
      >
        {t("Start private discovery")}
      </button>
    </form>
  );
}
