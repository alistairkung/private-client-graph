import { navigate } from "../../app/navigation";
import { useEffect, useState } from "react";
import { request } from "../../shared/api";
import { useLocale } from "../../shared/locale";
import { ErrorNotice, Loading } from "../../shared/Feedback";
import type { CanonicalState } from "../../shared/contracts";
import { Workspace } from "../review/ReviewPage";

interface ExampleSummary { id: string; title: string; description: string }
interface Example { id: string; title: string; notice: string; state: CanonicalState }

export function CuratedExamples({ id }: { id: string }) {
  const { t } = useLocale();
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
      if (active) { setCases(catalogue); setExample(detail); }
    }).catch(failure => { if (active) setError(failure); });
    return () => { active = false; };
  }, [id, attempt]);
  return <>
    <div className="page curated-selector">
      <label>{t("Choose a synthetic case")}
        <select value={id} onChange={event => {
          navigate("/app?example=" + encodeURIComponent(event.target.value), { replace: true });
        }}>
          {cases?.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
        </select>
      </label>
      <p>{t("Curated ideal fixtures, not live extraction or accepted Matter state.")}</p>
      {example && <p>{t(example.notice)}</p>}
      {error ? <ErrorNotice error={error} retry={() => setAttempt(value => value + 1)} /> : !example && <Loading />}
    </div>
    {example && <Workspace key={example.id} record={{ id: example.id, external_reference: example.id, title: example.title, authoritative_source: null, state: example.state }} proposal={false} curated />}
  </>;
}
