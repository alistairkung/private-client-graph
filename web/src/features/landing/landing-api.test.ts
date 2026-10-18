import { afterEach, describe, expect, it, vi } from "vitest";
import { getPublicExample } from "./landing-api";
afterEach(() => vi.unstubAllGlobals());
describe("public curated example boundary", () => {
  it("reads only the public curated GET endpoint and carries cancellation", async () => {
    const fixture = {
      result_kind: "curated_ideal_fixture",
      state: { entities: [], relationships: [], evidence: [], sources: [] },
    };
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => fixture });
    vi.stubGlobal("fetch", fetch);
    const controller = new AbortController();
    expect(await getPublicExample(controller.signal)).toBe(fixture);
    expect(fetch).toHaveBeenCalledExactlyOnceWith(
      "/api/showcase/cases/case-01",
      {
        signal: controller.signal,
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      },
    );
  });
  it("rejects analysis output and malformed or unsuccessful responses instead of inventing a diagram", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ result_kind: "live", state: {} }),
      })
      .mockResolvedValueOnce({ ok: false });
    vi.stubGlobal("fetch", fetch);
    await expect(
      getPublicExample(new AbortController().signal),
    ).rejects.toThrow("Example unavailable");
    await expect(
      getPublicExample(new AbortController().signal),
    ).rejects.toThrow("Example unavailable");
  });
});
