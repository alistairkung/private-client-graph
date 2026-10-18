import { useMemo, useRef, useState } from "react";
import {
  motion,
  useMotionValueEvent,
  useScroll,
  useTransform,
} from "motion/react";
import type { CanonicalState } from "../../shared/contracts";
import { useLocale } from "../../shared/locale";
import { relationshipWords, useLandingCopy } from "./copy";
import { useStoryCopy } from "./story-copy";
import { DocumentMontage } from "./DocumentMontage";
import { StoryGraph } from "./StoryGraph";
import { SourceReview } from "./SourceReview";
import { useDocumentOrigins, useStoryReducedMotion } from "./useDocumentStory";
import "./document-story.css";

export function DocumentStory({ state }: { state: CanonicalState }) {
  const copy = useStoryCopy();
  const landingCopy = useLandingCopy();
  const { locale } = useLocale();
  const track = useRef<HTMLDivElement>(null);
  const note = useRef<HTMLElement>(null);
  const review = useRef<HTMLDivElement>(null);
  const holder = useRef<HTMLDivElement>(null);
  const drawing = useRef<HTMLDivElement>(null);
  const reduced = useStoryReducedMotion();
  const { scrollYProgress } = useScroll({
    target: track,
    offset: ["start start", "end end"],
  });
  const [exploring, setExploring] = useState(false);
  const [selected, setSelected] = useState(0);
  useMotionValueEvent(scrollYProgress, "change", (value) =>
    setExploring(value >= 0.96),
  );
  const active = reduced || exploring;
  const headingOpacity = useTransform(scrollYProgress, [0.62, 0.69], [0, 1]);
  const graphX = useTransform(scrollYProgress, [0.86, 0.96], ["46%", "0%"]);
  const sourceOpacity = useTransform(scrollYProgress, [0.87, 0.97], [0, 1]);
  const sourceX = useTransform(scrollYProgress, [0.87, 0.97], [35, 0]);
  const origins = useDocumentOrigins(
    state,
    reduced,
    note,
    drawing,
    holder,
    locale,
  );
  const edge = state.relationships[selected];
  const evidence = useMemo(
    () =>
      edge
        ? state.evidence.filter((item) => edge.evidence_ids.includes(item.id))
        : [],
    [edge, state.evidence],
  );
  const source =
    state.sources.find((item) =>
      evidence.some((quote) => quote.source_id === item.id),
    ) ?? state.sources[0];
  const name = (id: string) =>
    state.entities.find((item) => item.id === id)?.name ?? id;
  const statement = edge
    ? `${name(edge.source)} — ${relationshipWords[locale][edge.type]} — ${name(edge.target)}`
    : copy.choose;
  function skipToReview() {
    if (!track.current || !review.current) return;
    if (reduced)
      review.current.scrollIntoView({ behavior: "instant", block: "start" });
    else
      window.scrollTo({
        top:
          track.current.getBoundingClientRect().top +
          window.scrollY +
          track.current.offsetHeight -
          window.innerHeight,
        behavior: "instant",
      });
    setExploring(true);
    requestAnimationFrame(() => review.current?.focus({ preventScroll: true }));
  }
  return (
    <div
      className={`landing-story${reduced ? " landing-story-static" : ""}`}
      role="region"
      aria-label={landingCopy.example}
      data-story-mode={reduced ? "static" : "scroll"}
    >
      <div ref={track} className="landing-story-track">
        <div className="landing-story-stage">
          <a
            className="landing-story-skip"
            href="#landing-story-review"
            onClick={(event) => {
              event.preventDefault();
              skipToReview();
            }}
          >
            {copy.skip}
          </a>
          <DocumentMontage
            state={state}
            progress={scrollYProgress}
            reduced={reduced}
            noteRef={note}
            hidden={!reduced && exploring}
          />
          <div
            id="landing-story-review"
            ref={review}
            tabIndex={-1}
            className="landing-story-graph-scene"
            inert={!active}
            aria-hidden={!active}
          >
            <motion.div
              ref={holder}
              className="landing-story-graph-holder"
              style={reduced ? undefined : { x: graphX }}
            >
              <motion.div
                className="landing-story-graph-heading"
                style={reduced ? undefined : { opacity: headingOpacity }}
              >
                <h2>{copy.graphTitle}</h2>
                <p>{copy.working}</p>
              </motion.div>
              <StoryGraph
                state={state}
                progress={scrollYProgress}
                reduced={reduced}
                selected={selected}
                onSelect={setSelected}
                origins={origins}
                drawingRef={drawing}
              />
            </motion.div>
            <motion.div
              className="landing-story-source-holder"
              style={
                reduced ? undefined : { opacity: sourceOpacity, x: sourceX }
              }
            >
              {source ? (
                <SourceReview
                  source={source}
                  evidence={evidence}
                  relationship={statement}
                  reduced={reduced}
                  active={active}
                />
              ) : (
                <p>{copy.unavailable}</p>
              )}
            </motion.div>
          </div>
          <p className="landing-story-notice">{copy.finalNotice}</p>
        </div>
      </div>
    </div>
  );
}
