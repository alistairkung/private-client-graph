import { useLayoutEffect, useId, useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useSessionState } from "../shared/session-state";
import type { Evidence, Source } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { exactSpan } from "./presentation";
export function SourceReader({
  sources,
  sourceId,
  evidence,
  onSource,
  onReturn,
  jumpRequest = 0,
  statement,
  active: panelActive = true,
  memoryKey = "review:sources",
}: {
  sources: Source[];
  sourceId: string | null;
  evidence?: Evidence;
  onSource: (id: string) => void;
  onReturn: () => void;
  jumpRequest?: number;
  statement?: string;
  active?: boolean;
  memoryKey?: string;
}) {
  const { t } = useLocale();
  const reduced = useReducedMotion();
  const scope = useId();
  const mark = useRef<HTMLElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const handledJump = useRef(0);
  const [positions, setPositions] = useSessionState<Record<string, number>>(
    memoryKey + ":source-scroll",
    {},
  );
  const source = sources.find((item) => item.id === sourceId);
  const active = evidence && evidence.source_id === source?.id;
  const span =
    active && source
      ? exactSpan(source.text, evidence.supporting_text)
      : undefined;
  useLayoutEffect(() => {
    if (scroll.current)
      scroll.current.scrollTop = sourceId ? (positions[sourceId] ?? 0) : 0;
  }, [sourceId]);
  useLayoutEffect(() => {
    if (!jumpRequest || handledJump.current === jumpRequest || !panelActive)
      return;
    handledJump.current = jumpRequest;
    const target = mark.current;
    const reader = scroll.current;
    if (target && reader) {
      reader.scrollTop = Math.max(
        0,
        reader.scrollTop +
          target.getBoundingClientRect().top -
          reader.getBoundingClientRect().top -
          Math.min(72, reader.clientHeight * 0.2),
      );
      if (sourceId)
        setPositions((previous) => ({
          ...previous,
          [sourceId]: reader.scrollTop,
        }));
      target.focus({ preventScroll: true });
    } else
      document
        .getElementById("sources-heading")
        ?.focus({ preventScroll: true });
  }, [jumpRequest, panelActive, sourceId, evidence?.id]);
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
      {statement && (
        <div className="source-relationship-context">
          <span>{t("Selected relationship")}</span>
          <p>{statement}</p>
        </div>
      )}
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
      <div
        className="source-scroll"
        ref={scroll}
        onScroll={(event) => {
          if (sourceId) {
            const top = event.currentTarget.scrollTop;
            setPositions((previous) => ({ ...previous, [sourceId]: top }));
          }
        }}
      >
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
        {active ? (
          <span>
            {t("Active Evidence")}: {evidence?.id}
          </span>
        ) : (
          <span>{t("Select a relationship to locate its Evidence.")}</span>
        )}
      </footer>
    </section>
  );
}
