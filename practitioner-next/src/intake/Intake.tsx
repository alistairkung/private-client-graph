import { useEffect, useState, type FormEvent } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { createProposal, RequestFailure } from "../shared/api";
import type { SourceUpload } from "../shared/contracts";
import { ErrorNotice } from "../shared/Feedback";
import { Icon } from "../shared/Icon";
import { useLocale } from "../shared/locale";
import { admissionError, addSources } from "./uploads";
import { FictionalPrompt } from "./FictionalPrompt";
import {
  forgetSessionState,
  sessionClearedEvent,
  useSessionState,
} from "../shared/session-state";
import { navigate, useNavigationLock } from "../app/navigation";
import "./intake.css";

export function Intake() {
  const { t } = useLocale();
  const [reference, setReference] = useSessionState("intake:reference", "");
  const [title, setTitle] = useSessionState("intake:title", "");
  const [sources, setSources] = useSessionState<SourceUpload[]>(
    "intake:sources",
    [],
  );
  const [confirmed, setConfirmed] = useSessionState("intake:confirmed", false);
  const [busy, setBusy] = useState(false);
  useNavigationLock(busy);
  const [error, setError] = useSessionState<unknown>("intake:error", undefined);
  const [prompt, setPrompt] = useState(false);
  const [dragging, setDragging] = useState(false);
  const reduced = useReducedMotion();
  const dirty = Boolean(reference || title || sources.length);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    const removeWarning = () =>
      window.removeEventListener("beforeunload", warn);
    window.addEventListener(sessionClearedEvent, removeWarning);
    return () => {
      removeWarning();
      window.removeEventListener(sessionClearedEvent, removeWarning);
    };
  }, [dirty]);
  const detail = error instanceof RequestFailure ? error.detail : undefined;
  const admission = admissionError(sources);
  useEffect(() => {
    if (!detail?.resets_at) return;
    const delay = Date.parse(detail.resets_at) - Date.now();
    if (!Number.isFinite(delay)) return;
    const timer = setTimeout(
      () => setError(undefined),
      Math.max(0, Math.min(delay, 2_147_483_647)),
    );
    return () => clearTimeout(timer);
  }, [detail]);
  function changeSources(files: File[]) {
    setSources((previous) => addSources(previous, files));
    setError(undefined);
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      busy ||
      !confirmed ||
      !sources.length ||
      admission ||
      detail?.retryable === false
    )
      return;
    setBusy(true);
    setError(undefined);
    try {
      const proposal = await createProposal({
        external_reference: reference,
        matter_title: title,
        synthetic_confirmation: confirmed,
        sources,
      });
      ["reference", "title", "sources", "confirmed", "error"].forEach((key) =>
        forgetSessionState("intake:" + key),
      );
      navigate("/app/matter-proposals/" + encodeURIComponent(proposal.id));
    } catch (failure) {
      setError(failure);
      setBusy(false);
    }
  }
  return (
    <div className="page intake-page">
      <a className="back-link" href="/app">
        {t("Back to Matters")}
      </a>
      <div className="page-heading">
        <div>
          <h1>{t("New proposal")}</h1>
          <p>
            {t(
              "Bring synthetic sources together. Review the relationships before accepting a Matter.",
            )}
          </p>
        </div>
      </div>
      <div className="intake-layout">
        <form onSubmit={submit} className="intake-form">
          <fieldset disabled={busy}>
            <legend>{t("Matter identity")}</legend>
            <label>
              {t("External Matter reference")}
              <input
                name="external_reference"
                maxLength={100}
                required
                value={reference}
                onChange={(event) => {
                  setReference(event.target.value);
                  setError(undefined);
                }}
              />
            </label>
            <p className="field-help">
              {t("Use the reference from your existing Matter system.")}
            </p>
            <label>
              {t("Matter title")}
              <input
                name="matter_title"
                maxLength={200}
                required
                value={title}
                onChange={(event) => {
                  setTitle(event.target.value);
                  setError(undefined);
                }}
              />
            </label>
          </fieldset>
          <fieldset disabled={busy}>
            <legend>{t("Source documents")}</legend>
            <p className="field-help">
              {t(
                "One to five text-layer PDFs. Up to 10 MiB combined, 50 pages per PDF and 100,000 extracted characters in total. Scanned and encrypted PDFs are unsupported.",
              )}
            </p>
            <button
              type="button"
              className="text-button source-help"
              onClick={() => setPrompt(true)}
            >
              {t("Need a fictional source?")}
            </button>
            <label
              className={"file-drop" + (dragging ? " dragging" : "")}
              onDragOver={(event) => {
                event.preventDefault();
                if (!busy) setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                if (!busy) changeSources(Array.from(event.dataTransfer.files));
              }}
            >
              <Icon name="file" />
              <strong>
                {t(sources.length ? "Add PDF sources" : "Choose PDF sources")}
              </strong>
              <span>{t("Drop PDFs here or choose files")}</span>
              <input
                name="pdf"
                type="file"
                multiple
                accept=".pdf,application/pdf"
                aria-label={t("PDF sources")}
                onChange={(event) => {
                  changeSources(Array.from(event.target.files ?? []));
                  event.target.value = "";
                }}
              />
            </label>
            {admission && (
              <p className="error-text" role="alert">
                {t(admission)}
              </p>
            )}
            <ol className="source-uploads">
              <AnimatePresence initial={false}>
                {sources.map((source, index) => (
                  <motion.li
                    layout="position"
                    key={source.id}
                    initial={{ opacity: 0, y: reduced ? 0 : 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, transition: { duration: 0.08 } }}
                    transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
                  >
                    <div className="source-upload-heading">
                      <span>
                        <Icon name="file" />
                        {source.pdf.name}
                      </span>
                      <button
                        type="button"
                        className="text-button danger"
                        aria-label={t("Remove {filename}", {
                          filename: source.pdf.name,
                        })}
                        onClick={() => {
                          setSources((previous) =>
                            previous.filter((item) => item.id !== source.id),
                          );
                          setError(undefined);
                        }}
                      >
                        {t("Remove")}
                      </button>
                    </div>
                    <label>
                      {t("Source {number} title", { number: index + 1 })}
                      <input
                        name={"source_title_" + index}
                        maxLength={200}
                        required
                        value={source.title}
                        onChange={(event) => {
                          setSources((previous) =>
                            previous.map((item) =>
                              item.id === source.id
                                ? { ...item, title: event.target.value }
                                : item,
                            ),
                          );
                          setError(undefined);
                        }}
                      />
                    </label>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ol>
          </fieldset>
          <fieldset disabled={busy}>
            <legend>{t("Review and submit")}</legend>
            <label className="consent">
              <input
                type="checkbox"
                required
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
              />
              <span>
                {t(
                  "I confirm that this material is synthetic or fictional and contains no real confidential client information.",
                )}
              </span>
            </label>
          </fieldset>
          {error !== undefined && <ErrorNotice error={error} />}
          <div className="form-actions">
            <button
              className="button primary"
              type="submit"
              disabled={
                busy ||
                !confirmed ||
                !sources.length ||
                !!admission ||
                detail?.retryable === false
              }
            >
              {t(
                busy
                  ? "Uploading and analysing…"
                  : detail?.outcome_unknown
                    ? "Check reference and retry"
                    : detail?.retryable
                      ? "Retry analysis"
                      : "Upload and analyse",
              )}
            </button>
            <a href="/app">{t("Cancel")}</a>
          </div>
          <p className="field-help" role={busy ? "status" : undefined}>
            {t(
              busy
                ? "Keep this page open while the proposal is prepared. Do not submit again."
                : detail?.outcome_unknown
                  ? "Your entries and selected PDFs are preserved. A retry checks for an existing reference before another analysis."
                  : "A proposal is saved only after analysis succeeds. Keep this page open during analysis.",
            )}
          </p>
          {!busy && (
            <p className="draft-note">
              {t(
                "Your entries and PDFs stay in this tab when you visit another page. Closing or reloading the tab clears them.",
              )}
            </p>
          )}
        </form>
      </div>
      <AnimatePresence>
        {prompt && <FictionalPrompt onClose={() => setPrompt(false)} />}
      </AnimatePresence>
    </div>
  );
}
