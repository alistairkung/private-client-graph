import type { Ref } from "react";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import type { FollowUp, View } from "./api";

export function SearchSummary({
  view,
  folder,
  label,
  headingRef,
  searching,
  interrupted,
  retry,
}: {
  view: View;
  folder: string;
  label: string;
  headingRef?: Ref<HTMLHeadingElement>;
  searching: boolean;
  interrupted: boolean;
  retry: () => void;
}) {
  const { t } = useLocale();
  const { first_day, last_day } = view.scope;
  const mailDates = first_day || last_day
    ? [first_day ?? t("Any start"), last_day ?? t("Any end")].join(" – ")
    : t("All dates");
  const unreadable = view.failed.length + view.skipped.length;
  const unfinished = view.pending.length > 0 || view.more_pages;
  let progress = t("Original search complete.");
  if (searching) progress = t("Still searching emails and PDFs…");
  else if (view.stop_reason === "Original item limit") {
    progress = t("Stopped at {limit} original results. More matches may be available.", { limit: view.original_item_limit });
  } else if (interrupted || view.stop_reason === "Original search incomplete") {
    progress = t("Search interrupted. Results already found are available.");
  } else if (unfinished) progress = t("This search reached its limit.");
  return (
    <header className="discovery-summary">
      <div className="discovery-summary-top">
        <div>
          <p className="discovery-caption">{t("Original search")}</p>
          <h2 className="discovery-title" ref={headingRef} tabIndex={-1}>{view.original_query}</h2>
        </div>
        <dl className="discovery-counts">
          {[
            [t("Emails returned"), view.returned_messages.length],
            [t("PDFs listed"), view.files.length],
          ].map(([name, count]) => (
            <div key={name}>
              <dt>{name}</dt>
              <dd>{count}</dd>
            </div>
          ))}
        </dl>
      </div>
      <dl className="discovery-scope discovery-applied-scope">
        <div><dt>{t("Drive folder")}</dt><dd>{folder}</dd></div>
        <div><dt>{t("Gmail label")}</dt><dd>{label}</dd></div>
        <div><dt>{t("Gmail dates (UTC)")}</dt><dd>{mailDates}</dd></div>
      </dl>
      <div className="discovery-inspection">
        <div role="status" aria-atomic="true">
          <p className="discovery-search-progress">
            {searching && <span className="discovery-spinner" aria-hidden="true" />}
            {progress}
          </p>
          {view.returned_messages.length > 0 && (
            <p>{t("Checked {read} of {total} emails for leads.", {
              read: view.inspected.length, total: view.returned_messages.length,
            })}</p>
          )}
          {unreadable > 0 && (
            <p>{t("Unavailable emails: {count}.", { count: unreadable })}</p>
          )}
        </div>
        {view.can_inspect_more && !searching && (
          <button onClick={retry}>{t("Resume original search")}</button>
        )}
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
      {(result.more_pages || result.stop_reason) && " · " + t("Partial results")}
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
