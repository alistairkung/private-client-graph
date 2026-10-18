import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { getMatters, getProposals } from "../shared/api";
import type { MatterSummary, ProposalSummary } from "../shared/contracts";
import { ErrorNotice, Loading } from "../shared/Feedback";
import { Icon } from "../shared/Icon";
import { useLocale } from "../shared/locale";
import { useSessionState } from "../shared/session-state";

export function Ledger() {
  const { t } = useLocale();
  const [matters, setMatters] = useState<MatterSummary[]>();
  const [proposals, setProposals] = useState<ProposalSummary[]>();
  const [errors, setErrors] = useState<{
    matters?: unknown;
    proposals?: unknown;
  }>({});
  const [query, setQuery] = useSessionState("ledger:query", "");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setErrors({});
    getMatters()
      .then((data) => {
        if (active) setMatters(data);
      })
      .catch((error) => {
        if (active) setErrors((previous) => ({ ...previous, matters: error }));
      });
    getProposals()
      .then((data) => {
        if (active) setProposals(data);
      })
      .catch((error) => {
        if (active)
          setErrors((previous) => ({ ...previous, proposals: error }));
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  const matches = (reference: string, title: string) =>
    (reference + " " + title)
      .toLocaleLowerCase()
      .includes(query.trim().toLocaleLowerCase());
  const current = matters?.filter((item) =>
    matches(item.external_reference, item.title),
  );
  const pending = proposals?.filter((item) =>
    matches(item.external_reference, item.matter_title),
  );
  return (
    <div className="ledger page">
      <div className="page-heading">
        <div>
          <h1>{t("Matters")}</h1>
          <p>{t("Your relationships, grounded in their sources.")}</p>
        </div>
        <a className="button primary" href="/app/matter-proposals/new">
          <Icon name="plus" />
          {t("New proposal")}
        </a>
      </div>
      <label className="search-field">
        <Icon name="search" />
        <span className="sr-only">{t("Search Matters")}</span>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("Search by reference or title")}
        />
      </label>
      {pending?.length === 0 && !errors.proposals ? (
        <p className="pending-empty">
          {t(
            query
              ? "No matching proposals."
              : "No proposals awaiting confirmation.",
          )}
        </p>
      ) : (
        <section className="ledger-section">
          <div className="section-heading">
            <h2>{t("Awaiting confirmation")}</h2>
            {proposals && <span className="count">{pending?.length}</span>}
          </div>
          <p className="section-description">
            {t(
              "Review the complete proposal before accepting it as current Matter state.",
            )}
          </p>
          {errors.proposals ? (
            <ErrorNotice
              error={errors.proposals}
              retry={() => setAttempt(attempt + 1)}
            />
          ) : !pending ? (
            <Loading />
          ) : pending.length ? (
            <RecordList
              records={pending.map((item) => ({
                ...item,
                title: item.matter_title,
              }))}
              proposal
            />
          ) : (
            <div className="empty-row">
              {t(
                query
                  ? "No matching proposals."
                  : "No proposals awaiting confirmation.",
              )}
            </div>
          )}
        </section>
      )}
      <section className="ledger-section">
        <div className="section-heading">
          <h2>{t("Accepted Matters")}</h2>
          {matters && <span className="count">{current?.length}</span>}
        </div>
        <p className="section-description">
          {t("Revisit accepted relationships and the Evidence behind them.")}
        </p>
        {errors.matters ? (
          <ErrorNotice
            error={errors.matters}
            retry={() => setAttempt(attempt + 1)}
          />
        ) : !current ? (
          <Loading />
        ) : current.length ? (
          <RecordList records={current} />
        ) : (
          <div className="empty-row">
            {t(
              query
                ? "No matching Matters."
                : "No accepted Matters yet. Start with a synthetic proposal.",
            )}
          </div>
        )}
      </section>
      <p className="ledger-footnote">
        {t(
          "Proposals become current Matter state only after your explicit confirmation.",
        )}
      </p>
    </div>
  );
}

function RecordList({
  records,
  proposal = false,
}: {
  records: MatterSummary[];
  proposal?: boolean;
}) {
  const { t } = useLocale();
  return (
    <div className="record-list">
      <AnimatePresence initial={false}>
        {records.map((item) => (
          <motion.a
            layout="position"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.08 } }}
            transition={{ duration: 0.14 }}
            className="record-row"
            href={`/app/${proposal ? "matter-proposals" : "matters"}/${encodeURIComponent(item.id)}`}
            key={item.id}
          >
            <span className="record-icon">
              <Icon name={proposal ? "file" : "atlas"} />
            </span>
            <span className="record-identity">
              <strong>{item.external_reference}</strong>
              <span>{item.title}</span>
            </span>
            {proposal && <span className="status">{t("Proposal")}</span>}
            <Icon name="arrow" />
          </motion.a>
        ))}
      </AnimatePresence>
    </div>
  );
}
