import { useLocale } from "../../shared/locale";
import { relationshipWords, useLandingCopy } from "./copy";
import { useId, useLayoutEffect, useState, type RefObject } from "react";
import {
  directionalTarget,
  relationshipLabelPoint,
  type GlyphSize,
} from "./story-geometry";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { CanonicalState, Entity } from "../../shared/contracts";
import { landingPositions, type LandingPoint } from "./landing-layout";
import { StoryRelationship } from "./StoryRelationship";

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

export function StoryGraph({
  state,
  progress,
  reduced,
  selected,
  inviting,
  onSelect,
  onInteract,
  origins,
  drawingRef,
}: {
  state: CanonicalState;
  progress: MotionValue<number>;
  reduced: boolean;
  selected: number;
  inviting: boolean;
  onSelect: (index: number) => void;
  onInteract: () => void;
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
  const invitationIndex = state.relationships.findIndex(
    (_, index) => index !== selected,
  );
  return (
    <div
      ref={drawingRef}
      className="landing-story-drawing"
      role="group"
      aria-label={copy.diagram}
    >
      {state.relationships.map((edge, index) => (
        <StoryRelationship
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
          onInteract={onInteract}
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
