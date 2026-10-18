import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { navigate } from "../../app/navigation";
import { request } from "../../shared/api";
import { useLocale } from "../../shared/locale";
import { ErrorNotice, Loading } from "../../shared/Feedback";
import { Icon } from "../../shared/Icon";
import type { CanonicalState } from "../../shared/contracts";
import { Workspace } from "../review/ReviewPage";
import "./curated-examples.css";

interface ExampleSummary {
  id: string;
  title: string;
  description: string;
}
interface Example {
  id: string;
  title: string;
  notice: string;
  state: CanonicalState;
}

export function CuratedExamples({ id }: { id: string }) {
  const [cases, setCases] = useState<ExampleSummary[]>();
  const [example, setExample] = useState<Example>();
  const [error, setError] = useState<unknown>();
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setError(undefined);
    setExample(undefined);
    Promise.all([
      request("/api/showcase/cases").then(response => response.json()),
      request("/api/showcase/cases/" + encodeURIComponent(id)).then(response => response.json()),
    ]).then(([catalogue, detail]) => {
      if (active) {
        setCases(catalogue);
        setExample(detail);
      }
    }).catch(failure => {
      if (active) setError(failure);
    });
    return () => { active = false; };
  }, [id, attempt]);
  return <>
    <section className="curated-selector" aria-labelledby="curated-heading">
      <ExampleToolbar
        cases={cases}
        selectedId={id}
        notice={example?.notice}
        onChoose={caseId => navigate("/app?example=" + encodeURIComponent(caseId), { replace: true })}
      />
      {error
        ? <ErrorNotice error={error} retry={() => setAttempt(value => value + 1)} />
        : !example && <Loading />}
    </section>
    {example && <Workspace
      key={example.id}
      record={{
        id: example.id,
        external_reference: example.id,
        title: example.title,
        authoritative_source: null,
        state: example.state,
      }}
      proposal={false}
      curated
    />}
  </>;
}

function ExampleToolbar({ cases, selectedId, notice, onChoose }: {
  cases?: ExampleSummary[];
  selectedId: string;
  notice?: string;
  onChoose: (id: string) => void;
}) {
  const { t } = useLocale();
  const reduced = useReducedMotion();
  const index = cases?.findIndex(item => item.id === selectedId) ?? -1;
  const previous = index > 0 ? cases?.[index - 1] : undefined;
  const next = index >= 0 ? cases?.[index + 1] : undefined;
  return <>
    <div className="curated-toolbar">
      <div className="curated-intro">
        <h2 id="curated-heading">{t("Curated examples")}</h2>
        <p>{t("Curated ideal fixtures, not live extraction or accepted Matter state.")}</p>
      </div>
      <div className="curated-picker">
        <label htmlFor="curated-case">{t("Choose a synthetic case")}</label>
        <div className="curated-controls">
          <select
            id="curated-case"
            value={selectedId}
            disabled={!cases?.length}
            onChange={event => onChoose(event.target.value)}
          >
            {!cases?.length && <option value={selectedId}>{t("Choose a synthetic case")}</option>}
            {cases?.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <div className="curated-steps">
            <motion.button
              type="button"
              className="curated-previous icon-button"
              aria-label={t("Previous example")}
              title={t("Previous example")}
              disabled={!previous}
              onClick={() => previous && onChoose(previous.id)}
              whileTap={{ scale: reduced ? 1 : 0.96 }}
              transition={{ type: "spring", visualDuration: 0.16, bounce: 0 }}
            >
              <Icon name="arrow" />
            </motion.button>
            <motion.button
              type="button"
              className="icon-button"
              aria-label={t("Next example")}
              title={t("Next example")}
              disabled={!next}
              onClick={() => next && onChoose(next.id)}
              whileTap={{ scale: reduced ? 1 : 0.96 }}
              transition={{ type: "spring", visualDuration: 0.16, bounce: 0 }}
            >
              <Icon name="arrow" />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
    {notice && <motion.p
      className="curated-notice"
      key={selectedId}
      initial={{ opacity: reduced ? 1 : 0.65 }}
      animate={{ opacity: 1 }}
      transition={{ duration: reduced ? 0 : 0.16 }}
    >
      {t(notice)}
    </motion.p>}
  </>;
}
