import { useEffect, useRef } from "react";

export function SourcePanel({
  source,
  practitioner = false,
  title = "Attendance note",
  span,
  activation,
  scrollWithinPanel = false,
  scrollId,
  onInteraction,
}: {
  source: string;
  practitioner?: boolean;
  title?: string;
  activation?: number;
  span?: { start: number; end: number };
  scrollWithinPanel?: boolean;
  scrollId?: string;
  onInteraction?: () => void;
}) {
  const highlight = useRef<HTMLElement>(null);
  const scroller = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!highlight.current) return;
    if (scrollWithinPanel && scroller.current) {
      const panel = scroller.current;
      const mark = highlight.current.getBoundingClientRect();
      // Only move the source viewport: scrollIntoView also moves the landing page.
      panel.scrollTop += mark.top - panel.getBoundingClientRect().top
        - (panel.clientHeight - mark.height) / 2;
    } else {
      highlight.current.scrollIntoView({ behavior: "instant", block: "center" });
    }
  }, [span?.start, span?.end, activation, scrollWithinPanel]);
  return (
    <section className="source-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{practitioner ? "Authoritative source" : "The source"}</p>
          <h2>{title}</h2>
        </div>
        <span className="pill">Read-only</span>
      </div>
      <div className="document-scroll" ref={scroller} id={scrollId} tabIndex={0}
        role="region" aria-label="Scrollable source" onWheel={onInteraction}>
        <article aria-label="Source document" className="source-text">
          {span ? (
            <>
              {source.slice(0, span.start)}
              <mark ref={highlight}>{source.slice(span.start, span.end)}</mark>
              {source.slice(span.end)}
            </>
          ) : (
            source
          )}
        </article>
      </div>
    </section>
  );
}
