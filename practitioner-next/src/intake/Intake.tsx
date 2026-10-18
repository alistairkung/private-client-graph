import { useEffect, useState, type FormEvent } from "react";
import { createProposal, RequestFailure } from "../shared/api";
import type { SourceUpload } from "../shared/contracts";
import { ErrorNotice } from "../shared/Feedback";
import { Icon } from "../shared/Icon";
import { useLocale } from "../shared/locale";
import { admissionError, addSources } from "./uploads";
import { FictionalPrompt } from "./FictionalPrompt";
import "./intake.css";

export function Intake() {
  const { t } = useLocale();
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const [sources, setSources] = useState<SourceUpload[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const [prompt, setPrompt] = useState(false);
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
      window.location.assign(
        "/app/matter-proposals/" + encodeURIComponent(proposal.id),
      );
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
            <label className="file-drop">
              <Icon name="file" />
              <strong>
                {t(sources.length ? "Add PDF sources" : "Choose PDF sources")}
              </strong>
              <span>{t("Select synthetic or fictional documents only")}</span>
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
              {sources.map((source, index) => (
                <li key={source.id}>
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
                </li>
              ))}
            </ol>
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
        </form>
        <aside className="intake-guide">
          <h2>{t("From source to review")}</h2>
          <div>
            <span className="guide-marker" />
            <h3>{t("Read together")}</h3>
            <p>
              {t(
                "Text is acquired from every PDF and analysed together. Each source keeps its own title and Evidence.",
              )}
            </p>
          </div>
          <div>
            <span className="guide-marker" />
            <h3>{t("Follow the Evidence")}</h3>
            <p>
              {t(
                "Inspect each proposed relationship beside the exact passage that supports it.",
              )}
            </p>
          </div>
          <div>
            <span className="guide-marker" />
            <h3>{t("Decide explicitly")}</h3>
            <p>
              {t(
                "Confirm the complete proposal to create current Matter state, or discard it.",
              )}
            </p>
          </div>
          <button className="text-button" onClick={() => setPrompt(true)}>
            {t("Need a fictional source?")}
          </button>
        </aside>
      </div>
      {prompt && <FictionalPrompt onClose={() => setPrompt(false)} />}
    </div>
  );
}
