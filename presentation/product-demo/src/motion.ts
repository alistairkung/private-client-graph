import { Easing, interpolate } from "remotion";
import type { Camera } from "./Stage";
import type { Locale } from "./story";
import type { CursorState } from "./Cursor";

/** Targets are measured in the original application capture's CSS pixels. */
type View = { scale: number; x: number; y: number };
type Keyframe = readonly [seconds: number, view: View];
const view = (scale: number, x: number, y: number): View => ({ scale, x, y });
const ease = {
  easing: Easing.bezier(0.32, 0, 0.18, 1),
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export function cameraAt(
  shotId: string,
  locale: Locale,
  seconds: number,
  sourceHeight: number,
): Camera {
  const zh = locale === "zh-CN";
  const form = view(1.65, 510, 450);
  const trust = view(2.25, 370, zh ? 824 : 850);
  const evidence = view(1.65, 420, zh ? 1204 : 1230);
  const source = view(2, 1019, 657);
  const intakeEnd = view(1.5, 510, zh ? 1070 : 1090);
  const moves: Record<string, readonly Keyframe[]> = {
    start: [
      [0, view(1, 720, 360)],
      [1.2, view(1, 720, 360)],
      [4, view(1.2, 1000, 250)],
    ],
    create: [
      [0, view(1.2, 1000, 250)],
      [0.3, view(1.2, 1000, 250)],
      [2.6, form],
    ],
    reference: [[0, form]],
    name: [
      [0, form],
      [2.3, form],
      [3.5, view(1.65, 510, 530)],
    ],
    documents: [
      [0, view(1.65, 510, 530)],
      [2.8, view(1.45, 510, zh ? 905 : 925)],
      [4.5, view(1.45, 510, zh ? 905 : 925)],
      [6.7, intakeEnd],
    ],
    analyse: [
      [0, intakeEnd],
      [2.4, view(1.65, 510, zh ? 1170 : 1190)],
    ],
    proposal: [
      [0, view(1.3, 650, 320)],
      [3.1, view(1.3, 650, 320)],
      [6.2, trust],
    ],
    relationship: [
      [0, trust],
      [1.8, trust],
      [4.3, evidence],
    ],
    source: [
      [0, evidence],
      [2.5, source],
    ],
    confirm: [
      [0, source],
      [2.6, view(1.3, 650, zh ? 1428 : 1477)],
    ],
    accepted: [
      [0, view(1.3, 650, 320)],
      [3.2, view(1.45, 600, 350)],
    ],
    return: [
      [0, view(1, 720, 450)],
      [2, view(1.45, 600, 740)],
    ],
    reopen: [
      [0, view(1.3, 650, 350)],
      [1.8, view(2.1, 535, zh ? 918 : 944)],
      [2.8, view(2.1, 535, zh ? 918 : 944)],
      [5, view(1.9, 1019, 570)],
    ],
    close: [
      [0, view(1.9, 1019, 570)],
      [1.2, view(1.9, 1019, 570)],
      [3.6, view(1, 720, 680)],
    ],
  };
  const keys = moves[shotId];
  if (!keys) throw new Error(`Missing camera direction for ${shotId}`);
  let result = keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [startTime, start] = keys[i - 1];
    const [endTime, end] = keys[i];
    if (seconds < startTime) break;
    const p = interpolate(seconds, [startTime, endTime], [0, 1], ease);
    result = view(
      start.scale + (end.scale - start.scale) * p,
      start.x + (end.x - start.x) * p,
      start.y + (end.y - start.y) * p,
    );
    if (seconds <= endTime) break;
  }
  return {
    scale: result.scale,
    x: result.x / 1440,
    y: result.y / sourceHeight,
  };
}

type PointerMove = {
  from: number;
  to: number;
  start: readonly [number, number];
  end: readonly [number, number];
  click?: number;
};

/** Cursor clicks precede the next recorded UI state; no in-app controls are fabricated. */
export function cursorAt(
  shotId: string,
  locale: Locale,
  seconds: number,
  sourceHeight: number,
): CursorState | undefined {
  const zh = locale === "zh-CN";
  const moves: Record<string, PointerMove> = {
    start: {
      from: 3.7,
      to: 5.4,
      start: [790, 420],
      end: [1245, 207],
      click: 5.7,
    },
    create: {
      from: 2.5,
      to: 3.6,
      start: [720, 550],
      end: [245, 460],
      click: 3.76,
    },
    reference: {
      from: 2.5,
      to: 3.6,
      start: [300, 460],
      end: [625, 460],
      click: 3.76,
    },
    name: {
      from: 2.6,
      to: 3.65,
      start: [625, 460],
      end: [195, 692],
      click: 3.78,
    },
    documents: {
      from: 5.3,
      to: 6.7,
      start: [610, zh ? 990 : 1010],
      end: [140, zh ? 1109 : 1129],
    },
    analyse: {
      from: 1.5,
      to: 3.4,
      start: [140, zh ? 1109 : 1129],
      end: [213, zh ? 1187 : 1207],
      click: 3.76,
    },
    relationship: {
      from: 6.8,
      to: 8.4,
      start: [530, zh ? 1190 : 1216],
      end: [203, zh ? 1258 : 1284],
      click: 8.76,
    },
    confirm: {
      from: 5.3,
      to: 7.4,
      start: [650, zh ? 1428 : 1477],
      end: [zh ? 224 : 261, zh ? 1478 : 1527],
      click: 7.76,
    },
    accepted: {
      from: 4,
      to: 5.4,
      start: [600, 420],
      end: [200, 207],
      click: 5.76,
    },
    return: {
      from: 2,
      to: 3.4,
      start: [800, 650],
      end: [480, 814],
      click: 3.76,
    },
  };
  const move = moves[shotId];
  if (!move || seconds < move.from) return undefined;
  const p = interpolate(seconds, [move.from, move.to], [0, 1], ease);
  return {
    x: (move.start[0] + (move.end[0] - move.start[0]) * p) / 1440,
    y: (move.start[1] + (move.end[1] - move.start[1]) * p) / sourceHeight,
    opacity: interpolate(seconds, [move.from, move.from + 0.25], [0, 1], {
      extrapolateRight: "clamp",
    }),
    click:
      move.click === undefined
        ? 0
        : interpolate(seconds, [move.click, move.click + 0.23], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
  };
}
