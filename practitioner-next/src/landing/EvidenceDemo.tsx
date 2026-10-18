import { useEffect, useRef, useState } from "react";
import type { AnimationSequence } from "motion";
import { motion, useAnimate, useReducedMotion } from "motion/react";
import type { CanonicalState, Relationship } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { relationshipWords, useLandingCopy } from "./copy";
import { landingPositions, sourceContext } from "./landing-layout";

export function claimStatement(
  state: CanonicalState,
  edge: Relationship,
  locale: "en" | "zh-CN",
) {
  const name = (id: string) =>
    state.entities.find((entity) => entity.id === id)?.name ?? id;
  return `${name(edge.source)} — ${relationshipWords[locale][edge.type]} — ${name(edge.target)}`;
}
export function EvidenceDemo({ state }: { state: CanonicalState }) {
  const copy = useLandingCopy();
  const { locale } = useLocale();
  const reduced = useReducedMotion();
  const [selected, setSelected] = useState(0);
  const [introVisible, setIntroVisible] = useState(!reduced);
  const [scope, animate] = useAnimate();
  const controls = useRef<{ stop: () => void }[]>([]);
  const manual = useRef(false);
  function settleIntro() {
    controls.current.forEach((control) => control.stop());
    setIntroVisible(false);
    const sequence: AnimationSequence = [
      [".landing-paper", { y: 0, opacity: 1 }, { duration: 0 }],
      [
        ".landing-exact",
        { backgroundColor: "#FFF0A6" },
        { at: 0, duration: 0 },
      ],
      [".landing-entity-content", { y: 0, opacity: 1 }, { at: 0, duration: 0 }],
      [".landing-evidence-locator", { opacity: 1 }, { at: 0, duration: 0 }],
    ];
    controls.current = [
      animate(
        sequence.filter(
          (segment) =>
            Array.isArray(segment) &&
            typeof segment[0] === "string" &&
            scope.current?.querySelector(segment[0]),
        ),
      ),
    ];
  }

  useEffect(() => {
    if (
      !state.relationships.length ||
      !scope.current?.querySelector(".landing-exact")
    )
      return;
    if (reduced || manual.current) {
      settleIntro();
      return () => controls.current.forEach((control) => control.stop());
    }
    const sequence = animate([
      [
        ".landing-paper",
        { y: [12, 0], opacity: [0.75, 1] },
        { duration: 0.36 },
      ],
      [
        ".landing-exact",
        { backgroundColor: ["#FFFFFF", "#FFF0A6"] },
        { at: 0.2, duration: 0.28 },
      ],
      [
        ".landing-entity-content",
        { y: [8, 0], opacity: [0.55, 1] },
        { at: 0.43, duration: 0.24 },
      ],
      [
        ".landing-intro-path",
        { pathLength: [0, 1] },
        { at: 0.6, duration: 0.38 },
      ],
      [
        ".landing-evidence-locator",
        { opacity: [0.4, 1] },
        { at: 0.9, duration: 0.16 },
      ],
    ]);
    controls.current = [sequence];
    let disposed = false;
    sequence.then(() => {
      if (!disposed) setIntroVisible(false);
    });
    return () => {
      disposed = true;
      controls.current.forEach((control) => control.stop());
    };
  }, [animate, reduced]);
  const edge = state.relationships[selected];
  const evidence = state.evidence.find(
    (item) => item.id === edge?.evidence_ids[0],
  );
  const source = state.sources.find((item) => item.id === evidence?.source_id);
  const exact =
    source && evidence ? source.text.indexOf(evidence.supporting_text) : -1;
  function choose(index: number) {
    manual.current = true;
    settleIntro();
    setSelected(index);
  }
  const positions = landingPositions(state);
  const context =
    source && evidence && exact >= 0
      ? sourceContext(source.text, exact, evidence.supporting_text.length)
      : undefined;
  return (
    <div
      ref={scope}
      className="landing-demo"
      role="region"
      aria-label={copy.example}
    >
      <div className="landing-demo-top">
        <span>{copy.curated}</span>
        <span>{copy.choose}</span>
      </div>
      <div className="landing-mechanism">
        <motion.article className="landing-paper">
          <div className="landing-paper-heading">
            <span>{copy.source}</span>
            <span>
              {copy.exampleSource} 1 · {source?.id}
            </span>
          </div>
          <h2>{source?.title ?? copy.evidence}</h2>
          <div className="landing-fragment">
            {exact >= 0 && source && evidence ? (
              <>
                <span className="landing-fragment-context">
                  {context?.before}
                </span>
                <mark className="landing-exact" data-evidence-id={evidence.id}>
                  {evidence.supporting_text}
                </mark>
                <span className="landing-fragment-context">
                  {context?.after}
                </span>
              </>
            ) : (
              <p>{copy.missing}</p>
            )}
          </div>
          <div className="landing-evidence-locator">
            <span>{copy.locator}</span>
            <strong>{evidence?.id ?? "—"}</strong>
          </div>
        </motion.article>
        <div className="landing-drawing" role="group" aria-label={copy.diagram}>
          <svg
            className="landing-connectors"
            viewBox="0 0 660 420"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="landing-parent-arrow"
                viewBox="0 0 8 8"
                refX="7"
                refY="4"
                markerWidth="7"
                markerHeight="7"
                orient="auto"
              >
                <path d="m1 1 5 3-5 3" fill="none" stroke="currentColor" />
              </marker>
            </defs>
            {state.relationships.map((item, index) => {
              const from = positions.get(item.source),
                to = positions.get(item.target);
              if (!from || !to) return null;
              const [x, y] = from,
                [tx, ty] = to;
              const parent = item.type === "parent_of";
              const family =
                parent ||
                item.type === "spouse_of" ||
                item.type === "sibling_of";
              return (
                <path
                  key={index}
                  data-source={item.source}
                  data-target={item.target}
                  className={
                    "landing-connector" +
                    (index === selected ? " landing-selected-line" : "")
                  }
                  d={`M ${x} ${y} L ${tx} ${ty}`}
                  fill="none"
                  stroke={index === selected ? "#E5EFE7" : "#A6C4B1"}
                  strokeWidth={index === selected ? 3 : 1.3}
                  strokeDasharray={family ? "5 5" : undefined}
                  markerEnd={parent ? "url(#landing-parent-arrow)" : undefined}
                />
              );
            })}
            {introVisible &&
              edge &&
              positions.has(edge.source) &&
              positions.has(edge.target) && (
                <g aria-hidden="true" pointerEvents="none">
                  <motion.path
                    className="landing-intro-path"
                    d={`M ${positions.get(edge.source)!.join(" ")} L ${positions.get(edge.target)!.join(" ")}`}
                    fill="none"
                    stroke="#E5EFE7"
                    strokeWidth={3}
                  />
                </g>
              )}
          </svg>
          {state.entities.map((entity) => {
            const [x, y] = positions.get(entity.id)!;
            return (
              <div
                key={entity.id}
                data-entity-id={entity.id}
                className={
                  "landing-entity landing-entity-" +
                  entity.type +
                  (edge && [edge.source, edge.target].includes(entity.id)
                    ? " landing-entity-active"
                    : "")
                }
                style={{
                  left: (x / 660) * 100 + "%",
                  top: (y / 420) * 100 + "%",
                }}
              >
                <div className="landing-entity-content">
                  <svg
                    viewBox={
                      entity.type === "trust" ? "0 0 70 52" : "0 0 24 24"
                    }
                    aria-hidden="true"
                  >
                    {entity.type === "trust" ? (
                      <path d="M35 3 67 49H3Z" />
                    ) : (
                      <circle cx="12" cy="12" r="9" />
                    )}
                  </svg>
                  <span>{entity.name}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="landing-claims" aria-label={copy.active}>
        {state.relationships.map((item, index) => (
          <button
            key={index}
            aria-pressed={selected === index}
            aria-label={claimStatement(state, item, locale)}
            onClick={() => choose(index)}
          >
            <span>
              {state.entities.find((entity) => entity.id === item.source)?.name}
            </span>
            <strong>{relationshipWords[locale][item.type]}</strong>
            <span>
              {state.entities.find((entity) => entity.id === item.target)?.name}
            </span>
          </button>
        ))}
      </div>
      {!edge && <p>{copy.noClaims}</p>}
      <p className="landing-demo-caption">{copy.curatedNote}</p>
    </div>
  );
}
