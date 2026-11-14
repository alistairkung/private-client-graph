import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import type { FollowUp, View } from "./api";

export function SearchSummary({
  view,
  folder,
  label,
  inspect,
}: {
  view: View;
  folder: string;
  label: string;
  inspect: () => void;
}) {
  const { t } = useLocale();
  return (
    <header className="discovery-summary">
      <div className="discovery-summary-top">
        <div>
          <p className="discovery-caption">{t("Original search")}</p>
          <h2 className="discovery-title">{view.original_query}</h2>
        </div>
        <dl className="discovery-counts">
          {[
            [t("Emails returned"), view.returned_messages.length],
            [t("Inspected"), view.inspected.length],
            [t("PDFs listed"), view.files.length],
          ].map(([name, count]) => (
            <div key={name}>
              <dt>{name}</dt>
              <dd>{count}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="discovery-inspection">
        <details>
          <summary>{t("Inspection details")}</summary>
          <dl className="discovery-scope">
            <div>
              <dt>{t("Drive folder")}</dt>
              <dd>{folder}</dd>
            </div>
            <div>
              <dt>{t("Gmail label")}</dt>
              <dd>{label}</dd>
            </div>
            <div>
              <dt>{t("Gmail dates (UTC)")}</dt>
              <dd>
                {view.scope.first_day || t("Any start")} –{" "}
                {view.scope.last_day || t("Any end")}
              </dd>
            </div>
          </dl>
          <ul>
            {view.inspected.map((id) => (
              <li key={id}>{view.inspected_titles[id]}</li>
            ))}
          </ul>
          <p>
            {t("{pending} pending · {skipped} skipped · {failed} failed", {
              pending: view.pending.length,
              skipped: view.skipped.length,
              failed: view.failed.length,
            })}
          </p>
          <p>
            {t("At this inspection: {requests} requests, {bytes} bytes.", {
              requests: view.requests,
              bytes: view.bytes,
            })}
          </p>
        </details>
        <div>
          <p>
            {t(
              view.more_pages
                ? "More original result pages remain."
                : "All original result pages returned.",
            )}
          </p>
          {view.stop_reason && <p>{t(view.stop_reason)}</p>}
          {view.can_inspect_more && (
            <button onClick={inspect}>
              {t("Inspect more original results")}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

function SearchOutcome({ result }: { result: FollowUp }) {
  const { t } = useLocale();
  return (
    <p className="discovery-outcome">
      {t("Search results")} ·{" "}
      {t("Emails: {mail} · PDFs: {pdf}", {
        mail: result.messages.length,
        pdf: result.files.length,
      })}
      {result.more_pages && " · " + t("More result pages remain.")}
      {result.stop_reason && " · " + t(result.stop_reason)}
    </p>
  );
}

export function DiscoveryResults({
  view,
  followups,
  approve,
}: {
  view: View;
  followups: FollowUp[];
  approve: (revision: number, query: string) => void;
}) {
  const { t } = useLocale();
  const previous = followups.filter(
    (f) => !view.suggestions.some((s) => s.query === f.query),
  );
  return (
    <section className="discovery-panel">
      <h2>{t("Suggested follow-up searches")}</h2>
      <p className="discovery-caption">
        {t("{used} of 3 searches used", { used: followups.length })}
      </p>
      {!view.suggestions.length && (
        <p>{t("No leads in the inspected emails.")}</p>
      )}
      <ol className="discovery-leads">
        {view.suggestions.map((lead) => {
          const result = followups.find((f) => f.query === lead.query);
          return (
            <li key={lead.query}>
              <h3>{lead.query}</h3>
              <figure>
                <blockquote>{lead.passage}</blockquote>
                <figcaption>{view.inspected_titles[lead.origin]}</figcaption>
              </figure>
              <p>{lead.rationale}</p>
              {result ? (
                <SearchOutcome result={result} />
              ) : (
                <button
                  disabled={followups.length >= 3}
                  onClick={() => approve(view.revision, lead.query)}
                >
                  <Icon name="search" />
                  {t("Search for {name}", { name: lead.query })}
                </button>
              )}
            </li>
          );
        })}
      </ol>
      {previous.map((f) => (
        <div key={f.query}>
          <strong>{f.query}</strong>
          <SearchOutcome result={f} />
        </div>
      ))}
    </section>
  );
}
