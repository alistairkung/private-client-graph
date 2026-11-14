import { useLocale } from "../../../shared/locale";
import type { FollowUp, View } from "./api";

export function DiscoveryResults({
  view,
  followups,
  inspect,
  approve,
}: {
  view: View;
  followups: FollowUp[];
  inspect: () => void;
  approve: (revision: number, query: string) => void;
}) {
  const { t } = useLocale();
  const scope = view.scope;
  return (
    <section>
      <h2>{view.original_query}</h2>
      <p>
        {scope.mailbox} · {scope.folder} · {scope.label} ·{" "}
        {t("Gmail dates (UTC)")} {scope.first_day || t("Any start")} –{" "}
        {scope.last_day || t("Any end")}
      </p>
      <p role="status">
        {t(
          "Original search: {mail} emails returned, {read} inspected, {pdf} PDFs listed.",
          {
            mail: view.returned_messages.length,
            read: view.inspected.length,
            pdf: view.files.length,
          },
        )}
      </p>
      <details>
        <summary>{t("Inspection details")}</summary>
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
      <p>
        {t(
          view.more_pages
            ? "More original result pages remain."
            : "All original result pages returned.",
        )}{" "}
        {view.stop_reason && t(view.stop_reason)}
      </p>
      <button
        disabled={
          (!view.pending.length && !view.more_pages) ||
          view.stop_reason?.startsWith("Session ")
        }
        onClick={inspect}
      >
        {t("Inspect more original results")}
      </button>
      <h3>{t("Suggested follow-up searches")}</h3>
      <ol>
        {view.suggestions.map((lead) => (
          <li key={lead.query}>
            <strong>{lead.query}</strong> · {view.inspected_titles[lead.origin]}
            <blockquote>{lead.passage}</blockquote>
            <p>{lead.rationale}</p>
            <button
              disabled={
                followups.length >= 3 ||
                followups.some((f) => f.query === lead.query)
              }
              onClick={() => approve(view.revision, lead.query)}
            >
              {t("Search for {name}", { name: lead.query })}
            </button>
          </li>
        ))}
      </ol>
      {followups.map((f) => (
        <p key={f.query}>
          {f.query} ·{" "}
          {t("{mail} email hits · {pdf} PDF hits", {
            mail: f.messages.length,
            pdf: f.files.length,
          })}
          {f.more_pages && " · " + t("More result pages remain.")}{" "}
          {f.stop_reason && t(f.stop_reason)}
        </p>
      ))}
    </section>
  );
}
