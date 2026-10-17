import { afterEach, expect, it, vi } from "vitest";
import { getPublicResearchSnapshot } from "./api";
afterEach(() => vi.unstubAllGlobals());
it("reads only the curated endpoint and refuses unavailable publications", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValue(new Response("unavailable", { status: 503 }));
  vi.stubGlobal("fetch", fetcher);
  await expect(getPublicResearchSnapshot()).rejects.toThrow();
  expect(fetcher).toHaveBeenCalledWith("/api/research-results", undefined);
});
it("rejects a response that is not the supported published artifact", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ schema_version: 2, runs: [], cases: [] }),
        ),
      ),
  );
  await expect(getPublicResearchSnapshot()).rejects.toThrow();
});
