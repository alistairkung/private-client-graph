import { useEffect, useRef, useState, type PointerEvent } from "react";
import {
  motion,
  useInView,
  useSpring,
  useTransform,
  type MotionValue,
} from "motion/react";
import type { Relationship } from "../../shared/contracts";
import { useLocale } from "../../shared/locale";
import { relationshipWords } from "./copy";
import type { LandingPoint } from "./landing-layout";
import "./story-relationship.css";

const chalk = "#dce8ca";
const selectedChalk = "#e3f1b4";
const settle = { type: "spring", visualDuration: 0.18, bounce: 0 } as const;

export function StoryRelationship({
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
  onInteract,
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
  onInteract: () => void;
  label: string;
  scope: string;
}) {
  const { locale } = useLocale();
  const button = useRef<HTMLButtonElement>(null);
  const visible = useInView(button, { amount: "all" });
  const [invitation, setInvitation] = useState<
    "waiting" | "playing" | "settled"
  >("waiting");
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  const attentive = hovered || focused;
  const x = useSpring(0, settle);
  const y = useSpring(0, settle);
  const playing = inviting && invitation === "playing" && !reduced;
  const breathing = inviting && visible && invitation === "settled" && !reduced;

  useEffect(() => {
    if (inviting && visible && invitation === "waiting")
      setInvitation(reduced ? "settled" : "playing");
    else if (invitation === "playing" && (!inviting || !visible || reduced))
      setInvitation("settled");
  }, [inviting, visible, reduced, invitation]);

  useEffect(() => {
    if (reduced) {
      x.jump(0);
      y.jump(0);
    }
  }, [reduced, x, y]);

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
  const midpoint = [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
  const mask = `${scope}-mask-${index}`;
  const arrow = `${scope}-arrow-${index}`;
  const stroke = selected ? selectedChalk : attentive || inviting ? chalk : "#8cae99";

  let scale: number | number[] = 1;
  if (!reduced) {
    if (pressed) scale = 0.97;
    else if (attentive) scale = 1.025;
    else if (playing) scale = [1, 1.045, 1];
    else if (breathing) scale = [1, 1.04, 1];
  }

  function enterPointer(event: PointerEvent<HTMLButtonElement>) {
    if (event.pointerType === "touch") return;
    setHovered(true);
    onInteract();
  }

  function followPointer(event: PointerEvent<HTMLButtonElement>) {
    if (reduced || event.pointerType === "touch") return;
    const box = event.currentTarget.getBoundingClientRect();
    x.set((event.clientX - box.left - box.width / 2) / box.width * 4);
    y.set((event.clientY - box.top - box.height / 2) / box.height * 4);
  }

  function releasePointer() {
    setHovered(false);
    setPressed(false);
    x.set(0);
    y.set(0);
  }

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
            <path d="m1 1 5 3-5 3" fill="none" stroke={stroke} />
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
          className={
            selected ? "landing-story-edge-selected" :
            attentive ? "landing-story-edge-attentive" :
            inviting ? "landing-story-edge-inviting" : ""
          }
          strokeDasharray={family ? "5 5" : undefined}
          markerEnd={
            edge.type === "spouse_of" || edge.type === "sibling_of"
              ? undefined
              : `url(#${arrow})`
          }
          mask={`url(#${mask})`}
        />
        {["beneficiary_of", "settlor_of"].includes(edge.type) &&
          labelAt[0] !== midpoint[0] && (
            <motion.line
              x1={midpoint[0]}
              y1={midpoint[1]}
              x2={labelAt[0]}
              y2={labelAt[1]}
              stroke={stroke}
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
              style={{ opacity: reduced ? 1 : labelOpacity }}
            />
          )}
        {playing && (
          <g>
            <motion.path
              className="landing-story-invitation-trace"
              d={`M${from.join(" ")} L${midpoint.join(" ")} L${labelAt.join(" ")}`}
              initial={{ pathLength: 0.16, pathOffset: -0.16, opacity: 0 }}
              animate={{ pathOffset: 1, opacity: [0, 1, 1, 0] }}
              transition={{ duration: 0.6, delay: 0.35, ease: "easeInOut" }}
            />
          </g>
        )}
      </svg>
      <div
        className="landing-story-edge-anchor"
        style={{
          left: `${labelAt[0] / 660 * 100}%`,
          top: `${labelAt[1] / 420 * 100}%`,
        }}
      >
        <motion.button
          ref={button}
          className="landing-story-edge-label"
          data-relationship-index={index}
          aria-label={label}
          aria-pressed={selected}
          data-inviting={inviting || undefined}
          data-invitation-state={inviting ? invitation : undefined}
          data-invitation-visible={visible || undefined}
          data-attentive={attentive || undefined}
          onClick={onSelect}
          onPointerEnter={enterPointer}
          onPointerMove={followPointer}
          onPointerLeave={releasePointer}
          onPointerCancel={releasePointer}
          onPointerDown={() => setPressed(true)}
          onPointerUp={() => setPressed(false)}
          onFocus={() => {
            setFocused(true);
            onInteract();
          }}
          onBlur={() => {
            setFocused(false);
            setPressed(false);
          }}
          onKeyDown={event => {
            if (event.key === "Enter" || event.key === " ") setPressed(true);
          }}
          onKeyUp={() => setPressed(false)}
          style={{ opacity: reduced ? 1 : labelOpacity }}
        >
          <motion.span
            className="landing-story-relationship-surface"
            style={reduced ? undefined : { x, y }}
            animate={{ scale }}
            transition={
              playing
                ? { duration: 0.4, delay: 0.85, times: [0, 0.45, 1], ease: "easeOut" }
                : breathing
                  ? { duration: 1.8, repeat: Infinity, ease: "easeInOut" }
                  : reduced ? { duration: 0 } : settle
            }
          >
            {relationshipWords[locale][edge.type]}
            {inviting && (reduced || invitation !== "waiting") && (
              <svg className="landing-story-invitation-outline" aria-hidden="true">
                <motion.rect
                  width="100%"
                  height="100%"
                  rx="22"
                  initial={playing ? { pathLength: 0 } : false}
                  animate={{ pathLength: 1 }}
                  transition={{
                    duration: reduced ? 0 : 0.4,
                    delay: playing ? 0.85 : 0,
                    ease: "easeOut",
                  }}
                  onAnimationComplete={() => setInvitation("settled")}
                />
              </svg>
            )}
          </motion.span>
        </motion.button>
      </div>
    </>
  );
}
