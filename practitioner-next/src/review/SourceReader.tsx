import { useEffect, useId, useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import type { Evidence, Source } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { exactSpan } from "./presentation";
export function SourceReader({
  sources,
  sourceId,
  evidence,
  onSource,
  onReturn,
}: {
  sources: Source[];
  sourceId: string | null;
  evidence?: Evidence;
  onSource: (id: string) => void;
  onReturn: () => void;
}) {
  const { t } = useLocale();
  const reduced = useReducedMotion();
  const scope = useId();
  const mark = useRef<HTMLElement>(null);
  const source = sources.find((item) => item.id === sourceId);
  const active = evidence && evidence.source_id === source?.id;
  const span =
    active && source
      ? exactSpan(source.text, evidence.supporting_text)
      : undefined;
  useEffect(() => {
    mark.current?.scrollIntoView?.({ block: "center", behavior: "instant" });
  }, [sourceId, evidence?.id]);
  return (
    <section className="source-panel" aria-labelledby="sources-heading">
      <header className="source-heading">
        <div>
          <h2 id="sources-heading" tabIndex={-1}>
            {t("Sources")}
          </h2>
          <span>{t("Exact source text")}</span>
        </div>
        {evidence && (
          <button className="text-button return-action" onClick={onReturn}>
            {t("Back to relationship")}
          </button>
        )}
      </header>
      <div className="source-tabs" aria-label={t("Choose source")}>
        {sources.map((item, index) => (
          <button
            key={item.id}
            className={sourceId === item.id ? "active" : ""}
            aria-pressed={sourceId === item.id}
            onClick={() => onSource(item.id)}
          >
            <span className="source-number">{index + 1}</span>
            <span>{item.title}</span>
            {sourceId === item.id && (
              <motion.span
                className="source-underline"
                layoutId={reduced ? undefined : scope + "-source"}
                transition={{ type: "spring", visualDuration: 0.18, bounce: 0 }}
              />
            )}
          </button>
        ))}
      </div>
      <div className="source-scroll">
        {source ? (
          <article className="source-document">
            <div className="document-heading">
              <h3>{source.title}</h3>
              <span>
                {t("Source {number}", { number: sources.indexOf(source) + 1 })}
              </span>
            </div>
            {active && !span && (
              <p role="alert" className="notice error">
                {t(
                  "The exact Evidence text could not be located in this source. No approximate highlight is shown.",
                )}
              </p>
            )}
            <div className="source-text">
              {span ? (
                <>
                  {source.text.slice(0, span.start)}
                  <mark
                    ref={mark}
                    data-evidence-id={evidence?.id}
                    tabIndex={-1}
                  >
                    {source.text.slice(span.start, span.end)}
                  </mark>
                  {source.text.slice(span.end)}
                </>
              ) : (
                source.text
              )}
            </div>
          </article>
        ) : (
          <div className="empty">
            {t(
              sources.length
                ? "The Evidence source could not be found. Select a source to continue."
                : "No source text was returned.",
            )}
          </div>
        )}
      </div>
      <footer className="source-footer">
        {evidence ? (
          <span>
            {t("Active Evidence")}: {evidence.id}
          </span>
        ) : (
          <span>{t("Select a relationship to locate its Evidence.")}</span>
        )}
      </footer>
    </section>
  );
}
