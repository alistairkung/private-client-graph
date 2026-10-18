import { useLocale } from "../../../shared/locale";
import { useEffect, useRef } from "react";

export function SourcePanel({
  source,
  practitioner = false,
  title = "Attendance note",
  span,
  activation,
  highlightId,
  focusRequest = 0,
  onReturn,
}: {
  source: string;
  practitioner?: boolean;
  title?: string;
  activation?: number;
  span?: { start: number; end: number };
  highlightId?: string;
  focusRequest?: number;
  onReturn?: () => void;
}) {
  const { t } = useLocale();
  const highlight = useRef<HTMLElement>(null);
  useEffect(() => {
    highlight.current?.scrollIntoView({ behavior: "instant", block: "center" });
  }, [span?.start, span?.end, activation]);
  useEffect(() => {
    if (!focusRequest) return;
    highlight.current?.focus();
    highlight.current?.scrollIntoView({ behavior: "instant", block: "center" });
  }, [focusRequest]);
  return (
    <section className="source-panel panel">
      <div className="panel-heading">
        <div>
          <h2>{practitioner ? t("Authoritative Source") : title}</h2>
        </div>
      </div>
      <div className="document-scroll">
        {practitioner && <h3 className="source-title">{title}</h3>}
        <article aria-label={t("Source document")} className="source-text">
          {span ? (
            <>
              {source.slice(0, span.start)}
              <mark ref={highlight} id={highlightId} tabIndex={-1}>{source.slice(span.start, span.end)}</mark>
              {source.slice(span.end)}
            </>
          ) : (
            source
          )}
        </article>
      </div>
      {span && onReturn && <button className="source-return" onClick={onReturn}>{t("Back to selected relationship")}</button>}
    </section>
  );
}
