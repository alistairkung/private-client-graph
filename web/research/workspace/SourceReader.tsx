import { useEffect, useRef, useState } from "react";
import { sourceSegments } from "../results/EvidenceInspector";
import type { EvidenceQuote, Source } from "../shared/contracts";

export type Passage = Pick<EvidenceQuote, "source_id" | "text" | "occurrences">;

export function SourceReader({
  passage,
  source,
  onClose,
}: {
  passage: Passage;
  source?: Source;
  onClose: () => void;
}) {
  const [occurrence, setOccurrence] = useState(0);
  const close = useRef<HTMLButtonElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const total = passage.occurrences.length;
  useEffect(() => {
    close.current?.focus();
  }, []);
  useEffect(() => {
    const frame = content.current;
    const mark = frame?.querySelectorAll("mark")[occurrence];
    if (frame && mark) {
      frame.scrollTop +=
        mark.getBoundingClientRect().top -
        frame.getBoundingClientRect().top -
        8;
    }
  }, [occurrence, passage]);
  let markIndex = 0;
  return (
    <section
      className="source-reader"
      aria-label="Source reader"
      onKeyDown={(event) => {
        if (event.key === "Escape") onClose();
      }}
    >
      <div className="reader-tools">
        <strong>{source?.title ?? passage.source_id}</strong>
        <button
          type="button"
          className="secondary"
          ref={close}
          onClick={onClose}
        >
          Close reader
        </button>
      </div>
      {total > 1 && (
        <div className="reader-tools occurrence-controls">
          <button
            type="button"
            className="secondary"
            disabled={!occurrence}
            aria-label="Previous occurrence"
            onClick={() => setOccurrence(occurrence - 1)}
          >
            ←
          </button>
          <span aria-live="polite">
            Occurrence {occurrence + 1} of {total}
          </span>
          <button
            type="button"
            className="secondary"
            disabled={occurrence === total - 1}
            aria-label="Next occurrence"
            onClick={() => setOccurrence(occurrence + 1)}
          >
            →
          </button>
        </div>
      )}
      <div
        className="reader-text"
        ref={content}
        tabIndex={0}
        role="region"
        aria-label="Full quotation and frozen Source"
      >
        <h6>Full quotation</h6>
        <blockquote>{passage.text}</blockquote>
        <h6>Frozen Source · {passage.source_id}</h6>
        <div className="frozen-source">
          {!source
            ? "Source text unavailable."
            : sourceSegments(source.text, {
                ...passage,
                id: passage.source_id,
              }).map((part, index) =>
                part.highlighted ? (
                  <mark
                    key={index}
                    data-current={markIndex++ === occurrence || undefined}
                  >
                    {part.text}
                  </mark>
                ) : (
                  part.text
                ),
              )}
        </div>
      </div>
    </section>
  );
}
