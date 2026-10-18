import { useLocale } from "../../shared/locale";
import { relationshipWords, useLandingCopy } from "./copy";
import { useId, useLayoutEffect, useState, type RefObject } from "react";
import {
  directionalTarget,
  relationshipLabelPoint,
  type GlyphSize,
} from "./story-geometry";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { CanonicalState, Entity, Relationship } from "../../shared/contracts";
import { landingPositions, type LandingPoint } from "./landing-layout";

export type EntityOrigins = Map<string, readonly [number, number]>;

function GraphEntity({
  entity,
  point,
  index,
  progress,
  reduced,
  origin,
}: {
  entity: Entity;
  point: LandingPoint;
  index: number;
  progress: MotionValue<number>;
  reduced: boolean;
  origin?: readonly [number, number];
}) {
  const start = 0.39 + index * 0.025;
  const opacity = useTransform(progress, [start, start + 0.025], [0, 1]);
  const x = useTransform(progress, [start, start + 0.2], [origin?.[0] ?? 0, 0]);
  const y = useTransform(progress, [start, start + 0.2], [origin?.[1] ?? 0, 0]);
  const glyphOpacity = useTransform(
    progress,
    [start + 0.08, start + 0.2],
    [0, 1],
  );
  // Switch both colors together so a travelling label never loses contrast.
  const nameColor = useTransform(() =>
    progress.get() < start + 0.18 ? "#203d30" : "#f2f5ef",
  );
  const nameBackground = useTransform(() =>
    progress.get() < start + 0.18 ? "#dce8ca" : "#173f31",
  );
  return (
    <div
      className={`landing-story-entity landing-story-entity-${entity.type}`}
      data-entity-id={entity.id}
      style={{
        left: `${(point[0] / 660) * 100}%`,
        top: `${(point[1] / 420) * 100}%`,
      }}
    >
      <motion.div
        className="landing-story-entity-content"
        style={reduced ? undefined : { opacity, x, y }}
      >
        <motion.svg
          viewBox="0 0 48 48"
          aria-hidden="true"
          style={reduced ? undefined : { opacity: glyphOpacity }}
        >
          {entity.type === "trust" ? (
            <path d="M24 4 45 42H3Z" />
          ) : (
            <circle cx="24" cy="24" r="13" />
          )}
        </motion.svg>
        <motion.span
          style={
            reduced
              ? undefined
              : { color: nameColor, backgroundColor: nameBackground }
          }
        >
          {entity.name}
        </motion.span>
      </motion.div>
    </div>
  );
}

function GraphEdge({
  edge,
  index,
  from,
  to,
  end,
  labelAt,
  selected,
  inviting,
  progress,
  reduced,
  onSelect,
  label,
  scope,
}: {
  edge: Relationship;
  index: number;
  from: LandingPoint;
  to: LandingPoint;
  end: LandingPoint;
  labelAt: LandingPoint;
  selected: boolean;
  inviting: boolean;
  progress: MotionValue<number>;
  reduced: boolean;
  onSelect: () => void;
  label: string;
  scope: string;
}) {
  const { locale } = useLocale();
  const start = 0.65 + index * 0.025;
  const draw = useTransform(progress, [start, start + 0.08], [0, 1]);
  const maskOpacity = useTransform(draw, [0, 0.015], [0, 1]);
  const labelOpacity = useTransform(
    progress,
    [start + 0.06, start + 0.09],
    [0, 1],
  );
  const family = ["parent_of", "spouse_of", "sibling_of"].includes(edge.type);
  const path = `M${from.join(" ")} L${end.join(" ")}`;
  const mask = `${scope}-mask-${index}`;
  const arrow = `${scope}-arrow-${index}`;
  return (
    <>
      <svg
        className="landing-story-edge-layer"
        viewBox="0 0 660 420"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <marker
            id={arrow}
            viewBox="0 0 8 8"
            refX="7"
            refY="4"
            markerWidth="6"
            markerHeight="6"
            orient="auto"
          >
            <path
              d="m1 1 5 3-5 3"
              fill="none"
              stroke={selected ? "#e3f1b4" : "#8cae99"}
            />
          </marker>
          <mask
            id={mask}
            maskUnits="userSpaceOnUse"
            x="-60"
            y="-60"
            width="780"
            height="540"
          >
            <motion.path
              d={path}
              fill="none"
              stroke="white"
              strokeWidth="36"
              strokeLinecap="round"
              style={{
                pathLength: reduced ? 1 : draw,
                opacity: reduced ? 1 : maskOpacity,
              }}
            />
          </mask>
        </defs>
        <path
          d={path}
          data-source={edge.source}
          data-target={edge.target}
          className={selected ? "landing-story-edge-selected" : ""}
          strokeDasharray={family ? "5 5" : undefined}
          markerEnd={
            edge.type === "spouse_of" || edge.type === "sibling_of"
              ? undefined
              : `url(#${arrow})`
          }
          mask={`url(#${mask})`}
        />
        {["beneficiary_of", "settlor_of"].includes(edge.type) &&
          labelAt[0] !== (from[0] + to[0]) / 2 && (
            <motion.line
              x1={(from[0] + to[0]) / 2}
              y1={(from[1] + to[1]) / 2}
              x2={labelAt[0]}
              y2={labelAt[1]}
              stroke="#729582"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
              style={{ opacity: reduced ? 1 : labelOpacity }}
            />
          )}
      </svg>
      <motion.button
        className="landing-story-edge-label"
        data-relationship-index={index}
        aria-label={label}
        aria-pressed={selected}
        aria-describedby={inviting ? "landing-story-interaction-hint" : undefined}
        data-inviting={inviting || undefined}
        onClick={onSelect}
        style={{
          left: `${(labelAt[0] / 660) * 100}%`,
          top: `${(labelAt[1] / 420) * 100}%`,
          opacity: reduced ? 1 : labelOpacity,
        }}
      >
        {relationshipWords[locale][edge.type]}
      </motion.button>
    </>
  );
}

export function StoryGraph({
  state,
  progress,
  reduced,
  selected,
  inviting,
  onSelect,
  origins,
  drawingRef,
}: {
  state: CanonicalState;
  progress: MotionValue<number>;
  reduced: boolean;
  selected: number;
  inviting: boolean;
  onSelect: (index: number) => void;
  origins: EntityOrigins;
  drawingRef: RefObject<HTMLDivElement | null>;
}) {
  const { locale } = useLocale();
  const copy = useLandingCopy();
  const scope = useId().replaceAll(":", "");
  const positions = landingPositions(state);
  const [geometry, setGeometry] = useState({
    width: 0,
    height: 0,
    glyphs: new Map<string, GlyphSize>(),
    captionWidths: new Map<string, number>(),
    labelWidths: new Map<number, number>(),
    mobile: false,
  });
  useLayoutEffect(() => {
    const drawing = drawingRef.current;
    if (!drawing) return;
    let mounted = true;
    const measure = () => {
      if (!mounted) return;
      const size = drawing.getBoundingClientRect();
      const glyphs = new Map<string, GlyphSize>();
      const captionWidths = new Map<string, number>();
      const labelWidths = new Map<number, number>();
      for (const entity of drawing.querySelectorAll<HTMLElement>(
        "[data-entity-id]",
      )) {
        const glyph = entity.querySelector("svg")?.getBoundingClientRect();
        const caption = entity.querySelector("span")?.getBoundingClientRect();
        if (caption && entity.dataset.entityId)
          captionWidths.set(entity.dataset.entityId, caption.width);
        if (glyph && entity.dataset.entityId)
          glyphs.set(entity.dataset.entityId, {
            width: glyph.width,
            height: glyph.height,
          });
      }
      for (const label of drawing.querySelectorAll<HTMLElement>(
        "[data-relationship-index]",
      ))
        labelWidths.set(
          Number(label.dataset.relationshipIndex),
          label.getBoundingClientRect().width,
        );
      setGeometry({
        width: size.width,
        height: size.height,
        glyphs,
        captionWidths,
        labelWidths,
        mobile: window.matchMedia("(max-width: 700px)").matches,
      });
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(drawing);
    for (const glyph of drawing.querySelectorAll(
      "[data-entity-id] svg, [data-entity-id] span, [data-relationship-index]",
    ))
      observer.observe(glyph);
    return () => {
      mounted = false;
      observer.disconnect();
    };
  }, [drawingRef, state, reduced]);
  const name = (id: string) =>
    state.entities.find((item) => item.id === id)?.name ?? id;
  const invitationIndex = state.relationships.length > 1 ? 1 : 0;
  return (
    <div
      ref={drawingRef}
      className="landing-story-drawing"
      role="group"
      aria-label={copy.diagram}
    >
      {state.relationships.map((edge, index) => (
        <GraphEdge
          key={`${edge.source}-${edge.type}-${edge.target}`}
          edge={edge}
          index={index}
          from={positions.get(edge.source)!}
          to={positions.get(edge.target)!}
          end={
            ["spouse_of", "sibling_of"].includes(edge.type)
              ? positions.get(edge.target)!
              : directionalTarget(
                  positions.get(edge.source)!,
                  positions.get(edge.target)!,
                  state.entities.find((entity) => entity.id === edge.target)!
                    .type,
                  geometry,
                  geometry.glyphs.get(edge.target) ?? { width: 0, height: 0 },
                )
          }
          labelAt={relationshipLabelPoint(
            edge.type,
            positions.get(edge.source)!,
            positions.get(edge.target)!,
            geometry,
            geometry.mobile,
            geometry.captionWidths.get(edge.target) ?? 110,
            geometry.labelWidths.get(index) ?? 74,
          )}
          selected={index === selected}
          inviting={inviting && index === invitationIndex}
          progress={progress}
          reduced={reduced}
          onSelect={() => onSelect(index)}
          label={`${name(edge.source)} — ${relationshipWords[locale][edge.type]} — ${name(edge.target)}`}
          scope={scope}
        />
      ))}
      {state.entities.map((entity, index) => (
        <GraphEntity
          key={entity.id}
          entity={entity}
          index={index}
          point={positions.get(entity.id)!}
          progress={progress}
          reduced={reduced}
          origin={origins.get(entity.id)}
        />
      ))}
    </div>
  );
}
