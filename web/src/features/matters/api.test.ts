import { expect, test, vi } from "vitest";
import { getMatter, getMatters } from "./api";

test("collection translates an unreadable response into its feature message", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("<html>proxy diagnostics</html>"),
  );

  await expect(getMatters()).rejects.toThrow("Matters could not be loaded.");
  expect(fetcher).toHaveBeenCalledExactlyOnceWith("/api/matters", undefined);
});

test("detail returns null only for a 404 and preserves URL encoding", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ error: "missing" }), { status: 404 }),
  );

  await expect(getMatter("matter/42")).resolves.toBeNull();
  expect(fetcher).toHaveBeenCalledOnce();
  expect(fetcher.mock.calls[0][0]).toBe("/api/matters/matter%2F42");
});

test.each([
  new Response(JSON.stringify({ error: "unavailable" }), { status: 503 }),
  new Response("<html>proxy diagnostics</html>"),
])(
  "detail translates a failed response into its feature message",
  async (response) => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response);

    await expect(getMatter("matter-42")).rejects.toThrow(
      "Matter could not be loaded.",
    );
  },
);
