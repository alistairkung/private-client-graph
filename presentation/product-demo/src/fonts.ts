import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Local, licensed fonts keep both language renders independent of the host OS.
const fonts = [
  ["Newsreader Display", "newsreader-display-latin-400-normal.woff2", "400"],
  ["Public Sans", "public-sans-latin-400-normal.woff2", "400"],
  ["Public Sans", "public-sans-latin-600-normal.woff2", "600"],
  ["Noto Serif SC", "noto-serif-sc-chinese-simplified-400-normal.woff2", "400"],
  ["Noto Sans SC", "noto-sans-sc-chinese-simplified-400-normal.woff2", "400"],
  ["Noto Sans SC", "noto-sans-sc-chinese-simplified-600-normal.woff2", "600"],
] as const;

for (const [family, file, weight] of fonts) {
  void loadFont({ family, url: staticFile(`fonts/${file}`), weight });
}
