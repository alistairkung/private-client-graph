import { useLayoutEffect, useRef, useState, type Ref } from "react";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import type { Candidate, FollowUp, View } from "./api";

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
        <h2 className="intake-section-title" ref={headingRef} tabIndex={-1}>{view.original_query}</h2>
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

function SearchOutcome({
  result,
  added,
  show,
  focus,
}: {
  result: FollowUp;
  added: number;
  show: (query: string) => void;
  focus: boolean;
}) {
  const { t } = useLocale();
  const outcome = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (focus) outcome.current?.focus({ preventScroll: true });
  }, [focus]);
  return (
    <div className="discovery-outcome" tabIndex={-1} ref={outcome}>
      <p>{t(added === 0 ? "No new Sources found." : added === 1 ? "1 new Source found." : "{count} new Sources found.", { count: added })}</p>
      {(result.more_pages || result.stop_reason) && <p>{t("Partial results")}</p>}
      {added > 0 && (
        <button className="discovery-text-action" onClick={() => show(result.query)}>
          {t("Show results for {query}", { query: result.query })}
        </button>
      )}
    </div>
  );
}

export function DiscoveryResults({
  view,
  followups,
  options,
  approve,
  show,
}: {
  view: View;
  followups: FollowUp[];
  options: Candidate[];
  approve: (revision: number, query: string) => void;
  show: (query: string) => void;
}) {
  const { t } = useLocale();
  const [expanded, setExpanded] = useState(false);
  const [submitted, setSubmitted] = useState<string>();
  const previous = followups.filter(
    (f) => !view.suggestions.some((s) => s.query === f.query),
  );
  const usage = t("{used} of 3 searches used", { used: followups.length });
  function outcome(result: FollowUp) {
    return (
      <SearchOutcome
        result={result}
        added={options.filter(item => item.followUp === result.query).length}
        show={show}
        focus={submitted === result.query}
      />
    );
  }
  return (
    <section className="discovery-panel discovery-suggestions">
      <div className="discovery-suggestions-heading">
        <h2 className="intake-section-title">{t("Suggested follow-up searches")}</h2>
        <p className="discovery-caption">{usage}</p>
      </div>
      <button
        className="discovery-suggestions-toggle"
        aria-expanded={expanded}
        aria-controls="discovery-follow-ups"
        onClick={() => setExpanded(!expanded)}
      >
        <span>{t("Suggested follow-up searches")}<small>{usage}</small></span>
        <Icon name="chevron" />
      </button>
      <div className="discovery-suggestions-content" id="discovery-follow-ups" data-expanded={expanded}>
        {!view.suggestions.length && <p>{t("No leads in the inspected emails.")}</p>}
        <ul className="discovery-leads">
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
                {result ? outcome(result) : (
                  <button
                    disabled={followups.length >= 3}
                    onClick={() => {
                      setSubmitted(lead.query);
                      approve(view.revision, lead.query);
                    }}
                  >
                    <Icon name="search" />
                    {t("Search for {name}", { name: lead.query })}
                  </button>
                )}
              </li>
            );
          })}
          {previous.map((result) => (
            <li key={result.query}>
              <h3>{result.query}</h3>
              {outcome(result)}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
