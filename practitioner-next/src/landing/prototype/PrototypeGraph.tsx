import { useId, type RefObject } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import type {
  CanonicalState,
  Entity,
  Relationship,
} from "../../shared/contracts";
import { landingPositions, type LandingPoint } from "../landing-layout";

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
      className={`prototype-entity prototype-entity-${entity.type}`}
      data-entity-id={entity.id}
      style={{
        left: `${(point[0] / 660) * 100}%`,
        top: `${(point[1] / 420) * 100}%`,
      }}
    >
      <motion.div
        className="prototype-entity-content"
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
  selected,
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
  selected: boolean;
  progress: MotionValue<number>;
  reduced: boolean;
  onSelect: () => void;
  label: string;
  scope: string;
}) {
  const start = 0.65 + index * 0.025;
  const draw = useTransform(progress, [start, start + 0.08], [0, 1]);
  const maskOpacity = useTransform(draw, [0, 0.015], [0, 1]);
  const labelOpacity = useTransform(
    progress,
    [start + 0.06, start + 0.09],
    [0, 1],
  );
  const family = ["parent_of", "spouse_of", "sibling_of"].includes(edge.type);
  const fraction = edge.type === "parent_of" ? 0.33 : 0.5;
  const path = `M${from.join(" ")} L${to.join(" ")}`;
  const mask = `${scope}-mask-${index}`;
  const arrow = `${scope}-arrow-${index}`;
  return (
    <>
      <svg
        className="prototype-edge-layer"
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
          className={selected ? "prototype-edge-selected" : ""}
          strokeDasharray={family ? "5 5" : undefined}
          markerEnd={
            edge.type === "spouse_of" || edge.type === "sibling_of"
              ? undefined
              : `url(#${arrow})`
          }
          mask={`url(#${mask})`}
        />
      </svg>
      <motion.button
        className="prototype-edge-label"
        data-relationship-index={index}
        aria-label={label}
        aria-pressed={selected}
        onClick={onSelect}
        style={{
          left: `${((from[0] + (to[0] - from[0]) * fraction) / 660) * 100}%`,
          top: `${((from[1] + (to[1] - from[1]) * fraction) / 420) * 100}%`,
          opacity: reduced ? 1 : labelOpacity,
        }}
      >
        {edge.type.replaceAll("_", " ")}
      </motion.button>
    </>
  );
}

export function PrototypeGraph({
  state,
  progress,
  reduced,
  selected,
  onSelect,
  origins,
  drawingRef,
}: {
  state: CanonicalState;
  progress: MotionValue<number>;
  reduced: boolean;
  selected: number;
  onSelect: (index: number) => void;
  origins: EntityOrigins;
  drawingRef: RefObject<HTMLDivElement | null>;
}) {
  const scope = useId().replaceAll(":", "");
  const positions = landingPositions(state);
  const name = (id: string) =>
    state.entities.find((item) => item.id === id)?.name ?? id;
  return (
    <div
      ref={drawingRef}
      className="prototype-drawing"
      role="group"
      aria-label="Interactive family and trust relationships"
    >
      {state.relationships.map((edge, index) => (
        <GraphEdge
          key={`${edge.source}-${edge.type}-${edge.target}`}
          edge={edge}
          index={index}
          from={positions.get(edge.source)!}
          to={positions.get(edge.target)!}
          selected={index === selected}
          progress={progress}
          reduced={reduced}
          onSelect={() => onSelect(index)}
          label={`${name(edge.source)} ${edge.type.replaceAll("_", " ")} ${name(edge.target)}`}
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
