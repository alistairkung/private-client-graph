import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { cp, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { checkCaptures } from "./captures.mjs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import test from "node:test";
import ts from "typescript";
import { Easing, interpolate } from "remotion";

const locales = ["en", "zh-CN"];
const captureKeys = [
  "ledger",
  "intake-empty",
  "intake-reference",
  "intake-title",
  "intake-files",
  "proposal",
  "selected-trustee",
  "source-trustee",
  "confirmation",
  "accepted",
  "ledger-saved",
  "reopened-parent",
];
const quotes = {
  trustee: "Morgan Example is trustee of the Fictional Trust.",
  parent: "Alice Example is the parent of Ben Example.",
};

function loadTypescript(relativePath, imports = {}) {
  const filename = fileURLToPath(new URL(relativePath, import.meta.url));
  const compiled = ts.transpileModule(readFileSync(filename, "utf8"), {
    fileName: filename,
    reportDiagnostics: true,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.ReactJSX,
    },
  });
  const errors = (compiled.diagnostics ?? []).filter(
    (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
  );
  assert.equal(
    errors.length,
    0,
    errors
      .map((error) => ts.flattenDiagnosticMessageText(error.messageText, "\n"))
      .join("\n"),
  );
  const module = { exports: {} };
  new vm.Script(compiled.outputText, { filename }).runInNewContext(
    {
      module,
      exports: module.exports,
      require(specifier) {
        assert.ok(
          Object.hasOwn(imports, specifier),
          `Unexpected import: ${specifier}`,
        );
        return imports[specifier];
      },
    },
    { timeout: 1000 },
  );
  return module.exports;
}

function renderingNotExpected() {
  assert.fail("Pure camera tests must not render components or load assets");
}

const story = loadTypescript("../src/story.ts");
const stage = loadTypescript("../src/Stage.tsx", {
  "react/jsx-runtime": {
    jsx: renderingNotExpected,
    jsxs: renderingNotExpected,
  },
  remotion: { Img: renderingNotExpected, staticFile: renderingNotExpected },
  "./Cursor": { Cursor: renderingNotExpected },
  "./fonts": {},
  "./story": story,
});

function captureStage({ isStudio, files = [] }) {
  const elements = [];
  const element = (type, props) => {
    const result = { type, props };
    elements.push(result);
    return result;
  };
  const component = loadTypescript("../src/Stage.tsx", {
    "react/jsx-runtime": { jsx: element, jsxs: element },
    remotion: {
      Img: "CaptureImage",
      staticFile: (filename) => `/static/${filename}`,
      getStaticFiles: () => files.map((name) => ({ name })),
      getRemotionEnvironment: () => ({ isStudio, isRendering: !isStudio }),
    },
    "./Cursor": { Cursor: "CaptureCursor" },
    "./fonts": {},
    "./story": story,
  });
  return { component, elements };
}

test("missing captures block video export in both languages", () => {
  for (const locale of locales) {
    const { component } = captureStage({ isStudio: false });
    assert.throws(
      () => component.BrowserFrame({ locale, imageKey: "ledger" }),
      /capture/i,
      `${locale}: an export must not substitute a missing capture`,
    );
  }
});

test("Studio can explain missing captures without displaying replacement UI", () => {
  for (const [locale, expectedMessage] of [
    ["en", "Application capture pending"],
    ["zh-CN", "等待录制应用画面"],
  ]) {
    const { component, elements } = captureStage({ isStudio: true });
    assert.doesNotThrow(() =>
      component.BrowserFrame({ locale, imageKey: "ledger" }),
    );
    assert.ok(JSON.stringify(elements).includes(expectedMessage));
    assert.ok(elements.every((item) => item.type !== "CaptureImage"));
  }
});

test("available localized captures remain renderable outside Studio", () => {
  for (const locale of locales) {
    const filename = `captures/${locale}-ledger.png`;
    const { component, elements } = captureStage({
      isStudio: false,
      files: [filename],
    });
    assert.doesNotThrow(() =>
      component.BrowserFrame({ locale, imageKey: "ledger" }),
    );
    const capture = elements.find((item) => item.type === "CaptureImage");
    assert.ok(capture, `${locale}: actual capture must be displayed`);
    assert.equal(capture.props.src, `/static/${filename}`);
  }
});

function assertLocalized(value, label) {
  assert.deepEqual(Object.keys(value).sort(), locales, `${label}: locale keys`);
  for (const locale of locales) {
    assert.equal(typeof value[locale], "string", `${label}: ${locale}`);
    assert.ok(value[locale].trim().length > 0, `${label}: empty ${locale}`);
  }
}

test("both languages have 14 contiguous shots lasting exactly 84 seconds", () => {
  assert.equal(story.FPS, 30);
  assert.equal(story.DURATION_SECONDS, 84);
  assert.equal(story.TOTAL_FRAMES, 2520);
  assert.equal(story.shots.length, 14);
  assert.equal(new Set(story.shots.map((shot) => shot.id)).size, 14);
  for (const locale of locales) {
    let end = 0;
    for (const shot of story.shots) {
      assert.match(shot.id, /^[a-z][a-z0-9-]*$/);
      assert.equal(
        shot.from,
        end,
        `${locale}/${shot.id}: timeline gap or overlap`,
      );
      assert.ok(Number.isFinite(shot.duration) && shot.duration > 0);
      assert.ok(Number.isInteger(shot.from * story.FPS));
      assert.ok(Number.isInteger(shot.duration * story.FPS));
      end += shot.duration;
    }
    assert.equal(end, story.DURATION_SECONDS, `${locale}: duration`);
    assert.equal(end * story.FPS, story.TOTAL_FRAMES, `${locale}: frames`);
    assert.ok(end <= 90, `${locale}: exceeds requested maximum`);
  }
});

test("the story references precisely the 12 agreed capture keys", () => {
  assert.deepEqual(
    [...new Set(story.shots.map((shot) => shot.image))].sort(),
    [...captureKeys].sort(),
  );
});

test("localized captions fill every shot and stay within word limits", () => {
  assertLocalized(story.scopeBadge, "scope badge");
  assertLocalized(story.fixtureNotice, "fixture notice");
  assert.equal(story.scopeBadge.en, "Synthetic workflow demonstration");
  assert.equal(story.scopeBadge["zh-CN"], "合成资料流程演示");
  for (const shot of story.shots) {
    assertLocalized(shot.title, `${shot.id} title`);
    assert.ok(
      shot.title.en.trim().split(/\s+/).length <= 7,
      `${shot.id}: long title`,
    );
    assert.ok(shot.cues.length > 0, `${shot.id}: no captions`);
    let end = 0;
    for (const cue of shot.cues) {
      assert.equal(cue.from, end, `${shot.id}: caption gap or overlap`);
      assert.ok(Number.isFinite(cue.duration) && cue.duration > 0);
      assert.ok(Number.isInteger(cue.from * story.FPS));
      assert.ok(Number.isInteger(cue.duration * story.FPS));
      end += cue.duration;
      assert.ok(end <= shot.duration, `${shot.id}: caption outside shot`);
      assertLocalized(cue.text, `${shot.id} caption`);
      assert.ok(
        cue.text.en.trim().split(/\s+/).length <= 12,
        `${shot.id}: long caption`,
      );
    }
    assert.equal(end, shot.duration, `${shot.id}: incomplete caption coverage`);
    if (shot.source) assertLocalized(shot.source, `${shot.id} Source label`);
  }
});

test("both localized versions retain exact English quotes and Source identities", () => {
  assert.deepEqual({ ...story.evidenceQuotes }, quotes);
  const quoted = Array.from(story.shots).filter(
    (shot) => shot.quote !== undefined,
  );
  assert.deepEqual(
    quoted.map((shot) => shot.id),
    ["source", "reopen"],
  );
  for (const [index, expectedQuote, sourceNumber] of [
    [0, quotes.trustee, 2],
    [1, quotes.parent, 1],
  ]) {
    assert.equal(quoted[index].quote, expectedQuote);
    assert.equal(
      quoted[index].source.en,
      `Source ${sourceNumber} · exact quotation`,
    );
    assert.equal(
      quoted[index].source["zh-CN"],
      `来源 ${sourceNumber} · 原文引文`,
    );
  }
});

const pdfText = spawnSync("pdftotext", ["-v"], { encoding: "utf8" });
const pdfFixtures = [
  ["multiple-role-proposal.pdf", quotes.trustee],
  ["synthetic-proposal.pdf", quotes.parent],
];

test("the source fixture PDFs exist", () => {
  for (const [filename] of pdfFixtures) {
    const path = new URL(
      `../../../tests/fixtures/${filename}`,
      import.meta.url,
    );
    assert.equal(
      readFileSync(path).subarray(0, 5).toString(),
      "%PDF-",
      filename,
    );
  }
});

test(
  "PDF text independently contains each displayed quotation",
  {
    skip:
      pdfText.error?.code === "ENOENT"
        ? "pdftotext is unavailable; fixed quotation contract is checked separately"
        : false,
  },
  () => {
    assert.ifError(pdfText.error);
    assert.equal(pdfText.status, 0, pdfText.stderr);
    for (const [filename, quote] of pdfFixtures) {
      const path = fileURLToPath(
        new URL(`../../../tests/fixtures/${filename}`, import.meta.url),
      );
      const extracted = spawnSync("pdftotext", ["-layout", path, "-"], {
        encoding: "utf8",
      });
      assert.ifError(extracted.error);
      assert.equal(extracted.status, 0, extracted.stderr);
      assert.ok(
        extracted.stdout.includes(quote),
        `${filename}: quotation changed`,
      );
    }
  },
);

const cameraExamples = [
  [
    "small capture is centred",
    { scale: 0.5, x: 0, y: 1 },
    { scale: 0.5, left: 365, top: 135 },
  ],
  [
    "full view stays at its top edge",
    stage.fullView,
    { scale: 1, left: 5, top: 0 },
  ],
  [
    "zoom centres the requested point",
    { scale: 1.5, x: 0.5, y: 0.5 },
    { scale: 1.5, left: -355, top: -315 },
  ],
  [
    "overshooting target clamps to bottom right",
    { scale: 2, x: 1.5, y: 1.5 },
    { scale: 2, left: -1430, top: -1080 },
  ],
];

for (const [name, camera, expected] of cameraExamples) {
  test(`camera: ${name}`, () => {
    assert.deepEqual(
      { ...stage.projectCamera(Object.freeze({ ...camera })) },
      expected,
    );
  });
}

test("100 camera positions keep captures centred or covering the viewport", () => {
  const { width, viewportHeight, sourceWidth, sourceHeight } =
    stage.browserGeometry;
  assert.deepEqual(
    [width, viewportHeight, sourceWidth, sourceHeight],
    [1450, 720, 1440, 900],
  );
  let checked = 0;
  for (const scale of [0.25, 0.75, 1, 1.5, 2.5]) {
    for (const x of [-0.5, 0, 0.5, 1, 1.5]) {
      for (const y of [-0.5, 0, 0.5, 1.5]) {
        const camera = Object.freeze({ scale, x, y });
        const result = stage.projectCamera(camera);
        assert.equal(result.scale, scale);
        for (const [offset, imageSize, viewportSize] of [
          [result.left, sourceWidth * scale, width],
          [result.top, sourceHeight * scale, viewportHeight],
        ]) {
          assert.ok(Number.isFinite(offset), JSON.stringify(camera));
          if (imageSize <= viewportSize) {
            assert.equal(offset, (viewportSize - imageSize) / 2);
          } else {
            assert.ok(
              offset <= 0,
              `Exposed leading edge: ${JSON.stringify(camera)}`,
            );
            assert.ok(
              offset + imageSize >= viewportSize,
              `Exposed trailing edge: ${JSON.stringify(camera)}`,
            );
          }
        }
        assert.deepEqual(
          stage.projectCamera(camera),
          result,
          "Camera projection must be deterministic",
        );
        checked++;
      }
    }
  }
  assert.equal(checked, 100);
});

const motion = loadTypescript("../src/motion.ts", {
  remotion: { Easing, interpolate },
});
const pages = loadTypescript("../src/captured-pages.ts").capturedPages;

test("camera stays continuous through each connected review cut", () => {
  for (const locale of locales) {
    for (const [before, after] of [
      ["proposal", "relationship"],
      ["relationship", "source"],
      ["source", "confirm"],
      ["reopen", "close"],
      ["name", "documents"],
      ["documents", "analyse"],
    ]) {
      const a = story.shots.find((shot) => shot.id === before);
      const b = story.shots.find((shot) => shot.id === after);
      const heightA = pages[`${locale}-${a.image}`].height;
      const heightB = pages[`${locale}-${b.image}`].height;
      const end = motion.cameraAt(before, locale, a.duration, heightA);
      const start = motion.cameraAt(after, locale, 0, heightB);
      assert.equal(
        end.scale,
        start.scale,
        `${locale}: ${before}→${after} scale`,
      );
      assert.ok(Math.abs(end.x - start.x) < 1e-9);
      assert.ok(Math.abs(end.y * heightA - start.y * heightB) < 1e-6);
    }
  }
});

test("every cursor click is visible inside the filmed browser viewport", () => {
  for (const locale of locales) {
    for (const shot of story.shots) {
      const height = pages[`${locale}-${shot.image}`].height;
      for (let frame = 0; frame < shot.duration * story.FPS; frame++) {
        const time = frame / story.FPS;
        const camera = motion.cameraAt(shot.id, locale, time, height);
        const projection = stage.projectCamera(camera, height);
        assert.ok(Object.values(projection).every(Number.isFinite));
        const cursor = motion.cursorAt(shot.id, locale, time, height);
        if (!cursor || cursor.click <= 0) continue;
        const x = projection.left + cursor.x * 1440 * projection.scale;
        const y = projection.top + cursor.y * height * projection.scale;
        assert.ok(
          x >= 20 && x <= 1430 && y >= 20 && y <= 700,
          `${locale}/${shot.id}: click clipped at (${x},${y})`,
        );
      }
    }
  }
});

test("capture preflight verifies every original viewport and full page", async () => {
  const root = fileURLToPath(new URL("..", import.meta.url));
  const captures = await checkCaptures(root, story.shots);
  assert.equal(captures.length, 46);
  assert.equal(
    captures.filter((item) => item.file.endsWith("-page.png")).length,
    22,
  );
});

test("capture preflight rejects modified pixels and missing full pages", async () => {
  const temporary = await mkdtemp(
    path.join(tmpdir(), "pcg-demo-capture-test-"),
  );
  try {
    await cp(
      new URL("../public/captures", import.meta.url),
      path.join(temporary, "public/captures"),
      { recursive: true },
    );
    const fullPage = path.join(
      temporary,
      "public/captures/en-source-trustee-page.png",
    );
    const original = await readFile(fullPage);
    const changed = Buffer.from(original);
    changed[changed.length - 10] ^= 1;
    await writeFile(fullPage, changed);
    await assert.rejects(checkCaptures(temporary, story.shots), /hash differs/);
    await rm(fullPage);
    await assert.rejects(
      checkCaptures(temporary, story.shots),
      /en-source-trustee-page.png: missing/,
    );
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});
