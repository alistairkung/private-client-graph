import type { ReactNode } from "react";
import {
  getRemotionEnvironment,
  getStaticFiles,
  Img,
  staticFile,
} from "remotion";
import { Cursor, type CursorState } from "./Cursor";
import "./fonts";
import { scopeBadge, type Locale } from "./story";

export type { Locale } from "./story";
export const palette = {
  paper: "#f6f6f1",
  ink: "#173e38",
  burgundy: "#773b46",
  muted: "#52665f",
  rule: "#d5d9d2",
  white: "#ffffff",
};
export const typography = {
  display: '"Newsreader Display", "Noto Serif SC"',
  body: '"Public Sans", "Noto Sans SC"',
};

export type Camera = {
  /** One source pixel becomes this many video pixels. */
  scale: number;
  /** Normalized source coordinate to keep at the viewport centre when possible. */
  x: number;
  y: number;
};

export const browserGeometry = {
  left: 235,
  top: 60,
  width: 1450,
  chromeHeight: 40,
  viewportHeight: 720,
  sourceWidth: 1440,
  sourceHeight: 900,
} as const;

export const fullView: Camera = { scale: 1, x: 0.5, y: 0.4 };

/** Centre undersized captures; clamp zoomed captures to their real boundaries. */
export function projectCamera(camera: Camera, sourceHeight: number = 900) {
  const { width, viewportHeight, sourceWidth } = browserGeometry;
  const imageWidth = sourceWidth * camera.scale;
  const imageHeight = sourceHeight * camera.scale;
  return {
    scale: camera.scale,
    left:
      imageWidth <= width
        ? (width - imageWidth) / 2
        : Math.max(
            width - imageWidth,
            Math.min(0, width / 2 - camera.x * imageWidth),
          ),
    top:
      imageHeight <= viewportHeight
        ? (viewportHeight - imageHeight) / 2
        : Math.max(
            viewportHeight - imageHeight,
            Math.min(0, viewportHeight / 2 - camera.y * imageHeight),
          ),
  };
}

export function BrowserFrame({
  locale,
  imageKey,
  camera = fullView,
  sourceHeight = 900,
  cursor,
  children,
}: {
  locale: Locale;
  imageKey: string;
  camera?: Camera;
  sourceHeight?: number;
  cursor?: CursorState;
  /** Optional annotation overlays use unscaled source-image pixel coordinates. */
  children?: ReactNode;
}) {
  const { left, top, width, chromeHeight, viewportHeight, sourceWidth } =
    browserGeometry;
  const projected = projectCamera(camera, sourceHeight);
  const capturePath = `captures/${locale}-${imageKey}.png`;
  const captureReady = getStaticFiles().some(
    (file) => file.name === capturePath,
  );
  if (!captureReady && !getRemotionEnvironment().isStudio) {
    throw new Error(
      `Actual application capture required before export: ${capturePath}`,
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width,
        height: chromeHeight + viewportHeight,
        border: `1px solid ${palette.rule}`,
        boxSizing: "content-box",
        borderRadius: 9,
        overflow: "hidden",
        background: palette.white,
      }}
    >
      <div
        style={{
          position: "relative",
          height: chromeHeight,
          borderBottom: `1px solid ${palette.rule}`,
          boxSizing: "border-box",
          background: "#eef0e9",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: palette.muted,
          fontSize: 18,
          letterSpacing: 0.6,
        }}
      >
        <div
          style={{ position: "absolute", left: 18, display: "flex", gap: 9 }}
          aria-hidden
        >
          {[0, 1, 2].map((dot) => (
            <span
              key={dot}
              style={{
                width: 8,
                height: 8,
                border: "1px solid #a9b2a7",
                borderRadius: "50%",
              }}
            />
          ))}
        </div>
        <span>Private Client Graph</span>
      </div>
      <div
        style={{
          position: "relative",
          width,
          height: viewportHeight,
          overflow: "hidden",
          background: palette.paper,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: projected.left,
            top: projected.top,
            width: sourceWidth,
            height: sourceHeight,
            scale: projected.scale,
            transformOrigin: "0 0",
            clipPath: "inset(0 14px 0 0)",
          }}
        >
          {captureReady ? (
            <Img
              src={staticFile(capturePath)}
              alt={
                locale === "en"
                  ? "Recorded synthetic application workflow"
                  : "已记录的合成资料应用流程"
              }
              style={{
                width: sourceWidth,
                height: sourceHeight,
                display: "block",
              }}
            />
          ) : (
            <div
              style={{
                padding: 80,
                color: palette.muted,
                fontSize: 28,
                lineHeight: 1.5,
              }}
            >
              {locale === "en"
                ? "Application capture pending"
                : "等待录制应用画面"}
              <div style={{ marginTop: 16, fontSize: 20 }}>
                {locale === "en"
                  ? "The local browser certificate needs your attention before this workflow can be recorded."
                  : "本地浏览器证书需要您确认后，才能录制此流程。"}
              </div>
            </div>
          )}
          {children}
        </div>
        {cursor && (
          <Cursor
            left={projected.left + cursor.x * sourceWidth * projected.scale}
            top={projected.top + cursor.y * sourceHeight * projected.scale}
            opacity={cursor.opacity}
            click={cursor.click}
          />
        )}
      </div>
    </div>
  );
}

export function Stage({
  locale,
  kicker,
  title,
  detail,
  children,
}: {
  locale: Locale;
  kicker?: string;
  title: string;
  detail?: string;
  children: ReactNode;
}) {
  return (
    <div
      lang={locale}
      style={{
        position: "absolute",
        inset: 0,
        background: palette.paper,
        color: palette.ink,
        fontFamily: typography.body,
        fontWeight: 400,
        fontSynthesis: "none",
        WebkitFontSmoothing: "antialiased",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 23,
          left: 120,
          right: 120,
          display: "flex",
          justifyContent: "space-between",
          fontSize: 22,
          lineHeight: 1,
          color: palette.muted,
        }}
      >
        <span style={{ letterSpacing: 2, fontSize: 19 }}>
          PRIVATE CLIENT GRAPH
        </span>
        <span>{scopeBadge[locale]}</span>
      </div>
      {children}
      <div style={{ position: "absolute", left: 120, right: 120, top: 842 }}>
        {kicker && (
          <div
            style={{
              fontSize: 20,
              lineHeight: 1.25,
              letterSpacing: locale === "en" ? 1.2 : 0,
              color: palette.burgundy,
            }}
          >
            {kicker}
          </div>
        )}
        <h1
          style={{
            margin: "8px 0 0",
            fontFamily: typography.display,
            fontWeight: 400,
            fontSize: locale === "en" ? 64 : 60,
            lineHeight: 1.05,
            letterSpacing: locale === "en" ? -0.9 : 0,
          }}
        >
          {title}
        </h1>
        {detail && (
          <div
            style={{
              marginTop: 10,
              fontSize: 32,
              lineHeight: 1.3,
              color: palette.muted,
            }}
          >
            {detail}
          </div>
        )}
      </div>
    </div>
  );
}
