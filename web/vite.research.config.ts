import { defineConfig } from "vitest/config";
export default defineConfig({
  root: "research",
  server: { host: "127.0.0.1", proxy: { "/api": "http://127.0.0.1:8080" } },
  build: { outDir: "../research-dist", emptyOutDir: true },
  test: {
    environment: "jsdom",
    setupFiles: "../src/test-setup.ts",
    include: ["**/*.test.{ts,tsx}"],
  },
});
