import { useEffect, useMemo, useRef } from "react";
import type { Evidence, Source } from "../../shared/contracts";

/** Split only at exact source occurrences; joining the pieces preserves the source. */
function highlightedSource(text: string, evidence: Evidence[]) {
  const ranges: { start: number; end: number; ids: string[] }[] = [];
  const quotes = new Map<string, string[]>();
  for (const item of evidence) {
    if (!item.supporting_text) continue;
    quotes.set(item.supporting_text, [
      ...(quotes.get(item.supporting_text) ?? []),
      item.id,
    ]);
  }
  for (const [quote, ids] of quotes) {
    let start = text.indexOf(quote);
    while (start >= 0) {
      ranges.push({ start, end: start + quote.length, ids });
      start = text.indexOf(quote, start + quote.length);
    }
  }
  const boundaries = [
    ...new Set([
      0,
      text.length,
      ...ranges.flatMap((range) => [range.start, range.end]),
    ]),
  ].sort((a, b) => a - b);
  return boundaries.slice(0, -1).map((start, index) => ({
    text: text.slice(start, boundaries[index + 1]),
    start,
    ids: [
      ...new Set(
        ranges
          .filter((range) => range.start <= start && range.end > start)
          .flatMap((range) => range.ids),
      ),
    ],
  }));
}

export function SourceReview({
  source,
  evidence,
  reduced,
  relationship,
  active,
}: {
  source: Source;
  evidence: Evidence[];
  reduced: boolean;
  relationship: string;
  active: boolean;
}) {
  const pane = useRef<HTMLDivElement>(null);
  const applicable = evidence.filter((item) => item.source_id === source.id);
  const parts = useMemo(
    () => highlightedSource(source.text, applicable),
    [source.text, evidence, source.id],
  );
  useEffect(() => {
    if (!active) return;
    const container = pane.current;
    const mark = container?.querySelector("mark");
    if (!container || !mark) return;
    container.scrollTo({
      top:
        container.scrollTop +
        mark.getBoundingClientRect().top -
        container.getBoundingClientRect().top -
        35,
      behavior: reduced ? "instant" : "smooth",
    });
  }, [active, parts, reduced]);
  return (
    <aside
      className="prototype-source-review"
      aria-label="Full source document and exact Evidence"
    >
      <div className="prototype-source-header">
        <h3>{source.title}</h3>
        <p className="prototype-source-meta">
          Source: {source.id} · Evidence:{" "}
          {applicable.map((item) => item.id).join(", ") ||
            "None for this source"}
        </p>
        <p className="prototype-source-selection" aria-live="polite">
          {relationship}
        </p>
      </div>
      <div
        ref={pane}
        className="prototype-source-scroll"
        tabIndex={0}
        aria-label="Scroll full source document"
      >
        <div className="prototype-source-text">
          {parts.map((part) =>
            part.ids.length ? (
              <mark key={part.start} data-evidence-ids={part.ids.join(" ")}>
                {part.text}
              </mark>
            ) : (
              <span key={part.start}>{part.text}</span>
            ),
          )}
        </div>
      </div>
    </aside>
  );
}
