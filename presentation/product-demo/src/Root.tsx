import { Composition, Folder } from "remotion";
import { Demo, DemoShot } from "./Demo";

export function RemotionRoot() {
  return (
    <>
      <Composition
        id="Demo-en"
        component={Demo}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={2520}
        defaultProps={{ locale: "en" }}
      />
      <Composition
        id="Demo-zh-CN"
        component={Demo}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={2520}
        defaultProps={{ locale: "zh-CN" }}
      />
      <Folder name="Representative-scenes">
        <Composition
          id="Source-en"
          component={DemoShot}
          width={1920}
          height={1080}
          fps={30}
          durationInFrames={270}
          defaultProps={{ locale: "en", shotId: "source" }}
        />
        <Composition
          id="Source-zh-CN"
          component={DemoShot}
          width={1920}
          height={1080}
          fps={30}
          durationInFrames={270}
          defaultProps={{ locale: "zh-CN", shotId: "source" }}
        />
      </Folder>
    </>
  );
}
