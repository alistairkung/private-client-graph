import { Img, staticFile } from "remotion";
import type { Locale } from "./story";

/** Reveal the recorded input pixels over the preceding authentic empty field. */
export function CapturedTyping({
  locale,
  field,
  sourceHeight,
  progress,
}: {
  locale: Locale;
  field: "reference" | "title";
  sourceHeight: number;
  progress: number;
}) {
  if (progress >= 1) return null;
  const reference = field === "reference";
  const x = reference ? 142 : 532;
  const end = reference ? 488 : 878;
  const revealWidth = reference ? 125 : 215;
  const previous = reference ? "intake-empty-page" : "intake-reference-page";
  return (
    <Img
      src={staticFile(`captures/${locale}-${previous}.png`)}
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        width: 1440,
        height: sourceHeight,
        clipPath: `inset(443px ${1440 - end}px ${sourceHeight - 478}px ${x + Math.floor(progress * revealWidth)}px)`,
      }}
    />
  );
}
