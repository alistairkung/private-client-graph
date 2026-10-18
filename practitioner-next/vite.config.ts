import { defineConfig } from "vitest/config";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

// Local TLS preserves the existing __Host- session/CSRF cookie contract.
function localTls() {
  const directory = resolve(".local");
  mkdirSync(directory, { recursive: true });
  const key = resolve(directory, "key.pem");
  const cert = resolve(directory, "cert.pem");
  if (!existsSync(key) || !existsSync(cert)) {
    execFileSync(
      "openssl",
      [
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        key,
        "-out",
        cert,
        "-days",
        "30",
        "-subj",
        "/CN=localhost",
        "-addext",
        "subjectAltName=DNS:localhost,IP:127.0.0.1",
      ],
      { stdio: "ignore" },
    );
  }
  return { key: readFileSync(key), cert: readFileSync(cert) };
}

export default defineConfig(({ command, mode }) => ({
  server: {
    https: mode === "test" ? undefined : localTls(),
    proxy: Object.fromEntries(
      ["/api", "/auth", "/_development"].map((path) => [
        path,
        {
          target: process.env.PCG_BACKEND_URL ?? "http://127.0.0.1:8001",
          changeOrigin: false,
          xfwd: true,
        },
      ]),
    ),
  },
  preview: command === "serve" && mode !== "test" ? { https: localTls() } : {},
  test: {
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
    include: ["src/**/*.test.{ts,tsx}", "tests/**/*.test.{ts,tsx}"],
  },
}));
