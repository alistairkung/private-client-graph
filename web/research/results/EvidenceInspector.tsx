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
  sources,
  onBack,
}: {
  relationship?: RelationshipOutcome;
  source: string | null;
  sources?: { id: string; title: string; text: string }[] | null;
  onBack?: () => void;
}) {
  const [quote, setQuote] = useState<EvidenceQuote>();
  const sourceRef = useRef<HTMLElement>(null);
  const selectedSource = sources?.find((item) => item.id === quote?.source_id);
  const sourceText = sources?.length ? selectedSource?.text ?? null : source;
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
          if (onBack) {
            onBack();
            return;
          }
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
                      <p>Source identity: {item.source_id}</p>
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
          <h3>Frozen Source{selectedSource ? ` · ${selectedSource.title} (${selectedSource.id})` : ""}</h3>
          {sourceText === null ? (
            <p>Source unavailable.</p>
          ) : (
            <article
              ref={sourceRef}
              tabIndex={-1}
              aria-label="Frozen Source"
              className="frozen-source"
            >
              {quote
                ? sourceSegments(sourceText, quote).map((segment, index) =>
                    segment.highlighted ? (
                      <mark key={index}>{segment.text}</mark>
                    ) : (
                      segment.text
                    ),
                  )
                : sourceText}
            </article>
          )}
        </>
      )}
    </aside>
  );
}
