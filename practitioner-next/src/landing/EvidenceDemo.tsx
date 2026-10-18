import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  motion,
  useTransform,
  useMotionValueEvent,
  type MotionValue,
} from "motion/react";
import type { CanonicalState, Relationship } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { relationshipWords, useLandingCopy } from "./copy";
import {
  canonicalSourceExcerpts,
  sourceContext,
  sourceEntitySpans,
} from "./landing-layout";
import { ConstructionDiagram } from "./ConstructionDiagram";
import { useConstructionPlayback } from "./useConstructionPlayback";

export function claimStatement(
  state: CanonicalState,
  edge: Relationship,
  locale: "en" | "zh-CN",
) {
  const name = (id: string) =>
    state.entities.find((entity) => entity.id === id)?.name ?? id;
  return `${name(edge.source)} — ${relationshipWords[locale][edge.type]} — ${name(edge.target)}`;
}
function ClaimButton({
  state,
  edge,
  index,
  selected,
  progress,
  choose,
}: {
  state: CanonicalState;
  edge: Relationship;
  index: number;
  selected: boolean;
  progress: MotionValue<number>;
  choose: () => void;
}) {
  const { locale } = useLocale();
  const opacity = useTransform(() =>
    Math.max(0, Math.min(1, (progress.get() - 1.5 - index * 0.3) / 0.3)),
  );
  const [available, setAvailable] = useState(false);
  useEffect(() => {
    setAvailable(progress.get() >= 1.5 + index * 0.3);
  }, [index, progress]);
  useMotionValueEvent(progress, "change", (time) => {
    setAvailable(time >= 1.5 + index * 0.3);
  });
  return (
    <motion.button
      style={{ opacity }}
      disabled={!available}
      aria-pressed={selected}
      aria-label={claimStatement(state, edge, locale)}
      onClick={choose}
    >
      <span>
        {state.entities.find((entity) => entity.id === edge.source)?.name}
      </span>
      <strong>{relationshipWords[locale][edge.type]}</strong>
      <span>
        {state.entities.find((entity) => entity.id === edge.target)?.name}
      </span>
    </motion.button>
  );
}

export function EvidenceDemo({ state }: { state: CanonicalState }) {
  const copy = useLandingCopy();
  const scope = useRef<HTMLDivElement>(null);
  const id = useId();
  const [selected, setSelected] = useState(0);
  const [capability, setCapability] = useState<"builder" | "evidence">(
    "builder",
  );
  const playback = useConstructionPlayback(scope);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const pauseButton = useRef<HTMLButtonElement | null>(null);
  const replayButton = useRef<HTMLButtonElement | null>(null);
  const fragment = useRef<HTMLDivElement | null>(null);
  const retainPlaybackFocus = useCallback(
    (element: HTMLButtonElement | null) => {
      if (!element && pauseButton.current === document.activeElement) {
        replayButton.current?.focus();
      }
      pauseButton.current = element;
    },
    [],
  );
  const capabilities = [
    { id: "builder", title: copy.buildTitle, body: copy.buildBody },
    { id: "evidence", title: copy.traceTitle, body: copy.traceBody },
  ] as const;
  const active = capability === "builder" ? 0 : 1;
  function switchCapability(index: number) {
    if (index === 1) playback.settle();
    setCapability(capabilities[index].id);
  }
  function navigateTabs(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    let next: number;
    if (["ArrowRight", "ArrowDown"].includes(event.key)) next = (index + 1) % 2;
    else if (["ArrowLeft", "ArrowUp"].includes(event.key))
      next = (index + 1) % 2;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = 1;
    else return;
    event.preventDefault();
    switchCapability(next);
    tabs.current[next]?.focus();
  }
  function choose(index: number) {
    playback.settle();
    setSelected(index);
    setCapability("evidence");
  }
  const edge = state.relationships[selected];
  const evidence = state.evidence.find(
    (item) => item.id === edge?.evidence_ids[0],
  );
  const source = state.sources.find((item) => item.id === evidence?.source_id);
  const exact =
    source && evidence ? source.text.indexOf(evidence.supporting_text) : -1;
  const context =
    source && evidence && exact >= 0
      ? sourceContext(source.text, exact, evidence.supporting_text.length)
      : undefined;
  useLayoutEffect(() => {
    const panel = fragment.current;
    if (!panel) return;
    panel.scrollTop = 0;
    const mark = panel.querySelector("mark");
    if (capability === "evidence" && mark) {
      const panelBounds = panel.getBoundingClientRect();
      const markBounds = mark.getBoundingClientRect();
      if (markBounds.bottom > panelBounds.bottom) {
        panel.scrollTop = Math.max(0, markBounds.top - panelBounds.top - 8);
      }
    }
  }, [capability, evidence?.id]);
  const captions = {
    source: copy.phaseSource,
    entities: copy.phaseEntities,
    relationships: copy.phaseRelationships,
    complete: copy.phaseComplete,
  };
  return (
    <div
      ref={scope}
      className="landing-demo"
      role="region"
      aria-label={copy.example}
      data-capability={capability}
      data-playback={playback.playback}
      data-construction-phase={playback.phase}
    >
      <div
        className="landing-capabilities"
        role="tablist"
        aria-label={copy.capabilities}
      >
        {capabilities.map((item, index) => (
          <button
            key={item.id}
            role="tab"
            id={`${id}-${item.id}`}
            aria-label={item.title}
            aria-describedby={`${id}-${item.id}-description`}
            aria-selected={active === index}
            aria-controls={`${id}-stage`}
            tabIndex={active === index ? 0 : -1}
            ref={(element) => {
              tabs.current[index] = element;
            }}
            onKeyDown={(event) => navigateTabs(event, index)}
            onClick={() => switchCapability(index)}
          >
            {active === index && (
              <motion.span
                className="landing-capability-indicator"
                layoutId={`${id}-indicator`}
                transition={{
                  type: "spring",
                  stiffness: 700,
                  damping: 53,
                  mass: 1,
                }}
              />
            )}
            <strong>{item.title}</strong>
            <span id={`${id}-${item.id}-description`}>{item.body}</span>
          </button>
        ))}
      </div>
      <div
        className="landing-capability-stage"
        role="tabpanel"
        id={`${id}-stage`}
        aria-labelledby={`${id}-${capability}`}
      >
        <div className="landing-demo-top">
          <span>{copy.curated}</span>
          <span>{copy.illustrative}</span>
        </div>
        <div className="landing-mechanism">
          <article className="landing-paper" data-source-id={source?.id}>
            <div className="landing-paper-heading">
              <span>
                {capability === "builder" ? copy.sourceExcerpts : copy.source}
              </span>
              <span>
                {copy.exampleSource} 1 · {source?.id}
              </span>
            </div>
            <h2>{source?.title ?? copy.evidence}</h2>
            <div className="landing-source-reading">
              <div
                className="landing-source-excerpts"
                aria-hidden={capability !== "builder"}
              >
                {source &&
                  canonicalSourceExcerpts(state, source.id).map(
                    (text, index) => (
                      <p className="landing-source-excerpt" key={index}>
                        {sourceEntitySpans(
                          text,
                          state.entities.map((entity) => entity.name),
                        ).map((part, partIndex) => (
                          <span
                            key={partIndex}
                            className={
                              part.entity ? "landing-source-entity" : undefined
                            }
                          >
                            {part.text}
                          </span>
                        ))}
                      </p>
                    ),
                  )}
              </div>
              <div
                ref={fragment}
                className="landing-fragment"
                aria-hidden={capability !== "evidence"}
              >
                {capability === "evidence" &&
                  (exact >= 0 && source && evidence ? (
                    <>
                      <span className="landing-fragment-context">
                        {context?.before}
                      </span>
                      <mark
                        className="landing-exact"
                        data-evidence-id={evidence.id}
                      >
                        {evidence.supporting_text}
                      </mark>
                      <span className="landing-fragment-context">
                        {context?.after}
                      </span>
                    </>
                  ) : (
                    <p>{copy.missing}</p>
                  ))}
              </div>
            </div>
            <div className="landing-evidence-locator">
              <span>{copy.locator}</span>
              <strong>{evidence?.id ?? "—"}</strong>
            </div>
          </article>
          <ConstructionDiagram
            state={state}
            selected={selected}
            markerId={`${id}-parent-arrow`}
            progress={playback.progress}
            label={copy.diagram}
          />
        </div>
        <div className="landing-playback-bar">
          <motion.p
            key={capability}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.16 }}
            className="landing-construction-caption"
            aria-live="polite"
          >
            {capability === "builder" ? captions[playback.phase] : copy.choose}
          </motion.p>
          <div
            className="landing-playback-controls"
            aria-label={copy.sequenceControls}
          >
            {capability === "builder" && playback.playback !== "complete" && (
              <button ref={retainPlaybackFocus} onClick={playback.togglePause}>
                {playback.playback === "playing" ? copy.pause : copy.resume}
              </button>
            )}
            <button
              ref={replayButton}
              onClick={() => {
                setCapability("builder");
                playback.replay();
              }}
            >
              {copy.replay}
            </button>
          </div>
        </div>
        <div className="landing-claims" aria-label={copy.active}>
          {state.relationships.map((item, index) => (
            <ClaimButton
              key={index}
              state={state}
              edge={item}
              index={index}
              selected={selected === index}
              progress={playback.progress}
              choose={() => choose(index)}
            />
          ))}
        </div>
        {!edge && <p>{copy.noClaims}</p>}
        <p className="landing-demo-caption">{copy.curatedNote}</p>
      </div>
    </div>
  );
}
