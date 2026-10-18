import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import ts from "typescript";
import { bundle } from "@remotion/bundler";
import { checkCaptures } from "./captures.mjs";
import {
  ensureBrowser,
  getCompositions,
  openBrowser,
  renderMedia,
  renderStill,
} from "@remotion/renderer";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const locales = ["en", "zh-CN"];
const mode = process.argv[2] ?? "qa";
if (!["qa", "video"].includes(mode)) {
  throw new Error("Usage: node scripts/render-demo.mjs [qa|video]");
}
process.chdir(root);

async function main() {
  const started = Date.now();
  const story = await loadStory();
  const captures = await checkCaptures(root, story.shots);
  const directory = mode === "qa" ? "qa/demo" : "output";
  await mkdir(path.join(root, directory), { recursive: true });
  const metadataPath = path.join(root, directory, `render-${mode}.json`);
  const metadata = {
    mode,
    status: "rendering",
    startedAt: new Date(started).toISOString(),
    dimensions: { width: 1920, height: 1080, fps: story.FPS },
    totalFrames: story.TOTAL_FRAMES,
    captures,
    browser: null,
    outputs: [],
  };
  const saveMetadata = () =>
    writeFile(metadataPath, JSON.stringify(metadata, null, 2) + "\n");
  await saveMetadata();
  let browser;
  try {
    // ensureBrowser reuses the installed, version-matched Remotion browser.
    // This export command never downloads a substitute browser implicitly.
    metadata.browser = await ensureBrowser({
      chromeMode: "headless-shell",
      onBrowserDownload: () => {
        throw new Error(
          "The bundled Remotion browser is missing or mismatched. Install the pinned browser before rendering.",
        );
      },
    });
    if (!("path" in metadata.browser)) {
      throw new Error(`No usable browser: ${metadata.browser.type}`);
    }
    const serveUrl = await bundle({
      entryPoint: path.join(root, "src/index.tsx"),
      rspack: true,
    });
    browser = await openBrowser("chrome", {
      browserExecutable: metadata.browser.path,
      chromeMode: "headless-shell",
    });
    const compositions = await getCompositions(serveUrl, {
      puppeteerInstance: browser,
    });
    const videos = locales.map((locale) => {
      const composition = compositions.find(
        (item) => item.id === `Demo-${locale}`,
      );
      if (!composition) throw new Error(`Missing composition Demo-${locale}`);
      if (
        composition.width !== 1920 ||
        composition.height !== 1080 ||
        composition.fps !== story.FPS ||
        composition.durationInFrames !== story.TOTAL_FRAMES
      ) {
        throw new Error(
          `${composition.id} must be 1920×1080, ${story.FPS} fps, ${story.TOTAL_FRAMES} frames`,
        );
      }
      return { locale, composition };
    });
    for (const { locale, composition } of videos) {
      const shared = { serveUrl, composition, puppeteerInstance: browser };
      if (mode === "qa") {
        for (const shot of story.shots) {
          const seconds = [
            ...new Set([
              0.6,
              shot.duration - 1,
              ...shot.cues.map(
                (cue) => cue.from + Math.min(1, cue.duration / 2),
              ),
              ...(shot.id === "relationship" ? [1.5, 4.8] : []),
              ...(shot.id === "reopen" ? [2.5] : []),
            ]),
          ].sort((a, b) => a - b);
          for (const second of seconds) {
            const frame = Math.round((shot.from + second) * story.FPS);
            const filename = `qa/demo/${locale}-${shot.id}-${frame}.png`;
            await renderStill({
              ...shared,
              frame,
              imageFormat: "png",
              output: path.join(root, filename),
            });
            metadata.outputs.push(
              await describeOutput(filename, { locale, shot: shot.id, frame }),
            );
            console.log(`QA ${locale}: ${shot.id}, frame ${frame}`);
          }
        }
        // Includes proposal → selected relationship → original-source continuity.
        const frameRange = [36 * story.FPS, 56 * story.FPS - 1];
        const filename = `qa/demo/private-client-graph-demo-review-${locale}.mp4`;
        await renderVideo(shared, locale, filename, frameRange);
        metadata.outputs.push(
          await describeOutput(filename, {
            locale,
            frameRange,
            frames: frameRange[1] - frameRange[0] + 1,
          }),
        );
      } else {
        const filename = `output/private-client-graph-demo-${locale}.mp4`;
        await renderVideo(shared, locale, filename);
        metadata.outputs.push(
          await describeOutput(filename, {
            locale,
            frames: story.TOTAL_FRAMES,
          }),
        );
      }
      await saveMetadata();
    }
    metadata.status = "complete";
    console.log(
      `Completed ${mode} in ${((Date.now() - started) / 1000).toFixed(1)}s`,
    );
  } catch (error) {
    metadata.status = "failed";
    metadata.error = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    metadata.finishedAt = new Date().toISOString();
    metadata.elapsedSeconds = (Date.now() - started) / 1000;
    try {
      await saveMetadata();
    } finally {
      if (browser) await browser.close({ silent: true });
    }
  }
}

async function loadStory() {
  const filename = path.join(root, "src/story.ts");
  const compiled = ts.transpileModule(await readFile(filename, "utf8"), {
    fileName: filename,
    reportDiagnostics: true,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.CommonJS,
    },
  });
  const errors = (compiled.diagnostics ?? []).filter(
    (item) => item.category === ts.DiagnosticCategory.Error,
  );
  if (errors.length)
    throw new Error(
      errors
        .map((item) => ts.flattenDiagnosticMessageText(item.messageText, "\n"))
        .join("\n"),
    );
  const module = { exports: {} };
  new vm.Script(compiled.outputText, { filename }).runInNewContext(
    {
      module,
      exports: module.exports,
      require(specifier) {
        throw new Error(
          `The story must remain data-only; unexpected import ${specifier}`,
        );
      },
    },
    { timeout: 1000 },
  );
  const story = module.exports;
  if (
    story.FPS !== 30 ||
    story.TOTAL_FRAMES !== 2520 ||
    !Array.isArray(story.shots) ||
    story.shots.length !== 14
  ) {
    throw new Error(
      "The demo contract requires 14 shots over 2520 frames at 30 fps",
    );
  }
  return story;
}

async function renderVideo(shared, locale, filename, frameRange) {
  let lastStep = -1;
  await renderMedia({
    ...shared,
    ...(frameRange ? { frameRange } : {}),
    codec: "h264",
    crf: 16,
    pixelFormat: "yuv420p",
    imageFormat: "png",
    concurrency: 4,
    muted: true,
    outputLocation: path.join(root, filename),
    onProgress: ({ progress }) => {
      const step = Math.floor(progress * 20);
      if (step !== lastStep) {
        lastStep = step;
        console.log(`${locale}: ${step * 5}%`);
      }
    },
  });
}

async function describeOutput(filename, details) {
  const bytes = await readFile(path.join(root, filename));
  return {
    file: filename,
    ...details,
    bytes: bytes.length,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  };
}

await main();
