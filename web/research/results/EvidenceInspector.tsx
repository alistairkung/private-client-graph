import { useEffect, useRef, useState } from "react";
import type { EvidenceQuote, RelationshipOutcome } from "../shared/contracts";

export function sourceSegments(
  source: string,
  quote: EvidenceQuote,
): { text: string; highlighted: boolean }[] {
  const characters = Array.from(source);
  const segments: { text: string; highlighted: boolean }[] = [];
  let cursor = 0;
  // Overlapping textual matches are represented by their union for rendering only.
  for (const [start, end] of quote.occurrences) {
    if (start > cursor)
      segments.push({
        text: characters.slice(cursor, start).join(""),
        highlighted: false,
      });
    if (end > cursor)
      segments.push({
        text: characters.slice(Math.max(cursor, start), end).join(""),
        highlighted: true,
      });
    cursor = Math.max(cursor, end);
  }
  segments.push({
    text: characters.slice(cursor).join(""),
    highlighted: false,
  });
  return segments;
}

export function EvidenceInspector({
  relationship,
  source,
}: {
  relationship?: RelationshipOutcome;
  source: string | null;
}) {
  const [quote, setQuote] = useState<EvidenceQuote>();
  const sourceRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (quote) {
      sourceRef.current?.focus({ preventScroll: true });
      sourceRef.current
        ?.querySelector("mark")
        ?.scrollIntoView({ block: "center", behavior: "instant" });
    }
  }, [quote]);
  return (
    <aside className="evidence-inspector" aria-label="Evidence inspector">
      <a
        className="mobile-back"
        href="#relationships"
        onClick={(event) => {
          event.preventDefault();
          const target = document.getElementById("relationships");
          target?.focus();
          target?.scrollIntoView({ block: "start" });
        }}
      >
        Back to relationships
      </a>
      <h2>Evidence</h2>
      {!relationship ? (
        <p>Select a relationship in this result.</p>
      ) : (
        <>
          <p>
            <strong>
              {relationship.edge[0]} · {relationship.edge[1]} ·{" "}
              {relationship.edge[2]}
            </strong>
          </p>
          {(
            [
              ["Expected", relationship.expected],
              ["Predicted", relationship.predicted],
            ] as const
          ).map(([label, quotes]) => (
            <section key={label} className="evidence-group">
              <h3>{label} Evidence</h3>
              {quotes.length ? (
                quotes.map((item) => (
                  <div key={item.id}>
                    <blockquote>{item.text}</blockquote>
                    <p className="muted">
                      {item.occurrences.length === 0
                        ? "Exact text not found in frozen Source."
                        : `${item.occurrences.length} exact ${item.occurrences.length === 1 ? "match" : "matches"} in Source`}
                    </p>
                    {item.occurrences.length > 1 && (
                      <p>
                        Multiple occurrences; no authoritative occurrence is
                        asserted.
                      </p>
                    )}
                    <button
                      disabled={!item.occurrences.length}
                      onClick={() => setQuote(item)}
                    >
                      View {label.toLowerCase()} in Source
                    </button>
                    <details>
                      <summary>Evidence identity</summary>
                      <p>{item.id}</p>
                      <p>Source SHA-256: {item.source_id}</p>
                    </details>
                  </div>
                ))
              ) : (
                <p>
                  {label === "Predicted" && relationship.outcome === "missing"
                    ? "No predicted relationship"
                    : label === "Expected" && relationship.outcome === "extra"
                      ? "No expected relationship"
                      : "Evidence unavailable"}
                </p>
              )}
            </section>
          ))}
          <h3>Frozen Source</h3>
          {source === null ? (
            <p>Source unavailable.</p>
          ) : (
            <article
              ref={sourceRef}
              tabIndex={-1}
              aria-label="Frozen Source"
              className="frozen-source"
            >
              {quote
                ? sourceSegments(source, quote).map((segment, index) =>
                    segment.highlighted ? (
                      <mark key={index}>{segment.text}</mark>
                    ) : (
                      segment.text
                    ),
                  )
                : source}
            </article>
          )}
        </>
      )}
    </aside>
  );
}
