import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";

const locales = ["en", "zh-CN"];

export async function checkCaptures(root, shots) {
  const keys = [...new Set(shots.map((shot) => shot.image))];
  if (keys.length !== 12 || keys.some((key) => !/^[a-z][a-z-]*$/.test(key))) {
    throw new Error("The story must reference exactly 12 valid capture keys");
  }
  const manifest = JSON.parse(
    await readFile(path.join(root, "public/captures/manifest.json"), "utf8"),
  );
  const expected = locales.flatMap((locale) =>
    keys.flatMap((key) =>
      ["", ...(key === "ledger" ? [] : ["-page"])].map(
        (suffix) => `${locale}-${key}${suffix}.png`,
      ),
    ),
  );
  if (
    manifest.length !== expected.length ||
    new Set(manifest.map((item) => item.file)).size !== expected.length
  ) {
    throw new Error(
      "Capture manifest must contain the 46 unique authenticated application captures",
    );
  }
  const entries = await Promise.all(
    expected.map(async (file) => {
      const filename = `public/captures/${file}`;
      const recorded = manifest.find((item) => item.file === file);
      if (!recorded)
        return { error: `${filename}: missing from capture manifest` };
      try {
        const bytes = await readFile(path.join(root, filename));
        const png =
          bytes.length > 24 &&
          bytes
            .subarray(0, 8)
            .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
        const fullPage = file.endsWith("-page.png");
        if (
          !png ||
          bytes.readUInt32BE(16) !== 1440 ||
          bytes.readUInt32BE(20) !== recorded.height ||
          (!fullPage && recorded.height !== 900)
        ) {
          return {
            error: `${filename}: capture dimensions do not match the recorded browser image`,
          };
        }
        const sha256 = createHash("sha256").update(bytes).digest("hex");
        if (sha256 !== recorded.sha256)
          return { error: `${filename}: hash differs from capture manifest` };
        return {
          file: filename,
          locale: recorded.locale,
          key: recorded.key,
          width: 1440,
          height: recorded.height,
          bytes: bytes.length,
          sha256,
        };
      } catch (error) {
        if (error.code === "ENOENT") return { error: `${filename}: missing` };
        throw error;
      }
    }),
  );
  const failures = entries.filter((entry) => "error" in entry);
  if (failures.length) {
    throw new Error(
      `Capture preflight failed before bundling or rendering:\n${failures.map((entry) => `- ${entry.error}`).join("\n")}\nSupply the actual app captures; replacement images are not generated.`,
    );
  }
  return entries;
}
