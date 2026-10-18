import { useEffect, useMemo, useRef } from "react";
import type { Evidence, Source } from "../../shared/contracts";
import { sourceHighlights } from "./source-highlights";
import { useStoryCopy } from "./story-copy";

export function SourceReview({
  source,
  evidence,
  reduced,
  relationship,
  active,
  selectionVersion,
}: {
  source: Source;
  evidence: Evidence[];
  reduced: boolean;
  relationship: string;
  active: boolean;
  selectionVersion: number;
}) {
  const copy = useStoryCopy();
  const pane = useRef<HTMLDivElement>(null);
  const applicable = useMemo(
    () => evidence.filter((item) => item.source_id === source.id),
    [evidence, source.id],
  );
  const parts = useMemo(
    () => sourceHighlights(source.text, applicable),
    [source.text, applicable],
  );
  useEffect(() => {
    const container = pane.current;
    const mark = container?.querySelector("mark");
    if (!active || !container || !mark) return;
    let followingSelection = true;
    const cancelScroll = () => {
      followingSelection = false;
      container.scrollTo({ top: container.scrollTop, behavior: "instant" });
    };
    const cancelOnKey = (event: KeyboardEvent) => {
      if (
        [
          "ArrowDown",
          "ArrowUp",
          "PageDown",
          "PageUp",
          "Home",
          "End",
          " ",
        ].includes(event.key)
      )
        cancelScroll();
    };
    container.addEventListener("wheel", cancelScroll, { passive: true });
    container.addEventListener("touchstart", cancelScroll, { passive: true });
    container.addEventListener("pointerdown", cancelScroll);
    container.addEventListener("keydown", cancelOnKey);
    const revealSelection = () => {
      if (!followingSelection) return;
      container.scrollTo({
        top: Math.max(
          0,
          container.scrollTop +
            mark.getBoundingClientRect().top -
            container.getBoundingClientRect().top -
            35,
        ),
        behavior: reduced ? "instant" : "smooth",
      });
    };
    revealSelection();
    const observer = new ResizeObserver(revealSelection);
    observer.observe(container.firstElementChild!);
    return () => {
      observer.disconnect();
      cancelScroll();
      container.removeEventListener("wheel", cancelScroll);
      container.removeEventListener("touchstart", cancelScroll);
      container.removeEventListener("pointerdown", cancelScroll);
      container.removeEventListener("keydown", cancelOnKey);
    };
  }, [active, parts, reduced, selectionVersion]);
  return (
    <aside className="landing-story-source-review" aria-label={copy.sourcePane}>
      <div className="landing-story-source-header">
        <h3>{source.title}</h3>
        <p className="landing-story-source-meta">
          {copy.source}: {source.id} · {copy.evidence}:{" "}
          {applicable.map((item) => item.id).join(", ") ||
            copy.noSourceEvidence}
        </p>
        <p className="landing-story-source-selection" aria-live="polite">
          {relationship}
        </p>
      </div>
      <div
        ref={pane}
        className="landing-story-source-scroll"
        tabIndex={0}
        aria-label={copy.scrollSource}
      >
        <div className="landing-story-source-text">
          {parts.map((part) =>
            part.ids.length ? (
              <mark
                key={`${selectionVersion}-${part.start}`}
                data-evidence-ids={part.ids.join(" ")}
                data-reveal={(selectionVersion > 0 && !reduced) || undefined}
              >
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
