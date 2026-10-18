import { motion, useTransform, type MotionValue } from "motion/react";
import type { CanonicalState, Entity, Relationship } from "../shared/contracts";
import { landingPositions, type LandingPoint } from "./landing-layout";

function reveal(time: number, start: number, duration: number) {
  return Math.max(0, Math.min(1, (time - start) / duration));
}
function ConstructionEdge({
  edge,
  index,
  selected,
  from,
  to,
  markerId,
  progress,
}: {
  edge: Relationship;
  index: number;
  selected: boolean;
  from: LandingPoint;
  to: LandingPoint;
  markerId: string;
  progress: MotionValue<number>;
}) {
  const opacity = useTransform(() =>
    reveal(progress.get(), 1.5 + index * 0.3, 0.3),
  );
  const parent = edge.type === "parent_of";
  const family =
    parent || edge.type === "spouse_of" || edge.type === "sibling_of";
  return (
    <motion.path
      data-source={edge.source}
      data-target={edge.target}
      data-build-edge={index}
      className={
        "landing-connector" + (selected ? " landing-selected-line" : "")
      }
      d={`M ${from.join(" ")} L ${to.join(" ")}`}
      fill="none"
      stroke={selected ? "#E5EFE7" : "#A6C4B1"}
      strokeWidth={selected ? 3 : 1.3}
      strokeDasharray={family ? "5 5" : undefined}
      markerEnd={parent ? `url(#${markerId})` : undefined}
      style={{ opacity }}
    />
  );
}
function ConstructionEntity({
  entity,
  index,
  point,
  active,
  progress,
}: {
  entity: Entity;
  index: number;
  point: LandingPoint;
  active: boolean;
  progress: MotionValue<number>;
}) {
  const opacity = useTransform(() =>
    reveal(progress.get(), 0.6 + index * 0.09, 0.26),
  );
  const y = useTransform(
    () => 8 * (1 - reveal(progress.get(), 0.6 + index * 0.09, 0.26)),
  );
  return (
    <div
      data-entity-id={entity.id}
      className={`landing-entity landing-entity-${entity.type}${active ? " landing-entity-active" : ""}`}
      style={{
        left: (point[0] / 660) * 100 + "%",
        top: (point[1] / 420) * 100 + "%",
      }}
    >
      <motion.div className="landing-entity-content" style={{ opacity, y }}>
        <svg
          viewBox={entity.type === "trust" ? "0 0 70 52" : "0 0 24 24"}
          aria-hidden="true"
        >
          {entity.type === "trust" ? (
            <path d="M35 3 67 49H3Z" />
          ) : (
            <circle cx="12" cy="12" r="9" />
          )}
        </svg>
        <span>{entity.name}</span>
      </motion.div>
    </div>
  );
}
export function ConstructionDiagram({
  state,
  selected,
  markerId,
  progress,
  label,
}: {
  state: CanonicalState;
  selected: number;
  markerId: string;
  progress: MotionValue<number>;
  label: string;
}) {
  const positions = landingPositions(state);
  const edge = state.relationships[selected];
  return (
    <div className="landing-drawing" role="group" aria-label={label}>
      <svg
        className="landing-connectors"
        viewBox="0 0 660 420"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <marker
            id={markerId}
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
        {state.relationships.map((item, index) =>
          positions.has(item.source) && positions.has(item.target) ? (
            <ConstructionEdge
              key={index}
              edge={item}
              index={index}
              selected={index === selected}
              from={positions.get(item.source)!}
              to={positions.get(item.target)!}
              markerId={markerId}
              progress={progress}
            />
          ) : null,
        )}
      </svg>
      {state.entities.map((entity, index) => (
        <ConstructionEntity
          key={entity.id}
          entity={entity}
          index={index}
          point={positions.get(entity.id)!}
          active={Boolean(
            edge && [edge.source, edge.target].includes(entity.id),
          )}
          progress={progress}
        />
      ))}
    </div>
  );
}
