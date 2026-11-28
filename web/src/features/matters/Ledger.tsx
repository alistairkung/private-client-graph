import { getMatters } from "../../shared/api";
import type { MatterSummary, ProposalSummary } from "../../shared/contracts";
import { ErrorNotice, Loading } from "../../shared/Feedback";
import { Icon } from "../../shared/Icon";
import { useLocale } from "../../shared/locale";
import { useSessionState } from "../../shared/session-state";
import { type RecordCollection, useRecordCollection } from "./useRecordCollection";
import "./ledger.css";

export function MatterLedger() {
  const collection = useRecordCollection(getMatters);
  return <RecordIndex kind="matters" collection={collection} />;
}

export function ProposalLedger({ collection }: { collection: RecordCollection<ProposalSummary> }) {
  return <RecordIndex kind="matter-proposals" collection={collection} />;
}

function RecordIndex({ kind, collection }: {
  kind: "matters" | "matter-proposals";
  collection: RecordCollection<MatterSummary | ProposalSummary>;
}) {
  const { t, locale } = useLocale();
  const proposals = kind === "matter-proposals";
  const [query, setQuery] = useSessionState(proposals ? "proposal-queue:query" : "ledger:query", "");
  const { result, retry } = collection;
  const search = query.trim().toLocaleLowerCase(locale);
  const records = result.status === "ready" ? result.records : [];
  const emptyQueue = proposals && result.status === "ready" && !records.length;
  const matches = records.filter((record) =>
    `${record.external_reference} ${recordTitle(record)}`.toLocaleLowerCase(locale).includes(search),
  );
  const format = new Intl.NumberFormat(locale);
  const total = format.format(records.length);
  const emptyMessage = proposals
    ? records.length ? "No matching proposals." : "No proposals awaiting confirmation."
    : records.length ? "No matching Matters." : "No accepted Matters yet. Start with a synthetic proposal.";
  const count = search
    ? t("{shown} of {total}", { shown: format.format(matches.length), total })
    : t(proposals ? "{count} awaiting confirmation" : "{count} accepted", { count: total });

  return (
    <div className="ledger page">
      <div className="page-heading">
        <div>
          <h1>{t(proposals ? "Review proposals" : "Matters")}</h1>
          {proposals && <p className="ledger-description">
            {t("Review the complete proposal before accepting it as current Matter state.")}
          </p>}
        </div>
        {!proposals && <NewProposalLink />}
      </div>
      <div className="matter-index">
        {!emptyQueue && (
          <div className="ledger-toolbar">
            <label className="search-field">
              <Icon name="search" />
              <span className="sr-only">{t(proposals ? "Search proposals" : "Search Matters")}</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={t("Reference or title")}
              />
            </label>
            {records.length > 0 && <p className="ledger-count">{count}</p>}
          </div>
        )}
        <div className="ledger-body">
          {result.status === "loading" ? <Loading /> : result.status === "error" ? (
            <ErrorNotice error={result.error} retry={retry} />
          ) : matches.length ? (
            <RecordList records={matches} kind={kind} />
          ) : (
            <div className="empty-row ledger-empty">
              <p>{t(emptyMessage)}</p>
              {proposals && !records.length && <NewProposalLink />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function NewProposalLink() {
  const { t } = useLocale();
  return (
    <a className="button primary" href="/app/matter-proposals/new">
      <Icon name="plus" />
      {t("New proposal")}
    </a>
  );
}

function recordTitle(record: MatterSummary | ProposalSummary) {
  return "matter_title" in record ? record.matter_title : record.title;
}

function RecordList({ records, kind }: {
  records: (MatterSummary | ProposalSummary)[];
  kind: "matters" | "matter-proposals";
}) {
  return (
    <ul className="record-list" role="list">
      {records.map((record) => (
        <li key={record.id}>
          <a className="record-row" href={`/app/${kind}/${encodeURIComponent(record.id)}`}>
            <span className="record-icon">
              <Icon name={kind === "matter-proposals" ? "file" : "atlas"} />
            </span>
            <span className="record-identity">
              <strong>{record.external_reference}</strong>
              <span>{recordTitle(record)}</span>
            </span>
            <Icon name="arrow" />
          </a>
        </li>
      ))}
    </ul>
  );
}
