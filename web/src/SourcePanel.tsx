import { useEffect, useRef } from "react";

export function SourcePanel({
  source,
  span,
  activation,
}: {
  source: string;
  activation?: number;
  span?: { start: number; end: number };
}) {
  const highlight = useRef<HTMLElement>(null);
  useEffect(() => {
    highlight.current?.scrollIntoView({ behavior: "instant", block: "center" });
  }, [span?.start, span?.end, activation]);
  return (
    <section className="source-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">THE SOURCE</p>
          <h2>Attendance note</h2>
        </div>
        <span className="pill">Read-only</span>
      </div>
      <div className="document-scroll">
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
