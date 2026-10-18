import {
  useLayoutEffect,
  useState,
  useSyncExternalStore,
  type RefObject,
} from "react";
import type { CanonicalState } from "../../shared/contracts";
import type { EntityOrigins } from "./StoryGraph";
// The phone graph needs 266px of drawing height to separate its 44px targets.
// Below the corresponding 800px viewport, use the readable in-flow alternative.
const query =
  "(prefers-reduced-motion: reduce), (max-height: 580px), (max-width: 700px) and (max-height: 800px)";
function subscribe(callback: () => void) {
  const media = window.matchMedia(query);
  media.addEventListener("change", callback);
  return () => media.removeEventListener("change", callback);
}
export function useStoryReducedMotion() {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => true,
  );
}

/** Compare stable layout anchors, removing the graph's current review translation. */
export function measureDocumentOrigins(
  note: HTMLElement,
  drawing: HTMLElement,
  holder: HTMLElement,
  mobile: boolean,
): EntityOrigins {
  const translation = new DOMMatrix(getComputedStyle(holder).transform).m41;
  const initialShift = mobile ? 0 : holder.offsetWidth * 0.46;
  const origins: EntityOrigins = new Map();
  for (const anchor of drawing.querySelectorAll<HTMLElement>(
    "[data-entity-id]",
  )) {
    const span = [
      ...note.querySelectorAll<HTMLElement>("[data-source-entity-id]"),
    ].find((item) => item.dataset.sourceEntityId === anchor.dataset.entityId);
    if (!span || !anchor.dataset.entityId) continue;
    const from = span.getClientRects()[0] ?? span.getBoundingClientRect();
    const to = anchor.getBoundingClientRect();
    origins.set(anchor.dataset.entityId, [
      from.left + from.width / 2 - (to.left - translation + initialShift),
      from.top + from.height / 2 - (to.top + 32),
    ]);
  }
  return origins;
}

export function useDocumentOrigins(
  state: CanonicalState,
  reduced: boolean,
  note: RefObject<HTMLElement | null>,
  drawing: RefObject<HTMLDivElement | null>,
  holder: RefObject<HTMLDivElement | null>,
  locale: string,
) {
  const [origins, setOrigins] = useState<EntityOrigins>(new Map());
  useLayoutEffect(() => {
    if (reduced || !note.current || !drawing.current || !holder.current) return;
    let mounted = true;
    const measure = () => {
      if (!mounted || !note.current || !drawing.current || !holder.current)
        return;
      setOrigins(
        measureDocumentOrigins(
          note.current,
          drawing.current,
          holder.current,
          window.matchMedia("(max-width: 700px)").matches,
        ),
      );
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(note.current);
    observer.observe(drawing.current);
    for (const surface of note.current.querySelectorAll(
      ".landing-story-montage-intro, .landing-story-document-deck, .landing-story-document-attendance",
    ))
      observer.observe(surface);
    window.addEventListener("resize", measure);
    void document.fonts?.ready.then(measure);
    return () => {
      mounted = false;
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [state, reduced, note, drawing, holder, locale]);
  return origins;
}
