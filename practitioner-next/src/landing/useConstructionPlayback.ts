import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type RefObject,
} from "react";
import { animate, useMotionValue, useMotionValueEvent } from "motion/react";

const reducedMotionQuery = "(prefers-reduced-motion: reduce)";
function subscribeReducedMotion(onChange: () => void) {
  const query = window.matchMedia?.(reducedMotionQuery);
  query?.addEventListener("change", onChange);
  return () => query?.removeEventListener("change", onChange);
}
function reducedMotionSnapshot() {
  return window.matchMedia?.(reducedMotionQuery).matches ?? false;
}

export type ConstructionPhase =
  | "source"
  | "entities"
  | "relationships"
  | "complete";
export function constructionPhase(time: number): ConstructionPhase {
  if (time >= 4) return "complete";
  if (time >= 1.5) return "relationships";
  if (time >= 0.6) return "entities";
  return "source";
}

/** One stoppable clock owns the illustration; the fetched graph never changes. */
export function useConstructionPlayback(
  scope: RefObject<HTMLDivElement | null>,
) {
  const reduced = useSyncExternalStore(
    subscribeReducedMotion,
    reducedMotionSnapshot,
    () => false,
  );
  const progress = useMotionValue(reduced ? 4 : 0);
  const [phase, setPhase] = useState<ConstructionPhase>(
    reduced ? "complete" : "source",
  );
  const [playback, setPlayback] = useState<"playing" | "paused" | "complete">(
    reduced ? "complete" : "playing",
  );
  const controls = useRef<ReturnType<typeof animate> | null>(null);
  const generation = useRef(0);
  const userPaused = useRef(false);
  const unavailable = useRef({
    hidden: false,
    offscreen: typeof IntersectionObserver !== "undefined",
  });
  const finished = useRef(Boolean(reduced));
  const reducedPreference = useRef(reduced);
  reducedPreference.current = reduced;
  const currentPhase = useRef(phase);
  useMotionValueEvent(progress, "change", (time) => {
    const nextPhase = constructionPhase(time);
    if (nextPhase !== currentPhase.current) {
      currentPhase.current = nextPhase;
      setPhase(nextPhase);
    }
  });

  const settle = useCallback(() => {
    generation.current += 1;
    controls.current?.stop();
    controls.current = null;
    finished.current = true;
    progress.set(4);
    currentPhase.current = "complete";
    setPhase("complete");
    setPlayback("complete");
  }, [progress]);

  const replay = useCallback(() => {
    if (reducedPreference.current) {
      settle();
      return;
    }
    const current = ++generation.current;
    controls.current?.stop();
    userPaused.current = false;
    finished.current = false;
    progress.set(0);
    currentPhase.current = "source";
    setPhase("source");
    const animation = animate(progress, 4, { duration: 4, ease: "linear" });
    controls.current = animation;
    if (unavailable.current.hidden || unavailable.current.offscreen) {
      animation.pause();
      setPlayback("paused");
    } else setPlayback("playing");
    animation.then(() => {
      if (generation.current === current) {
        finished.current = true;
        setPhase("complete");
        setPlayback("complete");
      }
    });
  }, [progress, settle]);

  const synchronizeAvailability = useCallback(() => {
    if (finished.current || !controls.current) return;
    if (
      userPaused.current ||
      unavailable.current.hidden ||
      unavailable.current.offscreen
    ) {
      controls.current.pause();
      setPlayback("paused");
    } else {
      controls.current.play();
      setPlayback("playing");
    }
  }, []);
  const togglePause = () => {
    userPaused.current = !userPaused.current;
    synchronizeAvailability();
  };
  useEffect(() => {
    replay();
    return () => {
      generation.current += 1;
      controls.current?.stop();
    };
  }, [replay]);
  useEffect(() => {
    if (reduced) settle();
  }, [reduced, settle]);
  useEffect(() => {
    const visibility = () => {
      unavailable.current.hidden = document.hidden;
      synchronizeAvailability();
    };
    visibility();
    document.addEventListener("visibilitychange", visibility);
    const observer =
      typeof IntersectionObserver === "undefined"
        ? undefined
        : new IntersectionObserver(
            ([entry]) => {
              unavailable.current.offscreen =
                !entry.isIntersecting || entry.intersectionRatio < 0.2;
              synchronizeAvailability();
            },
            { threshold: 0.2 },
          );
    const drawing = scope.current?.querySelector(".landing-drawing");
    if (drawing) observer?.observe(drawing);
    return () => {
      document.removeEventListener("visibilitychange", visibility);
      observer?.disconnect();
      generation.current += 1;
      controls.current?.stop();
    };
  }, [scope, synchronizeAvailability]);
  return { progress, phase, playback, replay, settle, togglePause, reduced };
}
