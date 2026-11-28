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
  uncertain,
}: {
  preview: Preview;
  edit: () => void;
  reference: string;
  title: string;
  setReference: (value: string) => void;
  setTitle: (value: string) => void;
  publish: () => void;
  uncertain: boolean;
}) {
  const { t } = useLocale();
  const heading = useRef<HTMLHeadingElement>(null);
  const [approved, setApproved] = useState(false);
  const count = preview.sources.length;
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <div className="discovery-columns discovery-review">
      <section className="discovery-panel discovery-preview">
        <div className="discovery-review-heading">
          <h2 ref={heading} tabIndex={-1} className="intake-section-title">
            {t("Review exact Sources")}
          </h2>
          <button onClick={edit} disabled={uncertain}>{t("Edit selection")}</button>
        </div>
        <SourcePreviewReader sources={preview.sources} />
      </section>
      <section className="discovery-panel discovery-publication">
        <h2 className="intake-section-title">{t("Publication details")}</h2>
        <label>
          {t("External Matter reference")}
          <input
            required
            maxLength={100}
            value={reference}
            disabled={uncertain}
            onChange={(event) => setReference(event.target.value)}
          />
        </label>
        <label>
          {t("Matter title")}
          <input
            required
            maxLength={200}
            value={title}
            disabled={uncertain}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <div className="discovery-public-disclosure">
          <p id="discovery-public-disclosure">
            {t("Saving immediately makes the Matter title and reference, full Source titles and texts, and proposed relationships public, before Matter confirmation.")}
            {" "}{t("Discarding the proposal cannot retract copies already read or downloaded.")}
          </p>
          <label className="discovery-consent">
            <input
              type="checkbox"
              checked={approved && !uncertain}
              disabled={uncertain}
              aria-describedby="discovery-public-disclosure"
              onChange={(event) => setApproved(event.target.checked)}
            />
            <span>
              {t(count === 1 ? "I approve publishing this synthetic Source." : "I approve publishing these {count} synthetic Sources in this order.", { count })}
            </span>
          </label>
        </div>
        <button
          className="button primary"
          disabled={uncertain || !approved || !title.trim() || !reference.trim()}
          onClick={publish}
        >
          {t("Create public proposal")}
        </button>
      </section>
    </div>
  );
}

function SourcePreviewReader({ sources }: { sources: Preview["sources"] }) {
  const { t } = useLocale();
  const [index, setIndex] = useState(0);
  const list = useRef<HTMLOListElement>(null);
  const active = useRef<HTMLButtonElement>(null);
  const text = useRef<HTMLDivElement>(null);
  const source = sources[index];
  useEffect(() => {
    const item = active.current;
    const container = list.current;
    if (item && container) {
      const itemBounds = item.getBoundingClientRect();
      const bounds = container.getBoundingClientRect();
      if (itemBounds.top < bounds.top) container.scrollTop += itemBounds.top - bounds.top;
      if (itemBounds.bottom > bounds.bottom) container.scrollTop += itemBounds.bottom - bounds.bottom;
    }
    if (text.current) text.current.scrollTop = 0;
  }, [index]);

  if (!source) return null;
  return (
    <div className="discovery-reader">
      <div className="discovery-reader-index">
        <h3>{t("Publication order")}</h3>
        <ol ref={list} className="discovery-preview-index" aria-label={t("Publication order")}>
          {sources.map((entry, position) => (
            <li key={entry.id}>
              <button
                ref={position === index ? active : undefined}
                aria-pressed={position === index}
                aria-controls="discovery-exact-text"
                onClick={() => setIndex(position)}
              >
                <span className="discovery-source-number">{position + 1}</span>
                <span>{entry.title}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>
      <article className="discovery-exact-source">
        <header aria-live="polite" aria-atomic="true">
          <p className="discovery-caption">
            {t("Source {number} of {total}", { number: index + 1, total: sources.length })}
          </p>
          <h3 id="discovery-exact-title">{source.title}</h3>
        </header>
        <div
          className="discovery-exact-text"
          id="discovery-exact-text"
          ref={text}
          role="region"
          aria-labelledby="discovery-exact-title"
          tabIndex={0}
        >
          <pre>{source.text}</pre>
        </div>
        {sources.length > 1 && (
          <nav className="discovery-reader-nav" aria-label={t("Source reader navigation")}>
            <button aria-disabled={index === 0} onClick={() => index > 0 && setIndex(index - 1)}>
              {t("Previous Source")}
            </button>
            <button aria-disabled={index === sources.length - 1} onClick={() => index < sources.length - 1 && setIndex(index + 1)}>
              {t("Next Source")}
            </button>
          </nav>
        )}
      </article>
    </div>
  );
}
