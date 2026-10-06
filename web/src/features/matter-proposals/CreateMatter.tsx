import { useEffect, useState, type FormEvent } from "react";
import { createProposal, ProposalRequestFailure } from "./api";
import type { ProposalError } from "./types";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import { FictionalSourcePrompt } from "./FictionalSourcePrompt";

export function CreateMatter({ onNavigate }: { onNavigate: (path: string) => void }) {
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [pdf, setPdf] = useState<File>();
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ProposalError>();
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    if (!error?.resets_at) return;
    const reset = Date.parse(error.resets_at);
    if (!Number.isFinite(reset)) return;
    let timer: ReturnType<typeof setTimeout>;
    function releaseAfterReset() {
      const remaining = reset - Date.now();
      if (remaining <= 0) setError(undefined);
      else timer = setTimeout(releaseAfterReset, Math.min(remaining, 2_147_483_647));
    }
    releaseAfterReset();
    return () => clearTimeout(timer);
  }, [error]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!confirmed || !pdf || pending || error?.retryable === false) return;
    setPending(true);
    setError(undefined);
    try {
      const proposal = await createProposal({
        external_reference: reference, matter_title: title, source_title: sourceTitle,
        pdf, synthetic_confirmation: confirmed,
      });
      onNavigate(`/app/matter-proposals/${encodeURIComponent(proposal.id)}`);
    } catch (failure) {
      if (failure instanceof ProposalRequestFailure) {
        const existing = failure.error.existing_resource;
        if (existing && ["matter_proposal", "matter"].includes(existing.resource_kind) && typeof existing.resource_id === "string") {
          const collection = existing.resource_kind === "matter" ? "matters" : "matter-proposals";
          onNavigate(`/app/${collection}/${encodeURIComponent(existing.resource_id)}`);
          return;
        }
        setError(failure.error);
      }
    } finally {
      setPending(false);
    }
  }

  return <>
    <a className="matter-back" href="/app">Back to Matters</a>
    <h1>Create Matter</h1>
    <p className="intake-intro">Upload one synthetic PDF. Review the proposed relationships before creating the Matter.</p>
    {showPrompt && <FictionalSourcePrompt onClose={() => setShowPrompt(false)} />}
    <div className="intake-layout">
    <form className="intake-form" onSubmit={submit}>
      <fieldset disabled={pending} onChange={() => setError(undefined)}>
        <legend>Matter details</legend>
        <div className="intake-identity">
          <div><label>External Matter reference<input required maxLength={100} name="external_reference" value={reference} onChange={event => setReference(event.target.value)} aria-describedby="reference-guidance" /></label>
            <p className="field-guidance" id="reference-guidance">Use the reference from your existing Matter system.</p></div>
          <label>Matter title<input required maxLength={200} name="matter_title" value={title} onChange={event => setTitle(event.target.value)} /></label>
        </div>
      </fieldset>
      <fieldset disabled={pending} onChange={() => setError(undefined)}>
        <legend>Source document</legend>
        <label>PDF<input required type="file" name="pdf" accept=".pdf,application/pdf" onChange={event => {
          const file = event.target.files?.[0];
          setPdf(file);
          if (file && !sourceTitle.trim()) setSourceTitle(file.name.replace(/\.pdf$/i, "").slice(0, 200));
        }} aria-describedby="pdf-admission" /></label>
        <p id="pdf-admission" className="field-guidance">One text-layer PDF, up to 10 MiB and 50 pages. Scanned and encrypted PDFs are unsupported. Extracted source text may contain up to 100,000 characters.</p>
        <label>Authoritative Source title<input required maxLength={200} name="source_title" value={sourceTitle} onChange={event => setSourceTitle(event.target.value)} aria-describedby="source-title-guidance" /></label>
        <p id="source-title-guidance" className="field-guidance">This title will appear beside the source evidence.</p>
        <label className="synthetic-confirmation"><input type="checkbox" required checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />I confirm that this material is synthetic or fictional and contains no real confidential client information.</label>
      </fieldset>
      {error && <ProposalFailureNotice error={error} />}
      <div className="intake-actions">
      <button className="intake-button" disabled={!confirmed || !pdf || pending || error?.retryable === false} type="submit">{error?.outcome_unknown ? "Check reference and retry" : error?.retryable ? "Retry analysis" : "Upload and analyse"}</button>
      {!pending && <a className="decision-return" href="/app">Back to Matters</a>}
      </div>
      {pending && <p role="status">Uploading and analysing… Keep this page open while the proposal is prepared.</p>}
      {!pending && <p className="intake-save-guidance">{error?.outcome_unknown
        ? "If this reference already has a proposal or Matter, we will open it. Otherwise, analysis can be tried again."
        : "Keep this page open during analysis. A proposal is saved only after analysis succeeds."}</p>}
    </form>
    <aside className="intake-guidance" aria-label="Intake guidance">
      <h2>{error?.outcome_unknown ? "Your entries are still here" : "What happens next"}</h2>
      <p>{error?.outcome_unknown ? "Keep this page open to retain the selected PDF for retry." : "We extract the text from your PDF."}</p>
      <p>You review the proposed graph against the exact source evidence.</p>
      <p>You decide whether to accept the whole proposal.</p>
      <div className="fictional-prompt-guidance">
        <button className="prompt-trigger" type="button" onClick={() => setShowPrompt(true)}>Need something to try?</button>
        <p>Get a prompt for creating a fictional source.</p>
      </div>
    </aside>
    </div>
  </>;
}
