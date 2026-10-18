import {
  Interactive,
  Track,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BrowserFrame, Stage } from "./Stage";
import { fixtureNotice, shots, type Locale } from "./story";
import { capturedPages } from "./captured-pages";
import { cameraAt, cursorAt } from "./motion";
import { CapturedTyping } from "./CapturedTyping";

function DemoShotInner({ locale, shotId }: { locale: Locale; shotId: string }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shot = shots.find((candidate) => candidate.id === shotId);
  if (!shot) throw new Error(`Unknown demo shot: ${shotId}`);
  const cue = shot.cues.find(
    (candidate) =>
      frame >= candidate.from * fps &&
      frame < (candidate.from + candidate.duration) * fps,
  );
  const capture = capturedPages[`${locale}-${shot.image}`];
  const camera = cameraAt(shotId, locale, frame / fps, capture.height);
  const cursor = cursorAt(shotId, locale, frame / fps, capture.height);
  const fixture = shotId === "analyse" || shotId === "proposal";
  return (
    <Stage
      locale={locale}
      kicker={
        fixture
          ? fixtureNotice[locale]
          : locale === "en"
            ? "THE PRACTITIONER WORKFLOW"
            : "专业人员工作流程"
      }
      title={shot.title[locale]}
      detail={cue?.text[locale]}
    >
      <BrowserFrame
        locale={locale}
        imageKey={capture.imageKey}
        camera={camera}
        sourceHeight={capture.height}
        cursor={cursor}
      >
        {(shotId === "reference" || shotId === "name") && (
          <CapturedTyping
            locale={locale}
            field={shotId === "reference" ? "reference" : "title"}
            sourceHeight={capture.height}
            progress={interpolate(frame, [0.3 * fps, 2.1 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })}
          />
        )}
      </BrowserFrame>
    </Stage>
  );
}

export const DemoShot = Interactive.create({
  Component: DemoShotInner,
  layout: "absolute-fill",
  schema: {
    locale: {
      type: "enum",
      default: "en",
      description: "Language",
      variants: { en: {}, "zh-CN": {} },
    },
    shotId: { type: "string", default: "source", description: "Workflow shot" },
  },
});

export function Demo({ locale }: { locale: Locale }) {
  const { fps } = useVideoConfig();
  return (
    <Track name="Practitioner workflow — 84 seconds">
      <DemoShot
        name="01 — Matters"
        from={0}
        durationInFrames={6 * fps}
        locale={locale}
        shotId="start"
      />
      <DemoShot
        name="02 — Create Matter"
        from={6 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="create"
      />
      <DemoShot
        name="03 — Existing reference"
        from={10 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="reference"
      />
      <DemoShot
        name="04 — Matter title"
        from={14 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="name"
      />
      <DemoShot
        name="05 — Source documents"
        from={18 * fps}
        durationInFrames={8 * fps}
        locale={locale}
        shotId="documents"
      />
      <DemoShot
        name="06 — Upload and analyse"
        from={26 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="analyse"
      />
      <DemoShot
        name="07 — Saved proposal"
        from={30 * fps}
        durationInFrames={8 * fps}
        locale={locale}
        shotId="proposal"
      />
      <DemoShot
        name="08 — Select relationship"
        from={38 * fps}
        durationInFrames={9 * fps}
        locale={locale}
        shotId="relationship"
      />
      <DemoShot
        name="09 — Exact source passage"
        from={47 * fps}
        durationInFrames={9 * fps}
        locale={locale}
        shotId="source"
      />
      <DemoShot
        name="10 — Confirm whole proposal"
        from={56 * fps}
        durationInFrames={8 * fps}
        locale={locale}
        shotId="confirm"
      />
      <DemoShot
        name="11 — Accepted Matter"
        from={64 * fps}
        durationInFrames={6 * fps}
        locale={locale}
        shotId="accepted"
      />
      <DemoShot
        name="12 — Return to Matters"
        from={70 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="return"
      />
      <DemoShot
        name="13 — Reopen and review"
        from={74 * fps}
        durationInFrames={6 * fps}
        locale={locale}
        shotId="reopen"
      />
      <DemoShot
        name="14 — Close"
        from={80 * fps}
        durationInFrames={4 * fps}
        locale={locale}
        shotId="close"
      />
    </Track>
  );
}
