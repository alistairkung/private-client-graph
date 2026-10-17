import { useEffect, useState } from "react";
import { BrandMark } from "../../shared/brand/BrandMark";
import { LanguageControl } from "../../shared/LanguageControl";
import { useLocale } from "../../shared/locale";
import { SourceDocuments } from "../matter-proposals/SourceDocuments";
import { SourceAwareReviewWorkspace } from "../review/SourceAwareReviewWorkspace";
import { getShowcaseCase } from "../showcase/api";
import type { ShowcaseCase } from "../showcase/types";
import "../matters/practitioner.css";
import "../matter-proposals/proposals.css";
import "./demo.css";

const examples = [
  { id: "hillcrest", caseId: "case-04", reference: "DEMO/2026/004", title: "Hillcrest Family Trust" },
  { id: "evergreen", caseId: "case-01", reference: "DEMO/2026/001", title: "Evergreen Family Trust" },
];
const proposalPath = "/demo/matter-proposals/hillcrest";

export function DemoApp() {
  const { t } = useLocale();
  const path = window.location.pathname.replace(/\/$/, "");
  return <div className="practitioner-shell demo-shell">
    <header className="ledger-header"><div className="ledger-header-inner ledger-width">
      <a href="/" className="ledger-brand"><BrandMark />Private Client Graph</a>
      <nav aria-label={t("Demo application")}>
        <a href="/demo" aria-current={path === "/demo" ? "page" : undefined}>{t("Matters")}</a>
        <a href="/app">{t("Practitioner sign-in")}</a>
      </nav>
      <LanguageControl />
    </div></header>
    <main className="ledger-content ledger-width">
      <aside className="practitioner-access demo-notice" aria-label={t("Read-only demo")}>
        <strong>{t("Read-only demo")}</strong>
        <p>{t("Curated synthetic examples. No uploads, live analysis or saved changes. These are ideal fixtures, not measured model results.")}</p>
      </aside>
      <DemoPage path={path} />
    </main>
    <footer className="ledger-footer ledger-width"><span>Private Client Graph</span><a href="/">{t("Back to public showcase")}</a></footer>
  </div>;
}

function DemoPage({ path }: { path: string }) {
  const { t } = useLocale();
  if (path === "/demo") return <DemoLedger />;
  if (path === "/demo/matter-proposals/new") return <DemoIntake />;
  if (path === proposalPath) return <DemoReview id="hillcrest" proposed />;
  if (path === "/demo/confirmation/hillcrest") return <ConfirmationPreview />;
  const matterId = path.match(/^\/demo\/matters\/([^/]+)$/)?.[1];
  if (matterId && examples.some(item => item.id === matterId)) return <DemoReview id={matterId} />;
  return <><h1>{t("Demo page not found")}</h1><p>{t("Choose one of the fixed examples from the demo Matter list.")}</p><BackToMatters /></>;
}

function BackToMatters() {
  const { t } = useLocale();
  return <a className="matter-back" href="/demo">{t("Back to Matters")}</a>;
}

function DemoLedger() {
  const { t } = useLocale();
  return <>
    <div className="ledger-title-row"><h1>{t("Demo Matters")}</h1><a className="intake-button" href="/demo/matter-proposals/new">{t("Create Matter preview")}</a></div>
    <p className="ledger-intro">{t("Explore a representative proposal and its already-existing completed example. Previewing confirmation never changes these examples.")}</p>
    <section className="proposal-collection"><h2>{t("Example proposal awaiting review")}</h2>
      <a className="matter-row" href={proposalPath}><span className="matter-reference">DEMO/2026/004</span><span className="matter-title">Hillcrest Family Trust</span></a>
    </section>
    <section className="matter-collection"><h2>{t("Completed examples")}</h2>
      <table className="matter-register" aria-label={t("Demo Matters")}><thead><tr><th>{t("Matter reference")}</th><th>{t("Matter")}</th></tr></thead><tbody>
        {examples.map(item => <tr key={item.id}><td colSpan={2}><a className="matter-row" href={`/demo/matters/${item.id}`}><span className="matter-reference">{item.reference}</span><span className="matter-title">{item.title}</span></a></td></tr>)}
      </tbody></table>
    </section>
  </>;
}

function DemoIntake() {
  const { t } = useLocale();
  return <><BackToMatters /><h1>{t("Create Matter preview")}</h1>
    <p className="intake-intro">{t("The live application accepts multiple synthetic PDFs. This public preview is disabled and cannot accept documents or start analysis.")}</p>
    <div className="intake-layout"><div className="intake-form">
      <fieldset disabled><legend>{t("Matter details")}</legend><div className="intake-identity">
        <label>{t("External Matter reference")}<input name="external_reference" defaultValue="" /></label>
        <label>{t("Matter title")}<input name="matter_title" defaultValue="" /></label>
      </div></fieldset>
      <fieldset disabled><legend>{t("Source documents")}</legend>
        <SourceDocuments files={[]} titles={[""]} onFiles={() => {}} onTitle={() => {}} />
        <p className="field-guidance">{t("One to five text-layer PDFs in the authenticated application. File selection is unavailable in this demo.")}</p>
      </fieldset>
      <button className="intake-button" disabled type="button">{t("Upload and analyse unavailable")}</button>
    </div><aside className="intake-guidance"><h2>{t("Continue with a fixed example")}</h2>
      <p>{t("No form submission is needed. Open the precomputed Hillcrest proposal to inspect its graph and exact Source evidence.")}</p>
      <a className="intake-button" href={proposalPath}>{t("View example proposal")}</a>
    </aside></div>
  </>;
}

function DemoReview({ id, proposed = false }: { id: string; proposed?: boolean }) {
  const { t } = useLocale();
  const example = examples.find(item => item.id === id)!;
  const [result, setResult] = useState<ShowcaseCase>();
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    getShowcaseCase(example.caseId).then(value => { if (active) setResult(value); }, () => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [example.caseId]);
  return <><BackToMatters /><header className="matter-context"><h1>{example.title}</h1>
    <p>{t("Matter reference")}: {example.reference}</p>
    <p>{proposed ? t("Representative proposal — precomputed relationships awaiting professional review in the real workflow.") : t("Completed example — fixed accepted-state illustration. It existed before this visit; no confirmation or save occurred.")}</p>
  </header>
    {result ? <SourceAwareReviewWorkspace state={result.state} practitioner graphTitle={proposed ? t("Proposed relationships") : t("Accepted relationships")} />
      : <p role={failed ? "alert" : "status"}>{failed ? t("The public example could not be loaded. Reload to try again.") : t("Loading public example…")}</p>}
    {proposed && <section className="demo-next"><h2>{t("Whole-proposal decision preview")}</h2><p>{t("Inspect each relationship and its Sources before reviewing what confirmation would mean.")}</p><a className="intake-button" href="/demo/confirmation/hillcrest">{t("Preview confirmation")}</a></section>}
  </>;
}

function ConfirmationPreview() {
  const { t } = useLocale();
  return <><BackToMatters /><section className="demo-confirmation"><h1>{t("Confirmation preview")}</h1>
    <h2>Hillcrest Family Trust</h2><p>DEMO/2026/004</p>
    <p>{t("In the authenticated workflow, confirmation accepts the whole proposed relationship graph and its supporting Sources as current Matter state.")}</p>
    <p><strong>{t("This is a preview only. No Matter will be created or changed.")}</strong></p>
    <p>{t("The completed example below is a fixed illustration, available before and after this preview. Following the link does not confirm the proposal.")}</p>
    <div className="intake-actions"><a className="intake-button" href="/demo/matters/hillcrest">{t("View completed example")}</a><a href={proposalPath}>{t("Return to example proposal")}</a></div>
  </section></>;
}
