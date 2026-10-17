import { SourceAwareReviewWorkspace } from "../../review/SourceAwareReviewWorkspace";
import { useShowcaseCases } from "../useShowcaseCases";
import "./demonstration.css";

export function ShowcaseDemonstration() {
  const { cases, caseId, setCaseId, detail, failed, reload } = useShowcaseCases();
  return <section id="case-01" tabIndex={-1} className="demonstration folio-width" aria-labelledby="demonstration-title">
    <div className="demonstration-caption">
      <h2 id="demonstration-title">See it in context.</h2>
      <p>Explore synthetic sources and follow each relationship to its exact Evidence.</p>
      <label className="showcase-case-label">Choose a synthetic case
        <select className="showcase-case-choice" disabled={!cases.length} value={caseId} onChange={event => setCaseId(event.target.value)}>
          {cases.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
        </select>
      </label>
      {detail && <><p className="demonstration-case">{detail.title}</p><p>{detail.description}</p></>}
      <p className="showcase-fixture-notice">Curated ideal fixtures. These examples illustrate the intended graph and Evidence; they are not measured model results.</p>
    </div>
    <div className="demonstration-stage">
      <div className="demonstration-frame" aria-busy={!detail && !failed}>
        {failed ? <div className="demonstration-load"><p role="alert">The synthetic case could not be loaded.</p><button onClick={reload}>Reload case</button></div>
          : detail ? <SourceAwareReviewWorkspace key={detail.id} state={detail.state} graphTitle="Curated relationships" />
          : <p role="status" className="demonstration-load">Loading the synthetic case…</p>}
      </div>
      <p className="demonstration-mode">Read-only synthetic demonstration · No sign-in or live analysis required</p>
    </div>
  </section>;
}
