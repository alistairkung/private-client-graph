import { useEffect, useState, type FormEvent } from "react";
import { createProposal, ProposalRequestFailure } from "./api";
import type { ProposalError } from "./types";
import { ProposalFailureNotice } from "./ProposalFailureNotice";

export function CreateMatter({ onNavigate }: { onNavigate: (path: string) => void }) {
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [pdf, setPdf] = useState<File>();
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ProposalError>();

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
    <p className="intake-intro">Upload one synthetic PDF to propose relationships for review. This creates a Matter Proposal awaiting confirmation.</p>
    <form className="intake-form" onSubmit={submit}>
      <fieldset disabled={pending} onChange={() => setError(undefined)}>
        <legend className="visually-hidden">Matter identity and source</legend>
        <label>External Matter reference<input required name="external_reference" value={reference} onChange={event => setReference(event.target.value)} /></label>
        <label>Matter title<input required name="matter_title" value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label>Authoritative Source title<input required name="source_title" value={sourceTitle} onChange={event => setSourceTitle(event.target.value)} /></label>
        <label>PDF<input required type="file" name="pdf" accept=".pdf,application/pdf" onChange={event => setPdf(event.target.files?.[0])} aria-describedby="pdf-admission" /></label>
        <p id="pdf-admission" className="field-guidance">One text-layer PDF, up to 10 MiB and 50 pages. Scanned and encrypted PDFs are unsupported. Extracted source text may contain up to 100,000 characters.</p>
        <label className="synthetic-confirmation"><input type="checkbox" required checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />I confirm that this material is synthetic or fictional and contains no real confidential client information.</label>
      </fieldset>
      {error && <ProposalFailureNotice error={error} />}
      <button className="intake-button" disabled={!confirmed || !pdf || pending || error?.retryable === false} type="submit">{error?.outcome_unknown ? "Check reference and retry" : error?.retryable ? "Retry analysis" : "Upload and analyse"}</button>
      {pending && <p role="status">Uploading and analysing… Keep this page open while the proposal is prepared.</p>}
    </form>
  </>;
}
