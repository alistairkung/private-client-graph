export type CursorState = {
  /** Coordinates in the original capture, normalized to its width and height. */
  x: number;
  y: number;
  opacity: number;
  /** One click's frame-derived progress, 0–1. Zero is the idle state. */
  click: number;
};

/** A constant-size pointer placed at the camera-projected source coordinate. */
export function Cursor({
  left,
  top,
  opacity,
  click,
}: Omit<CursorState, "x" | "y"> & { left: number; top: number }) {
  const clickProgress = Math.min(1, Math.max(0, click));
  const showingClick = clickProgress > 0 && clickProgress < 1;

  return (
    <div
      aria-hidden
      style={{
        position: "absolute",
        left,
        top,
        width: 36,
        height: 42,
        opacity,
        pointerEvents: "none",
        zIndex: 2,
      }}
    >
      {showingClick && (
        <svg
          width={80}
          height={80}
          viewBox="-40 -40 80 80"
          style={{
            position: "absolute",
            left: -40,
            top: -40,
            overflow: "visible",
          }}
        >
          <circle
            r={10 + 22 * clickProgress}
            fill="none"
            stroke="#773b46"
            strokeWidth={2}
            opacity={0.65 * (1 - clickProgress)}
          />
        </svg>
      )}
      <svg
        width={30}
        height={38}
        viewBox="0 0 30 38"
        style={{
          display: "block",
          scale: 1 - Math.sin(Math.PI * clickProgress) * 0.1,
          transformOrigin: "0 0",
          overflow: "visible",
        }}
      >
        <path
          d="M 1 1 L 1 29 L 8.4 21.8 L 14 34 L 20 31 L 14.4 19.2 L 24.4 19.2 Z"
          fill="#ffffff"
          stroke="#173e38"
          strokeWidth={1.6}
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
