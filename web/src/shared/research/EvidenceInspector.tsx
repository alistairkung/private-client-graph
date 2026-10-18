import { useEffect, useRef, useState } from "react";
import { useLocale } from "../locale";
export interface EvidenceQuote {
  id: string;
  text: string;
  source_id?: string;
  occurrences: number[][];
}
export interface RelationshipOutcome {
  edge: string[];
  outcome: string;
  expected: EvidenceQuote[];
  predicted: EvidenceQuote[];
}

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
  const { t } = useLocale();
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
    <aside className="evidence-inspector" aria-label={t("Evidence inspector")}>
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
        {t("Back to relationships")}
      </a>
      <h2>{t("Evidence")}</h2>
      {!relationship ? (
        <p>{t("Select a relationship in this result.")}</p>
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
              <h3>{t("{group} Evidence", { group: t(label) })}</h3>
              {quotes.length ? (
                quotes.map((item) => (
                  <div key={item.id}>
                    <blockquote>{item.text}</blockquote>
                    <p className="muted">
                      {item.occurrences.length === 0
                        ? t("Exact text not found in frozen Source.")
                        : t("{count} exact matches in Source", { count: item.occurrences.length })}
                    </p>
                    {item.occurrences.length > 1 && (
                      <p>
                        {t("Multiple occurrences; no authoritative occurrence is asserted.")}
                      </p>
                    )}
                    <button
                      disabled={!item.occurrences.length}
                      onClick={() => setQuote(item)}
                    >
                      {t("View {group} in Source", { group: t(label.toLowerCase()) })}
                    </button>
                    <details>
                      <summary>{t("Evidence identity")}</summary>
                      <p>{item.id}</p>
                      <p>{t("Source identity")}: {item.source_id}</p>
                    </details>
                  </div>
                ))
              ) : (
                <p>
                  {label === "Predicted" && relationship.outcome === "missing"
                    ? t("No predicted relationship")
                    : label === "Expected" && relationship.outcome === "extra"
                      ? t("No expected relationship")
                      : t("Evidence unavailable")}
                </p>
              )}
            </section>
          ))}
          <h3>{t("Frozen Source")}{selectedSource ? ` · ${selectedSource.title} (${selectedSource.id})` : ""}</h3>
          {sourceText === null ? (
            <p>{t("Source unavailable.")}</p>
          ) : (
            <article
              ref={sourceRef}
              tabIndex={-1}
              aria-label={t("Frozen Source")}
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
