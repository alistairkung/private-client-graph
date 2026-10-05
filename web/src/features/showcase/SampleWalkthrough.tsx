import { useEffect, useMemo, useRef, useState } from "react";
import { ReviewWorkspace } from "../review/ReviewWorkspace";
import { sampleMoments, resolveSamplePassages, type SamplePassage } from "./sample-walkthrough";
import type { CaseAnalysis } from "./types";

export function SampleStory({ passages, active }: { passages?: SamplePassage[]; active?: number }) {
  let index = 0;
  return <aside className="sample-story" aria-label="Case 01 explanation">
    {sampleMoments.map((moment) => <section key={moment.title}>
      <h3>{moment.title}</h3>
      {moment.passages.map((passage) => {
        const current = index++;
        return <div key={`${passage.source}-${passage.type}`} data-passage={current}
          className={`sample-passage${active === current ? " sample-passage-active" : ""}`}>
          <p>{passage.explanation}</p>
          {passages && <blockquote>{passages[current].quote}</blockquote>}
        </div>;
      })}
    </section>)}
  </aside>;
}

export function SampleWalkthrough({ analysis, source, expanded, skipRequested }: {
  analysis: CaseAnalysis;
  source: string;
  expanded: boolean;
  skipRequested: boolean;
}) {
  const passages = useMemo(() => resolveSamplePassages(analysis, source), [analysis, source]);
  const [active, setActive] = useState(0);
  const [userControlled, setUserControlled] = useState(skipRequested || expanded);
  const scene = useRef<HTMLDivElement>(null);
  // Handoff is permanent for this mounted review, including after collapse or resizing.
  useEffect(() => {
    if (skipRequested || expanded) setUserControlled(true);
  }, [skipRequested, expanded]);
  useEffect(() => {
    if (!passages || userControlled || skipRequested || expanded) return;
    const media = window.matchMedia("(min-width: 1200px) and (min-height: 850px) and (prefers-reduced-motion: no-preference)");
    let frame = 0;
    function update() {
      if (!media.matches) return;
      const steps = scene.current?.querySelectorAll<HTMLElement>("[data-passage]");
      if (!steps?.length) return;
      let next = 0;
      steps.forEach((step, index) => {
        if (step.getBoundingClientRect().top <= window.innerHeight * 0.45) next = index;
      });
      setActive(next);
    }
    function schedule() {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    }
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    media.addEventListener("change", schedule);
    schedule();
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      media.removeEventListener("change", schedule);
    };
  }, [passages, userControlled, skipRequested, expanded]);
  return <div ref={scene} className={`sample-scene${passages && !expanded ? " sample-scene-guided" : ""}`}>
    {passages && <SampleStory passages={passages} active={userControlled ? undefined : active} />}
    <div className="sample-review" id="interactive-demonstration" tabIndex={-1}>
      <div className="workspace-bar">
        <span>Choose a relationship. Read what supports it.</span>
        <span className={analysis.execution.mode === "sample" ? "mode sample" : "mode"}>
          {analysis.execution.mode === "live"
            ? "Live analysis · Newly extracted"
            : "Sample analysis · Demonstration fixture"}
        </span>
      </div>
      {passages && <p className="guidance-status">
        {userControlled || skipRequested || expanded
          ? "You control the review. Scrolling will keep your selection."
          : "Guided sample walkthrough. Choose any relationship or Evidence to take control."}
      </p>}
      <ReviewWorkspace embedded source={source} graph={analysis.graph}
        guidedSelection={passages?.[active]} onReviewInteraction={() => setUserControlled(true)} />
    </div>
  </div>;
}
