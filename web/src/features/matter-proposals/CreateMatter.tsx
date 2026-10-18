import { useLocale } from "../../shared/locale";
import { useEffect, useState, type FormEvent } from "react";
import { createProposal, ProposalRequestFailure } from "./api";
import type { ProposalError } from "./types";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import { FictionalSourcePrompt } from "./FictionalSourcePrompt";
import { SourceDocuments, sourceAdmissionError } from "./SourceDocuments";

export function CreateMatter({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t } = useLocale();
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const [sourceTitles, setSourceTitles] = useState<string[]>([""]);
  const [pdfs, setPdfs] = useState<File[]>([]);
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

  function selectPdfs(files: File[]) {
    setPdfs(files);
    setSourceTitles(previous => files.length ? files.map((file, index) =>
      previous[index]?.trim() ? previous[index] : file.name.replace(/\.pdf$/i, "").slice(0, 200)) : [previous[0] ?? ""]);
  }

  function editSourceTitle(index: number, value: string) {
    setSourceTitles(previous => previous.map((title, position) => position === index ? value : title));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!confirmed || !pdfs.length || sourceAdmissionError(pdfs) || pending || error?.retryable === false) return;
    setPending(true);
    setError(undefined);
    try {
      const identity = { external_reference: reference, matter_title: title, synthetic_confirmation: confirmed };
      const proposal = await createProposal(pdfs.length === 1
        ? { ...identity, source_title: sourceTitles[0], pdf: pdfs[0] }
        : { ...identity, sources: pdfs.map((pdf, index) => ({
          id: `source_${String(index + 1).padStart(3, "0")}`, title: sourceTitles[index], pdf,
        })) });
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
    <a className="matter-back" href="/app">{t("Back to Matters")}</a>
    <h1>{t("Create Matter")}</h1>
    <p className="intake-intro">{t("Upload synthetic PDFs together. Review one combined proposal before creating the Matter.")}</p>
    <p>{t("Uploaded Source text and the resulting proposal will be publicly readable before confirmation. Confirmed Matters are public too.")}</p>
    {showPrompt && <FictionalSourcePrompt onClose={() => setShowPrompt(false)} />}
    <div className="intake-layout">
    <form className="intake-form" onSubmit={submit}>
      <fieldset disabled={pending} onChange={() => setError(undefined)}>
        <legend>{t("Matter details")}</legend>
        <div className="intake-identity">
          <div><label>{t("External Matter reference")}<input required maxLength={100} name="external_reference" value={reference} onChange={event => setReference(event.target.value)} aria-describedby="reference-guidance" /></label>
            <p className="field-guidance" id="reference-guidance">{t("Use the reference from your existing Matter system.")}</p></div>
          <label>{t("Matter title")}<input required maxLength={200} name="matter_title" value={title} onChange={event => setTitle(event.target.value)} /></label>
        </div>
      </fieldset>
      <fieldset disabled={pending} onChange={() => setError(undefined)}>
        <legend>{t("Source documents")}</legend>
        <SourceDocuments files={pdfs} titles={sourceTitles} onFiles={selectPdfs} onTitle={editSourceTitle} />
        <label className="synthetic-confirmation"><input type="checkbox" required checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />{t("I confirm that this material is synthetic or fictional and contains no real confidential client information.")}</label>
      </fieldset>
      {error && <ProposalFailureNotice error={error} />}
      <div className="intake-actions">
      <button className="intake-button" disabled={!confirmed || !pdfs.length || !!sourceAdmissionError(pdfs) || pending || error?.retryable === false} type="submit">{error?.outcome_unknown ? t("Check reference and retry") : error?.retryable ? t("Retry analysis") : t("Upload and analyse")}</button>
      {!pending && <a className="decision-return" href="/app">{t("Back to Matters")}</a>}
      </div>
      {pending && <p role="status">{t("Uploading and analysing… Keep this page open while the proposal is prepared.")}</p>}
      {!pending && <p className="intake-save-guidance">{error?.outcome_unknown
        ? t("If this reference already has a proposal or Matter, we will open it. Otherwise, analysis can be tried again.")
        : t("Keep this page open during analysis. A proposal is saved only after analysis succeeds.")}</p>}
    </form>
    <aside className="intake-guidance" aria-label={t("Intake guidance")}>
      <h2>{error?.outcome_unknown ? t("Your entries are still here") : t("What happens next")}</h2>
      <p>{error?.outcome_unknown ? t("Keep this page open to retain the selected PDFs for retry.") : t("We extract the text from each PDF and analyse the documents together.")}</p>
      <p>{t("You review the proposed graph against the exact source evidence.")}</p>
      <p>{t("You decide whether to accept the whole proposal.")}</p>
      <div className="fictional-prompt-guidance">
        <button className="prompt-trigger" type="button" onClick={() => setShowPrompt(true)}>{t("Need something to try?")}</button>
        <p>{t("Get a prompt for creating a fictional source.")}</p>
      </div>
    </aside>
    </div>
  </>;
}
