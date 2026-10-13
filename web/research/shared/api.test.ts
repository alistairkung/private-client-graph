import { afterEach, expect, it, vi } from "vitest";
import { comparison, experiment, history } from "./api";
afterEach(() => vi.unstubAllGlobals());
it("uses read-only versioned routes and preserves filters and abort signals", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetch);
  const signal = new AbortController().signal;
  await history(new URLSearchParams({ q: "Case 03", offset: "25" }), signal);
  expect(fetch).toHaveBeenCalledWith(
    "/api/research/v1/experiments?q=Case+03&offset=25",
    { signal },
  );
  await experiment("a/b", signal);
  expect(fetch).toHaveBeenLastCalledWith("/api/research/v1/experiments/a%2Fb", {
    signal,
  });
  await comparison("left", "right", signal);
  expect(fetch).toHaveBeenLastCalledWith(
    "/api/research/v1/comparison?left=left&right=right",
    { signal },
  );
});
it("surfaces the backend read error without provider retry", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Artifacts changed." }),
    });
  vi.stubGlobal("fetch", fetch);
  await expect(experiment("id", new AbortController().signal)).rejects.toThrow(
    "Artifacts changed.",
  );
  expect(fetch).toHaveBeenCalledTimes(1);
});
