import { useEffect, useRef, useState } from "react";
import { useLocale } from "../../../shared/locale";
import type { Preview } from "./api";

export function PublicationReview({
  preview,
  edit,
  reference,
  title,
  setReference,
  setTitle,
  publish,
}: {
  preview: Preview;
  edit: () => void;
  reference: string;
  title: string;
  setReference: (value: string) => void;
  setTitle: (value: string) => void;
  publish: () => void;
}) {
  const { t } = useLocale();
  const heading = useRef<HTMLHeadingElement>(null);
  const [approved, setApproved] = useState(false);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <>
      <div className="discovery-review-heading">
        <h2 ref={heading} tabIndex={-1} className="discovery-title">
          {t("Review exact Sources")}
        </h2>
        <button onClick={edit}>{t("Edit selection")}</button>
      </div>
      <div className="discovery-columns">
        <section className="discovery-papers" aria-label={t("Preview order")}>
          {preview.sources.map((source, index) => (
            <article key={source.id}>
              <p className="discovery-caption">
                {t("Source {number} of {total}", {
                  number: index + 1,
                  total: preview.sources.length,
                })}
              </p>
              <h3>{source.title}</h3>
              <pre>{source.text}</pre>
            </article>
          ))}
        </section>
        <section className="discovery-panel discovery-publication">
          <h2>{t("Publication details")}</h2>
          <label>
            {t("External Matter reference")}
            <input
              required
              maxLength={100}
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            />
          </label>
          <label>
            {t("Matter title")}
            <input
              required
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label className="discovery-consent">
            <input
              type="checkbox"
              checked={approved}
              onChange={(e) => setApproved(e.target.checked)}
            />
            <span>
              {t(
                "I approve publishing these synthetic Sources in this order. Every reader can see their full titles, texts and proposed relationships as soon as the proposal is saved, before Matter confirmation.",
              )}
            </span>
          </label>
          <p className="discovery-caption">
            {t(
              "The Matter reference is also public. Discard cannot retract copies already read or downloaded.",
            )}
          </p>
          <button
            className="button primary"
            disabled={!approved || !title.trim() || !reference.trim()}
            onClick={publish}
          >
            {t("Create public proposal")}
          </button>
        </section>
      </div>
    </>
  );
}
